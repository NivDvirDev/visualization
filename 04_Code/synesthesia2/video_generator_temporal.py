"""
SYNESTHESIA 3.0 - Temporal Video Generator
===========================================
Complete pipeline for audio-to-video transformation with temporal features:
- Multi-scale audio analysis (frame, note, motif, phrase, atmosphere)
- Temporal visualization (melodic trail, rhythm pulse, harmonic aura, atmosphere)
- FFmpeg video encoding with audio sync

This generator creates videos where you can SEE the melody, FEEL the rhythm,
and SENSE the harmony - not just hear them.
"""

import numpy as np
import os
import subprocess
import tempfile
import shutil
from dataclasses import dataclass
from typing import Optional, Callable, List
from pathlib import Path
import json

from audio_analyzer import AudioAnalyzer, AudioAnalysisConfig, AnalysisResult
from temporal_analyzer import TemporalAudioAnalyzer, TemporalConfig, TemporalFeatures
from temporal_renderer import TemporalSpiralRenderer, TemporalRenderConfig


@dataclass
class TemporalVideoConfig:
    """Configuration for temporal video generation."""
    # Output settings
    output_width: int = 1280
    output_height: int = 720
    frame_rate: int = 30
    video_codec: str = "libx264"
    video_preset: str = "medium"
    video_crf: int = 20
    audio_codec: str = "aac"
    audio_bitrate: str = "320k"

    # Temporal features
    enable_melody_trail: bool = True
    enable_rhythm_pulse: bool = True
    enable_harmonic_aura: bool = True
    enable_atmosphere: bool = True

    # Processing
    temp_dir: Optional[str] = None
    keep_frames: bool = False


class TemporalVideoGenerator:
    """
    Complete SYNESTHESIA 3.0 video generation pipeline with temporal features.

    Analyzes audio at multiple time scales and generates visualizations that
    show melody, rhythm, harmony, and atmosphere - not just instantaneous spectrum.
    """

    def __init__(self, config: Optional[TemporalVideoConfig] = None):
        self.config = config or TemporalVideoConfig()

        # Audio analysis configs
        self.audio_config = AudioAnalysisConfig(frame_rate=self.config.frame_rate)
        self.temporal_config = TemporalConfig(frame_rate=self.config.frame_rate)

        # Render config
        self.render_config = TemporalRenderConfig(
            frame_width=self.config.output_width,
            frame_height=self.config.output_height,
            enable_melody_trail=self.config.enable_melody_trail,
            enable_rhythm_pulse=self.config.enable_rhythm_pulse,
            enable_harmonic_aura=self.config.enable_harmonic_aura,
            enable_atmosphere=self.config.enable_atmosphere
        )

        # Initialize analyzers
        self.frame_analyzer = AudioAnalyzer(self.audio_config)
        self.temporal_analyzer = TemporalAudioAnalyzer(self.temporal_config)

        # Initialize renderer
        self.renderer = TemporalSpiralRenderer(self.render_config, self.config.frame_rate)

    def generate(self,
                 audio_path: str,
                 output_path: str,
                 start_time: float = 0,
                 duration: Optional[float] = None,
                 progress_callback: Optional[Callable[[int, int, str], None]] = None) -> str:
        """
        Generate a SYNESTHESIA 3.0 temporal visualization video.

        Args:
            audio_path: Path to input audio file
            output_path: Path for output video file
            start_time: Start time in audio (seconds)
            duration: Duration to process (None = entire file)
            progress_callback: Optional callback(current_frame, total_frames, stage)

        Returns:
            Path to generated video
        """
        # Create temp directory
        temp_dir = self.config.temp_dir or tempfile.mkdtemp(prefix="synesthesia3_")
        frames_dir = os.path.join(temp_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)

        try:
            # Stage 1: Frame-level audio analysis
            if progress_callback:
                progress_callback(0, 100, "Analyzing frame-level audio...")

            print(f"Stage 1: Frame-level analysis of {audio_path}")
            frame_analysis = self.frame_analyzer.analyze(
                audio_path,
                start_time=start_time,
                duration=duration
            )

            total_frames = frame_analysis.total_frames
            print(f"Total frames: {total_frames}")

            # Stage 2: Temporal analysis (melody, rhythm, harmony, atmosphere)
            if progress_callback:
                progress_callback(0, 100, "Analyzing temporal features...")

            print(f"Stage 2: Temporal analysis (melody, rhythm, harmony, atmosphere)")
            temporal_features = self.temporal_analyzer.analyze(
                audio_path,
                start_time=start_time,
                duration=duration
            )

            # Stage 3: Pre-compute beat frames for synchronization
            beat_frame_set = set(temporal_features.beat_frames) if temporal_features.beat_frames is not None else set()
            downbeat_frame_set = set(temporal_features.downbeat_frames) if temporal_features.downbeat_frames is not None else set()

            # Build chord timeline
            chord_timeline = self._build_chord_timeline(temporal_features, total_frames)

            # Stage 4: Render frames with temporal features
            if progress_callback:
                progress_callback(0, total_frames, "Rendering temporal visualization...")

            print(f"Stage 3: Rendering {total_frames} frames with temporal features...")

            for frame_idx in range(total_frames):
                # Get frame-level amplitude
                amplitude = frame_analysis.amplitude_data[:, frame_idx]

                # Get temporal features for this frame
                pitch_hz = 0.0
                pitch_confidence = 0.0
                if temporal_features.pitch_contour is not None and frame_idx < len(temporal_features.pitch_contour):
                    pitch_hz = temporal_features.pitch_contour[frame_idx]
                    if temporal_features.pitch_confidence is not None:
                        pitch_confidence = temporal_features.pitch_confidence[frame_idx]

                # Check if this frame is a beat
                is_beat = frame_idx in beat_frame_set
                is_downbeat = frame_idx in downbeat_frame_set

                # Get beat strength
                beat_strength = 0.0
                if is_beat and temporal_features.beat_strength is not None:
                    if frame_idx < len(temporal_features.beat_strength):
                        beat_strength = temporal_features.beat_strength[frame_idx]

                # Get chord for this frame
                chord_label = chord_timeline.get(frame_idx, "N")

                # Get energy and tension
                energy = 0.5
                tension = 0.3
                if temporal_features.energy_curve is not None and frame_idx < len(temporal_features.energy_curve):
                    energy = float(temporal_features.energy_curve[frame_idx])
                    # Normalize
                    if temporal_features.energy_curve.max() > 0:
                        energy = energy / temporal_features.energy_curve.max()

                if temporal_features.tension_curve is not None and frame_idx < len(temporal_features.tension_curve):
                    tension = float(temporal_features.tension_curve[frame_idx])

                # Get brightness (spectral centroid normalized)
                brightness = 0.5
                if temporal_features.spectral_centroid is not None and frame_idx < len(temporal_features.spectral_centroid):
                    centroid = temporal_features.spectral_centroid[frame_idx]
                    # Normalize to 0-1 (assuming 0-4000 Hz range)
                    brightness = min(1.0, centroid / 4000)

                # Update renderer with temporal features
                self.renderer.update_temporal_features(
                    pitch_hz=float(pitch_hz) if pitch_hz else 0,
                    pitch_confidence=float(pitch_confidence) if pitch_confidence else 0,
                    is_beat=is_beat,
                    is_downbeat=is_downbeat,
                    beat_strength=float(beat_strength),
                    chord_label=chord_label,
                    energy=energy,
                    tension=tension,
                    brightness=brightness
                )

                # Render frame
                frame_path = os.path.join(frames_dir, f"frame_{frame_idx:06d}.png")
                self.renderer.save_frame(
                    amplitude_data=amplitude,
                    output_path=frame_path,
                    frame_idx=frame_idx,
                    frequencies=frame_analysis.frequencies
                )

                # Progress
                if progress_callback and frame_idx % 10 == 0:
                    progress_callback(frame_idx, total_frames, "Rendering temporal visualization...")

                if frame_idx % 100 == 0:
                    print(f"  Frame {frame_idx}/{total_frames}")

            # Stage 5: Encode video with FFmpeg
            if progress_callback:
                progress_callback(total_frames, total_frames, "Encoding video...")

            print(f"Stage 4: Encoding video with FFmpeg...")
            self._encode_video(
                frames_dir=frames_dir,
                audio_path=audio_path,
                output_path=output_path,
                start_time=start_time,
                duration=duration or frame_analysis.duration_seconds
            )

            print(f"✅ Video saved to: {output_path}")

            # Save metadata
            self._save_metadata(output_path, audio_path, frame_analysis, temporal_features)

            return output_path

        finally:
            if not self.config.keep_frames:
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _build_chord_timeline(self, temporal_features: TemporalFeatures,
                               total_frames: int) -> dict:
        """Build frame-to-chord mapping."""
        timeline = {}

        if temporal_features.chord_frames is None or len(temporal_features.chord_labels) == 0:
            return timeline

        chord_frames = temporal_features.chord_frames
        chord_labels = temporal_features.chord_labels

        current_chord_idx = 0
        for frame_idx in range(total_frames):
            # Check if we've passed to next chord
            while (current_chord_idx < len(chord_frames) - 1 and
                   frame_idx >= chord_frames[current_chord_idx + 1]):
                current_chord_idx += 1

            if current_chord_idx < len(chord_labels):
                timeline[frame_idx] = chord_labels[current_chord_idx]

        return timeline

    def _encode_video(self, frames_dir: str, audio_path: str, output_path: str,
                      start_time: float, duration: float):
        """Encode frames to video with FFmpeg."""
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(self.config.frame_rate),
            "-i", os.path.join(frames_dir, "frame_%06d.png"),
            "-ss", str(start_time),
            "-t", str(duration),
            "-i", audio_path,
            "-c:v", self.config.video_codec,
            "-preset", self.config.video_preset,
            "-crf", str(self.config.video_crf),
            "-c:a", self.config.audio_codec,
            "-b:a", self.config.audio_bitrate,
            "-pix_fmt", "yuv420p",
            "-shortest",
            output_path
        ]

        print(f"Running FFmpeg...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"FFmpeg error: {result.stderr}")
            raise RuntimeError(f"FFmpeg encoding failed")

    def _save_metadata(self, video_path: str, audio_path: str,
                       frame_analysis: AnalysisResult,
                       temporal_features: TemporalFeatures):
        """Save generation metadata."""
        metadata = {
            "generator": "SYNESTHESIA 3.0 - Temporal",
            "audio_source": os.path.basename(audio_path),
            "duration_seconds": frame_analysis.duration_seconds,
            "total_frames": frame_analysis.total_frames,
            "resolution": f"{self.config.output_width}x{self.config.output_height}",
            "frame_rate": self.config.frame_rate,
            "temporal_features": {
                "melody_trail": self.config.enable_melody_trail,
                "rhythm_pulse": self.config.enable_rhythm_pulse,
                "harmonic_aura": self.config.enable_harmonic_aura,
                "atmosphere": self.config.enable_atmosphere,
            },
            "detected_tempo": float(temporal_features.tempo) if temporal_features.tempo else None,
            "detected_chords": temporal_features.chord_labels[:10] if temporal_features.chord_labels else [],
        }

        metadata_path = video_path.rsplit(".", 1)[0] + "_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)


def generate_temporal_demo(output_path: str = "synesthesia3_demo.mp4",
                           duration_seconds: float = 8.0):
    """
    Generate a demo video with synthetic audio showcasing temporal features.
    """
    import wave
    import struct

    print("=" * 60)
    print("SYNESTHESIA 3.0 - Temporal Demo Generation")
    print("=" * 60)

    # Create synthetic audio
    print("\n1. Creating synthetic musical audio...")

    sample_rate = 44100
    num_samples = int(duration_seconds * sample_rate)
    t = np.linspace(0, duration_seconds, num_samples)

    audio = np.zeros(num_samples)

    # Create a chord progression: C -> Am -> F -> G
    chord_duration = duration_seconds / 4
    chords = [
        [261.63, 329.63, 392.00],  # C major: C E G
        [220.00, 261.63, 329.63],  # A minor: A C E
        [174.61, 220.00, 261.63],  # F major: F A C
        [196.00, 246.94, 293.66],  # G major: G B D
    ]

    # Add melody on top
    melody_notes = [
        (523.25, 0.5), (587.33, 0.5), (659.25, 1.0),  # C5 D5 E5
        (523.25, 0.5), (493.88, 0.5), (440.00, 1.0),  # C5 B4 A4
        (349.23, 0.5), (392.00, 0.5), (440.00, 1.0),  # F4 G4 A4
        (392.00, 1.0), (329.63, 0.5), (293.66, 0.5),  # G4 E4 D4
    ]

    # Generate chord tones
    for chord_idx, chord_freqs in enumerate(chords):
        start_time = chord_idx * chord_duration
        start_sample = int(start_time * sample_rate)
        end_sample = int((start_time + chord_duration) * sample_rate)

        chord_t = t[start_sample:end_sample] - start_time

        for freq in chord_freqs:
            # Envelope
            env = np.exp(-0.5 * chord_t)
            audio[start_sample:end_sample] += env * 0.15 * np.sin(2 * np.pi * freq * chord_t)

            # Harmonics
            for h in [2, 3]:
                audio[start_sample:end_sample] += env * 0.05 / h * np.sin(2 * np.pi * freq * h * chord_t)

    # Generate melody
    current_time = 0
    for freq, dur in melody_notes:
        start_sample = int(current_time * sample_rate)
        end_sample = int((current_time + dur) * sample_rate)

        if end_sample > num_samples:
            break

        note_t = t[start_sample:end_sample] - current_time
        env = np.exp(-2 * note_t / dur)

        audio[start_sample:end_sample] += env * 0.25 * np.sin(2 * np.pi * freq * note_t)

        # Harmonics
        for h in [2, 3, 4]:
            audio[start_sample:end_sample] += env * 0.08 / h * np.sin(2 * np.pi * freq * h * note_t)

        current_time += dur

    # Add subtle bass
    bass_freq = 65.41  # C2
    audio += 0.15 * np.sin(2 * np.pi * bass_freq * t) * (1 + 0.3 * np.sin(2 * np.pi * 2 * t))

    # Add rhythm (kick-like pulse)
    beat_period = 0.5  # 120 BPM
    for beat_time in np.arange(0, duration_seconds, beat_period):
        start_sample = int(beat_time * sample_rate)
        end_sample = min(start_sample + int(0.1 * sample_rate), num_samples)

        kick_t = np.linspace(0, 0.1, end_sample - start_sample)
        kick = np.exp(-30 * kick_t) * np.sin(2 * np.pi * 60 * kick_t)
        audio[start_sample:end_sample] += 0.3 * kick

    # Normalize
    audio = audio / np.max(np.abs(audio)) * 0.85

    # Convert to 16-bit
    audio_int = (audio * 32767).astype(np.int16)

    # Write WAV file
    temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    with wave.open(temp_audio.name, 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(audio_int.tobytes())

    print(f"   Created: {temp_audio.name}")

    # Generate video
    print("\n2. Generating temporal visualization video...")

    config = TemporalVideoConfig(
        output_width=1280,
        output_height=720,
        frame_rate=30,
        enable_melody_trail=True,
        enable_rhythm_pulse=True,
        enable_harmonic_aura=True,
        enable_atmosphere=True
    )

    generator = TemporalVideoGenerator(config)

    try:
        generator.generate(
            audio_path=temp_audio.name,
            output_path=output_path,
            duration=duration_seconds
        )
    finally:
        os.unlink(temp_audio.name)

    # Report
    file_size = os.path.getsize(output_path) / 1024
    print(f"\n✅ Demo video generated!")
    print(f"   Output: {output_path}")
    print(f"   Size: {file_size:.1f} KB")
    print(f"   Duration: {duration_seconds}s @ {config.frame_rate}fps")

    return output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SYNESTHESIA 3.0 Temporal Video Generator")
    parser.add_argument("audio_file", nargs="?", help="Path to audio file")
    parser.add_argument("--output", "-o", default="output_temporal.mp4", help="Output video path")
    parser.add_argument("--start", "-s", type=float, default=0, help="Start time (seconds)")
    parser.add_argument("--duration", "-d", type=float, help="Duration (seconds)")
    parser.add_argument("--demo", action="store_true", help="Generate demo with synthetic audio")
    parser.add_argument("--no-melody", action="store_true", help="Disable melody trail")
    parser.add_argument("--no-rhythm", action="store_true", help="Disable rhythm pulse")
    parser.add_argument("--no-harmony", action="store_true", help="Disable harmonic aura")
    parser.add_argument("--no-atmosphere", action="store_true", help="Disable atmosphere")

    args = parser.parse_args()

    if args.demo:
        generate_temporal_demo(args.output, duration_seconds=args.duration or 8.0)
    elif args.audio_file:
        config = TemporalVideoConfig(
            enable_melody_trail=not args.no_melody,
            enable_rhythm_pulse=not args.no_rhythm,
            enable_harmonic_aura=not args.no_harmony,
            enable_atmosphere=not args.no_atmosphere
        )

        generator = TemporalVideoGenerator(config)
        generator.generate(
            audio_path=args.audio_file,
            output_path=args.output,
            start_time=args.start,
            duration=args.duration
        )
    else:
        parser.print_help()
