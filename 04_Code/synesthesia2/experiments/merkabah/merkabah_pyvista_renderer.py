#!/usr/bin/env python3
"""
SYNESTHESIA 3.0 - PyVista GPU Edition
======================================
Faithful 3D recreation of the Synesthesia 3.0 temporal visualization
using PyVista/VTK GPU-accelerated rendering.

Features (matching the original 2D Synesthesia 3.0):
- Cochlear spiral (Fermat helix) with chromesthesia solfège colors
- Melodic Trail: Pitch history as golden glowing spheres
- Rhythm Pulse: Spiral breathes ±12% on beats
- Harmonic Aura: Chord-driven background color shifts
- Atmosphere Field: Energy/tension modulates rotation & particle scale
- Wave animation along the spiral

Rendered in TRUE 3D with PyVista GPU rendering, orbiting camera,
multi-point lighting, and cinematic post-processing.

Requirements:
    pip install pyvista vtk numpy pillow scipy librosa

Usage:
    python merkabah_pyvista_renderer.py audio.mp3 -o output.mp4 --duration 30
    python merkabah_pyvista_renderer.py --test
"""

import os
import sys
import numpy as np
import math
from PIL import Image, ImageEnhance
from dataclasses import dataclass, field
from typing import Tuple, Optional, Dict
from collections import deque
import colorsys
from scipy import ndimage

# Configure PyVista for off-screen rendering
os.environ['PYVISTA_OFF_SCREEN'] = 'true'
import pyvista as pv
pv.OFF_SCREEN = True


# ============================================================================
# CHROMESTHESIA COLORS (solfège-based, matching Synesthesia 3.0)
# ============================================================================

CHROMESTHESIA_COLORS = [
    (0, 0, 255),      # Do - Blue (C)
    (75, 0, 130),     # C# - Indigo
    (255, 105, 180),  # Re - Pink (D)
    (238, 130, 238),  # D# - Violet
    (255, 0, 0),      # Mi - Red (E)
    (255, 165, 0),    # Fa - Orange (F)
    (255, 140, 0),    # F# - Dark Orange
    (255, 255, 0),    # Sol - Yellow (G)
    (173, 255, 47),   # G# - Green Yellow
    (0, 255, 0),      # La - Green (A)
    (0, 206, 209),    # A# - Dark Turquoise
    (0, 255, 255),    # Si - Cyan (B)
]

MELODY_TRAIL_COLOR = (255, 220, 100)  # Golden

# Circle of fifths color mapping for harmonic aura
HARMONY_COLORS = {
    'C': (255, 80, 80),
    'G': (255, 140, 80),
    'D': (255, 200, 80),
    'A': (255, 255, 80),
    'E': (200, 255, 80),
    'B': (80, 255, 80),
    'F#': (80, 255, 160),
    'Db': (80, 255, 255),
    'Ab': (80, 160, 255),
    'Eb': (80, 80, 255),
    'Bb': (160, 80, 255),
    'F': (255, 80, 200),
    'N': (60, 60, 80),
}


# ============================================================================
# CONFIG
# ============================================================================

@dataclass
class SpiralPyVistaConfig:
    """Configuration for SYNESTHESIA 3.0 PyVista spiral renderer."""
    # Frame
    frame_width: int = 1920
    frame_height: int = 1080
    fps: int = 30

    # Spiral geometry
    num_freq_bins: int = 381
    spiral_turns: float = 7.0
    spiral_height: float = 8.0
    base_radius: float = 2.5

    # Rendering
    base_point_size: int = 12
    tube_radius: float = 0.03
    tube_sides: int = 12
    glow_sphere_interval: int = 3  # Every Nth bright point

    # Melodic Trail
    trail_duration_sec: float = 3.0
    trail_decay: float = 0.92
    trail_point_size: int = 15
    trail_opacity: float = 0.8

    # Rhythm Pulse
    pulse_scale_amount: float = 0.12
    pulse_brightness_amount: float = 0.25
    pulse_decay: float = 0.85

    # Harmonic Aura
    aura_transition_speed: float = 0.08
    aura_brightness: float = 0.15
    base_bg_color: Tuple[int, int, int] = (15, 20, 30)

    # Atmosphere
    atmosphere_smooth: float = 0.05

    # Camera
    camera_orbit_speed: float = 0.8  # degrees per frame
    camera_elev_base: float = 20.0
    camera_elev_amplitude: float = 15.0
    camera_elev_freq: float = 0.02
    camera_distance: float = 10.0

    # Lighting
    key_light_intensity: float = 0.7
    fill_light_intensity: float = 0.4

    # Post-processing
    bloom_intensity: float = 0.6
    bloom_radius: int = 20
    vignette_strength: float = 0.35


# ============================================================================
# SPIRAL GEOMETRY
# ============================================================================

def create_spiral_helix(num_bins, turns, height, base_radius,
                        rotation=0.0, scale=1.0, wave_phase=0.0):
    """
    Create 3D Fermat-like spiral helix matching Synesthesia 3.0 geometry.
    Low freq at bottom center, high freq spiraling up and outward.
    """
    t = np.linspace(0, 1, num_bins)
    theta = t * turns * 2 * np.pi + np.radians(rotation)

    # Fermat spiral radius (sqrt growth)
    r = np.sqrt(t) * base_radius * scale

    # Wave animation
    wave = np.sin(theta * 3 + wave_phase) * 0.05 * r
    r_animated = r + wave

    x = r_animated * np.cos(theta)
    y = r_animated * np.sin(theta)
    z = t * height

    return np.column_stack([x, y, z])


def get_chromesthesia_color(freq_idx, num_bins, amplitude=1.0, brightness_boost=0.0):
    """Get chromesthesia color for frequency bin."""
    octave_pos = (freq_idx / num_bins) * 7  # 7 octaves
    note_in_octave = (octave_pos % 1) * 12
    color_idx = int(note_in_octave) % 12

    base_color = CHROMESTHESIA_COLORS[color_idx]
    brightness = 0.3 + amplitude * 0.7 + brightness_boost

    r = min(255, int(base_color[0] * brightness))
    g = min(255, int(base_color[1] * brightness))
    b = min(255, int(base_color[2] * brightness))

    return (r, g, b)


# ============================================================================
# TEMPORAL COMPONENTS
# ============================================================================

class MelodicTrail:
    """Tracks pitch history and provides trail data for rendering."""

    def __init__(self, config: SpiralPyVistaConfig):
        self.config = config
        trail_length = int(config.trail_duration_sec * config.fps)
        self.pitch_history = deque(maxlen=trail_length)

    def update(self, spectrum):
        """Record dominant pitch from spectrum."""
        peak_idx = np.argmax(spectrum)
        peak_amp = spectrum[peak_idx]
        if peak_amp > 0.3:
            self.pitch_history.append((peak_idx, peak_amp))

    def get_trail_data(self, all_points):
        """Get trail point positions with alpha values."""
        trail = []
        for i, (freq_idx, amp) in enumerate(self.pitch_history):
            age = len(self.pitch_history) - i - 1
            alpha = self.config.trail_decay ** age * amp
            if alpha > 0.05 and freq_idx < len(all_points):
                trail.append((all_points[freq_idx], alpha))
        return trail


class RhythmPulse:
    """Beat-synchronized pulsing effects."""

    def __init__(self, config: SpiralPyVistaConfig):
        self.config = config
        self.current_pulse = 0.0

    def on_beat(self, strength=1.0):
        """Called when a beat is detected."""
        self.current_pulse = min(1.0, self.current_pulse + strength)

    def update(self):
        """Decay pulse and return current effects."""
        scale = 1.0 + self.current_pulse * self.config.pulse_scale_amount
        brightness = self.current_pulse * self.config.pulse_brightness_amount
        self.current_pulse *= self.config.pulse_decay
        return scale, brightness


class HarmonicAura:
    """Chord-driven background color."""

    def __init__(self, config: SpiralPyVistaConfig):
        self.config = config
        self.current_color = np.array(config.base_bg_color, dtype=float)
        self.target_color = np.array(config.base_bg_color, dtype=float)
        self.current_chord = "N"

    def set_chord(self, chord_label):
        """Set target background color based on detected chord."""
        self.current_chord = chord_label

        root = chord_label.rstrip('m').rstrip('7').rstrip('maj').rstrip('dim').rstrip('aug')
        root = root.replace('#', '#').replace('b', 'b')

        if root in HARMONY_COLORS:
            base_color = np.array(HARMONY_COLORS[root], dtype=float)
        else:
            base_color = np.array(HARMONY_COLORS['N'], dtype=float)

        # Minor chords shift cooler
        if 'm' in chord_label and 'maj' not in chord_label:
            base_color = base_color * 0.7 + np.array([0, 30, 60])

        # Diminished darker
        if 'dim' in chord_label:
            base_color = base_color * 0.5

        self.target_color = np.clip(base_color * self.config.aura_brightness, 0, 255)

    def update(self):
        """Smooth transition toward target color. Returns (r,g,b) as 0-1 floats."""
        self.current_color += (self.target_color - self.current_color) * self.config.aura_transition_speed
        c = np.clip(self.current_color, 0, 255) / 255.0
        return tuple(c)


class AtmosphereField:
    """Long-term mood modulation based on energy and tension."""

    def __init__(self, config: SpiralPyVistaConfig):
        self.config = config
        self.energy = 0.5
        self.tension = 0.3

    def update(self, energy, tension):
        """Smooth update of atmosphere parameters."""
        smooth = self.config.atmosphere_smooth
        self.energy = self.energy * (1 - smooth) + energy * smooth
        self.tension = self.tension * (1 - smooth) + tension * smooth

    def get_effects(self):
        """Get current atmosphere modulation effects."""
        return {
            'rotation_speed': 0.5 + self.energy * 1.5,  # 0.5x to 2x
            'particle_scale': 0.8 + self.energy * 0.4,  # 0.8x to 1.2x
            'color_warmth': self.tension * 0.3,
        }


# ============================================================================
# MAIN RENDERER
# ============================================================================

class SynesthesiaSpiralRenderer:
    """
    SYNESTHESIA 3.0 PyVista GPU Renderer.

    Faithful 3D recreation of the cochlear spiral with all four
    temporal visualization layers.
    """

    def __init__(self, config: SpiralPyVistaConfig = None):
        self.config = config or SpiralPyVistaConfig()

        # Temporal components
        self.melody_trail = MelodicTrail(self.config)
        self.rhythm_pulse = RhythmPulse(self.config)
        self.harmonic_aura = HarmonicAura(self.config)
        self.atmosphere = AtmosphereField(self.config)

        # Animation state
        self.frame_count = 0

    def update_temporal(self, spectrum, pitch_hz=0, pitch_confidence=0,
                        is_beat=False, beat_strength=0, chord_label="N",
                        energy=0.5, tension=0.3):
        """Update all temporal feature trackers for current frame."""
        # Melody trail
        self.melody_trail.update(spectrum)

        # Rhythm
        if is_beat:
            self.rhythm_pulse.on_beat(beat_strength)

        # Harmony
        if chord_label and chord_label != self.harmonic_aura.current_chord:
            self.harmonic_aura.set_chord(chord_label)

        # Atmosphere
        self.atmosphere.update(energy, tension)

    def render_frame(self, spectrum, onset_strength=0.0):
        """Render one frame of the SYNESTHESIA 3.0 spiral."""
        self.frame_count += 1
        spectrum = np.clip(spectrum, 0, 1)
        cfg = self.config

        # Get temporal effects
        pulse_scale, pulse_brightness = self.rhythm_pulse.update()
        bg_color = self.harmonic_aura.update()
        atmos = self.atmosphere.get_effects()

        # Animation params
        rotation = self.frame_count * cfg.camera_orbit_speed * atmos['rotation_speed']
        wave_phase = self.frame_count * 0.15
        scale = pulse_scale * atmos['particle_scale']

        # Create spiral points
        points = create_spiral_helix(
            cfg.num_freq_bins, cfg.spiral_turns, cfg.spiral_height,
            cfg.base_radius, rotation, scale, wave_phase
        )

        # Create plotter
        pl = pv.Plotter(off_screen=True, window_size=[cfg.frame_width, cfg.frame_height])
        pl.set_background(bg_color)

        # === SPINE TUBE (colored by frequency) ===
        spline = pv.Spline(points, cfg.num_freq_bins * 2)
        spine_tube = spline.tube(radius=cfg.tube_radius, n_sides=cfg.tube_sides)

        n_spine = spine_tube.n_points
        spine_colors = np.zeros((n_spine, 3), dtype=np.uint8)
        for i in range(n_spine):
            z = spine_tube.points[i, 2]
            t = np.clip(z / cfg.spiral_height, 0, 1)
            freq_idx = int(t * (cfg.num_freq_bins - 1))
            amp = spectrum[freq_idx]
            r, g, b = get_chromesthesia_color(freq_idx, cfg.num_freq_bins, amp, pulse_brightness)
            spine_colors[i] = [r, g, b]

        spine_tube['colors'] = spine_colors
        pl.add_mesh(spine_tube, scalars='colors', rgb=True,
                    smooth_shading=True, opacity=0.6)

        # === FREQUENCY DOTS (active bins) ===
        active_mask = spectrum > 0.1
        active_indices = np.where(active_mask)[0]

        if len(active_indices) > 0:
            active_points = points[active_indices]
            active_cloud = pv.PolyData(active_points)

            sizes = np.array([
                cfg.base_point_size * (0.3 + spectrum[idx] * 0.7) * scale
                for idx in active_indices
            ])
            active_cloud['sizes'] = sizes

            active_colors = np.zeros((len(active_indices), 3), dtype=np.uint8)
            for j, idx in enumerate(active_indices):
                r, g, b = get_chromesthesia_color(
                    idx, cfg.num_freq_bins, spectrum[idx], pulse_brightness
                )
                active_colors[j] = [r, g, b]

            active_cloud['colors'] = active_colors
            pl.add_mesh(active_cloud, scalars='colors', rgb=True,
                        point_size=cfg.base_point_size,
                        render_points_as_spheres=True)

        # === GLOW SPHERES (high amplitude) ===
        bright_indices = np.where(spectrum > 0.5)[0]
        for idx in bright_indices[::cfg.glow_sphere_interval]:
            pt = points[idx]
            r, g, b = get_chromesthesia_color(idx, cfg.num_freq_bins, spectrum[idx])
            glow_size = 0.05 + spectrum[idx] * 0.08

            sphere = pv.Sphere(radius=glow_size, center=pt)
            pl.add_mesh(sphere, color=[r / 255, g / 255, b / 255],
                        opacity=0.35, smooth_shading=True)

        # === MELODIC TRAIL (golden glow) ===
        trail = self.melody_trail.get_trail_data(points)
        if trail:
            trail_pts = np.array([p for p, _ in trail])
            trail_alphas = np.array([a for _, a in trail])

            trail_cloud = pv.PolyData(trail_pts)

            trail_colors = np.zeros((len(trail), 3), dtype=np.uint8)
            for j, alpha in enumerate(trail_alphas):
                trail_colors[j] = [
                    int(MELODY_TRAIL_COLOR[0] * alpha),
                    int(MELODY_TRAIL_COLOR[1] * alpha),
                    int(MELODY_TRAIL_COLOR[2] * alpha),
                ]

            trail_cloud['colors'] = trail_colors
            pl.add_mesh(trail_cloud, scalars='colors', rgb=True,
                        point_size=cfg.trail_point_size,
                        render_points_as_spheres=True,
                        opacity=cfg.trail_opacity)

        # === CAMERA ===
        cam_angle = self.frame_count * cfg.camera_orbit_speed
        elev = cfg.camera_elev_base + cfg.camera_elev_amplitude * np.sin(
            self.frame_count * cfg.camera_elev_freq
        )
        dist = cfg.camera_distance

        cam_x = dist * np.cos(np.radians(cam_angle)) * np.cos(np.radians(elev))
        cam_y = dist * np.sin(np.radians(cam_angle)) * np.cos(np.radians(elev))
        cam_z = cfg.spiral_height * 0.4 + dist * 0.4 * np.sin(np.radians(elev))

        pl.camera.position = (cam_x, cam_y, cam_z)
        pl.camera.focal_point = (0, 0, cfg.spiral_height * 0.4)
        pl.camera.up = (0, 0, 1)

        # === LIGHTING ===
        pl.enable_anti_aliasing('msaa')
        light1 = pv.Light(position=(5, 5, 12), intensity=cfg.key_light_intensity)
        pl.add_light(light1)
        light2 = pv.Light(position=(-5, -3, 8), intensity=cfg.fill_light_intensity,
                          color=[0.6, 0.7, 1.0])
        pl.add_light(light2)

        # Screenshot
        img = pl.screenshot(return_img=True)
        pl.close()

        # Post-processing
        image = Image.fromarray(img)
        image = self._apply_post_processing(image)

        return image

    def _apply_post_processing(self, image):
        """Apply cinematic post-processing (bloom, vignette, color grading)."""
        img_array = np.array(image).astype(np.float32)
        cfg = self.config

        # === BLOOM ===
        luminance = 0.299 * img_array[:, :, 0] + 0.587 * img_array[:, :, 1] + 0.114 * img_array[:, :, 2]
        bright_mask = (luminance > 170).astype(np.float32)

        bloom = np.zeros_like(img_array)
        for c in range(3):
            bright_channel = img_array[:, :, c] * bright_mask
            bloom[:, :, c] = ndimage.gaussian_filter(bright_channel, sigma=cfg.bloom_radius)

        img_array = img_array + bloom * cfg.bloom_intensity

        # === VIGNETTE ===
        h, w = img_array.shape[:2]
        yy, xx = np.ogrid[:h, :w]
        center_y, center_x = h // 2, w // 2
        dist = np.sqrt(((xx - center_x) / (w / 2)) ** 2 + ((yy - center_y) / (h / 2)) ** 2)
        vignette = 1 - np.clip(dist * cfg.vignette_strength, 0, 0.65)
        vignette = ndimage.gaussian_filter(vignette, sigma=40)

        for c in range(3):
            img_array[:, :, c] *= vignette

        # === COLOR GRADING ===
        shadows = img_array < 70
        highlights = img_array > 180

        # Warm shadows
        img_array[:, :, 0] = np.where(shadows[:, :, 0], img_array[:, :, 0] * 1.05, img_array[:, :, 0])
        # Cool highlights
        img_array[:, :, 2] = np.where(highlights[:, :, 2], img_array[:, :, 2] * 1.03, img_array[:, :, 2])

        # Clip and convert
        img_array = np.clip(img_array, 0, 255).astype(np.uint8)
        image = Image.fromarray(img_array)

        # Contrast and saturation boost
        image = ImageEnhance.Contrast(image).enhance(1.1)
        image = ImageEnhance.Color(image).enhance(1.08)

        return image


# Aliases for backward compatibility
PyVistaMerkabah = SynesthesiaSpiralRenderer
EarthSkyMerkabah = SynesthesiaSpiralRenderer


def create_pyvista_renderer(width=1920, height=1080):
    """Create a SYNESTHESIA 3.0 spiral renderer."""
    config = SpiralPyVistaConfig(frame_width=width, frame_height=height)
    return SynesthesiaSpiralRenderer(config)


# ============================================================================
# VIDEO GENERATOR
# ============================================================================

def generate_video_local(audio_path, output_path, duration=None):
    """Generate SYNESTHESIA 3.0 spiral video with full temporal analysis."""
    import tempfile
    import subprocess
    import time

    try:
        from audio_analyzer import AudioAnalyzer, AudioAnalysisConfig
        from temporal_analyzer import TemporalAudioAnalyzer, TemporalConfig
        HAS_ANALYZERS = True
    except ImportError:
        HAS_ANALYZERS = False
        print("Warning: Audio analyzers not found. Using synthetic data.")

    print("=" * 70)
    print("SYNESTHESIA 3.0 - PyVista GPU Edition")
    print("  Cochlear Spiral / Temporal Visualization")
    print("=" * 70)
    print(f"\nInput:  {audio_path}")
    print(f"Output: {output_path}")

    temp_dir = tempfile.mkdtemp(prefix='synth3_pyvista_')
    frames_dir = os.path.join(temp_dir, 'frames')
    os.makedirs(frames_dir)

    try:
        if HAS_ANALYZERS and os.path.exists(audio_path):
            print("\nAnalyzing audio (frequency + temporal)...")
            frame_analyzer = AudioAnalyzer(AudioAnalysisConfig(frame_rate=30))
            frame_analysis = frame_analyzer.analyze(audio_path, duration=duration)

            temporal_analyzer = TemporalAudioAnalyzer(TemporalConfig(frame_rate=30))
            temporal_analysis = temporal_analyzer.analyze(audio_path, duration=duration)

            num_frames = frame_analysis.total_frames
            beat_frames = set(temporal_analysis.beat_frames.tolist()) if temporal_analysis.beat_frames is not None else set()

            # Build chord timeline (chord_frames are frame indices)
            chord_timeline = {}
            if temporal_analysis.chord_labels is not None and temporal_analysis.chord_frames is not None:
                for cf, cl in zip(temporal_analysis.chord_frames, temporal_analysis.chord_labels):
                    chord_timeline[int(cf)] = cl
        else:
            num_frames = int((duration or 30) * 30)
            frame_analysis = None
            temporal_analysis = None
            beat_frames = set()
            chord_timeline = {}

        print(f"Rendering {num_frames} frames...")

        config = SpiralPyVistaConfig()
        renderer = SynesthesiaSpiralRenderer(config)

        start_time = time.time()
        current_chord = "N"

        for i in range(num_frames):
            if frame_analysis is not None:
                spectrum = frame_analysis.amplitude_data[:, i]
                frequencies = frame_analysis.frequencies
                spec_max = spectrum.max()
                spectrum_norm = spectrum / spec_max if spec_max > 0 else spectrum

                # Get temporal features
                pitch = float(temporal_analysis.pitch_contour[i]) if i < len(temporal_analysis.pitch_contour) else 0
                energy = float(temporal_analysis.energy_curve[i]) if i < len(temporal_analysis.energy_curve) else 0.5
                tension = float(temporal_analysis.tension_curve[i]) if i < len(temporal_analysis.tension_curve) else 0.3

                # Onset strength for rhythm
                onset_strength = 1.0 if i in beat_frames else 0.0

                # Chord
                if i in chord_timeline:
                    current_chord = chord_timeline[i]

                # Update temporal state
                renderer.update_temporal(
                    spectrum_norm,
                    pitch_hz=pitch,
                    pitch_confidence=0.9 if pitch > 0 else 0,
                    is_beat=(i in beat_frames),
                    beat_strength=1.0 if i in beat_frames else 0,
                    chord_label=current_chord,
                    energy=energy,
                    tension=tension
                )
            else:
                # Synthetic fallback
                spectrum_norm = np.random.rand(config.num_freq_bins) * 0.5
                spectrum_norm[50:60] = 0.8
                spectrum_norm[120:130] = 0.7
                spectrum_norm[200:210] = 0.6
                onset_strength = 0.7 if i % 15 == 0 else 0.0

            frame = renderer.render_frame(spectrum_norm, onset_strength)
            frame.save(os.path.join(frames_dir, f'frame_{i:06d}.png'))

            if i % 30 == 0:
                elapsed = time.time() - start_time
                fps_rate = (i + 1) / elapsed if elapsed > 0 else 0
                eta = (num_frames - i - 1) / fps_rate if fps_rate > 0 else 0
                print(f"  Frame {i}/{num_frames} - {fps_rate:.1f} fps, ETA: {eta:.0f}s")

        total_time = time.time() - start_time
        print(f"\nRendered {num_frames} frames in {total_time:.1f}s ({num_frames / total_time:.1f} fps)")

        # Encode with FFmpeg
        print("\nEncoding video with FFmpeg...")
        ffmpeg_path = '/opt/homebrew/bin/ffmpeg'
        if not os.path.exists(ffmpeg_path):
            ffmpeg_path = 'ffmpeg'

        cmd = [
            ffmpeg_path, '-y',
            '-framerate', '30',
            '-i', os.path.join(frames_dir, 'frame_%06d.png'),
            '-i', audio_path,
            '-c:v', 'libx264', '-preset', 'slow', '-crf', '17',
            '-pix_fmt', 'yuv420p',
            '-c:a', 'aac', '-b:a', '192k',
            '-shortest', '-movflags', '+faststart',
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"FFmpeg error: {result.stderr}")

        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"\n{'=' * 70}")
        print(f"Done! {output_path} ({size_mb:.1f} MB)")
        print(f"{'=' * 70}")

    finally:
        import shutil
        shutil.rmtree(temp_dir)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='SYNESTHESIA 3.0 - PyVista GPU Edition')
    parser.add_argument('input', nargs='?', help='Input audio file')
    parser.add_argument('-o', '--output', default='synth3_pyvista.mp4', help='Output video')
    parser.add_argument('--duration', type=float, default=30, help='Duration in seconds')
    parser.add_argument('--test', action='store_true', help='Run quick test render')

    args = parser.parse_args()

    if args.test:
        print("SYNESTHESIA 3.0 - PyVista GPU Test Render")
        print("=" * 50)

        config = SpiralPyVistaConfig(frame_width=1280, frame_height=720)
        renderer = SynesthesiaSpiralRenderer(config)

        melody_pitches = [60, 120, 200, 280, 350]  # Simulated pitch indices

        for i in range(5):
            # Synthetic spectrum
            spectrum = np.random.rand(config.num_freq_bins) * 0.4
            spectrum[40:55] = 0.85
            spectrum[100:120] = 0.75
            spectrum[180:200] = 0.7
            spectrum[250:270] = 0.6

            # Simulate temporal features
            renderer.update_temporal(
                spectrum,
                pitch_hz=440 * (1 + i * 0.2),
                pitch_confidence=0.9,
                is_beat=(i % 2 == 0),
                beat_strength=0.8 if i % 2 == 0 else 0,
                chord_label=['C', 'Am', 'F', 'G', 'C'][i],
                energy=0.5 + 0.1 * i,
                tension=0.3 + 0.05 * i
            )

            frame = renderer.render_frame(spectrum, onset_strength=0.7 if i % 2 == 0 else 0.0)
            out_path = f'test_pyvista_{i:03d}.png'
            frame.save(out_path)
            print(f"  Saved: {out_path}")

        print("Test complete!")

    elif args.input:
        generate_video_local(args.input, args.output, args.duration)

    else:
        print("Usage:")
        print("  python merkabah_pyvista_renderer.py audio.mp3 -o output.mp4 --duration 30")
        print("  python merkabah_pyvista_renderer.py --test")
