#!/usr/bin/env python3
"""
SYNESTHESIA - Complete 3D Merkabah Video Generator
====================================================
Generate videos with TRUE 3D perspective rendering.
"""

import sys
import os
import time
import tempfile
import subprocess

from audio_analyzer import AudioAnalyzer, AudioAnalysisConfig
from temporal_analyzer import TemporalAudioAnalyzer, TemporalConfig
from merkabah_3d_complete import Complete3DMerkabah, Complete3DConfig


def generate_complete_3d_video(audio_path: str, output_path: str, duration: float = 30):
    """Generate a complete 3D Merkabah video."""

    print("=" * 65)
    print("SYNESTHESIA - Complete 3D Merkabah Video Generator")
    print("  TRUE 3D with orbiting camera, curved planes, all elements")
    print("=" * 65)
    print(f"\nInput: {audio_path}")
    print(f"Output: {output_path}")
    print(f"Duration: {duration}s")
    sys.stdout.flush()

    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="merkabah_3d_complete_")
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

    # Create renderer
    print("\n[2/4] Creating Complete 3D Merkabah renderer...")
    sys.stdout.flush()

    config = Complete3DConfig(
        frame_width=1280,
        frame_height=720,
        glow_radius=6,
        enable_stars=True,
        enable_fire=True
    )
    renderer = Complete3DMerkabah(config)
    print("  ✓ Complete 3D renderer initialized")
    print("    - TRUE 3D perspective with orbiting camera")
    print("    - 3D curved heaven/earth planes")
    print("    - 3D Star Tetrahedron emerging from planes")
    print("    - Ophanim, Chayot, Eyes, Fire, Lightning in 3D")
    sys.stdout.flush()

    # Beat frames
    beat_frames_set = set()
    if temporal_analysis.beat_frames is not None:
        beat_frames_set = set(temporal_analysis.beat_frames.tolist())

    # Render frames
    total_frames = frame_analysis.total_frames
    print(f"\n[3/4] Rendering {total_frames} TRUE 3D frames...")
    sys.stdout.flush()

    render_start = time.time()
    for i in range(total_frames):
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
        beat_strength = float(temporal_analysis.beat_strength[i]) if i < len(temporal_analysis.beat_strength) else 0.0
        is_beat = i in beat_frames_set

        chroma = None
        if temporal_analysis.chroma is not None and i < temporal_analysis.chroma.shape[1]:
            chroma = temporal_analysis.chroma[:, i]

        renderer.update_state(
            beat_strength=beat_strength,
            is_beat=is_beat,
            pitch=pitch,
            chroma=chroma,
            rms=rms,
            bass=bass,
            treble=treble
        )

        frame = renderer.render_frame(spectrum, frequencies)
        frame.save(os.path.join(frames_dir, f"frame_{i:06d}.png"))

        if i % 30 == 0:
            elapsed = time.time() - render_start
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            eta = (total_frames - i) / rate if rate > 0 else 0
            print(f"  Frame {i}/{total_frames} ({100*i/total_frames:.1f}%) - {rate:.1f} fps, ETA: {eta:.0f}s")
            sys.stdout.flush()

    render_time = time.time() - render_start
    print(f"\n  Rendered {total_frames} frames in {render_time:.1f}s ({total_frames/render_time:.1f} fps)")
    sys.stdout.flush()

    # Encode
    print("\n[4/4] Encoding video...")
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
    print(f"\n{'='*65}")
    print(f"✅ Done! Output: {output_path} ({file_size:.1f} MB)")
    print(f"{'='*65}")

    return output_path


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Generate complete 3D Merkabah video')
    parser.add_argument('input', help='Input audio file')
    parser.add_argument('-o', '--output', default='merkabah_3d_complete.mp4')
    parser.add_argument('--duration', type=float, default=30)
    args = parser.parse_args()

    generate_complete_3d_video(args.input, args.output, args.duration)
