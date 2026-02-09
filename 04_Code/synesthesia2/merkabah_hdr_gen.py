#!/usr/bin/env python3
"""
SYNESTHESIA - HDR Merkabah Video Generator
===========================================
Generates high-quality video using the HDR renderer with:
- 2x supersampling for anti-aliasing
- HDR bloom post-processing
- Chromatic aberration
- Film grain
- Vignette effect

Usage:
    python merkabah_hdr_gen.py input.mp3 -o output.mp4 [--duration 30]
"""

import os
import sys
import argparse
import tempfile
import shutil
import time
import subprocess
import numpy as np
import math

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from merkabah_hdr_renderer import HDRMerkabahRenderer, HDRConfig
from audio_analyzer import AudioAnalyzer, AudioAnalysisConfig
from temporal_analyzer import TemporalAudioAnalyzer, TemporalConfig


def generate_hdr_video(audio_path: str, output_path: str, duration: float = None):
    """Generate high-quality HDR video synchronized to audio."""

    print("=" * 65)
    print("SYNESTHESIA - HDR Merkabah Video Generator")
    print("  High-quality rendering with HDR bloom, supersampling, effects")
    print("=" * 65)
    print()
    print(f"Input: {audio_path}")
    print(f"Output: {output_path}")
    if duration:
        print(f"Duration: {duration}s")
    sys.stdout.flush()

    # Create temp directory for frames
    temp_dir = tempfile.mkdtemp(prefix='merkabah_hdr_')
    frames_dir = os.path.join(temp_dir, 'frames')
    os.makedirs(frames_dir)
    print(f"Frames dir: {frames_dir}")
    print()
    sys.stdout.flush()

    try:
        # Analyze audio
        print("[1/4] Analyzing audio...")
        sys.stdout.flush()

        t0 = time.time()
        frame_analyzer = AudioAnalyzer(AudioAnalysisConfig(frame_rate=30))
        frame_analysis = frame_analyzer.analyze(audio_path, duration=duration)
        print(f"  Frame analysis: {time.time()-t0:.1f}s, {frame_analysis.total_frames} frames")
        sys.stdout.flush()

        t0 = time.time()
        temporal_analyzer = TemporalAudioAnalyzer(TemporalConfig(frame_rate=30))
        temporal_analysis = temporal_analyzer.analyze(audio_path, duration=duration)
        print(f"  Temporal analysis: {time.time()-t0:.1f}s")
        sys.stdout.flush()

        num_frames = frame_analysis.total_frames

        # Create HDR renderer
        print("\n[2/4] Creating HDR renderer...")
        sys.stdout.flush()

        config = HDRConfig(
            frame_width=1280,
            frame_height=720,
            supersample=2,  # 2x supersampling
            bloom_threshold=0.55,
            bloom_intensity=0.5,
            bloom_radius=14,
            vignette_strength=0.35,
            chromatic_aberration=0.0012,
            film_grain=0.018,
            plane_resolution=20,
            num_stars=180,
            fire_particles=45,
        )
        renderer = HDRMerkabahRenderer(config)

        print("  ✓ HDR renderer initialized")
        print("    - 2x supersampling (renders at 2560x1440)")
        print("    - HDR bloom with energy conservation")
        print("    - Chromatic aberration & film grain")
        print("    - Atmospheric vignette")
        print()
        sys.stdout.flush()

        # Beat frames
        beat_frames_set = set()
        if temporal_analysis.beat_frames is not None:
            beat_frames_set = set(temporal_analysis.beat_frames.tolist())

        # Render frames
        print(f"[3/4] Rendering {num_frames} HDR frames...")
        sys.stdout.flush()

        render_start = time.time()

        for i in range(num_frames):
            spectrum = frame_analysis.amplitude_data[:, i]
            frequencies = frame_analysis.frequencies

            bass_mask = frequencies < 250
            treble_mask = frequencies >= 2000

            spec_max = spectrum.max()
            if spec_max > 0:
                spectrum_norm = spectrum / spec_max
            else:
                spectrum_norm = spectrum

            bass = float(spectrum_norm[bass_mask].mean()) if bass_mask.any() else 0.33
            treble = float(spectrum_norm[treble_mask].mean()) if treble_mask.any() else 0.33

            pitch = float(temporal_analysis.pitch_contour[i]) if i < len(temporal_analysis.pitch_contour) else 0.0
            rms = float(temporal_analysis.energy_curve[i]) if i < len(temporal_analysis.energy_curve) else 0.5

            is_beat = i in beat_frames_set
            beat_strength = 1.0 if is_beat else 0.2

            # Update renderer state
            renderer.update_state(
                beat_strength=beat_strength,
                is_beat=is_beat,
                pitch=pitch,
                rms=rms,
                bass=bass,
                treble=treble
            )

            # Render frame
            frame = renderer.render_frame(spectrum_norm, frequencies)

            # Save frame
            frame_path = os.path.join(frames_dir, f'frame_{i:06d}.png')
            frame.save(frame_path)

            # Progress report
            if i % 15 == 0 or i == num_frames - 1:
                elapsed = time.time() - render_start
                avg_fps = (i + 1) / elapsed if elapsed > 0 else 0
                eta = (num_frames - i - 1) / avg_fps if avg_fps > 0 else 0
                print(f"  Frame {i}/{num_frames} ({100*i/num_frames:.1f}%) - "
                      f"{avg_fps:.2f} fps, ETA: {eta:.0f}s")
                sys.stdout.flush()

        total_render = time.time() - render_start
        avg_fps = num_frames / total_render
        print()
        print(f"  Rendered {num_frames} frames in {total_render:.1f}s ({avg_fps:.2f} fps)")
        print()
        sys.stdout.flush()

        # Encode video
        print("[4/4] Encoding video with FFmpeg...")
        sys.stdout.flush()

        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-framerate', '30',
            '-i', os.path.join(frames_dir, 'frame_%06d.png'),
            '-i', audio_path,
            '-c:v', 'libx264',
            '-preset', 'slow',  # Better quality
            '-crf', '18',  # High quality
            '-pix_fmt', 'yuv420p',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-shortest',
            '-movflags', '+faststart',
            output_path
        ]

        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"FFmpeg error: {result.stderr}")
            return

        # Get output size
        output_size = os.path.getsize(output_path) / (1024 * 1024)

        print()
        print("=" * 65)
        print(f"✅ Done! Output: {output_path} ({output_size:.1f} MB)")
        print("=" * 65)

    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate HDR Merkabah video')
    parser.add_argument('input', help='Input audio file')
    parser.add_argument('-o', '--output', default='merkabah_hdr.mp4',
                        help='Output video path')
    parser.add_argument('--duration', type=float, default=None,
                        help='Limit duration in seconds')

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    generate_hdr_video(args.input, args.output, args.duration)
