#!/usr/bin/env python3
"""
SYNESTHESIA 3.0 - Comprehensive Demo

Generates a showcase video demonstrating all temporal intelligence features:
1. Side-by-side comparison (basic vs temporal)
2. Individual feature demos (melody, rhythm, harmony, atmosphere)
3. Full combined visualization
4. Analysis overlay showing detected features

Usage:
    python demo_comprehensive.py --output demo_showcase.mp4
"""

import os
import sys
import numpy as np
from scipy.io import wavfile
import tempfile
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Tuple
import warnings

warnings.filterwarnings('ignore')


@dataclass
class DemoConfig:
    """Configuration for comprehensive demo."""
    output_width: int = 1920
    output_height: int = 1080
    frame_rate: int = 60
    segment_duration: float = 8.0  # Duration of each demo segment
    video_crf: int = 18


def generate_rich_demo_audio(duration: float = 40.0, sample_rate: int = 44100) -> str:
    """
    Generate rich demo audio with clear musical features:
    - Strong melody with pitch changes
    - Clear rhythm with beats
    - Chord progression
    - Dynamic energy changes
    """
    print("🎵 Generating rich demo audio...")

    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = np.zeros_like(t)

    # === SECTION 1: Melody Focus (0-10s) ===
    # Clear ascending/descending melody
    section1_end = int(10 * sample_rate)
    t1 = t[:section1_end]

    # Melody: C4 -> E4 -> G4 -> C5 -> G4 -> E4 -> C4
    melody_notes = [261.6, 329.6, 392.0, 523.3, 392.0, 329.6, 261.6]
    note_duration = 10.0 / len(melody_notes)

    for i, freq in enumerate(melody_notes):
        start_idx = int(i * note_duration * sample_rate)
        end_idx = int((i + 1) * note_duration * sample_rate)
        end_idx = min(end_idx, section1_end)

        # Apply envelope
        note_t = np.linspace(0, 1, end_idx - start_idx)
        envelope = np.exp(-2 * note_t) * (1 - np.exp(-50 * note_t))

        audio[start_idx:end_idx] += 0.5 * envelope * np.sin(2 * np.pi * freq * t[start_idx:end_idx])
        # Add harmonics for richer tone
        audio[start_idx:end_idx] += 0.2 * envelope * np.sin(4 * np.pi * freq * t[start_idx:end_idx])

    # === SECTION 2: Rhythm Focus (10-20s) ===
    section2_start = int(10 * sample_rate)
    section2_end = int(20 * sample_rate)

    # Strong kick drum at 120 BPM
    beat_interval = 0.5  # 120 BPM
    for beat_time in np.arange(10, 20, beat_interval):
        beat_idx = int(beat_time * sample_rate)
        decay_len = int(0.15 * sample_rate)
        decay = np.exp(-15 * np.linspace(0, 0.15, decay_len))

        end_idx = min(beat_idx + decay_len, len(audio))
        actual_len = end_idx - beat_idx

        # Kick drum (low frequency pulse)
        audio[beat_idx:end_idx] += 0.4 * decay[:actual_len] * np.sin(
            2 * np.pi * 60 * t[beat_idx:end_idx]
        )

        # Hi-hat on off-beats (every other beat)
        if int((beat_time - 10) / beat_interval) % 2 == 1:
            noise = np.random.randn(actual_len) * decay[:actual_len] * 0.1
            audio[beat_idx:end_idx] += noise

    # Add sustained bass note
    audio[section2_start:section2_end] += 0.2 * np.sin(
        2 * np.pi * 110 * t[section2_start:section2_end]
    )

    # === SECTION 3: Harmony Focus (20-30s) ===
    section3_start = int(20 * sample_rate)
    section3_end = int(30 * sample_rate)

    # Clear chord progression: C -> Am -> F -> G
    chords = [
        ([261.6, 329.6, 392.0], "C"),   # C major
        ([220.0, 261.6, 329.6], "Am"),  # A minor
        ([349.2, 440.0, 523.3], "F"),   # F major
        ([392.0, 493.9, 587.3], "G"),   # G major
    ]

    chord_duration = 2.5  # seconds per chord
    for i, (chord_freqs, chord_name) in enumerate(chords):
        start_idx = section3_start + int(i * chord_duration * sample_rate)
        end_idx = start_idx + int(chord_duration * sample_rate)
        end_idx = min(end_idx, section3_end)

        chord_t = np.linspace(0, chord_duration, end_idx - start_idx)
        envelope = 0.8 * (1 - np.exp(-10 * chord_t)) * np.exp(-0.3 * chord_t)

        for freq in chord_freqs:
            audio[start_idx:end_idx] += 0.2 * envelope * np.sin(
                2 * np.pi * freq * t[start_idx:end_idx]
            )

    # === SECTION 4: Atmosphere Focus (30-40s) ===
    section4_start = int(30 * sample_rate)
    section4_end = int(40 * sample_rate)

    t4 = t[section4_start:section4_end]
    t4_norm = (t4 - t4[0]) / (t4[-1] - t4[0])

    # Energy builds then releases
    energy_curve = np.sin(np.pi * t4_norm)  # 0 -> 1 -> 0

    # Low drone with energy modulation
    audio[section4_start:section4_end] += 0.3 * energy_curve * np.sin(2 * np.pi * 80 * t4)

    # Mid-range pad with increasing density
    for harmonic in [1, 1.5, 2, 2.5, 3]:
        audio[section4_start:section4_end] += (
            0.1 * energy_curve * np.sin(2 * np.pi * 220 * harmonic * t4)
        )

    # High shimmer appearing at peak
    shimmer_envelope = np.clip(2 * (energy_curve - 0.5), 0, 1)
    audio[section4_start:section4_end] += (
        0.05 * shimmer_envelope * np.sin(2 * np.pi * 3000 * t4)
    )

    # Tension through dissonance at peak
    tension_envelope = np.exp(-((t4_norm - 0.5) ** 2) / 0.05)
    audio[section4_start:section4_end] += (
        0.1 * tension_envelope * np.sin(2 * np.pi * 466.2 * t4)  # Bb (tension against A)
    )

    # Normalize
    audio = audio / np.max(np.abs(audio)) * 0.9

    # Save
    temp_path = tempfile.mktemp(suffix='_demo_rich.wav')
    wavfile.write(temp_path, sample_rate, (audio * 32767).astype(np.int16))

    print(f"   Generated {duration}s audio: {temp_path}")
    return temp_path


def render_segment_basic(audio_path: str, output_dir: str, start: float, duration: float,
                         config: DemoConfig) -> str:
    """Render a segment with basic (frame-only) visualization."""
    from video_generator import VideoGenerator, VideoConfig

    video_config = VideoConfig(
        output_width=config.output_width // 2,
        output_height=config.output_height,
        frame_rate=config.frame_rate,
        video_crf=config.video_crf,
        video_preset="fast",
        keep_frames=False,
    )

    output_path = os.path.join(output_dir, f"segment_basic_{start:.0f}.mp4")

    generator = VideoGenerator(video_config=video_config)
    generator.generate(
        audio_path=audio_path,
        output_path=output_path,
        start_time=start,
        duration=duration,
    )

    return output_path


def render_segment_temporal(audio_path: str, output_dir: str, start: float, duration: float,
                           config: DemoConfig, features_enabled: dict = None) -> str:
    """Render a segment with temporal visualization."""
    from video_generator_temporal import TemporalVideoGenerator, TemporalVideoConfig

    if features_enabled is None:
        features_enabled = {
            'melody': True, 'rhythm': True, 'harmony': True, 'atmosphere': True
        }

    video_config = TemporalVideoConfig(
        output_width=config.output_width // 2,
        output_height=config.output_height,
        frame_rate=config.frame_rate,
        video_crf=config.video_crf,
        video_preset="fast",
        keep_frames=False,
        enable_melody_trail=features_enabled.get('melody', True),
        enable_rhythm_pulse=features_enabled.get('rhythm', True),
        enable_harmonic_aura=features_enabled.get('harmony', True),
        enable_atmosphere=features_enabled.get('atmosphere', True),
    )

    feature_str = "_".join([k for k, v in features_enabled.items() if v])
    output_path = os.path.join(output_dir, f"segment_temporal_{start:.0f}_{feature_str}.mp4")

    generator = TemporalVideoGenerator(config=video_config)
    generator.generate(
        audio_path=audio_path,
        output_path=output_path,
        start_time=start,
        duration=duration,
    )

    return output_path


def create_side_by_side(left_video: str, right_video: str, output_path: str,
                        left_label: str = "Basic", right_label: str = "Temporal"):
    """Combine two videos side by side with labels."""
    # FFmpeg filter for side-by-side with labels
    filter_complex = (
        f"[0:v]scale=960:1080,drawtext=text='{left_label}':fontsize=48:fontcolor=white:"
        f"x=40:y=40:shadowcolor=black:shadowx=2:shadowy=2[left];"
        f"[1:v]scale=960:1080,drawtext=text='{right_label}':fontsize=48:fontcolor=white:"
        f"x=40:y=40:shadowcolor=black:shadowx=2:shadowy=2[right];"
        f"[left][right]hstack=inputs=2[v];"
        f"[0:a][1:a]amix=inputs=2:duration=shortest[a]"
    )

    cmd = [
        'ffmpeg', '-y',
        '-i', left_video,
        '-i', right_video,
        '-filter_complex', filter_complex,
        '-map', '[v]', '-map', '[a]',
        '-c:v', 'libx264', '-crf', '18', '-preset', 'fast',
        '-c:a', 'aac', '-b:a', '192k',
        output_path
    ]

    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def create_title_card(text: str, subtext: str, duration: float, output_path: str,
                      width: int = 1920, height: int = 1080, fps: int = 60):
    """Create a title card video."""
    # Use FFmpeg to create title card
    filter_str = (
        f"color=c=black:s={width}x{height}:d={duration}:r={fps},"
        f"drawtext=text='{text}':fontsize=72:fontcolor=white:"
        f"x=(w-text_w)/2:y=(h-text_h)/2-50:font=monospace,"
        f"drawtext=text='{subtext}':fontsize=36:fontcolor=#888888:"
        f"x=(w-text_w)/2:y=(h-text_h)/2+50:font=monospace"
    )

    cmd = [
        'ffmpeg', '-y',
        '-f', 'lavfi', '-i', filter_str,
        '-f', 'lavfi', '-i', f'anullsrc=channel_layout=stereo:sample_rate=44100:d={duration}',
        '-c:v', 'libx264', '-crf', '18', '-preset', 'fast',
        '-c:a', 'aac',
        '-shortest',
        output_path
    ]

    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def concat_videos(video_paths: List[str], output_path: str):
    """Concatenate multiple videos."""
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Create concat file
    concat_file = tempfile.mktemp(suffix='.txt')
    with open(concat_file, 'w') as f:
        for path in video_paths:
            # Use absolute paths for safety
            abs_path = os.path.abspath(path)
            f.write(f"file '{abs_path}'\n")

    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat', '-safe', '0',
        '-i', concat_file,
        '-c:v', 'libx264', '-crf', '18', '-preset', 'medium',
        '-c:a', 'aac', '-b:a', '192k',
        os.path.abspath(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFmpeg concat error: {result.stderr}")
        raise RuntimeError(f"FFmpeg concat failed: {result.stderr}")

    os.remove(concat_file)
    return output_path


def generate_comprehensive_demo(output_path: str, config: DemoConfig = None):
    """Generate the comprehensive demo showcasing all features."""

    if config is None:
        config = DemoConfig()

    print("\n" + "=" * 60)
    print("   SYNESTHESIA 3.0 - Comprehensive Demo Generator")
    print("=" * 60 + "\n")

    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix='synesthesia_demo_')
    print(f"📁 Working directory: {temp_dir}\n")

    try:
        # 1. Generate demo audio
        audio_path = generate_rich_demo_audio(duration=40.0)

        segments = []

        # 2. Create intro title card
        print("\n📽️ Creating intro title card...")
        intro_path = os.path.join(temp_dir, "intro.mp4")
        create_title_card(
            "SYNESTHESIA 3.0",
            "Temporal Intelligence Edition",
            3.0, intro_path, config.output_width, config.output_height
        )
        segments.append(intro_path)

        # 3. Section 1: Side-by-side comparison (Melody focus)
        print("\n🎼 Section 1: Melody Focus (Side-by-Side)...")

        title1_path = os.path.join(temp_dir, "title1.mp4")
        create_title_card(
            "MELODIC TRAIL",
            "Pitch history as glowing particles",
            2.0, title1_path, config.output_width, config.output_height
        )
        segments.append(title1_path)

        basic1 = render_segment_basic(audio_path, temp_dir, 0, 8, config)
        temporal1 = render_segment_temporal(audio_path, temp_dir, 0, 8, config,
                                           {'melody': True, 'rhythm': False, 'harmony': False, 'atmosphere': False})

        sbs1_path = os.path.join(temp_dir, "sbs_melody.mp4")
        create_side_by_side(basic1, temporal1, sbs1_path, "Basic", "Melody Trail")
        segments.append(sbs1_path)

        # 4. Section 2: Rhythm focus
        print("\n🥁 Section 2: Rhythm Focus (Side-by-Side)...")

        title2_path = os.path.join(temp_dir, "title2.mp4")
        create_title_card(
            "RHYTHM PULSE",
            "Beat-synchronized visualization",
            2.0, title2_path, config.output_width, config.output_height
        )
        segments.append(title2_path)

        basic2 = render_segment_basic(audio_path, temp_dir, 10, 8, config)
        temporal2 = render_segment_temporal(audio_path, temp_dir, 10, 8, config,
                                           {'melody': False, 'rhythm': True, 'harmony': False, 'atmosphere': False})

        sbs2_path = os.path.join(temp_dir, "sbs_rhythm.mp4")
        create_side_by_side(basic2, temporal2, sbs2_path, "Basic", "Rhythm Pulse")
        segments.append(sbs2_path)

        # 5. Section 3: Harmony focus
        print("\n🎹 Section 3: Harmony Focus (Side-by-Side)...")

        title3_path = os.path.join(temp_dir, "title3.mp4")
        create_title_card(
            "HARMONIC AURA",
            "Chord-driven background colors",
            2.0, title3_path, config.output_width, config.output_height
        )
        segments.append(title3_path)

        basic3 = render_segment_basic(audio_path, temp_dir, 20, 8, config)
        temporal3 = render_segment_temporal(audio_path, temp_dir, 20, 8, config,
                                           {'melody': False, 'rhythm': False, 'harmony': True, 'atmosphere': False})

        sbs3_path = os.path.join(temp_dir, "sbs_harmony.mp4")
        create_side_by_side(basic3, temporal3, sbs3_path, "Basic", "Harmonic Aura")
        segments.append(sbs3_path)

        # 6. Section 4: Atmosphere focus
        print("\n🌌 Section 4: Atmosphere Focus (Side-by-Side)...")

        title4_path = os.path.join(temp_dir, "title4.mp4")
        create_title_card(
            "ATMOSPHERE FIELD",
            "Energy and tension modulation",
            2.0, title4_path, config.output_width, config.output_height
        )
        segments.append(title4_path)

        basic4 = render_segment_basic(audio_path, temp_dir, 30, 8, config)
        temporal4 = render_segment_temporal(audio_path, temp_dir, 30, 8, config,
                                           {'melody': False, 'rhythm': False, 'harmony': False, 'atmosphere': True})

        sbs4_path = os.path.join(temp_dir, "sbs_atmosphere.mp4")
        create_side_by_side(basic4, temporal4, sbs4_path, "Basic", "Atmosphere")
        segments.append(sbs4_path)

        # 7. Section 5: All features combined
        print("\n✨ Section 5: All Features Combined...")

        title5_path = os.path.join(temp_dir, "title5.mp4")
        create_title_card(
            "FULL TEMPORAL INTELLIGENCE",
            "All features combined",
            2.0, title5_path, config.output_width, config.output_height
        )
        segments.append(title5_path)

        basic_full = render_segment_basic(audio_path, temp_dir, 0, 12, config)
        temporal_full = render_segment_temporal(audio_path, temp_dir, 0, 12, config,
                                               {'melody': True, 'rhythm': True, 'harmony': True, 'atmosphere': True})

        sbs_full_path = os.path.join(temp_dir, "sbs_full.mp4")
        create_side_by_side(basic_full, temporal_full, sbs_full_path, "Basic", "Full Temporal")
        segments.append(sbs_full_path)

        # 8. Outro
        print("\n📽️ Creating outro...")
        outro_path = os.path.join(temp_dir, "outro.mp4")
        create_title_card(
            "SYNESTHESIA 3.0",
            "youtube.com/@NivDvir-ND",
            3.0, outro_path, config.output_width, config.output_height
        )
        segments.append(outro_path)

        # 9. Concatenate all segments
        print("\n🎬 Concatenating final video...")
        concat_videos(segments, output_path)

        # Get file size
        file_size = os.path.getsize(output_path) / (1024 * 1024)

        print("\n" + "=" * 60)
        print("   ✅ DEMO GENERATION COMPLETE!")
        print("=" * 60)
        print(f"\n   Output: {output_path}")
        print(f"   Size: {file_size:.1f} MB")
        print(f"\n   Sections:")
        print(f"   1. Melodic Trail - Pitch history visualization")
        print(f"   2. Rhythm Pulse - Beat-synchronized effects")
        print(f"   3. Harmonic Aura - Chord-driven colors")
        print(f"   4. Atmosphere Field - Energy/tension modulation")
        print(f"   5. Full Combined - All temporal features")
        print()

        return output_path

    finally:
        # Cleanup temp files
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        if os.path.exists(audio_path):
            os.remove(audio_path)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="SYNESTHESIA 3.0 Comprehensive Demo")
    parser.add_argument("-o", "--output", default="SYNESTHESIA_3.0_Demo.mp4",
                       help="Output video path")
    parser.add_argument("--width", type=int, default=1920, help="Output width")
    parser.add_argument("--height", type=int, default=1080, help="Output height")
    parser.add_argument("--fps", type=int, default=60, help="Frame rate")

    args = parser.parse_args()

    config = DemoConfig(
        output_width=args.width,
        output_height=args.height,
        frame_rate=args.fps,
    )

    generate_comprehensive_demo(args.output, config)


if __name__ == "__main__":
    main()
