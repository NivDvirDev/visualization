#!/usr/bin/env python3
"""
SYNESTHESIA - Original Cochlear Spiral TUBE Renderer (PyVista)

The original MATLAB piperecord11 visualization:
- Flat spiral tube with radial waves
- Camera orbiting and looking INTO the tube
- Amplitude modulates tube surface
- Wave animation propagates along spiral
- Chromesthesia color mapping

This is the "inner wave view" from the YouTube videos.

Usage:
    python spiral_tube_pyvista.py audio.mp3 -o output.mp4 --start 140 --duration 10
    python spiral_tube_pyvista.py --test
"""

import os
import sys
import numpy as np
import subprocess
import tempfile
import argparse

os.environ['PYVISTA_OFF_SCREEN'] = 'true'

import pyvista as pv
pv.OFF_SCREEN = True

import librosa
from scipy.ndimage import zoom
from PIL import Image

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))
from spiral_renderer import SpiralTubeRenderer, RenderConfig


# ============================================================================
# CONFIG
# ============================================================================

WIDTH = 1920
HEIGHT = 1080
FPS = 30


def render_video(audio_path, output_path, start=0.0, duration=10.0):
    """Render video using the original spiral tube geometry with PyVista."""
    
    print(f"🎵 Loading: {audio_path}", flush=True)
    y, sr = librosa.load(audio_path, sr=22050, offset=start, duration=duration)
    
    # Compute spectrogram
    print("📊 Analyzing audio...", flush=True)
    n_fft = 2048
    hop_length = 512
    
    S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop_length))
    
    # Resize to match renderer's expected frequency bins (381)
    config = RenderConfig(
        frame_width=WIDTH,
        frame_height=HEIGHT,
        frame_rate=FPS,
    )
    
    num_bins = config.num_frequency_bins  # 381
    
    # Create frequency axis
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    
    # Map to log scale and resize to num_bins
    if S.shape[0] != num_bins:
        zf = num_bins / S.shape[0]
        spectrogram = zoom(S, (zf, 1), order=1)
    else:
        spectrogram = S
    
    spectrogram = spectrogram.T  # [time, freq]
    
    # Normalize
    max_val = np.max(spectrogram)
    if max_val > 0:
        spectrogram = spectrogram / max_val
    
    # Scale amplitude for visible tube deformation  
    spectrogram = spectrogram * 30  # Scale factor for tube visibility
    
    total_frames = int(duration * FPS)
    frames_per_spec = len(spectrogram) / total_frames
    
    print(f"🎬 Rendering {total_frames} frames (original tube geometry, PyVista)...", flush=True)
    
    renderer = SpiralTubeRenderer(config)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        pattern = os.path.join(tmpdir, "f_%06d.png")
        
        for fi in range(total_frames):
            si = min(int(fi * frames_per_spec), len(spectrogram) - 1)
            amplitude = spectrogram[si]
            
            # Update camera motion
            renderer.update_camera(fi, total_frames)
            
            # Render with PyVista
            frame = renderer.render_frame_pyvista(
                amplitude_data=amplitude,
                frame_idx=fi,
                show_labels=False
            )
            
            Image.fromarray(frame).save(pattern % fi)
            
            if fi % 10 == 0:
                print(f"   {fi+1}/{total_frames} ({100*(fi+1)/total_frames:.0f}%)", flush=True)
        
        # Encode
        print("🎬 Encoding video...", flush=True)
        audio_seg = os.path.join(tmpdir, "seg.mp3")
        subprocess.run([
            'ffmpeg', '-y', '-ss', str(start), '-t', str(duration),
            '-i', audio_path, '-c:a', 'libmp3lame', '-q:a', '2', audio_seg
        ], check=True, capture_output=True)
        
        subprocess.run([
            'ffmpeg', '-y',
            '-framerate', str(FPS), '-i', pattern,
            '-i', audio_seg,
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
            '-c:a', 'aac', '-b:a', '192k',
            '-pix_fmt', 'yuv420p', '-shortest',
            output_path
        ], check=True, capture_output=True)
    
    sz = os.path.getsize(output_path) / (1024 * 1024)
    print(f"✅ Done! {output_path} ({sz:.1f} MB)", flush=True)


def run_test():
    """Quick test render."""
    print("🧪 Testing original tube renderer with PyVista...", flush=True)
    
    config = RenderConfig(
        frame_width=WIDTH,
        frame_height=HEIGHT,
        frame_rate=FPS,
    )
    
    renderer = SpiralTubeRenderer(config)
    
    num_bins = config.num_frequency_bins
    
    for i in range(3):
        # Synthetic amplitude
        t = np.linspace(0, 1, num_bins)
        amplitude = np.zeros(num_bins)
        for h in [0.1, 0.25, 0.4, 0.55, 0.7]:
            amplitude += 20 * np.exp(-((t - h) ** 2) / 0.01)
        amplitude += np.random.random(num_bins) * 2
        amplitude *= (1.0 - i * 0.2)
        
        renderer.update_camera(i * 30, 300)
        
        frame = renderer.render_frame_pyvista(
            amplitude_data=amplitude,
            frame_idx=i * 30,
            show_labels=False
        )
        
        out = f"/Users/guydvir/Project/04_Code/synesthesia2/tube_test_{i:03d}.png"
        Image.fromarray(frame).save(out)
        print(f"   Saved: {out}", flush=True)
    
    print("✅ Done!", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Original Cochlear Spiral Tube (PyVista)")
    parser.add_argument('audio', nargs='?')
    parser.add_argument('-o', '--output', default='spiral_tube_output.mp4')
    parser.add_argument('--duration', type=float, default=10.0)
    parser.add_argument('--start', type=float, default=0.0)
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()
    
    if args.test:
        run_test()
    elif args.audio:
        render_video(args.audio, args.output, args.start, args.duration)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
