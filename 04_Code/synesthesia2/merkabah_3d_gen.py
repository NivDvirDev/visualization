#!/usr/bin/env python3
"""
SYNESTHESIA - 3D Merkabah Video Generator
==========================================
Generate high-quality videos with true 3D perspective rendering.

The Star Tetrahedron stretches between heaven and earth:
- Upper tetrahedron reaches toward the celestial sky
- Lower tetrahedron grounds into the earth below
- Camera orbits the sacred geometry in 3D space
"""

import sys
import os
import time
import tempfile
import subprocess

from audio_analyzer import AudioAnalyzer, AudioAnalysisConfig
from temporal_analyzer import TemporalAudioAnalyzer, TemporalConfig
from merkabah_3d_renderer import Merkabah3DRenderer, Merkabah3DConfig


def generate_merkabah_3d_video(audio_path: str, output_path: str, duration: float = 30,
                                glow_radius: int = 12, camera_speed: float = 0.3):
    """Generate a 3D Merkabah video with perspective projection."""

    print("=" * 60)
    print("SYNESTHESIA - 3D Merkabah Video Generator")
    print("=" * 60)
    print(f"\nInput: {audio_path}")
    print(f"Output: {output_path}")
    print(f"Duration: {duration}s")
    print(f"Quality: glow_radius={glow_radius}, camera_speed={camera_speed}")
    sys.stdout.flush()

    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="merkabah_3d_")
    frames_dir = os.path.join(temp_dir, "frames")
    os.makedirs(frames_dir)
    print(f"Frames dir: {frames_dir}")
    sys.stdout.flush()

    # Analyze audio
    print("\n[1/4] Analyzing audio...")
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

    # Create 3D renderer
    print("\n[2/4] Creating 3D Merkabah renderer...")
    sys.stdout.flush()

    config = Merkabah3DConfig(
        frame_width=1280,
        frame_height=720,
        glow_radius=glow_radius,
        camera_orbit_speed=camera_speed,
        enable_atmosphere=True,
        enable_stars=True,
        num_stars=250
    )
    renderer = Merkabah3DRenderer(config)
    print("  ✓ 3D renderer initialized")
    sys.stdout.flush()

    # Pre-calculate beat frames
    beat_frames_set = set()
    if temporal_analysis.beat_frames is not None:
        beat_frames_set = set(temporal_analysis.beat_frames.tolist())

    # Render frames
    total_frames = frame_analysis.total_frames
    print(f"\n[3/4] Rendering {total_frames} 3D frames...")
    print("  (Camera orbits the Merkabah in 3D space)")
    sys.stdout.flush()

    render_start = time.time()
    for i in range(total_frames):
        # Get spectrum
        spectrum = frame_analysis.amplitude_data[:, i]
        frequencies = frame_analysis.frequencies

        # Calculate band energies for renderer
        bass_mask = frequencies < 250
        mid_mask = (frequencies >= 250) & (frequencies < 2000)
        treble_mask = frequencies >= 2000

        # Normalize spectrum first
        spec_max = spectrum.max()
        if spec_max > 0:
            spectrum_norm = spectrum / spec_max
        else:
            spectrum_norm = spectrum

        bass_energy = float(spectrum_norm[bass_mask].mean()) if bass_mask.any() else 0.33
        treble_energy = float(spectrum_norm[treble_mask].mean()) if treble_mask.any() else 0.33

        # Get temporal features
        pitch = float(temporal_analysis.pitch_contour[i]) if i < len(temporal_analysis.pitch_contour) else 0.0
        rms = float(temporal_analysis.energy_curve[i]) if i < len(temporal_analysis.energy_curve) else 0.5
        beat_strength = float(temporal_analysis.beat_strength[i]) if i < len(temporal_analysis.beat_strength) else 0.0
        is_beat = i in beat_frames_set

        chroma = None
        if temporal_analysis.chroma is not None and i < temporal_analysis.chroma.shape[1]:
            chroma = temporal_analysis.chroma[:, i]

        # Update and render
        renderer.update_state(
            beat_strength=beat_strength,
            is_beat=is_beat,
            pitch=pitch,
            chroma=chroma,
            rms=rms,
            bass=bass_energy,
            treble=treble_energy
        )

        frame = renderer.render_frame(spectrum, frequencies)

        # Save frame
        frame_path = os.path.join(frames_dir, f"frame_{i:06d}.png")
        frame.save(frame_path)

        if i % 30 == 0:
            elapsed = time.time() - render_start
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            eta = (total_frames - i) / rate if rate > 0 else 0
            print(f"  Frame {i}/{total_frames} ({100*i/total_frames:.1f}%) - {rate:.1f} fps, ETA: {eta:.0f}s")
            sys.stdout.flush()

    render_time = time.time() - render_start
    print(f"\n  Rendered {total_frames} frames in {render_time:.1f}s ({total_frames/render_time:.1f} fps)")
    sys.stdout.flush()

    # Encode video
    print("\n[4/4] Encoding video with FFmpeg...")
    sys.stdout.flush()

    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-framerate', '30',
        '-i', os.path.join(frames_dir, 'frame_%06d.png'),
        '-i', audio_path,
        '-t', str(duration),
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '18',
        '-c:a', 'aac',
        '-b:a', '320k',
        '-pix_fmt', 'yuv420p',
        '-shortest',
        output_path
    ]

    subprocess.run(ffmpeg_cmd, check=True, capture_output=True)

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)

    file_size = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\n{'='*60}")
    print(f"✅ Done! Output: {output_path} ({file_size:.1f} MB)")
    print(f"{'='*60}")
    sys.stdout.flush()

    return output_path


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Generate 3D Merkabah visualization video')
    parser.add_argument('input', help='Input audio file')
    parser.add_argument('-o', '--output', default='merkabah_3d_output.mp4')
    parser.add_argument('--duration', type=float, default=30, help='Duration in seconds')
    parser.add_argument('--glow', type=int, default=12, help='Glow blur radius')
    parser.add_argument('--camera-speed', type=float, default=0.3,
                        help='Camera orbit speed (degrees per frame)')
    args = parser.parse_args()

    generate_merkabah_3d_video(
        args.input,
        args.output,
        args.duration,
        glow_radius=args.glow,
        camera_speed=args.camera_speed
    )
