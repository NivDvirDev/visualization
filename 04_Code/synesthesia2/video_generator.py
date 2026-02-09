"""
SYNESTHESIA 2.0 - Video Generator
Complete pipeline for audio-to-video transformation.

Integrates:
- Audio analysis (audio_analyzer.py)
- 2D spiral rendering (spiral_renderer_2d.py) - Fast, reliable PIL-based renderer
- FFmpeg video encoding
- AI classification overlay (Phase 2)
"""

import numpy as np
import os
import subprocess
import tempfile
import shutil
from dataclasses import dataclass
from typing import Optional, Callable
from pathlib import Path
import json

from audio_analyzer import AudioAnalyzer, AudioAnalysisConfig, AnalysisResult
from spiral_renderer_2d import FastSpiralRenderer, Render2DConfig


@dataclass
class VideoConfig:
    """Configuration for video generation."""
    # Output settings
    output_width: int = 1920
    output_height: int = 1080
    frame_rate: int = 60
    video_codec: str = "libx264"
    video_preset: str = "slow"
    video_crf: int = 18  # Quality (lower = better, 18 is visually lossless)
    audio_codec: str = "aac"
    audio_bitrate: str = "320k"

    # 4K option
    use_4k: bool = False  # Set True for 3840x2160

    # Processing
    temp_dir: Optional[str] = None
    keep_frames: bool = False  # Keep individual frames after encoding

    # AI overlay (Phase 2)
    enable_ai_overlay: bool = False
    ai_model_path: Optional[str] = None

    def __post_init__(self):
        if self.use_4k:
            self.output_width = 3840
            self.output_height = 2160


class VideoGenerator:
    """
    Complete SYNESTHESIA video generation pipeline.
    """

    def __init__(self,
                 video_config: Optional[VideoConfig] = None,
                 audio_config: Optional[AudioAnalysisConfig] = None,
                 render_config: Optional[Render2DConfig] = None):

        self.video_config = video_config or VideoConfig()
        self.audio_config = audio_config or AudioAnalysisConfig(
            frame_rate=self.video_config.frame_rate
        )
        self.render_config = render_config or Render2DConfig(
            frame_width=self.video_config.output_width,
            frame_height=self.video_config.output_height
        )

        self.analyzer = AudioAnalyzer(self.audio_config)
        self.renderer = FastSpiralRenderer(self.render_config)

        # AI classifier (Phase 2)
        self.classifier = None
        if self.video_config.enable_ai_overlay:
            self._load_classifier()

    def _load_classifier(self):
        """Load AI classifier for overlay (Phase 2)."""
        try:
            from ai_overlay import AIOverlayClassifier
            self.classifier = AIOverlayClassifier(self.video_config.ai_model_path)
            print("AI classifier loaded successfully")
        except ImportError:
            print("AI overlay not available (Phase 2 not implemented)")
            self.classifier = None

    def generate(self,
                 audio_path: str,
                 output_path: str,
                 start_time: float = 0,
                 duration: Optional[float] = None,
                 progress_callback: Optional[Callable[[int, int, str], None]] = None) -> str:
        """
        Generate a SYNESTHESIA visualization video.

        Args:
            audio_path: Path to input audio file
            output_path: Path for output video file
            start_time: Start time in audio (seconds)
            duration: Duration to process (None = entire file)
            progress_callback: Optional callback(current_frame, total_frames, stage)

        Returns:
            Path to generated video
        """
        # Create temp directory for frames
        temp_dir = self.video_config.temp_dir or tempfile.mkdtemp(prefix="synesthesia_")
        frames_dir = os.path.join(temp_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)

        try:
            # Stage 1: Analyze audio
            if progress_callback:
                progress_callback(0, 100, "Analyzing audio...")

            print(f"Analyzing audio: {audio_path}")
            analysis = self.analyzer.analyze(
                audio_path,
                start_time=start_time,
                duration=duration
            )

            total_frames = analysis.total_frames
            print(f"Total frames to render: {total_frames}")

            # Stage 2: Render frames using fast 2D renderer
            print("Rendering frames with 2D spiral renderer...")
            for frame_idx in range(total_frames):
                # Get amplitude data for this frame
                amplitude = analysis.amplitude_data[:, frame_idx]

                # Render frame using fast PIL-based 2D renderer
                frame_path = os.path.join(frames_dir, f"frame_{frame_idx:06d}.png")
                self.renderer.save_frame(
                    amplitude_data=amplitude,
                    output_path=frame_path,
                    frame_idx=frame_idx,
                    frequencies=analysis.frequencies
                )

                # AI overlay (Phase 2)
                if self.classifier:
                    self._add_ai_overlay(frame_path, amplitude, analysis.frequencies)

                # Progress callback
                if progress_callback and frame_idx % 10 == 0:
                    progress_callback(frame_idx, total_frames, "Rendering frames...")

                if frame_idx % 100 == 0:
                    print(f"  Rendered frame {frame_idx}/{total_frames}")

            # Stage 3: Encode video with FFmpeg
            if progress_callback:
                progress_callback(total_frames, total_frames, "Encoding video...")

            print("Encoding video with FFmpeg...")
            self._encode_video(
                frames_dir=frames_dir,
                audio_path=audio_path,
                output_path=output_path,
                start_time=start_time,
                duration=duration or analysis.duration_seconds
            )

            print(f"Video saved to: {output_path}")

            # Save metadata
            self._save_metadata(output_path, audio_path, analysis)

            return output_path

        finally:
            # Cleanup
            if not self.video_config.keep_frames:
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _add_ai_overlay(self, frame_path: str, amplitude: np.ndarray, frequencies: np.ndarray):
        """Add AI classification overlay to frame (Phase 2)."""
        if self.classifier is None:
            return

        # This will be implemented in Phase 2
        # - Load frame
        # - Run through classifier
        # - Add instrument label, confidence, attention heatmap
        pass

    def _encode_video(self,
                      frames_dir: str,
                      audio_path: str,
                      output_path: str,
                      start_time: float,
                      duration: float):
        """
        Encode frames to video with FFmpeg.
        Matches the MATLAB/FFmpeg pipeline from RunSound8AndCP.sh
        """
        # Build FFmpeg command
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-framerate", str(self.video_config.frame_rate),
            "-i", os.path.join(frames_dir, "frame_%06d.png"),
            "-ss", str(start_time),
            "-t", str(duration),
            "-i", audio_path,
            "-c:v", self.video_config.video_codec,
            "-preset", self.video_config.video_preset,
            "-crf", str(self.video_config.video_crf),
            "-c:a", self.video_config.audio_codec,
            "-b:a", self.video_config.audio_bitrate,
            "-pix_fmt", "yuv420p",
            "-vf", f"scale={self.video_config.output_width}:{self.video_config.output_height}",
            "-shortest",
            output_path
        ]

        print(f"Running FFmpeg: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"FFmpeg error: {result.stderr}")
            raise RuntimeError(f"FFmpeg encoding failed: {result.stderr}")

    def _save_metadata(self, video_path: str, audio_path: str, analysis: AnalysisResult):
        """Save generation metadata alongside video."""
        metadata = {
            "audio_source": os.path.basename(audio_path),
            "duration_seconds": analysis.duration_seconds,
            "total_frames": analysis.total_frames,
            "sample_rate": analysis.sample_rate,
            "frequency_range": [float(analysis.frequencies[0]), float(analysis.frequencies[-1])],
            "num_frequency_bins": len(analysis.frequencies),
            "resolution": f"{self.video_config.output_width}x{self.video_config.output_height}",
            "frame_rate": self.video_config.frame_rate,
            "generator": "SYNESTHESIA 2.0",
            "ai_overlay_enabled": self.video_config.enable_ai_overlay
        }

        metadata_path = video_path.rsplit(".", 1)[0] + "_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)


def generate_demo_video(output_path: str = "demo_synesthesia.mp4",
                        duration_seconds: float = 10.0):
    """
    Generate a demo video with synthetic audio.
    Useful for testing the pipeline without real audio.
    """
    import wave
    import struct

    # Create synthetic audio file
    temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)

    sample_rate = 44100
    num_samples = int(duration_seconds * sample_rate)

    # Generate synthetic music (chord progression with harmonics)
    t = np.linspace(0, duration_seconds, num_samples)

    # Base frequencies (C major chord progression)
    audio = np.zeros(num_samples)

    # Add multiple harmonics that change over time
    for i, freq in enumerate([261.63, 329.63, 392.00, 523.25]):  # C4, E4, G4, C5
        # Amplitude envelope
        envelope = 0.5 * (1 + np.sin(2 * np.pi * 0.5 * t + i * np.pi / 4))
        audio += envelope * 0.2 * np.sin(2 * np.pi * freq * t)

        # Add harmonics
        for h in range(2, 5):
            audio += envelope * 0.1 / h * np.sin(2 * np.pi * freq * h * t)

    # Add some bass
    bass_freq = 65.41  # C2
    audio += 0.3 * np.sin(2 * np.pi * bass_freq * t)

    # Normalize
    audio = audio / np.max(np.abs(audio)) * 0.8

    # Convert to 16-bit
    audio_int = (audio * 32767).astype(np.int16)

    # Write WAV file
    with wave.open(temp_audio.name, 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(audio_int.tobytes())

    print(f"Created synthetic audio: {temp_audio.name}")

    # Generate video
    config = VideoConfig(
        output_width=1280,
        output_height=720,
        frame_rate=30,  # Lower for faster demo
        video_crf=23
    )

    generator = VideoGenerator(video_config=config)

    try:
        generator.generate(
            audio_path=temp_audio.name,
            output_path=output_path,
            duration=duration_seconds,
            progress_callback=lambda c, t, s: print(f"{s} {c}/{t}")
        )
    finally:
        os.unlink(temp_audio.name)

    return output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SYNESTHESIA 2.0 Video Generator")
    parser.add_argument("audio_file", nargs="?", help="Path to audio file")
    parser.add_argument("--output", "-o", default="output.mp4", help="Output video path")
    parser.add_argument("--start", "-s", type=float, default=0, help="Start time (seconds)")
    parser.add_argument("--duration", "-d", type=float, help="Duration (seconds)")
    parser.add_argument("--width", type=int, default=1920, help="Output width")
    parser.add_argument("--height", type=int, default=1080, help="Output height")
    parser.add_argument("--fps", type=int, default=60, help="Frame rate")
    parser.add_argument("--4k", dest="use_4k", action="store_true", help="Use 4K resolution")
    parser.add_argument("--demo", action="store_true", help="Generate demo with synthetic audio")
    parser.add_argument("--keep-frames", action="store_true", help="Keep rendered frames")

    args = parser.parse_args()

    if args.demo:
        generate_demo_video(args.output, duration_seconds=args.duration or 10.0)
    elif args.audio_file:
        config = VideoConfig(
            output_width=args.width,
            output_height=args.height,
            frame_rate=args.fps,
            use_4k=args.use_4k,
            keep_frames=args.keep_frames
        )

        generator = VideoGenerator(video_config=config)
        generator.generate(
            audio_path=args.audio_file,
            output_path=args.output,
            start_time=args.start,
            duration=args.duration
        )
    else:
        parser.print_help()
