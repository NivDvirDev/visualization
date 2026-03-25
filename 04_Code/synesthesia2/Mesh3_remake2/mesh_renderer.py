"""
SYNESTHESIA 3D Mesh Renderer v2 — ModernGL

Port of piperecord11_LEF.m (latest SSD version) — the exact code that
produces the YouTube channel videos.

Key differences from Mesh3_remake1:
  - Spiral uses mRadius (=angle) for XY positions
  - Z formula: 0.79*cos(v/4)*sin(v) instead of simple sin(v)
  - Per-frame spiral rotation: u + pi - (2π/(60*180))*sample
  - ISO 226 loudness weighting on tube deformation
  - EdgeAlpha=0.3 (semi-transparent wireframe)
  - AmbientStrength=0.3
  - Camera: full 360° orbit over ~3 minutes
  - tsul formula: (maxIso226-iso226ForFreq)*flip(u)*(0.00003*amp+0.00002)
"""

import os
import numpy as np
import subprocess
import sys
import time as _time
from dataclasses import dataclass
from typing import Optional, Callable

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
# GLSL Shaders — Phong headlight lighting
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

    vec3 N = normalize(in_normal);
    vec3 L = normalize(u_eye_pos - in_position);
    float NdotL = max(dot(N, L), 0.0);

    // MATLAB AmbientStrength=0.3
    float ambient = 0.3;
    float diffuse = 0.7 * NdotL;
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
# ISO 226 Equal-Loudness Contour (simplified)
# ---------------------------------------------------------------------------

def compute_iso226_weights(frequencies: np.ndarray, phon: float = 40.0) -> np.ndarray:
    """Approximate ISO 226 equal-loudness contour weights."""
    # Simplified A-weighting approximation for speed
    f = np.maximum(frequencies, 1.0)
    # A-weighting formula (simplified)
    ra = (12194**2 * f**4) / ((f**2 + 20.6**2) *
         np.sqrt((f**2 + 107.7**2) * (f**2 + 737.9**2)) *
         (f**2 + 12194**2))
    ra = ra / np.max(ra)  # Normalize to [0, 1]
    return ra / 20.0  # Scale similar to MATLAB iso226/20


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class MeshRenderConfig:
    """Configuration for the 3D mesh renderer v2."""
    width: int = 1920
    height: int = 1080
    fps: int = 60

    # Spiral geometry — loaded from spiral_freq_data.npz
    num_freq_bins: int = 1000
    inner_circle_points: int = 60     # MATLAB InerCircel=60 (latest)
    use_spiral_freqs: bool = True

    # Tube parameters — calibrated to our amplitude range
    # MATLAB uses 0.00003 with ~30 amp range → product 0.0009
    # Our amp range after scaling is ~0-110, so we use 0.0005
    # to get proportional deformation (tsul ≈ 0.5-1.0 at peaks)
    tube_base: float = 0.0002
    tube_amp_scale: float = 0.0015

    # Amplitude normalization
    amp_target: float = 110.0

    # Wave parameters
    wave_lambda: float = 4.8701
    wave_v0: float = 4.7124
    wave_speed: float = 70.0

    # Z offset
    z_offset: float = -30.0           # Raised from MATLAB's -50 for better centering

    # Rendering — MATLAB latest values
    edge_alpha: float = 0.7           # MATLAB=0.3 but we need more since no Phong face boost
    line_width: float = 1.5
    background_color: tuple = (0.0, 0.0, 0.0)
    theta_line_step: int = 1

    # Camera
    camera_fov: float = 30.0
    camera_distance: float = 280.0

    # Camera animation (piperecord11_LEF.m latest)
    cam_el_base: float = 12.0         # Lower base for edge-on YouTube look
    cam_el_oscillate: float = 5.0     # ±5° oscillation
    cam_el_max: float = 13.95         # For el variable
    cam_el_min: float = 9.95
    cam_del: float = 0.05
    cam_orbit_period_frames: int = 10800  # 60fps * 180s = full 360° orbit

    # Video encoding
    video_crf: int = 18
    video_preset: str = "slow"


# ---------------------------------------------------------------------------
# Matrix math
# ---------------------------------------------------------------------------

def _perspective(fov_rad, aspect, near, far):
    f = 1.0 / np.tan(fov_rad / 2.0)
    m = np.zeros((4, 4), dtype=np.float32)
    m[0, 0] = f / aspect
    m[1, 1] = f
    m[2, 2] = (far + near) / (near - far)
    m[2, 3] = 2.0 * far * near / (near - far)
    m[3, 2] = -1.0
    return m

def _look_at(eye, center, up):
    f = center - eye
    f = f / np.linalg.norm(f)
    s = np.cross(f, up)
    s_norm = np.linalg.norm(s)
    if s_norm < 1e-8:
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
    ModernGL 3D wireframe mesh renderer v2.
    Port of latest piperecord11_LEF.m from SSD.
    """

    def __init__(self, config: Optional[MeshRenderConfig] = None):
        if not HAS_MODERNGL:
            raise ImportError("ModernGL required. Install: pip install moderngl")

        self.config = config or MeshRenderConfig()
        cfg = self.config

        # OpenGL context
        self.ctx = moderngl.create_standalone_context()
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

        # FBO
        color_att = self.ctx.texture((cfg.width, cfg.height), 4)
        depth_att = self.ctx.depth_renderbuffer((cfg.width, cfg.height))
        self.fbo = self.ctx.framebuffer(
            color_attachments=[color_att], depth_attachment=depth_att)
        self.ctx.line_width = cfg.line_width

        # Shaders
        self.prog = self.ctx.program(
            vertex_shader=VERTEX_SHADER, fragment_shader=FRAGMENT_SHADER)
        self.prog['u_alpha'].value = cfg.edge_alpha

        # Load spiral geometry
        spiral_path = os.path.join(os.path.dirname(__file__), 'spiral_freq_data.npz')
        if cfg.use_spiral_freqs and os.path.exists(spiral_path):
            data = np.load(spiral_path)
            full_theta = data['theta']
            full_freqs = data['frequencies']
            indices = np.linspace(0, len(full_theta)-1, cfg.num_freq_bins).astype(int)
            self.theta = full_theta[indices].astype(np.float32)
            self.spiral_frequencies = full_freqs[indices].astype(np.float32)
            print(f"Loaded spiral: {cfg.num_freq_bins} bins, "
                  f"{self.spiral_frequencies[0]:.1f}-{self.spiral_frequencies[-1]:.0f} Hz")
        else:
            self.theta = np.linspace(0, 8.0*2*np.pi, cfg.num_freq_bins).astype(np.float32)
            self.spiral_frequencies = np.logspace(
                np.log10(20), np.log10(8000), cfg.num_freq_bins).astype(np.float32)

        # R range: -pi to pi (MATLAB latest: linspace(-pi,pi,60))
        self.R = np.linspace(-np.pi, np.pi, cfg.inner_circle_points).astype(np.float32)

        # Meshgrid
        self.u, self.v = np.meshgrid(self.theta, self.R)
        self.u_min = float(np.min(self.u))
        self.u_range = float(np.max(self.u) - self.u_min)

        # Trig tables
        self.cos_v = np.cos(self.v)
        self.sin_v = np.sin(self.v)
        # Z modulation: 0.79*cos(v/4)*sin(v) — from latest MATLAB
        self.z_cross_section = 0.79 * np.cos(self.v / 4.0) * np.sin(self.v)
        self.wave_u_arg = (self.u - self.u_min) * (cfg.wave_lambda / self.u_range)

        # flip(u) with cap
        raw_flip = np.flip(self.u, axis=1)
        self.flip_u = np.minimum(raw_flip, 25.0)

        # ISO 226 loudness weights
        self.iso226_weights = compute_iso226_weights(self.spiral_frequencies)
        max_iso = 1.0 + np.max(self.iso226_weights)
        self.iso226_factor = (max_iso - self.iso226_weights).astype(np.float32)

        # Colormap
        self.colormap = create_myjet_colormap(cfg.num_freq_bins, theta=self.theta)

        # Wireframe topology
        line_indices = self._build_line_indices()
        self.num_indices = len(line_indices)
        self.ibo = self.ctx.buffer(line_indices.tobytes())

        # Vertex buffer (pos + color + normal = 9 floats)
        num_verts = cfg.inner_circle_points * cfg.num_freq_bins
        self.vbo = self.ctx.buffer(reserve=num_verts * 9 * 4)

        # VAO
        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.vbo, '3f 3f 3f', 'in_position', 'in_color', 'in_normal')],
            index_buffer=self.ibo)

        # Camera state
        self.az = 270.0
        self.el = 12.0  # Start between el_min and el_max
        self.del_el = cfg.cam_del
        self._amp_scale = 1.0

        # Initial MVP
        self._upload_mvp_dynamic(self.az, self.el)

    def _build_line_indices(self):
        cfg = self.config
        rows, cols, step = cfg.inner_circle_points, cfg.num_freq_bins, cfg.theta_line_step
        indices = []
        for i in range(rows):
            for j in range(0, cols-1, step):
                j_end = min(j+step, cols-1)
                indices.extend([i*cols+j, i*cols+j_end])
        for j in range(0, cols, step):
            for i in range(rows-1):
                idx = i*cols+j
                indices.extend([idx, idx+cols])
        return np.array(indices, dtype=np.int32)

    def _upload_mvp_dynamic(self, az_deg, el_deg, target_z=-5.0):
        cfg = self.config
        az, el = np.radians(az_deg), np.radians(el_deg)
        center = np.array([0.0, 0.0, target_z], dtype=np.float32)
        dist = cfg.camera_distance
        eye = np.array([
            dist*np.cos(el)*np.cos(az),
            dist*np.cos(el)*np.sin(az),
            dist*np.sin(el),
        ], dtype=np.float32) + center

        # Gentle zoom — MATLAB uses 0.80 but our coordinate system differs
        factor = 0.25 - 0.10 * np.sin(np.radians(el_deg))
        eye = eye - factor * (eye - center)

        up = np.array([0.0, 0.0, 1.0], dtype=np.float32)
        proj = _perspective(np.radians(cfg.camera_fov), cfg.width/cfg.height, 1.0, 2000.0)
        view = _look_at(eye, center, up)
        mvp = (proj @ view).astype(np.float32)
        self.prog['mvp'].write(mvp.tobytes(order='F'))
        self.prog['u_eye_pos'].value = tuple(eye.tolist())

    def _update_camera(self, frame_idx, total_frames):
        """Port of latest MATLAB SetCameraMotion with full orbit."""
        cfg = self.config

        # Elevation oscillation (MATLAB: el bounces between el_min and el_max)
        if self.el >= cfg.cam_el_max:
            self.del_el = -abs(self.del_el)
        if self.el <= cfg.cam_el_min:
            self.del_el = abs(self.del_el)
        self.el += self.del_el * np.cos(np.pi * self.el / 180.0)

        # Combined elevation: base + oscillation + el variable
        # MATLAB: nel = 25 + 5*sin(2pi/(60*180)*sample) + el
        nel = (cfg.cam_el_base
               + cfg.cam_el_oscillate * np.sin(2*np.pi * frame_idx / cfg.cam_orbit_period_frames)
               + self.el)

        # Azimuth: full 360° orbit over cam_orbit_period_frames
        # MATLAB: az = 270 + mod((360/(60*180))*sample, 360)
        self.az = 270.0 + (360.0 * frame_idx / cfg.cam_orbit_period_frames) % 360.0

        # Dynamic target Z
        el_range = cfg.cam_el_max - cfg.cam_el_min
        teta_0to1 = np.clip((self.el - cfg.cam_el_min) / el_range, 0.0, 1.0)
        target_z = -5.0 - 30.0 * teta_0to1

        self._upload_mvp_dynamic(self.az, nel, target_z)
        return nel

    def _compute_frame_vertices(self, amplitude, flow_amp_value, t, el_deg, frame_idx):
        cfg = self.config
        rows, cols = cfg.inner_circle_points, cfg.num_freq_bins
        dFrame = 1.0 / cfg.fps

        amp_scaled = amplitude * self._amp_scale

        # Smooth amplitude
        kernel = np.ones(7) / 7
        amp_smooth = np.convolve(amp_scaled, kernel, mode='same')

        # ISO 226 weighted tube scaling (MATLAB latest formula)
        # tsul = (maxIso226-iso226ForFreq)*flip(u)*(0.00003*amp + 0.00002)
        amp_row = amp_smooth[np.newaxis, :]
        iso_row = self.iso226_factor[np.newaxis, :]
        tsul = iso_row * self.flip_u * (cfg.tube_amp_scale * amp_row + cfg.tube_base)

        # XY uses mRadius (=theta in latest MATLAB) + tube cross-section
        # MATLAB: xy = (mRadius + tsul.*cos(v))
        xy = self.theta[np.newaxis, :] + tsul * self.cos_v

        # Per-frame spiral rotation (MATLAB: u+pi-(2pi/(60*180))*sample)
        rotation_angle = np.pi - (2*np.pi / cfg.cam_orbit_period_frames) * frame_idx
        cos_rot = np.cos(self.u + rotation_angle)
        sin_rot = np.sin(self.u + rotation_angle)

        x1 = xy * cos_rot
        y1 = xy * sin_rot

        # Z with new cross-section formula (MATLAB: 0.79*cos(v/4)*sin(v))
        el_rad = np.radians(el_deg)
        zz = (tsul * self.z_cross_section
              + cfg.z_offset
              + 10.0 * np.cos(el_rad))

        # Colors
        colors = modulate_colors(self.colormap, amp_scaled, self.theta)
        colors_full = np.broadcast_to(
            colors[np.newaxis, :, :], (rows, cols, 3)).copy()

        # Normals (tube surface outward direction)
        nx = self.cos_v * cos_rot
        ny = self.cos_v * sin_rot
        nz = self.sin_v
        n_len = np.sqrt(nx*nx + ny*ny + nz*nz) + 1e-8
        nx /= n_len; ny /= n_len; nz /= n_len

        # Pack vertices (pos + color + normal = 9 floats)
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

    def render_frame(self, amplitude, flow_amp_value, t, el_deg=30.0, frame_idx=0):
        vertex_data = self._compute_frame_vertices(
            amplitude, flow_amp_value, t, el_deg, frame_idx)
        self.vbo.write(vertex_data.tobytes())

        self.fbo.use()
        bg = self.config.background_color
        self.ctx.clear(bg[0], bg[1], bg[2], 1.0)
        self.vao.render(moderngl.LINES)

        data = self.fbo.color_attachments[0].read()
        frame = np.frombuffer(data, dtype=np.uint8).reshape(
            self.config.height, self.config.width, 4)
        frame = frame[::-1, :, :3].copy()

        # Post-processing bloom
        h, w = frame.shape[:2]
        small = frame[::4, ::4].astype(np.float32)
        bright = np.maximum(small - 60.0, 0.0)
        from scipy.ndimage import uniform_filter
        glow_small = uniform_filter(bright, size=(3, 4, 1))
        glow = np.repeat(np.repeat(glow_small, 4, axis=0), 4, axis=1)[:h, :w]
        return np.clip(frame.astype(np.float32) + glow * 0.5, 0, 255).astype(np.uint8)

    def render_video(self, audio_path, output_path, start_time=0,
                     duration=None, progress_callback=None):
        cfg = self.config
        dFrame = 1.0 / cfg.fps

        print("Analyzing audio...")
        audio_config = AudioAnalysisConfig(
            frame_rate=cfg.fps,
            num_frequency_bins=len(self.spiral_frequencies),
            custom_frequencies=self.spiral_frequencies)
        analyzer = AudioAnalyzer(audio_config)
        analysis = analyzer.analyze(audio_path, start_time=start_time, duration=duration)
        total_frames = analysis.total_frames
        print(f"Total frames: {total_frames}")

        amp_p99 = np.percentile(analysis.amplitude_data, 99.5) + 1e-6
        self._amp_scale = cfg.amp_target / amp_p99
        print(f"Amplitude scale: {self._amp_scale:.6f}")

        print("Computing energy envelope...")
        flow_amp = compute_flow_amp(analysis.amplitude_data)
        flow_amp_scaled = 0.5 + 2.0 * flow_amp

        # Reset camera
        self.az = 270.0
        self.el = 12.0
        self.del_el = cfg.cam_del

        actual_duration = duration or analysis.duration_seconds
        ffmpeg_cmd = [
            'ffmpeg', '-y', '-f', 'rawvideo', '-vcodec', 'rawvideo',
            '-s', f'{cfg.width}x{cfg.height}', '-pix_fmt', 'rgb24',
            '-r', str(cfg.fps), '-i', '-',
            '-ss', str(start_time), '-t', str(actual_duration),
            '-i', audio_path,
            '-c:v', 'libx264', '-preset', cfg.video_preset,
            '-crf', str(cfg.video_crf), '-pix_fmt', 'yuv420p',
            '-c:a', 'aac', '-b:a', '320k', '-shortest', output_path]

        print("Starting FFmpeg...")
        proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

        print("Rendering...")
        t = 0.0
        t0 = _time.monotonic()
        try:
            for fi in range(total_frames):
                nel = self._update_camera(fi, total_frames)
                amp = analysis.amplitude_data[:, fi]
                fav = flow_amp_scaled[min(fi, len(flow_amp_scaled)-1)]

                frame = self.render_frame(amp, fav, t, nel, fi)
                proc.stdin.write(frame.tobytes())
                t += dFrame

                if fi % 100 == 0:
                    elapsed = _time.monotonic() - t0
                    fps = (fi+1)/elapsed if elapsed > 0 else 0
                    pct = 100*fi/total_frames
                    print(f"  Frame {fi}/{total_frames} ({pct:.1f}%) — "
                          f"{fps:.1f} fps az={self.az:.0f} el={nel:.1f}")

                if progress_callback:
                    progress_callback(fi, total_frames, "Rendering 3D mesh v2...")
        except BrokenPipeError:
            raise RuntimeError(f"FFmpeg pipe broke: {proc.stderr.read().decode()}")

        proc.stdin.close()
        proc.wait()
        elapsed = _time.monotonic() - t0
        print(f"Render: {total_frames} frames in {elapsed:.1f}s ({total_frames/elapsed:.1f} fps)")

        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {proc.stderr.read().decode()}")

        print(f"Video saved: {output_path}")
        return output_path

    def cleanup(self):
        self.vbo.release(); self.ibo.release(); self.vao.release()
        self.fbo.release(); self.prog.release(); self.ctx.release()


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="SYNESTHESIA Mesh Renderer v2")
    p.add_argument("audio_file")
    p.add_argument("-o", "--output", default="output_mesh3d_v2.mp4")
    p.add_argument("-s", "--start", type=float, default=0)
    p.add_argument("-d", "--duration", type=float)
    p.add_argument("--width", type=int, default=1920)
    p.add_argument("--height", type=int, default=1080)
    p.add_argument("--fps", type=int, default=60)
    args = p.parse_args()

    cfg = MeshRenderConfig(width=args.width, height=args.height, fps=args.fps)
    renderer = MeshRenderer(cfg)
    try:
        renderer.render_video(args.audio_file, args.output, args.start, args.duration)
    finally:
        renderer.cleanup()
