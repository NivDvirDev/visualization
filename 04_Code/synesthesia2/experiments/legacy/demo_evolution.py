"""
SYNESTHESIA 3.0 - Evolution Demo
================================
Demonstrates the attention-guided visualization-classification feedback loop.

This script generates a side-by-side comparison video showing:
- LEFT: Original spiral visualization
- RIGHT: Attention-enhanced spiral visualization

The difference shows how the AI's understanding shapes what we see.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import subprocess
import tempfile
from typing import List, Tuple
import json

from spiral_renderer_2d import FastSpiralRenderer, Render2DConfig
from attention_guided_renderer import AttentionGuidedRenderer, AttentionConfig


def generate_synthetic_audio_frames(duration_seconds: float = 5.0,
                                    frame_rate: int = 30,
                                    num_freq_bins: int = 381) -> Tuple[List[np.ndarray], np.ndarray]:
    """
    Generate synthetic audio amplitude data simulating a musical phrase.
    Returns frames of amplitude data and frequency array.
    """
    total_frames = int(duration_seconds * frame_rate)
    frequencies = np.logspace(np.log10(20), np.log10(8000), num_freq_bins)

    frames = []

    # Musical notes (C major scale ascending then descending)
    notes = [
        (261.63, "C4"),  # Do
        (293.66, "D4"),  # Re
        (329.63, "E4"),  # Mi
        (349.23, "F4"),  # Fa
        (392.00, "G4"),  # Sol
        (440.00, "A4"),  # La
        (493.88, "B4"),  # Si
        (523.25, "C5"),  # Do
    ]

    notes_sequence = notes + notes[::-1][1:]  # Up and down
    note_duration_frames = total_frames // len(notes_sequence)

    for frame_idx in range(total_frames):
        amplitude = np.zeros(num_freq_bins)

        # Which note are we on?
        note_idx = min(frame_idx // note_duration_frames, len(notes_sequence) - 1)
        fundamental, _ = notes_sequence[note_idx]

        # Position within note (for envelope)
        pos_in_note = (frame_idx % note_duration_frames) / note_duration_frames
        envelope = np.exp(-2 * pos_in_note)  # Decay envelope

        # Add fundamental and harmonics
        fund_idx = np.argmin(np.abs(frequencies - fundamental))
        amplitude[fund_idx] = envelope

        # Harmonics with decreasing amplitude
        for h in range(2, 8):
            harmonic_freq = fundamental * h
            if harmonic_freq < 8000:
                h_idx = np.argmin(np.abs(frequencies - harmonic_freq))
                amplitude[h_idx] = envelope * (0.7 ** (h - 1))

        # Add some noise for realism
        amplitude += np.random.rand(num_freq_bins) * 0.02 * envelope

        frames.append(amplitude)

    return frames, frequencies


def generate_synthetic_attention(amplitude: np.ndarray,
                                 frequencies: np.ndarray,
                                 frame_idx: int) -> np.ndarray:
    """
    Generate synthetic attention map that would come from a ViT classifier.
    In production, this comes from ai_overlay.py.
    """
    # Standard ViT attention size
    attn_size = 14
    attention = np.zeros((attn_size, attn_size))

    # Find peaks in amplitude (active frequencies)
    peaks = np.where(amplitude > amplitude.max() * 0.3)[0]

    for peak_idx in peaks:
        # Map frequency index to attention grid
        rel_pos = peak_idx / len(frequencies)
        attn_x = int(rel_pos * attn_size)
        attn_y = int(rel_pos * attn_size)

        # Add attention blob
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                nx, ny = attn_x + dx, attn_y + dy
                if 0 <= nx < attn_size and 0 <= ny < attn_size:
                    dist = np.sqrt(dx**2 + dy**2)
                    attention[ny, nx] = max(
                        attention[ny, nx],
                        amplitude[peak_idx] * np.exp(-dist * 0.5)
                    )

    # Add some temporal variation
    attention += np.random.rand(attn_size, attn_size) * 0.1

    # Normalize
    if attention.max() > 0:
        attention = attention / attention.max()

    return attention


def create_comparison_frame(original: Image.Image,
                            enhanced: Image.Image,
                            frame_idx: int,
                            total_frames: int,
                            attention_map: np.ndarray) -> Image.Image:
    """Create side-by-side comparison frame with labels."""
    # Create combined image
    width = original.width * 2 + 60  # 60px for center divider
    height = original.height + 120  # Space for header and footer

    combined = Image.new('RGB', (width, height), (20, 25, 35))
    draw = ImageDraw.Draw(combined)

    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        title_font = label_font = small_font = ImageFont.load_default()

    # Header
    draw.text((width // 2 - 200, 15), "SYNESTHESIA 3.0 - Evolution Demo",
              fill=(255, 255, 255), font=title_font)

    # Paste images
    y_offset = 70
    combined.paste(original, (20, y_offset))
    combined.paste(enhanced, (original.width + 40, y_offset))

    # Labels
    draw.text((20 + original.width // 2 - 80, y_offset + original.height + 10),
              "Original Visualization", fill=(180, 180, 180), font=label_font)
    draw.text((original.width + 40 + original.width // 2 - 100, y_offset + original.height + 10),
              "Attention-Enhanced", fill=(100, 255, 100), font=label_font)

    # Center divider
    divider_x = original.width + 30
    draw.line([(divider_x, y_offset), (divider_x, y_offset + original.height)],
              fill=(100, 100, 100), width=2)

    # VS text
    draw.text((divider_x - 10, y_offset + original.height // 2 - 15),
              "VS", fill=(255, 255, 255), font=label_font)

    # Progress bar
    progress_y = height - 35
    progress_width = width - 100
    progress = frame_idx / max(total_frames - 1, 1)
    draw.rectangle([(50, progress_y), (50 + progress_width, progress_y + 10)],
                   outline=(100, 100, 100))
    draw.rectangle([(50, progress_y), (50 + int(progress_width * progress), progress_y + 10)],
                   fill=(0, 200, 150))

    # Frame counter
    draw.text((50 + progress_width + 10, progress_y - 3),
              f"{frame_idx + 1}/{total_frames}", fill=(150, 150, 150), font=small_font)

    # Attention intensity indicator
    mean_attention = attention_map.mean()
    max_attention = attention_map.max()
    draw.text((width - 250, 50),
              f"Attention: {mean_attention:.2f} (max: {max_attention:.2f})",
              fill=(255, 200, 100), font=small_font)

    return combined


def generate_evolution_demo(output_path: str = "evolution_demo.mp4",
                            duration_seconds: float = 8.0,
                            frame_rate: int = 30):
    """Generate the complete evolution demo video."""
    print("=" * 60)
    print("SYNESTHESIA 3.0 - Generating Evolution Demo")
    print("=" * 60)

    # Configuration
    render_config = Render2DConfig(
        frame_width=640,
        frame_height=480,
        background_color=(20, 25, 35)
    )

    attention_config = AttentionConfig(
        attention_alpha=0.5,
        amplification_factor=2.0,
        suppression_factor=0.4,
        show_attention_overlay=True,
        show_attention_border=True,
        glow_threshold=0.6
    )

    # Create renderers
    base_renderer = FastSpiralRenderer(render_config)
    attention_renderer = AttentionGuidedRenderer(attention_config)

    # Generate synthetic audio
    print("\n1. Generating synthetic audio data...")
    audio_frames, frequencies = generate_synthetic_audio_frames(
        duration_seconds=duration_seconds,
        frame_rate=frame_rate,
        num_freq_bins=381
    )
    total_frames = len(audio_frames)
    print(f"   Generated {total_frames} frames")

    # Create temp directory for frames
    temp_dir = tempfile.mkdtemp(prefix="evolution_demo_")
    frames_dir = os.path.join(temp_dir, "frames")
    os.makedirs(frames_dir)

    print(f"\n2. Rendering comparison frames to {frames_dir}...")

    for frame_idx, amplitude in enumerate(audio_frames):
        # Generate synthetic attention
        attention_map = generate_synthetic_attention(amplitude, frequencies, frame_idx)

        # Render original
        original_img = base_renderer.render_frame(
            amplitude, frame_idx=frame_idx, frequencies=frequencies
        )

        # Compute attention-modulated amplitude
        modulated_amp, _ = attention_renderer.compute_amplitude_modulation(
            amplitude, attention_map, frequencies
        )

        # Render enhanced base
        enhanced_base = base_renderer.render_frame(
            modulated_amp, frame_idx=frame_idx, frequencies=frequencies
        )

        # Add attention overlay
        enhanced_img = attention_renderer.render_attention_enhanced_frame(
            enhanced_base,
            attention_map,
            prediction="C Major Scale",
            confidence=0.92
        )

        # Create comparison frame
        comparison = create_comparison_frame(
            original_img, enhanced_img, frame_idx, total_frames, attention_map
        )

        # Save
        frame_path = os.path.join(frames_dir, f"frame_{frame_idx:06d}.png")
        comparison.save(frame_path)

        if frame_idx % 30 == 0:
            print(f"   Frame {frame_idx + 1}/{total_frames}")

    print(f"\n3. Encoding video with FFmpeg...")

    # FFmpeg command
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(frame_rate),
        "-i", os.path.join(frames_dir, "frame_%06d.png"),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"FFmpeg error: {result.stderr}")
        raise RuntimeError("Video encoding failed")

    # Get file size
    file_size = os.path.getsize(output_path) / 1024

    print(f"\n✅ Demo video generated: {output_path}")
    print(f"   Size: {file_size:.1f} KB")
    print(f"   Duration: {duration_seconds}s @ {frame_rate}fps")

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)

    return output_path


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="SYNESTHESIA 3.0 Evolution Demo")
    parser.add_argument("--output", "-o", default="evolution_demo.mp4",
                        help="Output video path")
    parser.add_argument("--duration", "-d", type=float, default=8.0,
                        help="Duration in seconds")
    parser.add_argument("--fps", type=int, default=30,
                        help="Frame rate")

    args = parser.parse_args()

    generate_evolution_demo(
        output_path=args.output,
        duration_seconds=args.duration,
        frame_rate=args.fps
    )


if __name__ == "__main__":
    main()
