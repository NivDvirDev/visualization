"""
SYNESTHESIA 3D Mesh Renderer — ModernGL

Reproduces the MATLAB wireframe spiral tube visualization from
piperecord11_LE.m / piperecord11_LEF.m using modern OpenGL for
fast offline video export.

Architecture:
  - Headless ModernGL context → FBO → raw RGB piped to FFmpeg
  - Single spiral tube (cochlear tonotopy)
  - Wireframe-only rendering with interpolated vertex colors
  - Depth-tested alpha blending for clean wireframe occlusion
  - Traveling sine wave along z-axis, amplitude-modulated tube radius
  - Rotating camera with dynamic elevation (two-phase motion)

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
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_this_dir = os.path.dirname(os.path.abspath(__file__))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)

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
in vec3 in_normal;

uniform mat4 mvp;
uniform vec3 u_eye_pos;

out vec3 v_color;

void main() {
    gl_Position = mvp * vec4(in_position, 1.0);

    // Phong-like headlight lighting (light at camera position)
    vec3 N = normalize(in_normal);
    vec3 L = normalize(u_eye_pos - in_position);  // Light direction = toward camera
    float NdotL = max(dot(N, L), 0.0);

    // Ambient + diffuse (MATLAB AmbientStrength=0.4, rest is diffuse)
    float ambient = 0.4;
    float diffuse = 0.6 * NdotL;
    float lighting = ambient + diffuse;

    v_color = in_color * lighting;
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

    # Spiral geometry — loaded from MATLAB-derived spiral_freq_data.npz
    # Set to 0 to auto-load from file; otherwise uses this as subsample count
    num_freq_bins: int = 1000         # Subsampled from MATLAB's ~10K for performance
    inner_circle_points: int = 21     # Thin tube: ridge-like peaks, not bloated spheres
    use_spiral_freqs: bool = True     # Use MATLAB spiral frequencies instead of logspace

    # Tube parameters (piperecord11_LE.m line 97)
    tube_base: float = 0.001          # Very thin when quiet (single-pixel lines)
    tube_amp_scale: float = 0.004     # Strong deformation when active

    # Amplitude normalization
    amp_target: float = 110.0

    # Wave parameters (piperecord11_LE.m lines 132-154)
    wave_lambda: float = 4.8701
    wave_v0: float = 4.7124
    wave_speed: float = 70.0          # speed = 70 * dFrame

    # Z offset (piperecord11_LE.m line 100)
    z_offset: float = -40.0

    # Rendering
    edge_alpha: float = 1.0           # MATLAB EdgeAlpha=1
    line_width: float = 1.5           # Slightly thicker for visibility (YouTube look)
    background_color: tuple = (0.0, 0.0, 0.0)  # Pure black

    # Wireframe density — 1 = full MATLAB density
    theta_line_step: int = 1

    # Camera initial values — pulled back to show full spiral like YouTube
    camera_fov: float = 35.0          # Moderate FOV
    camera_distance: float = 160.0    # Pulled back to match YouTube framing

    # Camera animation (piperecord11_LE.m SetCameraMotion)
    # Lowered from MATLAB values for more edge-on YouTube look
    cam_el_max: float = 20.0
    cam_el_min: float = 5.95
    cam_del: float = 0.05             # Elevation step per frame
    cam_daz: float = 0.3              # Azimuth rotation per frame

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
    s_norm = np.linalg.norm(s)
    if s_norm < 1e-8:
        # Fallback: pick a different up vector if camera is looking straight up/down
        up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        s = np.cross(f, up)
        s_norm = np.linalg.norm(s)
    s = s / s_norm
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

    Reproduces the MATLAB single spiral tube visualization with:
    - Single spiral tube with amplitude-driven deformation
    - Wireframe rendering with per-vertex rainbow colors
    - Traveling sine wave along z-axis
    - Rotating camera with two-phase elevation animation
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

        # Standard alpha blending
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

        # Create FBO for offscreen rendering
        color_attachment = self.ctx.texture((cfg.width, cfg.height), 4)
        depth_attachment = self.ctx.depth_renderbuffer((cfg.width, cfg.height))
        self.fbo = self.ctx.framebuffer(
            color_attachments=[color_attachment],
            depth_attachment=depth_attachment,
        )

        # Line width
        self.ctx.line_width = cfg.line_width

        # Compile shaders
        self.prog = self.ctx.program(
            vertex_shader=VERTEX_SHADER,
            fragment_shader=FRAGMENT_SHADER,
        )
        self.prog['u_alpha'].value = cfg.edge_alpha

        # Load spiral geometry from MATLAB-derived data or use linspace fallback
        if cfg.use_spiral_freqs:
            spiral_data_path = os.path.join(os.path.dirname(__file__),
                                            'spiral_freq_data.npz')
            if os.path.exists(spiral_data_path):
                data = np.load(spiral_data_path)
                full_theta = data['theta']
                full_freqs = data['frequencies']
                # Subsample to requested bin count
                n_full = len(full_theta)
                indices = np.linspace(0, n_full - 1, cfg.num_freq_bins).astype(int)
                self.theta = full_theta[indices].astype(np.float32)
                self.spiral_frequencies = full_freqs[indices].astype(np.float32)
                print(f"Loaded MATLAB spiral: {cfg.num_freq_bins} bins, "
                      f"{self.spiral_frequencies[0]:.1f}-{self.spiral_frequencies[-1]:.0f} Hz, "
                      f"theta {self.theta[0]:.2f}-{self.theta[-1]:.2f}")
            else:
                print(f"Warning: spiral_freq_data.npz not found, using linspace fallback")
                self.theta = np.linspace(0, 8.0 * 2 * np.pi,
                                         cfg.num_freq_bins).astype(np.float32)
                self.spiral_frequencies = np.logspace(
                    np.log10(20), np.log10(8000), cfg.num_freq_bins).astype(np.float32)
        else:
            self.theta = np.linspace(0, 8.0 * 2 * np.pi,
                                     cfg.num_freq_bins).astype(np.float32)
            self.spiral_frequencies = np.logspace(
                np.log10(20), np.log10(8000), cfg.num_freq_bins).astype(np.float32)

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
        self.wave_u_arg = (self.u - self.u_min) * (cfg.wave_lambda / self.u_range)

        # flip(u) — MATLAB reverses theta so low frequencies get larger weight
        # Cap max value to prevent disproportionate outer-turn blobs
        raw_flip = np.flip(self.u, axis=1)
        self.flip_u = np.minimum(raw_flip, 20.0)  # Cap at 20 (was up to ~50)

        # Colormap
        # Colormap: hue derived from spiral angle (octave-aligned)
        self.colormap = create_myjet_colormap(cfg.num_freq_bins, theta=self.theta)

        # Precompute wireframe topology (constant across frames)
        line_indices = self._build_line_indices()
        self.num_indices = len(line_indices)
        self.ibo = self.ctx.buffer(line_indices.tobytes())

        # Allocate vertex buffer (single spiral: pos + color + normal = 9 floats)
        num_verts = cfg.inner_circle_points * cfg.num_freq_bins
        self.vbo = self.ctx.buffer(reserve=num_verts * 9 * 4)

        # Create VAO with normal attribute for Phong lighting
        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.vbo, '3f 3f 3f', 'in_position', 'in_color', 'in_normal')],
            index_buffer=self.ibo,
        )

        # Camera state (initialized for Phase 1)
        self.az = 270.0
        self.el = cfg.cam_el_max - 0.90 + cfg.cam_del  # ~30.10°
        self.del_el = cfg.cam_del

        # Upload initial MVP
        self._upload_mvp_dynamic(self.az, self.el)

        # Amplitude scale factor (set during render_video)
        self._amp_scale = 1.0

    def _build_line_indices(self) -> np.ndarray:
        """Build wireframe line indices for a single mesh spiral."""
        cfg = self.config
        rows = cfg.inner_circle_points
        cols = cfg.num_freq_bins
        step = cfg.theta_line_step

        indices = []

        # Horizontal lines (along theta / frequency axis)
        for i in range(rows):
            for j in range(0, cols - 1, step):
                j_end = min(j + step, cols - 1)
                idx0 = i * cols + j
                idx1 = i * cols + j_end
                indices.append(idx0)
                indices.append(idx1)

        # Vertical lines (around tube circumference)
        for j in range(0, cols, step):
            for i in range(rows - 1):
                idx = i * cols + j
                indices.append(idx)
                indices.append(idx + cols)

        return np.array(indices, dtype=np.int32)

    def _upload_mvp_dynamic(self, az_deg: float, el_deg: float,
                            target_z: float = -5.0):
        """
        Compute and upload MVP matrix matching MATLAB's view() + camera zoom.

        Port of MATLAB SetCameraMotion camera position logic.
        """
        cfg = self.config

        az = np.radians(az_deg)
        el = np.radians(el_deg)

        # Camera target (MATLAB: [-1 -1 target_z])
        center = np.array([-1.0, -1.0, target_z], dtype=np.float32)

        # Eye position: spherical coordinates relative to origin
        dist = cfg.camera_distance
        eye = np.array([
            dist * np.cos(el) * np.cos(az),
            dist * np.cos(el) * np.sin(az),
            dist * np.sin(el),
        ], dtype=np.float32)

        # Offset eye relative to target
        eye = eye + center

        # MATLAB zoom: newcp = cpos - factor*(cpos - ctarg)
        # Tuned factor for better framing at all elevation angles
        factor = 0.35 - 0.15 * np.sin(np.radians(el_deg))
        eye = eye - factor * (eye - center)

        up = np.array([0.0, 0.0, 1.0], dtype=np.float32)

        fov = np.radians(cfg.camera_fov)
        aspect = cfg.width / cfg.height
        proj = _perspective(fov, aspect, 1.0, 2000.0)
        view = _look_at(eye, center, up)
        mvp = (proj @ view).astype(np.float32)
        self.prog['mvp'].write(mvp.tobytes(order='F'))

        # Upload eye position for Phong headlight
        self.prog['u_eye_pos'].value = tuple(eye.tolist())

    def _update_camera(self, frame_idx: int, total_frames: int):
        """
        Port of MATLAB SetCameraMotion — two-phase camera animation.

        Phase 1 (first half): elevation ~30° constant, azimuth rotates
        Phase 2 (second half): elevation oscillates between el_min and el_max
        """
        cfg = self.config
        half = total_frames // 2

        if frame_idx >= half:
            # Phase 2: elevation oscillates with bounce
            if self.el >= cfg.cam_el_max:
                self.del_el = -abs(self.del_el)
            if self.el <= cfg.cam_el_min:
                self.del_el = abs(self.del_el)
            self.el += self.del_el * np.cos(np.pi * self.el / 180.0)
            self.az -= cfg.cam_daz
        else:
            # Phase 1: elevation roughly constant, azimuth rotates
            self.az -= cfg.cam_daz
            self.el = cfg.cam_el_max - 0.90 + self.del_el

        # Dynamic camera target Z (MATLAB: -5 - 30*teta_0to1)
        el_range = cfg.cam_el_max - cfg.cam_el_min
        teta_0to1 = (self.el - (cfg.cam_el_min + self.del_el)) / el_range
        teta_0to1 = np.clip(teta_0to1, 0.0, 1.0)
        target_z = -15.0 - 20.0 * teta_0to1

        # Upload new MVP
        self._upload_mvp_dynamic(self.az, self.el, target_z)

    def _compute_frame_vertices(self,
                                amplitude: np.ndarray,
                                flow_amp_value: float,
                                t: float,
                                el_deg: float) -> np.ndarray:
        """
        Compute vertex positions and colors for one frame (single spiral).
        Port of piperecord11_LE.m lines 94-106.
        """
        cfg = self.config
        rows = cfg.inner_circle_points
        cols = cfg.num_freq_bins
        dFrame = 1.0 / cfg.fps

        # Normalize amplitude to MATLAB-compatible range
        amp_scaled = amplitude * self._amp_scale

        # Light smoothing — enough to form ridges but keep distinct peaks separated
        kernel_size = 7
        kernel = np.ones(kernel_size) / kernel_size
        amp_smooth = np.convolve(amp_scaled, kernel, mode='same')

        # Tube radius modulated by amplitude (MATLAB: tsul=flip(u).*(0.0001+0.0015*amp'))
        amp_row = amp_smooth[np.newaxis, :]  # [1, cols]
        tsul = self.flip_u * (cfg.tube_base + cfg.tube_amp_scale * amp_row)

        # Tube cross-section (MATLAB: xx=(mtheta+(tsul).*cos(v)))
        xx = self.theta[np.newaxis, :] + tsul * self.cos_v

        # Traveling wave phase (MATLAB SetRadialWave)
        T = 100.0 * dFrame
        f_wave = 1.0 / T
        omega = 2.0 * np.pi * f_wave
        speed = cfg.wave_speed * dFrame
        Xt = speed * flow_amp_value
        phaz = omega * (t + Xt) * (-1.0)

        # Z coordinate with traveling wave (MATLAB line 100)
        # Rectified wave for upward-only peaks; scale tube Z-contribution
        # down to create taller/narrower peaks (less blob, more ridge)
        wave = np.sin(phaz + self.wave_u_arg)
        wave_rectified = np.maximum(wave, 0.0)
        el_rad = np.radians(el_deg)
        zz = (2.0 * wave_rectified
              + tsul * self.sin_v * 0.5   # Compressed Z: flatter cross-section = ridge-like
              + cfg.z_offset
              + 10.0 * np.cos(el_rad))

        # Colors
        colors = modulate_colors(self.colormap, amp_scaled, self.theta)
        colors_full = np.broadcast_to(colors[np.newaxis, :, :],
                                       (rows, cols, 3)).copy()

        # Single spiral (MATLAB: h3.XData=xx.*cos(u+pi/2), h3.YData=yy.*sin(u+pi/2))
        x1 = xx * self.cos_u_p
        y1 = xx * self.sin_u_p

        # Compute surface normals for Phong lighting
        # Normal points outward from tube center: (cos(v)*cos(u+pi/2), cos(v)*sin(u+pi/2), sin(v))
        nx = self.cos_v * self.cos_u_p
        ny = self.cos_v * self.sin_u_p
        nz = self.sin_v
        # Normalize
        n_len = np.sqrt(nx*nx + ny*ny + nz*nz) + 1e-8
        nx /= n_len
        ny /= n_len
        nz /= n_len

        # Pack vertex buffer (single spiral: pos + color + normal = 9 floats)
        n = rows * cols
        verts = np.empty((n, 9), dtype=np.float32)

        verts[:, 0] = x1.ravel()
        verts[:, 1] = y1.ravel()
        verts[:, 2] = zz.ravel()
        verts[:, 3:6] = colors_full.reshape(-1, 3)
        verts[:, 6] = nx.ravel()
        verts[:, 7] = ny.ravel()
        verts[:, 8] = nz.ravel()

        return verts

    def render_frame(self,
                     amplitude: np.ndarray,
                     flow_amp_value: float,
                     t: float,
                     el_deg: float = 30.0) -> np.ndarray:
        """
        Render a single frame to a numpy RGB array.

        Args:
            amplitude: [num_freq_bins] amplitude values
            flow_amp_value: energy envelope value for this frame
            t: current time in seconds
            el_deg: current camera elevation in degrees

        Returns:
            [height, width, 3] uint8 RGB array
        """
        vertex_data = self._compute_frame_vertices(amplitude, flow_amp_value, t, el_deg)
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

        # Post-processing bloom: downsample, blur, upsample for fast glow
        h, w = frame.shape[:2]
        # Downsample 4x for fast blur
        small = frame[::4, ::4].astype(np.float32)
        bright = np.maximum(small - 60.0, 0.0)
        # Simple box blur (fast, ~2px at full res = ~8px effective)
        from scipy.ndimage import uniform_filter
        glow_small = uniform_filter(bright, size=(3, 4, 1))
        # Upsample back with nearest-neighbor
        glow = np.repeat(np.repeat(glow_small, 4, axis=0), 4, axis=1)
        glow = glow[:h, :w]  # Trim to exact size
        result = np.clip(frame.astype(np.float32) + glow * 0.6, 0, 255).astype(np.uint8)
        return result

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

        # Stage 1: Analyze audio using spiral frequencies
        print("Analyzing audio...")
        audio_config = AudioAnalysisConfig(
            frame_rate=cfg.fps,
            num_frequency_bins=len(self.spiral_frequencies),
            custom_frequencies=self.spiral_frequencies,
        )
        analyzer = AudioAnalyzer(audio_config)
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

        # Reset camera state for this render
        self.az = 270.0
        self.el = cfg.cam_el_max - 0.90 + cfg.cam_del
        self.del_el = cfg.cam_del

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

        # Stage 5: Render loop with camera animation
        print("Rendering 3D mesh frames...")
        t = 0.0
        t0 = _time.monotonic()
        try:
            for frame_idx in range(total_frames):
                # Update camera (rotates azimuth, oscillates elevation)
                self._update_camera(frame_idx, total_frames)

                amplitude = analysis.amplitude_data[:, frame_idx]
                fav = flow_amp_scaled[min(frame_idx, len(flow_amp_scaled) - 1)]

                frame = self.render_frame(amplitude, fav, t, self.el)
                proc.stdin.write(frame.tobytes())

                t += dFrame

                if frame_idx % 100 == 0:
                    elapsed = _time.monotonic() - t0
                    fps = (frame_idx + 1) / elapsed if elapsed > 0 else 0
                    pct = 100 * frame_idx / total_frames
                    print(f"  Frame {frame_idx}/{total_frames} "
                          f"({pct:.1f}%) — {fps:.1f} fps "
                          f"az={self.az:.1f} el={self.el:.1f}")

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
