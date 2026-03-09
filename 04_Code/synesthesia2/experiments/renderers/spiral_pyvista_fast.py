#!/usr/bin/env python3
"""
SYNESTHESIA 3.0 - Fast PyVista Cochlear Spiral Renderer

Optimized for speed: uses single tube mesh + point clouds instead of
individual sphere objects. The cochlear spiral rises vertically (3D helix).

Usage:
    python spiral_pyvista_fast.py --test
    python spiral_pyvista_fast.py audio.mp3 -o output.mp4 --duration 10 --start 140
"""

import os
import sys
import numpy as np
from pathlib import Path
import colorsys
import subprocess
import tempfile
import argparse

os.environ['PYVISTA_OFF_SCREEN'] = 'true'

import pyvista as pv
pv.OFF_SCREEN = True

import librosa
from scipy.ndimage import zoom
from PIL import Image


# ============================================================================
# CONFIG
# ============================================================================

WIDTH = 1920
HEIGHT = 1080
FPS = 30
BG_COLOR = (0.02, 0.02, 0.06)

# Spiral geometry - TALL cochlear helix
NUM_FREQ_BINS = 256
SPIRAL_TURNS = 3.5
SPIRAL_HEIGHT = 6.0        # Total vertical rise
INNER_RADIUS = 0.3
OUTER_RADIUS = 2.0

# Research-optimized visuals
TRAIL_LENGTH = 10
TRAIL_DECAY = 0.70
COLOR_SATURATION = 0.95
BRIGHTNESS_MIN = 0.35
BRIGHTNESS_MAX = 1.0

# Tube rendering
TUBE_BASE_RADIUS = 0.03
TUBE_AMP_SCALE = 0.12
TUBE_SIDES = 16


# ============================================================================
# COCHLEAR SPIRAL GEOMETRY
# ============================================================================

def create_cochlear_helix(num_bins):
    """
    Create 3D cochlear helix - spiral that rises vertically.
    Low frequencies at bottom (wide), high frequencies at top (narrow).
    """
    t = np.linspace(0, 1, num_bins)
    theta = t * SPIRAL_TURNS * 2 * np.pi
    
    # Radius: decreases as we go up (like real cochlea)
    # Wide at base (low freq), narrow at apex (high freq)
    radius = OUTER_RADIUS * (1 - t * 0.7)
    
    x = radius * np.cos(theta)
    y = radius * np.sin(theta)
    z = t * SPIRAL_HEIGHT  # Linear rise
    
    return np.column_stack([x, y, z])


# ============================================================================
# COLOR HELPERS
# ============================================================================

def freq_to_rgb(freq_norm, amplitude):
    """Rainbow colormap with research-optimized parameters."""
    hue = freq_norm * 0.75
    sat = COLOR_SATURATION
    val = BRIGHTNESS_MIN + amplitude * (BRIGHTNESS_MAX - BRIGHTNESS_MIN)
    r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
    return [r, g, b]


def spectrum_to_colors(spectrum):
    """Convert full spectrum to RGB array (0-255)."""
    n = len(spectrum)
    colors = np.zeros((n, 3), dtype=np.uint8)
    for i in range(n):
        freq_norm = i / (n - 1)
        r, g, b = freq_to_rgb(freq_norm, spectrum[i])
        colors[i] = [int(r * 255), int(g * 255), int(b * 255)]
    return colors


# ============================================================================
# FAST PYVISTA RENDERER
# ============================================================================

class FastSpiralRenderer:
    """
    Optimized PyVista renderer using single mesh operations.
    """
    
    def __init__(self):
        self.base_points = create_cochlear_helix(NUM_FREQ_BINS)
        self.trail_history = []
        self.camera_angle = 0.0
    
    def render_frame(self, spectrum, frame_idx):
        """Render a single frame. Returns numpy RGB image."""
        spectrum = np.clip(spectrum, 0, 1)
        
        # Update trail
        self.trail_history.append(spectrum.copy())
        if len(self.trail_history) > TRAIL_LENGTH:
            self.trail_history.pop(0)
        
        # Create plotter
        pl = pv.Plotter(off_screen=True, window_size=[WIDTH, HEIGHT])
        pl.set_background(BG_COLOR)
        
        # === MAIN SPIRAL TUBE ===
        # Modulate points by amplitude (push outward + up)
        points = self.base_points.copy()
        amp_boost = spectrum * TUBE_AMP_SCALE
        
        # Expand radius based on amplitude
        theta = np.linspace(0, SPIRAL_TURNS * 2 * np.pi, NUM_FREQ_BINS)
        points[:, 0] += amp_boost * np.cos(theta)
        points[:, 1] += amp_boost * np.sin(theta)
        points[:, 2] += amp_boost * 0.5  # Slight Z boost
        
        # Create spline and tube
        spline = pv.Spline(points, NUM_FREQ_BINS * 2)
        
        # Tube radius varies with amplitude
        avg_amp = np.mean(spectrum)
        tube_radius = TUBE_BASE_RADIUS + avg_amp * TUBE_AMP_SCALE * 0.3
        tube = spline.tube(radius=tube_radius, n_sides=TUBE_SIDES)
        
        # Color the tube by position along spline (frequency mapping)
        n_pts = tube.n_points
        tube_colors = np.zeros((n_pts, 3), dtype=np.uint8)
        
        # Map each tube point back to nearest spiral point for coloring
        for i in range(n_pts):
            pt = tube.points[i]
            # Find closest base point by Z coordinate (most reliable)
            z_norm = np.clip(pt[2] / SPIRAL_HEIGHT, 0, 1)
            freq_idx = int(z_norm * (NUM_FREQ_BINS - 1))
            freq_norm = freq_idx / (NUM_FREQ_BINS - 1)
            amp = spectrum[freq_idx]
            r, g, b = freq_to_rgb(freq_norm, max(amp, 0.2))
            tube_colors[i] = [int(r * 255), int(g * 255), int(b * 255)]
        
        tube['colors'] = tube_colors
        pl.add_mesh(tube, scalars='colors', rgb=True, smooth_shading=True,
                     specular=0.5, specular_power=15)
        
        # === TRAIL GHOST TUBES ===
        for age_idx, old_spectrum in enumerate(reversed(self.trail_history[:-1])):
            age = age_idx + 1
            alpha = TRAIL_DECAY ** age
            if alpha < 0.08:
                break
            
            trail_pts = self.base_points.copy()
            trail_amp = old_spectrum * TUBE_AMP_SCALE * alpha
            trail_pts[:, 0] += trail_amp * np.cos(theta)
            trail_pts[:, 1] += trail_amp * np.sin(theta)
            
            try:
                trail_spline = pv.Spline(trail_pts, NUM_FREQ_BINS)
                trail_tube = trail_spline.tube(radius=TUBE_BASE_RADIUS * alpha, n_sides=8)
                
                # Simple average color for trail
                avg_freq = 0.5
                r, g, b = freq_to_rgb(avg_freq, np.mean(old_spectrum) * alpha)
                pl.add_mesh(trail_tube, color=[r, g, b], opacity=alpha * 0.4,
                           smooth_shading=True)
            except:
                pass
        
        # === GLOW PARTICLES at peaks ===
        peaks = np.where(spectrum > 0.5)[0]
        if len(peaks) > 0:
            peak_pts = points[peaks]
            peak_cloud = pv.PolyData(peak_pts)
            
            peak_colors = np.zeros((len(peaks), 3), dtype=np.uint8)
            for j, idx in enumerate(peaks):
                freq_norm = idx / (NUM_FREQ_BINS - 1)
                r, g, b = freq_to_rgb(freq_norm, spectrum[idx])
                peak_colors[j] = [int(r * 255), int(g * 255), int(b * 255)]
            
            peak_cloud['colors'] = peak_colors
            pl.add_mesh(peak_cloud, scalars='colors', rgb=True,
                       point_size=15, render_points_as_spheres=True,
                       opacity=0.9)
        
        # === AMBIENT PARTICLES (background sparkle) ===
        n_ambient = 50
        np.random.seed(frame_idx % 100)
        amb_pts = np.random.randn(n_ambient, 3) * 1.5
        amb_pts[:, 2] = np.abs(amb_pts[:, 2]) * 2  # Keep above ground
        amb_cloud = pv.PolyData(amb_pts)
        pl.add_mesh(amb_cloud, color=[0.3, 0.4, 0.6], point_size=3,
                   render_points_as_spheres=True, opacity=0.3)
        
        # === CAMERA ===
        self.camera_angle += 1.2  # Rotation speed
        elev = 25 + 15 * np.sin(frame_idx * 0.03)
        dist = 8.0
        
        cam_x = dist * np.cos(np.radians(self.camera_angle)) * np.cos(np.radians(elev))
        cam_y = dist * np.sin(np.radians(self.camera_angle)) * np.cos(np.radians(elev))
        cam_z = SPIRAL_HEIGHT * 0.5 + dist * np.sin(np.radians(elev))
        
        pl.camera.position = (cam_x, cam_y, cam_z)
        pl.camera.focal_point = (0, 0, SPIRAL_HEIGHT * 0.45)
        pl.camera.up = (0, 0, 1)
        
        # === LIGHTING ===
        pl.enable_anti_aliasing('msaa')
        
        # Add a light
        light = pv.Light(position=(5, 5, 10), color=[1.0, 0.95, 0.9], intensity=0.8)
        pl.add_light(light)
        
        # Render
        img = pl.screenshot(return_img=True)
        pl.close()
        
        return img


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Fast PyVista Cochlear Spiral")
    parser.add_argument('audio', nargs='?', help='Input audio file')
    parser.add_argument('-o', '--output', default='spiral_pyvista_output.mp4')
    parser.add_argument('--duration', type=float, default=10.0)
    parser.add_argument('--start', type=float, default=0.0)
    parser.add_argument('--fps', type=int, default=FPS)
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()
    
    if args.test:
        print("🧪 Running test...", flush=True)
        renderer = FastSpiralRenderer()
        
        for i in range(3):
            spectrum = np.zeros(NUM_FREQ_BINS)
            for p in [40, 80, 120, 160, 200]:
                spectrum[max(0,p-8):min(NUM_FREQ_BINS,p+8)] = 0.8 - i * 0.15
            
            print(f"   Test frame {i+1}/3...", flush=True)
            img = renderer.render_frame(spectrum, i)
            out = f"/Users/guydvir/Project/04_Code/synesthesia2/spiral3d_test_{i:03d}.png"
            Image.fromarray(img).save(out)
            print(f"   Saved: {out}", flush=True)
        
        print("✅ Test done!", flush=True)
        return
    
    if not args.audio:
        parser.print_help()
        return
    
    print(f"🎵 Loading: {args.audio} (start={args.start}s, dur={args.duration}s)", flush=True)
    y, sr = librosa.load(args.audio, sr=22050, offset=args.start, duration=args.duration)
    
    print("📊 Analyzing audio...", flush=True)
    mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=2048, hop_length=512, n_mels=128)
    mel_db = librosa.power_to_db(mel_spec, ref=np.max)
    mel_norm = (mel_db - mel_db.min()) / (mel_db.max() - mel_db.min() + 1e-8)
    
    zf = NUM_FREQ_BINS / mel_norm.shape[0]
    spectrogram = zoom(mel_norm, (zf, 1), order=1).T
    
    total_frames = int(args.duration * args.fps)
    frames_per_spec = len(spectrogram) / total_frames
    
    print(f"🎬 Rendering {total_frames} frames...", flush=True)
    
    renderer = FastSpiralRenderer()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        pattern = os.path.join(tmpdir, "f_%06d.png")
        
        for fi in range(total_frames):
            si = min(int(fi * frames_per_spec), len(spectrogram) - 1)
            img = renderer.render_frame(spectrogram[si], fi)
            Image.fromarray(img).save(pattern % fi)
            
            if fi % 10 == 0:
                print(f"   {fi+1}/{total_frames} ({100*(fi+1)/total_frames:.0f}%)", flush=True)
        
        print("🎬 Encoding...", flush=True)
        
        audio_seg = os.path.join(tmpdir, "seg.mp3")
        subprocess.run([
            'ffmpeg', '-y', '-ss', str(args.start), '-t', str(args.duration),
            '-i', args.audio, '-c:a', 'libmp3lame', '-q:a', '2', audio_seg
        ], check=True, capture_output=True)
        
        subprocess.run([
            'ffmpeg', '-y',
            '-framerate', str(args.fps), '-i', pattern,
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
