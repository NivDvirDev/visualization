"""
SYNESTHESIA 3D Mesh Renderer — ModernGL

Reproduces the MATLAB wireframe double-helix visualization from
piperecord11_LE-2C.m using modern OpenGL for fast offline video export.

Architecture:
  - Headless ModernGL context → FBO → raw RGB piped to FFmpeg
  - Two mirrored mesh spirals (DNA-like double helix)
  - Wireframe-only rendering with interpolated vertex colors
  - Depth-tested alpha blending for clean wireframe occlusion
  - Traveling sine wave along z-axis, amplitude-modulated tube radius

Performance target: 60s @ 1080p60 in ~30 seconds.
"""

import os
import numpy as np
import subprocess
import sys
import time as _time
from dataclasses import dataclass
from typing import Optional, Callable

# Ensure parent directory (synesthesia2/) is on sys.path for shared modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import moderngl
    HAS_MODERNGL = True
except ImportError:
    HAS_MODERNGL = False

from audio_analyzer import AudioAnalyzer, AudioAnalysisConfig, AnalysisResult
from mesh_colormap import create_myjet_colormap, modulate_colors
from flow_amp import compute_flow_amp


# ---------------------------------------------------------------------------
# GLSL Shaders
# ---------------------------------------------------------------------------

VERTEX_SHADER = """
#version 330

in vec3 in_position;
in vec3 in_color;

uniform mat4 mvp;

out vec3 v_color;

void main() {
    gl_Position = mvp * vec4(in_position, 1.0);
    v_color = in_color;
}
"""

FRAGMENT_SHADER = """
#version 330

in vec3 v_color;

uniform float u_alpha;

out vec4 fragColor;

void main() {
    fragColor = vec4(v_color, u_alpha);
}
"""


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class MeshRenderConfig:
    """Configuration for the 3D mesh renderer."""
    # Output
    width: int = 1920
    height: int = 1080
    fps: int = 60

    # Spiral geometry (from MATLAB)
    num_freq_bins: int = 381
    inner_circle_points: int = 31     # Reduced from MATLAB's 61 for cleaner wireframe
    spiral_turns: float = 8.0         # ~8 turns matches MATLAB theta range

    # Tube parameters (piperecord11 lines 67, 191)
    tube_base: float = 0.01
    tube_amp_scale: float = 0.0015

    # Amplitude normalization — Python AudioAnalyzer produces values ~0-100K,
    # but the MATLAB tube formula expects ~0-100.  We rescale so that the
    # 99.5th-percentile amplitude maps to this target.
    amp_target: float = 80.0

    # Wave parameters (piperecord11 lines 201-226)
    wave_lambda: float = 4.8701
    wave_v0: float = 4.7124
    wave_speed: float = 70.0          # speed = 70 * dFrame

    # Double helix offset (line 234)
    dpol: float = 62.83

    # Z offset (line 226)
    z_offset: float = -40.0

    # Rendering
    edge_alpha: float = 1.0           # Fully opaque — MATLAB uses 0.5 but has Phong lighting boost
    line_width: float = 1.5           # Slightly thicker than default 1.0 for visibility
    background_color: tuple = (0.01, 0.01, 0.03)

    # Wireframe decimation — draw every Nth line along theta axis.
    # 1 = full density (MATLAB default), 2 = half, 3 = third, etc.
    theta_line_step: int = 2

    # Camera (lines 159-162, 278-279)
    camera_azimuth: float = 270.0     # degrees
    camera_elevation: float = 88.0    # degrees — near top-down (MATLAB uses 90)
    camera_fov: float = 50.0          # degrees — wider than default 30 to fit both spirals
    camera_distance: float = 350.0
    camera_target: tuple = (0.0, 0.0, -25.0)
    camera_zoom: float = 0.55

    # Video encoding
    video_crf: int = 18
    video_preset: str = "slow"


# ---------------------------------------------------------------------------
# Matrix math (no pyrr dependency)
# ---------------------------------------------------------------------------

def _perspective(fov_rad: float, aspect: float, near: float, far: float) -> np.ndarray:
    f = 1.0 / np.tan(fov_rad / 2.0)
    m = np.zeros((4, 4), dtype=np.float32)
    m[0, 0] = f / aspect
    m[1, 1] = f
    m[2, 2] = (far + near) / (near - far)
    m[2, 3] = 2.0 * far * near / (near - far)
    m[3, 2] = -1.0
    return m


def _look_at(eye: np.ndarray, center: np.ndarray, up: np.ndarray) -> np.ndarray:
    f = center - eye
    f = f / np.linalg.norm(f)
    s = np.cross(f, up)
    s = s / np.linalg.norm(s)
    u = np.cross(s, f)

    m = np.eye(4, dtype=np.float32)
    m[0, :3] = s
    m[1, :3] = u
    m[2, :3] = -f
    m[0, 3] = -np.dot(s, eye)
    m[1, 3] = -np.dot(u, eye)
    m[2, 3] = np.dot(f, eye)
    return m


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

class MeshRenderer:
    """
    ModernGL-based 3D wireframe mesh renderer.

    Reproduces the MATLAB double-helix spiral visualization with:
    - Two mirrored mesh spirals (h3 + h4)
    - Wireframe rendering with per-vertex colors
    - Traveling sine wave along z-axis
    - Amplitude-modulated tube radius
    - Direct FFmpeg pipe for video output
    """

    def __init__(self, config: Optional[MeshRenderConfig] = None):
        if not HAS_MODERNGL:
            raise ImportError(
                "ModernGL required for 3D mesh rendering. "
                "Install with: pip install moderngl"
            )

        self.config = config or MeshRenderConfig()
        cfg = self.config

        # Create headless OpenGL context
        try:
            self.ctx = moderngl.create_standalone_context()
        except Exception as e:
            raise RuntimeError(
                f"Failed to create OpenGL context: {e}\n"
                "On headless systems, try: pip install moderngl[headless]"
            ) from e

        # Depth testing for proper wireframe occlusion
        self.ctx.enable(moderngl.DEPTH_TEST)

        # Standard alpha blending (not additive — avoids nebula look)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

        # Create FBO for offscreen rendering
        color_attachment = self.ctx.texture((cfg.width, cfg.height), 4)
        depth_attachment = self.ctx.depth_renderbuffer((cfg.width, cfg.height))
        self.fbo = self.ctx.framebuffer(
            color_attachments=[color_attachment],
            depth_attachment=depth_attachment,
        )

        # Line width (thicker = more visible wireframe)
        self.ctx.line_width = cfg.line_width

        # Compile shaders
        self.prog = self.ctx.program(
            vertex_shader=VERTEX_SHADER,
            fragment_shader=FRAGMENT_SHADER,
        )
        self.prog['u_alpha'].value = cfg.edge_alpha

        # Precompute spiral theta and inner circle R
        self.theta = np.linspace(0, cfg.spiral_turns * 2 * np.pi,
                                 cfg.num_freq_bins).astype(np.float32)
        self.R = np.linspace(0, 2 * np.pi,
                             cfg.inner_circle_points).astype(np.float32)

        # Meshgrid: u[i,j] = theta[j], v[i,j] = R[i]
        self.u, self.v = np.meshgrid(self.theta, self.R)
        self.u_min = float(np.min(self.u))
        self.u_range = float(np.max(self.u) - self.u_min)

        # Precompute trig tables (avoid recomputing every frame)
        self.cos_v = np.cos(self.v)
        self.sin_v = np.sin(self.v)
        self.cos_u_p = np.cos(self.u + np.pi / 2)
        self.sin_u_p = np.sin(self.u + np.pi / 2)
        self.cos_u_m = np.cos(self.u - np.pi / 2)
        self.sin_u_m = np.sin(self.u - np.pi / 2)
        self.wave_u_arg = (self.u - self.u_min) * (cfg.wave_lambda / self.u_range)

        # Colormap
        self.colormap = create_myjet_colormap(cfg.num_freq_bins)

        # Precompute wireframe topology (constant across frames)
        line_indices = self._build_line_indices()
        self.num_indices = len(line_indices)
        self.ibo = self.ctx.buffer(line_indices.tobytes())

        # Allocate vertex buffer (updated each frame)
        num_verts = 2 * cfg.inner_circle_points * cfg.num_freq_bins
        self.vbo = self.ctx.buffer(reserve=num_verts * 6 * 4)

        # Create VAO
        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.vbo, '3f 3f', 'in_position', 'in_color')],
            index_buffer=self.ibo,
        )

        # Compute and upload MVP matrix
        self._upload_mvp()

        # Amplitude scale factor (set during render_video)
        self._amp_scale = 1.0

    def _build_line_indices(self) -> np.ndarray:
        """Build decimated wireframe line indices for two mesh spirals."""
        cfg = self.config
        rows = cfg.inner_circle_points
        cols = cfg.num_freq_bins
        step = cfg.theta_line_step

        indices = []
        for spiral in range(2):
            offset = spiral * rows * cols

            # Horizontal lines (along theta / frequency axis)
            # Draw every row but every step-th column connection
            for i in range(rows):
                for j in range(0, cols - 1, step):
                    j_end = min(j + step, cols - 1)
                    idx0 = offset + i * cols + j
                    idx1 = offset + i * cols + j_end
                    indices.append(idx0)
                    indices.append(idx1)

            # Vertical lines (around tube circumference)
            # Draw at every step-th theta position
            for j in range(0, cols, step):
                for i in range(rows - 1):
                    idx = offset + i * cols + j
                    indices.append(idx)
                    indices.append(idx + cols)

        return np.array(indices, dtype=np.int32)

    def _upload_mvp(self):
        """Compute and upload the model-view-projection matrix."""
        cfg = self.config

        fov = np.radians(cfg.camera_fov)
        aspect = cfg.width / cfg.height
        proj = _perspective(fov, aspect, 1.0, 1000.0)

        az = np.radians(cfg.camera_azimuth)
        el = np.radians(cfg.camera_elevation)
        dist = cfg.camera_distance

        eye = np.array([
            dist * np.cos(el) * np.cos(az),
            dist * np.cos(el) * np.sin(az),
            dist * np.sin(el),
        ], dtype=np.float32)

        center = np.array(cfg.camera_target, dtype=np.float32)
        up = np.array([0.0, 0.0, 1.0], dtype=np.float32)

        # Zoom
        eye = eye - (1.0 - cfg.camera_zoom) * (eye - center)

        view = _look_at(eye, center, up)
        mvp = (proj @ view).astype(np.float32)
        self.prog['mvp'].write(mvp.tobytes(order='F'))

    def _compute_frame_vertices(self,
                                amplitude: np.ndarray,
                                flow_amp_value: float,
                                t: float) -> np.ndarray:
        """
        Compute vertex positions and colors for one frame (both spirals).
        Port of piperecord11_LE-2C.m lines 191-245.
        """
        cfg = self.config
        rows = cfg.inner_circle_points
        cols = cfg.num_freq_bins
        dFrame = 1.0 / cfg.fps

        # Normalize amplitude to MATLAB-compatible range
        amp_scaled = amplitude * self._amp_scale

        # Tube radius modulated by amplitude
        amp_row = amp_scaled[np.newaxis, :]  # [1, cols]
        tsul = self.u * (cfg.tube_base + cfg.tube_amp_scale * amp_row)

        # Tube cross-section
        xx = self.theta[np.newaxis, :] + tsul * self.cos_v

        # Traveling wave phase
        T = 100.0 * dFrame
        f_wave = 1.0 / T
        omega = 2.0 * np.pi * f_wave
        speed = cfg.wave_speed * dFrame
        Xt = speed * flow_amp_value
        phaz = omega * (t + Xt) * (-1.0)

        el_rad = np.radians(cfg.camera_elevation)
        zz = (2.0 * np.sin(phaz + self.wave_u_arg)
              + tsul * self.sin_v
              + cfg.z_offset
              + 10.0 * np.cos(el_rad))

        # Colors
        colors = modulate_colors(self.colormap, amp_scaled, self.theta)
        colors_full = np.broadcast_to(colors[np.newaxis, :, :],
                                       (rows, cols, 3)).copy()

        # Spiral 1 (h3)
        x1 = xx * self.cos_u_p
        y1 = xx * self.sin_u_p - cfg.dpol

        # Spiral 2 (h4)
        x2 = xx * self.cos_u_m
        y2 = xx * self.sin_u_m + cfg.dpol

        # Pack vertex buffer
        n = rows * cols
        verts = np.empty((2 * n, 6), dtype=np.float32)

        verts[:n, 0] = x1.ravel()
        verts[:n, 1] = y1.ravel()
        verts[:n, 2] = zz.ravel()
        verts[:n, 3:] = colors_full.reshape(-1, 3)

        verts[n:, 0] = x2.ravel()
        verts[n:, 1] = y2.ravel()
        verts[n:, 2] = zz.ravel()
        verts[n:, 3:] = colors_full.reshape(-1, 3)

        return verts

    def render_frame(self,
                     amplitude: np.ndarray,
                     flow_amp_value: float,
                     t: float) -> np.ndarray:
        """
        Render a single frame to a numpy RGB array.

        Args:
            amplitude: [num_freq_bins] amplitude values
            flow_amp_value: energy envelope value for this frame
            t: current time in seconds

        Returns:
            [height, width, 3] uint8 RGB array
        """
        vertex_data = self._compute_frame_vertices(amplitude, flow_amp_value, t)
        self.vbo.write(vertex_data.tobytes())

        self.fbo.use()
        bg = self.config.background_color
        self.ctx.clear(bg[0], bg[1], bg[2], 1.0)
        self.vao.render(moderngl.LINES)

        # Read framebuffer (bottom-up) and flip to top-down
        data = self.fbo.color_attachments[0].read()
        frame = np.frombuffer(data, dtype=np.uint8).reshape(
            self.config.height, self.config.width, 4
        )
        frame = frame[::-1, :, :3].copy()  # Flip Y, drop alpha
        return frame

    def render_video(self,
                     audio_path: str,
                     output_path: str,
                     start_time: float = 0,
                     duration: Optional[float] = None,
                     progress_callback: Optional[Callable] = None) -> str:
        """
        Full pipeline: analyze audio -> render all frames -> encode video.

        Pipes raw RGB frames directly to FFmpeg stdin.
        """
        cfg = self.config
        dFrame = 1.0 / cfg.fps

        # Stage 1: Analyze audio
        print("Analyzing audio...")
        analyzer = AudioAnalyzer(AudioAnalysisConfig(frame_rate=cfg.fps))
        analysis = analyzer.analyze(audio_path, start_time=start_time, duration=duration)
        total_frames = analysis.total_frames
        print(f"Total frames: {total_frames}")

        # Stage 2: Normalize amplitude to MATLAB-compatible range
        amp_p99 = np.percentile(analysis.amplitude_data, 99.5) + 1e-6
        self._amp_scale = cfg.amp_target / amp_p99
        print(f"Amplitude scale: {self._amp_scale:.6f} "
              f"(p99.5={amp_p99:.0f} -> target={cfg.amp_target})")

        # Stage 3: Compute flow amplitude envelope
        print("Computing energy envelope...")
        flow_amp = compute_flow_amp(analysis.amplitude_data)
        flow_amp_scaled = 0.5 + 2.0 * flow_amp

        # Stage 4: Start FFmpeg encoder
        actual_duration = duration or analysis.duration_seconds
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-s', f'{cfg.width}x{cfg.height}',
            '-pix_fmt', 'rgb24',
            '-r', str(cfg.fps),
            '-i', '-',
            '-ss', str(start_time),
            '-t', str(actual_duration),
            '-i', audio_path,
            '-c:v', 'libx264',
            '-preset', cfg.video_preset,
            '-crf', str(cfg.video_crf),
            '-pix_fmt', 'yuv420p',
            '-c:a', 'aac',
            '-b:a', '320k',
            '-shortest',
            output_path,
        ]

        print("Starting FFmpeg encoder...")
        proc = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Stage 5: Render loop
        print("Rendering 3D mesh frames...")
        t = 0.0
        t0 = _time.monotonic()
        try:
            for frame_idx in range(total_frames):
                amplitude = analysis.amplitude_data[:, frame_idx]
                fav = flow_amp_scaled[min(frame_idx, len(flow_amp_scaled) - 1)]

                frame = self.render_frame(amplitude, fav, t)
                proc.stdin.write(frame.tobytes())

                t += dFrame

                if frame_idx % 100 == 0:
                    elapsed = _time.monotonic() - t0
                    fps = (frame_idx + 1) / elapsed if elapsed > 0 else 0
                    pct = 100 * frame_idx / total_frames
                    print(f"  Frame {frame_idx}/{total_frames} "
                          f"({pct:.1f}%) — {fps:.1f} fps")

                if progress_callback:
                    progress_callback(frame_idx, total_frames, "Rendering 3D mesh...")

        except BrokenPipeError:
            stderr = proc.stderr.read().decode()
            raise RuntimeError(f"FFmpeg pipe broke: {stderr}")

        proc.stdin.close()
        proc.wait()

        elapsed = _time.monotonic() - t0
        print(f"Render: {total_frames} frames in {elapsed:.1f}s "
              f"({total_frames/elapsed:.1f} fps)")

        if proc.returncode != 0:
            stderr = proc.stderr.read().decode()
            raise RuntimeError(f"FFmpeg failed (exit {proc.returncode}): {stderr}")

        print(f"Video saved: {output_path}")
        return output_path

    def cleanup(self):
        """Release GPU resources."""
        self.vbo.release()
        self.ibo.release()
        self.vao.release()
        self.fbo.release()
        self.prog.release()
        self.ctx.release()


# ---------------------------------------------------------------------------
# Standalone CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="SYNESTHESIA 3D Mesh Renderer (ModernGL)"
    )
    parser.add_argument("audio_file", help="Path to audio file")
    parser.add_argument("-o", "--output", default="output_mesh3d.mp4",
                        help="Output video path")
    parser.add_argument("-s", "--start", type=float, default=0,
                        help="Start time (seconds)")
    parser.add_argument("-d", "--duration", type=float,
                        help="Duration (seconds)")
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--fps", type=int, default=60)
    parser.add_argument("--crf", type=int, default=18)
    parser.add_argument("--preset", default="slow")

    args = parser.parse_args()

    config = MeshRenderConfig(
        width=args.width,
        height=args.height,
        fps=args.fps,
        video_crf=args.crf,
        video_preset=args.preset,
    )

    renderer = MeshRenderer(config)
    try:
        renderer.render_video(
            audio_path=args.audio_file,
            output_path=args.output,
            start_time=args.start,
            duration=args.duration,
        )
    finally:
        renderer.cleanup()
