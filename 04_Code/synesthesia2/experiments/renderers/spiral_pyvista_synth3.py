#!/usr/bin/env python3
"""
SYNESTHESIA 3.0 - PyVista Edition

Faithful 3D recreation of the Synesthesia 3.0 temporal visualization,
now with a tall cochlear helix rendered in PyVista.

Same features as the original:
- Chromesthesia solfège color mapping
- Melodic trail (golden glow)
- Rhythm pulse (spiral breathes)
- Harmonic aura (chord-driven background)
- Wave animation along spiral

But now in TRUE 3D with PyVista GPU rendering.

Usage:
    python spiral_pyvista_synth3.py audio.mp3 -o output.mp4 --start 140 --duration 10
"""

import os
import sys
import numpy as np
from pathlib import Path
import colorsys
import subprocess
import tempfile
import argparse
from collections import deque

os.environ['PYVISTA_OFF_SCREEN'] = 'true'

import pyvista as pv
pv.OFF_SCREEN = True

import librosa
from scipy.ndimage import zoom
from PIL import Image

# ============================================================================
# CHROMESTHESIA COLORS (matching Synesthesia 3.0 exactly)
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

# ============================================================================
# CONFIG
# ============================================================================

WIDTH = 1920
HEIGHT = 1080
FPS = 30

# Spiral geometry - tall 3D helix
NUM_FREQ_BINS = 381
SPIRAL_TURNS = 7.0
SPIRAL_HEIGHT = 8.0
BASE_RADIUS = 2.5

# Rendering
BASE_POINT_SIZE = 8
TUBE_SIDES = 12

# Melody trail
TRAIL_DURATION_SEC = 3.0
TRAIL_DECAY = 0.92

# Rhythm
PULSE_SCALE = 0.12
PULSE_DECAY = 0.85


# ============================================================================
# SPIRAL GEOMETRY
# ============================================================================

def create_synth3_helix(num_bins, rotation=0.0, scale=1.0, wave_phase=0.0):
    """
    Create 3D Fermat-like spiral helix matching Synesthesia 3.0 geometry.
    Low freq at bottom center, high freq spiraling up and outward.
    """
    t = np.linspace(0, 1, num_bins)
    theta = t * SPIRAL_TURNS * 2 * np.pi + np.radians(rotation)
    
    # Fermat spiral radius (sqrt growth, like original)
    r = np.sqrt(t) * BASE_RADIUS * scale
    
    # Add wave animation
    wave = np.sin(theta * 3 + wave_phase) * 0.05 * r
    r_animated = r + wave
    
    x = r_animated * np.cos(theta)
    y = r_animated * np.sin(theta)
    z = t * SPIRAL_HEIGHT  # Linear height rise
    
    return np.column_stack([x, y, z])


def get_chromesthesia_color(freq_idx, num_bins, amplitude=1.0, brightness_boost=0.0):
    """Get chromesthesia color for frequency bin, matching original mapping."""
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
# TEMPORAL FEATURES
# ============================================================================

class TemporalState:
    """Tracks melody trails, rhythm pulses, and harmonic aura."""
    
    def __init__(self, fps=30):
        self.fps = fps
        self.trail_length = int(TRAIL_DURATION_SEC * fps)
        self.pitch_history = deque(maxlen=self.trail_length)
        self.pulse = 0.0
        self.bg_color = np.array([15, 20, 30], dtype=float)
        self.target_bg = np.array([15, 20, 30], dtype=float)
        self.energy = 0.5
    
    def update(self, spectrum, onset_strength=0.0):
        """Update temporal state from spectrum."""
        # Detect dominant pitch (simplified)
        peak_idx = np.argmax(spectrum)
        peak_amp = spectrum[peak_idx]
        
        if peak_amp > 0.3:
            self.pitch_history.append((peak_idx, peak_amp))
        
        # Rhythm pulse from onset
        if onset_strength > 0.5:
            self.pulse = min(1.0, self.pulse + onset_strength)
        
        self.pulse *= PULSE_DECAY
        
        # Energy tracking
        self.energy = self.energy * 0.95 + np.mean(spectrum) * 0.05
        
        # Background color shift based on energy
        warmth = self.energy * 40
        self.target_bg = np.array([15 + warmth * 0.5, 20 + warmth * 0.2, 30 - warmth * 0.3])
        self.bg_color += (self.target_bg - self.bg_color) * 0.08
    
    def get_pulse_scale(self):
        return 1.0 + self.pulse * PULSE_SCALE
    
    def get_bg_rgb(self):
        """Get background color as 0-1 float tuple."""
        c = np.clip(self.bg_color, 0, 255) / 255.0
        return tuple(c)
    
    def get_trail_points(self, all_points):
        """Get trail point positions with alpha values."""
        trail = []
        for i, (freq_idx, amp) in enumerate(self.pitch_history):
            age = len(self.pitch_history) - i - 1
            alpha = TRAIL_DECAY ** age * amp
            if alpha > 0.05 and freq_idx < len(all_points):
                trail.append((all_points[freq_idx], alpha))
        return trail


# ============================================================================
# PYVISTA RENDERER
# ============================================================================

class Synth3PyVistaRenderer:
    """Faithful PyVista recreation of Synesthesia 3.0."""
    
    def __init__(self):
        self.temporal = TemporalState(FPS)
        self.frame_count = 0
    
    def render_frame(self, spectrum, onset_strength=0.0):
        """Render one frame."""
        self.frame_count += 1
        spectrum = np.clip(spectrum, 0, 1)
        
        # Update temporal state
        self.temporal.update(spectrum, onset_strength)
        
        # Animation params
        rotation = self.frame_count * 0.5 * (0.5 + self.temporal.energy * 1.5)
        wave_phase = self.frame_count * 0.15
        scale = self.temporal.get_pulse_scale()
        
        # Create spiral points
        points = create_synth3_helix(NUM_FREQ_BINS, rotation, scale, wave_phase)
        
        # Create plotter
        pl = pv.Plotter(off_screen=True, window_size=[WIDTH, HEIGHT])
        pl.set_background(self.temporal.get_bg_rgb())
        
        # === MAIN SPIRAL ===
        # Build tube along spiral
        spline = pv.Spline(points, NUM_FREQ_BINS * 2)
        
        # Base tube (thin spine)
        spine_tube = spline.tube(radius=0.03, n_sides=TUBE_SIDES)
        
        # Color the spine by frequency
        n_spine = spine_tube.n_points
        spine_colors = np.zeros((n_spine, 3), dtype=np.uint8)
        for i in range(n_spine):
            z = spine_tube.points[i, 2]
            t = np.clip(z / SPIRAL_HEIGHT, 0, 1)
            freq_idx = int(t * (NUM_FREQ_BINS - 1))
            amp = spectrum[freq_idx]
            r, g, b = get_chromesthesia_color(freq_idx, NUM_FREQ_BINS, amp)
            spine_colors[i] = [r, g, b]
        
        spine_tube['colors'] = spine_colors
        pl.add_mesh(spine_tube, scalars='colors', rgb=True, 
                   smooth_shading=True, opacity=0.6)
        
        # === FREQUENCY DOTS (matching original circular points) ===
        # Only show dots with significant amplitude
        active_mask = spectrum > 0.1
        active_indices = np.where(active_mask)[0]
        
        if len(active_indices) > 0:
            active_points = points[active_indices]
            active_cloud = pv.PolyData(active_points)
            
            # Sizes based on amplitude
            sizes = np.array([
                BASE_POINT_SIZE * (0.3 + spectrum[idx] * 0.7) * scale
                for idx in active_indices
            ])
            active_cloud['sizes'] = sizes
            
            # Colors
            active_colors = np.zeros((len(active_indices), 3), dtype=np.uint8)
            for j, idx in enumerate(active_indices):
                r, g, b = get_chromesthesia_color(
                    idx, NUM_FREQ_BINS, spectrum[idx], 
                    self.temporal.pulse * 0.25
                )
                active_colors[j] = [r, g, b]
            
            active_cloud['colors'] = active_colors
            
            pl.add_mesh(active_cloud, scalars='colors', rgb=True,
                       point_size=12, render_points_as_spheres=True)
        
        # === HIGH AMPLITUDE GLOW SPHERES ===
        bright_indices = np.where(spectrum > 0.5)[0]
        for idx in bright_indices[::3]:  # Every 3rd for perf
            pt = points[idx]
            r, g, b = get_chromesthesia_color(idx, NUM_FREQ_BINS, spectrum[idx])
            glow_size = 0.05 + spectrum[idx] * 0.08
            
            sphere = pv.Sphere(radius=glow_size, center=pt)
            pl.add_mesh(sphere, color=[r/255, g/255, b/255],
                       opacity=0.35, smooth_shading=True)
        
        # === MELODIC TRAIL (golden glow) ===
        trail = self.temporal.get_trail_points(points)
        if trail:
            trail_pts = np.array([p for p, _ in trail])
            trail_alphas = np.array([a for _, a in trail])
            
            trail_cloud = pv.PolyData(trail_pts)
            
            # Golden color with alpha
            trail_colors = np.zeros((len(trail), 3), dtype=np.uint8)
            for j, alpha in enumerate(trail_alphas):
                trail_colors[j] = [
                    int(MELODY_TRAIL_COLOR[0] * alpha),
                    int(MELODY_TRAIL_COLOR[1] * alpha),
                    int(MELODY_TRAIL_COLOR[2] * alpha),
                ]
            
            trail_cloud['colors'] = trail_colors
            pl.add_mesh(trail_cloud, scalars='colors', rgb=True,
                       point_size=15, render_points_as_spheres=True,
                       opacity=0.8)
        
        # === CAMERA ===
        cam_angle = self.frame_count * 0.8
        elev = 20 + 15 * np.sin(self.frame_count * 0.02)
        dist = 10.0
        
        cam_x = dist * np.cos(np.radians(cam_angle)) * np.cos(np.radians(elev))
        cam_y = dist * np.sin(np.radians(cam_angle)) * np.cos(np.radians(elev))
        cam_z = SPIRAL_HEIGHT * 0.4 + dist * 0.4 * np.sin(np.radians(elev))
        
        pl.camera.position = (cam_x, cam_y, cam_z)
        pl.camera.focal_point = (0, 0, SPIRAL_HEIGHT * 0.4)
        pl.camera.up = (0, 0, 1)
        
        # Lighting
        pl.enable_anti_aliasing('msaa')
        light = pv.Light(position=(5, 5, 12), intensity=0.7)
        pl.add_light(light)
        light2 = pv.Light(position=(-5, -3, 8), intensity=0.4, color=[0.6, 0.7, 1.0])
        pl.add_light(light2)
        
        img = pl.screenshot(return_img=True)
        pl.close()
        
        return img


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="SYNESTHESIA 3.0 - PyVista Edition")
    parser.add_argument('audio', nargs='?')
    parser.add_argument('-o', '--output', default='synth3_pyvista.mp4')
    parser.add_argument('--duration', type=float, default=10.0)
    parser.add_argument('--start', type=float, default=0.0)
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()
    
    if args.test:
        print("🧪 Test mode...", flush=True)
        renderer = Synth3PyVistaRenderer()
        
        for i in range(3):
            spectrum = np.random.rand(NUM_FREQ_BINS) * 0.7
            spectrum[50:60] = 0.9
            spectrum[120:130] = 0.8
            spectrum[200:210] = 0.75
            
            img = renderer.render_frame(spectrum, onset_strength=0.7 if i == 1 else 0.0)
            out = f"/Users/guydvir/Project/04_Code/synesthesia2/synth3_test_{i:03d}.png"
            Image.fromarray(img).save(out)
            print(f"   Saved: {out}", flush=True)
        
        print("✅ Done!", flush=True)
        return
    
    if not args.audio:
        parser.print_help()
        return
    
    print(f"🎵 Loading: {args.audio}", flush=True)
    y, sr = librosa.load(args.audio, sr=22050, offset=args.start, duration=args.duration)
    
    # Mel spectrogram
    print("📊 Analyzing...", flush=True)
    mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=2048, hop_length=512, n_mels=128)
    mel_db = librosa.power_to_db(mel_spec, ref=np.max)
    mel_norm = (mel_db - mel_db.min()) / (mel_db.max() - mel_db.min() + 1e-8)
    
    zf = NUM_FREQ_BINS / mel_norm.shape[0]
    spectrogram = zoom(mel_norm, (zf, 1), order=1).T
    
    # Onset detection for rhythm
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=512)
    onset_norm = onset_env / (onset_env.max() + 1e-8)
    
    total_frames = int(args.duration * FPS)
    spec_ratio = len(spectrogram) / total_frames
    onset_ratio = len(onset_norm) / total_frames
    
    print(f"🎬 Rendering {total_frames} frames...", flush=True)
    
    renderer = Synth3PyVistaRenderer()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        pattern = os.path.join(tmpdir, "f_%06d.png")
        
        for fi in range(total_frames):
            si = min(int(fi * spec_ratio), len(spectrogram) - 1)
            oi = min(int(fi * onset_ratio), len(onset_norm) - 1)
            
            img = renderer.render_frame(spectrogram[si], onset_norm[oi])
            Image.fromarray(img).save(pattern % fi)
            
            if fi % 10 == 0:
                print(f"   {fi+1}/{total_frames} ({100*(fi+1)/total_frames:.0f}%)", flush=True)
        
        # Encode
        print("🎬 Encoding...", flush=True)
        audio_seg = os.path.join(tmpdir, "seg.mp3")
        subprocess.run([
            'ffmpeg', '-y', '-ss', str(args.start), '-t', str(args.duration),
            '-i', args.audio, '-c:a', 'libmp3lame', '-q:a', '2', audio_seg
        ], check=True, capture_output=True)
        
        subprocess.run([
            'ffmpeg', '-y',
            '-framerate', str(FPS), '-i', pattern,
            '-i', audio_seg,
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
            '-c:a', 'aac', '-b:a', '192k',
            '-pix_fmt', 'yuv420p', '-shortest',
            args.output
        ], check=True, capture_output=True)
    
    sz = os.path.getsize(args.output) / (1024 * 1024)
    print(f"✅ Done! {args.output} ({sz:.1f} MB)", flush=True)


if __name__ == "__main__":
    main()
