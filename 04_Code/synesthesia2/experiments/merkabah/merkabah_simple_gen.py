#!/usr/bin/env python3
"""Simple Merkabah video generator for debugging."""

import sys
import os
import time
import tempfile
import subprocess

from audio_analyzer import AudioAnalyzer, AudioAnalysisConfig
from temporal_analyzer import TemporalAudioAnalyzer, TemporalConfig
from merkabah_renderer import MerkabahRenderer, MerkabahConfig


def generate_merkabah_video(audio_path: str, output_path: str, duration: float = 30):
    """Generate a Merkabah video with minimal overhead."""

    print(f"Input: {audio_path}")
    print(f"Output: {output_path}")
    print(f"Duration: {duration}s")
    sys.stdout.flush()

    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="merkabah_simple_")
    frames_dir = os.path.join(temp_dir, "frames")
    os.makedirs(frames_dir)
    print(f"Frames dir: {frames_dir}")
    sys.stdout.flush()

    # Analyze audio
    print("\nAnalyzing audio...")
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
    print("\nCreating Merkabah renderer...")
    sys.stdout.flush()

    config = MerkabahConfig(frame_width=1280, frame_height=720)
    renderer = MerkabahRenderer(config)

    # Pre-calculate beat frames
    beat_frames_set = set()
    if temporal_analysis.beat_frames is not None:
        beat_frames_set = set(temporal_analysis.beat_frames.tolist())

    # Render frames
    total_frames = frame_analysis.total_frames
    print(f"\nRendering {total_frames} frames...")
    sys.stdout.flush()

    render_start = time.time()
    for i in range(total_frames):
        # Get spectrum
        spectrum = frame_analysis.amplitude_data[:, i]
        frequencies = frame_analysis.frequencies

        # Get temporal features (with safe access)
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
            rms=rms
        )

        frame = renderer.render_frame(spectrum, frequencies)

        # Save frame
        frame_path = os.path.join(frames_dir, f"frame_{i:06d}.png")
        frame.save(frame_path)

        if i % 50 == 0:
            elapsed = time.time() - render_start
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            print(f"  Frame {i}/{total_frames} ({100*i/total_frames:.1f}%) - {rate:.1f} fps")
            sys.stdout.flush()

    render_time = time.time() - render_start
    print(f"\nRendered {total_frames} frames in {render_time:.1f}s ({total_frames/render_time:.1f} fps)")
    sys.stdout.flush()

    # Encode video
    print("\nEncoding video with FFmpeg...")
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
    print(f"\n✅ Done! Output: {output_path} ({file_size:.1f} MB)")
    sys.stdout.flush()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='Input audio file')
    parser.add_argument('-o', '--output', default='merkabah_output.mp4')
    parser.add_argument('--duration', type=float, default=30)
    args = parser.parse_args()

    generate_merkabah_video(args.input, args.output, args.duration)
