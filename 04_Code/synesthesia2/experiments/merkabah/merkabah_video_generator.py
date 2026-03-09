#!/usr/bin/env python3
"""
SYNESTHESIA - Merkabah Sacred Geometry Video Generator
=======================================================
Video generator using Merkabah mysticism geometry from Ezekiel's vision.

The Divine Chariot visualization maps audio to sacred geometry:
- Bass frequencies → Lower tetrahedron (Earth/Foundation)
- Mid frequencies → Ophanim wheels (Movement/Rotation)
- High frequencies → Upper tetrahedron (Heaven/Spirit)
- Rhythm/Beats → Lightning flashes and rotation speed
- Melody/Pitch → Throne/Center glow
- Harmony/Chroma → Overall color temperature shift

Visual elements from Ezekiel 1:
- Star Tetrahedron (two interlocking triangles)
- Ophanim (wheels within wheels, "full of eyes")
- Four Living Creatures (Chayot) at cardinal positions
- Divine Throne at center with radiant light
- Fire moving between elements
- Lightning on strong beats

References:
- Ezekiel 1:4-28 (The Vision of the Merkabah)
- Ezekiel 10 (The Cherubim and Wheels)
"""

import numpy as np
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from typing import Optional, Callable, Tuple
from pathlib import Path
from PIL import Image

from audio_analyzer import AudioAnalyzer, AudioAnalysisConfig
from temporal_analyzer import TemporalAudioAnalyzer, TemporalConfig
from merkabah_renderer import MerkabahRenderer, MerkabahConfig
from research_optimized_config import ResearchOptimizedConfig, load_research_config


@dataclass
class MerkabahVideoConfig:
    """Configuration for Merkabah video generation."""
    output_width: int = 1280
    output_height: int = 720
    frame_rate: int = 30
    video_codec: str = "libx264"
    video_preset: str = "medium"
    video_crf: int = 18  # Higher quality for sacred geometry details
    audio_codec: str = "aac"
    audio_bitrate: str = "320k"
    temp_dir: Optional[str] = None
    keep_frames: bool = False

    # Merkabah-specific settings
    rotation_speed: float = 0.5  # Base rotation degrees per frame
    wheel_rotation_speed: float = 1.2  # Ophanim wheels rotate faster
    fire_intensity: float = 0.5
    lightning_on_beat: bool = True
    trail_length: int = 10  # From research optimization
    color_saturation: float = 0.95  # From research optimization


class MerkabahVideoGenerator:
    """
    Complete video generation pipeline using Merkabah sacred geometry.

    Integrates:
    - Audio frame analysis (spectrum, frequencies)
    - Temporal analysis (pitch, beats, chroma, energy)
    - Merkabah renderer (sacred geometry visualization)
    """

    def __init__(self, video_config: Optional[MerkabahVideoConfig] = None,
                 research_config: Optional[ResearchOptimizedConfig] = None):
        self.video_config = video_config or MerkabahVideoConfig()
        self.research_config = research_config or load_research_config()

        # Audio analysis configs
        self.audio_config = AudioAnalysisConfig(frame_rate=self.video_config.frame_rate)
        self.temporal_config = TemporalConfig(frame_rate=self.video_config.frame_rate)

        # Analyzers
        self.frame_analyzer = AudioAnalyzer(self.audio_config)
        self.temporal_analyzer = TemporalAudioAnalyzer(self.temporal_config)

        # Merkabah renderer config
        self.merkabah_config = MerkabahConfig(
            frame_width=self.video_config.output_width,
            frame_height=self.video_config.output_height,
            rotation_speed=self.video_config.rotation_speed,
            wheel_rotation_speed=self.video_config.wheel_rotation_speed,
            fire_intensity=self.video_config.fire_intensity,
            lightning_on_beat=self.video_config.lightning_on_beat,
            trail_length=self.video_config.trail_length,
            color_saturation=self.video_config.color_saturation,
            # Apply research findings where applicable
            trail_decay=self.research_config.trail_decay_rate,
            brightness_min=self.research_config.color_brightness_min,
            brightness_max=self.research_config.color_brightness_max,
        )

        # Renderer
        self.renderer = MerkabahRenderer(self.merkabah_config)

    def generate(self, audio_path: str, output_path: str,
                 start_time: float = 0, duration: Optional[float] = None,
                 progress_callback: Optional[Callable] = None) -> str:
        """
        Generate Merkabah sacred geometry visualization video.

        Args:
            audio_path: Path to input audio file
            output_path: Path for output video
            start_time: Start time in seconds
            duration: Duration in seconds (None for full audio)
            progress_callback: Optional callback(current, total, stage)

        Returns:
            Path to generated video
        """

        temp_dir = self.video_config.temp_dir or tempfile.mkdtemp(prefix="synesthesia_merkabah_")
        frames_dir = os.path.join(temp_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)

        try:
            # Analyze audio
            print("📊 Analyzing audio for Merkabah visualization...")
            frame_analysis = self.frame_analyzer.analyze(
                audio_path, start_time=start_time, duration=duration
            )
            temporal_analysis = self.temporal_analyzer.analyze(
                audio_path, start_time=start_time, duration=duration
            )

            total_frames = frame_analysis.total_frames
            print(f"   Total frames: {total_frames}")
            print(f"   Duration: {total_frames / self.video_config.frame_rate:.1f}s")
            print(f"   Resolution: {self.video_config.output_width}x{self.video_config.output_height}")

            # Pre-calculate beat frames for quick lookup
            beat_frames_set = set()
            if temporal_analysis.beat_frames is not None:
                beat_frames_set = set(temporal_analysis.beat_frames)

            # Render frames
            print("\n🔯 Rendering Merkabah sacred geometry frames...")

            for frame_idx in range(total_frames):
                # Extract audio features for this frame
                spectrum = frame_analysis.amplitude_data[:, frame_idx]
                frequencies = frame_analysis.frequencies

                # Extract temporal features
                pitch = 0.0
                confidence = 0.0
                is_beat = frame_idx in beat_frames_set
                beat_strength = 0.0
                rms = 0.5
                chroma = None

                # Pitch contour (melody)
                if (temporal_analysis.pitch_contour is not None and
                    frame_idx < len(temporal_analysis.pitch_contour)):
                    pitch = temporal_analysis.pitch_contour[frame_idx]
                    if temporal_analysis.pitch_confidence is not None:
                        confidence = temporal_analysis.pitch_confidence[frame_idx]
                    else:
                        confidence = 0.8 if pitch > 0 else 0.0

                # Beat strength (rhythm)
                if (temporal_analysis.beat_strength is not None and
                    frame_idx < len(temporal_analysis.beat_strength)):
                    beat_strength = temporal_analysis.beat_strength[frame_idx]

                # Energy/RMS
                if (temporal_analysis.energy_curve is not None and
                    frame_idx < len(temporal_analysis.energy_curve)):
                    rms = temporal_analysis.energy_curve[frame_idx]

                # Chroma (harmony)
                if (temporal_analysis.chroma is not None and
                    frame_idx < temporal_analysis.chroma.shape[1]):
                    chroma = temporal_analysis.chroma[:, frame_idx]

                # Update renderer state with audio features
                self.renderer.update_state(
                    beat_strength=beat_strength,
                    is_beat=is_beat,
                    pitch=pitch,
                    chroma=chroma,
                    rms=rms
                )

                # Render frame
                frame = self.renderer.render_frame(spectrum, frequencies)

                # Save frame (PNG without optimize for speed)
                frame_path = os.path.join(frames_dir, f"frame_{frame_idx:06d}.png")
                frame.save(frame_path)

                # Progress reporting
                if progress_callback:
                    progress_callback(frame_idx + 1, total_frames, "Rendering")
                elif frame_idx % 50 == 0:
                    pct = 100 * frame_idx / total_frames
                    print(f"   Frame {frame_idx}/{total_frames} ({pct:.1f}%)")
                    sys.stdout.flush()

            print(f"   Rendered {total_frames} frames")

            # Encode video with FFmpeg
            print("\n🎬 Encoding video with FFmpeg...")
            self._encode_video(frames_dir, audio_path, output_path, start_time, duration)

            # Calculate file size
            file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            print(f"\n✅ Merkabah visualization complete!")
            print(f"   Output: {output_path}")
            print(f"   Size: {file_size:.1f} MB")
            print(f"   Frames: {total_frames}")

            return output_path

        finally:
            if not self.video_config.keep_frames:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _encode_video(self, frames_dir: str, audio_path: str, output_path: str,
                      start_time: float, duration: Optional[float]):
        """Encode frames to video with audio using FFmpeg."""

        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-framerate', str(self.video_config.frame_rate),
            '-i', os.path.join(frames_dir, 'frame_%06d.png'),
            '-ss', str(start_time),
            '-i', audio_path,
        ]

        if duration:
            ffmpeg_cmd.extend(['-t', str(duration)])

        ffmpeg_cmd.extend([
            '-c:v', self.video_config.video_codec,
            '-preset', self.video_config.video_preset,
            '-crf', str(self.video_config.video_crf),
            '-c:a', self.video_config.audio_codec,
            '-b:a', self.video_config.audio_bitrate,
            '-pix_fmt', 'yuv420p',
            '-shortest',
            output_path
        ])

        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)


def generate_merkabah_video(audio_path: str, output_path: str,
                            start_time: float = 0,
                            duration: Optional[float] = None,
                            width: int = 1280, height: int = 720,
                            fps: int = 30) -> str:
    """
    Convenience function to generate Merkabah visualization.

    Args:
        audio_path: Path to input audio
        output_path: Path for output video
        start_time: Start time in seconds
        duration: Duration in seconds (None for full)
        width: Output width
        height: Output height
        fps: Frame rate

    Returns:
        Path to generated video
    """
    config = MerkabahVideoConfig(
        output_width=width,
        output_height=height,
        frame_rate=fps,
    )

    generator = MerkabahVideoGenerator(config)
    return generator.generate(audio_path, output_path, start_time, duration)


def main():
    """CLI for Merkabah video generation."""
    import argparse

    parser = argparse.ArgumentParser(
        description='SYNESTHESIA Merkabah Sacred Geometry Video Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python merkabah_video_generator.py song.mp3 -o merkabah_output.mp4
  python merkabah_video_generator.py song.mp3 --duration 60 --rotation 0.8
  python merkabah_video_generator.py song.mp3 --width 1920 --height 1080 --fps 60
        """
    )

    parser.add_argument('input', help='Input audio file')
    parser.add_argument('-o', '--output', default='merkabah_output.mp4',
                        help='Output video file')
    parser.add_argument('--width', type=int, default=1280, help='Output width')
    parser.add_argument('--height', type=int, default=720, help='Output height')
    parser.add_argument('--fps', type=int, default=30, help='Frame rate')
    parser.add_argument('--start', type=float, default=0, help='Start time (seconds)')
    parser.add_argument('--duration', type=float, default=None,
                        help='Duration (seconds, None for full)')
    parser.add_argument('--rotation', type=float, default=0.5,
                        help='Base rotation speed (degrees/frame)')
    parser.add_argument('--wheel-speed', type=float, default=1.2,
                        help='Ophanim wheel rotation speed')
    parser.add_argument('--fire', type=float, default=0.5,
                        help='Fire intensity (0-1)')
    parser.add_argument('--no-lightning', action='store_true',
                        help='Disable lightning effects on beats')
    parser.add_argument('--keep-frames', action='store_true',
                        help='Keep rendered frames after encoding')

    args = parser.parse_args()

    video_config = MerkabahVideoConfig(
        output_width=args.width,
        output_height=args.height,
        frame_rate=args.fps,
        rotation_speed=args.rotation,
        wheel_rotation_speed=args.wheel_speed,
        fire_intensity=args.fire,
        lightning_on_beat=not args.no_lightning,
        keep_frames=args.keep_frames,
    )

    generator = MerkabahVideoGenerator(video_config)

    print("=" * 60)
    print("  SYNESTHESIA - Merkabah Sacred Geometry Visualization")
    print("=" * 60)
    print(f"\n  Input:  {args.input}")
    print(f"  Output: {args.output}")
    print(f"  Resolution: {args.width}x{args.height} @ {args.fps}fps")
    print(f"  Rotation: {args.rotation}°/frame, Wheels: {args.wheel_speed}x")
    print(f"  Fire: {args.fire}, Lightning: {not args.no_lightning}")
    print()

    generator.generate(
        args.input,
        args.output,
        start_time=args.start,
        duration=args.duration
    )


if __name__ == '__main__':
    main()
