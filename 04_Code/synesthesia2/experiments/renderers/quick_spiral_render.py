#!/usr/bin/env python3
"""
Quick Cochlear Spiral Renderer - Fast 2D with research-optimized parameters.
Designed for rapid rendering using PIL (no PyVista overhead).
"""

import os
import sys
import numpy as np
from PIL import Image, ImageDraw
from pathlib import Path
import colorsys
import subprocess
import tempfile

# Audio
import librosa

# ============================================================================
# CONFIG
# ============================================================================

WIDTH = 1920
HEIGHT = 1080
FPS = 30
BACKGROUND = (5, 5, 15)

# Research-optimized spiral params
SPIRAL_TURNS = 3.5
NUM_FREQ_BINS = 256
TRAIL_LENGTH = 10
TRAIL_DECAY = 0.70
COLOR_SATURATION = 0.95
BRIGHTNESS_MIN = 0.35
BRIGHTNESS_MAX = 1.0


# ============================================================================
# FAST RENDERING
# ============================================================================

def freq_to_color(freq_norm, amplitude):
    """Rainbow colormap: frequency -> hue, amplitude -> brightness."""
    hue = freq_norm * 0.75  # Red to violet
    sat = COLOR_SATURATION
    val = BRIGHTNESS_MIN + amplitude * (BRIGHTNESS_MAX - BRIGHTNESS_MIN)
    r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
    return (int(r * 255), int(g * 255), int(b * 255))


def create_spiral_points(num_bins, width, height):
    """Create cochlear spiral points in screen space."""
    cx, cy = width // 2, height // 2
    max_r = min(width, height) * 0.42
    
    points = []
    for i in range(num_bins):
        t = i / (num_bins - 1)
        theta = t * SPIRAL_TURNS * 2 * np.pi
        r = 0.08 * max_r + np.sqrt(t) * 0.92 * max_r
        
        x = cx + r * np.cos(theta)
        y = cy + r * np.sin(theta)
        points.append((x, y))
    
    return points


def render_frame(draw, points, spectrum, trail_history, frame_idx):
    """Render one frame of the spiral visualization."""
    num_bins = len(spectrum)
    
    # Draw trail history (older = more faded)
    for age, old_spectrum in enumerate(reversed(trail_history)):
        alpha_factor = TRAIL_DECAY ** (age + 1)
        if alpha_factor < 0.05:
            continue
        
        for i in range(0, num_bins, 2):  # Skip every other for speed
            amp = old_spectrum[i]
            if amp < 0.1:
                continue
            
            x, y = points[i]
            freq_norm = i / (num_bins - 1)
            r, g, b = freq_to_color(freq_norm, amp)
            
            # Fade color
            r = int(r * alpha_factor)
            g = int(g * alpha_factor)
            b = int(b * alpha_factor)
            
            size = 2 + amp * 6 * alpha_factor
            draw.ellipse(
                [x - size, y - size, x + size, y + size],
                fill=(r, g, b)
            )
    
    # Draw current frame (brightest)
    # First pass: glow halos for high-amplitude bins
    for i in range(0, num_bins, 3):
        amp = spectrum[i]
        if amp < 0.4:
            continue
        
        x, y = points[i]
        freq_norm = i / (num_bins - 1)
        r, g, b = freq_to_color(freq_norm, amp * 0.5)
        
        glow_size = 5 + amp * 20
        draw.ellipse(
            [x - glow_size, y - glow_size, x + glow_size, y + glow_size],
            fill=(r // 4, g // 4, b // 4)
        )
    
    # Second pass: main dots
    for i in range(num_bins):
        amp = spectrum[i]
        if amp < 0.05:
            continue
        
        x, y = points[i]
        freq_norm = i / (num_bins - 1)
        r, g, b = freq_to_color(freq_norm, amp)
        
        # Size based on amplitude (log scale)
        log_amp = np.log1p(amp * 10) / np.log(11)
        size = 2 + log_amp * 10
        
        draw.ellipse(
            [x - size, y - size, x + size, y + size],
            fill=(r, g, b)
        )
    
    # Draw spiral spine (subtle connecting line)
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        amp = max(spectrum[i], spectrum[min(i+1, num_bins-1)])
        
        if amp > 0.05:
            freq_norm = i / (num_bins - 1)
            r, g, b = freq_to_color(freq_norm, amp * 0.3)
            draw.line([(x1, y1), (x2, y2)], fill=(r, g, b), width=1)


def main():
    audio_path = "/Users/guydvir/Project/07_Media/Papaoutai_Stromae.mp3"
    output_path = "/Users/guydvir/Project/04_Code/synesthesia2/spiral_papaoutai_quick.mp4"
    
    # Extract 10 seconds from the middle
    start_time = 140.0
    duration = 10.0
    
    print(f"🎵 Loading audio: {audio_path}", flush=True)
    print(f"   Extracting {duration}s from {start_time}s", flush=True)
    
    y, sr = librosa.load(audio_path, sr=22050, offset=start_time, duration=duration)
    
    # Compute mel spectrogram
    print("📊 Computing spectrogram...", flush=True)
    mel_spec = librosa.feature.melspectrogram(
        y=y, sr=sr, n_fft=2048, hop_length=512, n_mels=128
    )
    mel_db = librosa.power_to_db(mel_spec, ref=np.max)
    mel_norm = (mel_db - mel_db.min()) / (mel_db.max() - mel_db.min() + 1e-8)
    
    # Resize to NUM_FREQ_BINS
    from scipy.ndimage import zoom
    zoom_factor = NUM_FREQ_BINS / mel_norm.shape[0]
    spectrogram = zoom(mel_norm, (zoom_factor, 1), order=1).T  # [time, freq]
    
    total_frames = int(duration * FPS)
    frames_per_spec = len(spectrogram) / total_frames
    
    print(f"🎬 Rendering {total_frames} frames at {FPS} fps...", flush=True)
    
    # Create spiral points
    points = create_spiral_points(NUM_FREQ_BINS, WIDTH, HEIGHT)
    
    # Trail history
    trail_history = []
    
    with tempfile.TemporaryDirectory() as tmpdir:
        frame_pattern = os.path.join(tmpdir, "frame_%06d.png")
        
        for frame_idx in range(total_frames):
            # Get spectrum
            spec_idx = min(int(frame_idx * frames_per_spec), len(spectrogram) - 1)
            spectrum = spectrogram[spec_idx]
            
            # Create image
            img = Image.new('RGB', (WIDTH, HEIGHT), BACKGROUND)
            draw = ImageDraw.Draw(img)
            
            # Render
            render_frame(draw, points, spectrum, trail_history, frame_idx)
            
            # Update trail
            trail_history.append(spectrum.copy())
            if len(trail_history) > TRAIL_LENGTH:
                trail_history.pop(0)
            
            # Save
            frame_path = frame_pattern % frame_idx
            img.save(frame_path)
            
            if frame_idx % 30 == 0:
                print(f"   Frame {frame_idx+1}/{total_frames} ({100*(frame_idx+1)/total_frames:.0f}%)", flush=True)
        
        # Encode with ffmpeg + audio
        print("🎬 Encoding video with audio...", flush=True)
        
        # First extract audio segment
        audio_segment = os.path.join(tmpdir, "audio_segment.mp3")
        subprocess.run([
            'ffmpeg', '-y',
            '-ss', str(start_time),
            '-t', str(duration),
            '-i', audio_path,
            '-c:a', 'libmp3lame', '-q:a', '2',
            audio_segment
        ], check=True, capture_output=True)
        
        # Encode video
        subprocess.run([
            'ffmpeg', '-y',
            '-framerate', str(FPS),
            '-i', frame_pattern,
            '-i', audio_segment,
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '20',
            '-c:a', 'aac', '-b:a', '192k',
            '-pix_fmt', 'yuv420p',
            '-shortest',
            output_path
        ], check=True, capture_output=True)
    
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"✅ Done! {output_path} ({size_mb:.1f} MB)", flush=True)


if __name__ == "__main__":
    main()
