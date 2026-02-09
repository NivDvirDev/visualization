#!/usr/bin/env python3
"""
SYNESTHESIA 2.0 - Command Line Interface

Generate stunning psychoacoustic visualizations from audio files.

Usage:
    python synesthesia_cli.py input.wav -o output.mp4
    python synesthesia_cli.py input.mp3 -o output.mp4 --4k
    python synesthesia_cli.py --demo  # Generate demo with synthetic audio
"""

import argparse
import sys
import os
from pathlib import Path


def print_banner():
    """Print SYNESTHESIA banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   ███████╗██╗   ██╗███╗   ██╗███████╗███████╗████████╗        ║
    ║   ██╔════╝╚██╗ ██╔╝████╗  ██║██╔════╝██╔════╝╚══██╔══╝        ║
    ║   ███████╗ ╚████╔╝ ██╔██╗ ██║█████╗  ███████╗   ██║           ║
    ║   ╚════██║  ╚██╔╝  ██║╚██╗██║██╔══╝  ╚════██║   ██║           ║
    ║   ███████║   ██║   ██║ ╚████║███████╗███████║   ██║           ║
    ║   ╚══════╝   ╚═╝   ╚═╝  ╚═══╝╚══════╝╚══════╝   ╚═╝           ║
    ║                                                               ║
    ║            HESIA 2.0 - AI-Enhanced Visualization              ║
    ║                                                               ║
    ║   Psychoacoustic Cochlear Spiral • Deep Learning Overlay      ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def main():
    parser = argparse.ArgumentParser(
        description="SYNESTHESIA 2.0 - AI-Enhanced Psychoacoustic Visualization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s song.wav -o visualization.mp4
  %(prog)s song.mp3 -o output.mp4 --4k --ai-overlay
  %(prog)s song.wav -o output.mp4 --start 30 --duration 60
  %(prog)s --demo -o demo.mp4

For more information, visit: https://youtube.com/@NivDvir-ND
        """
    )

    # Input/Output
    parser.add_argument("audio_file", nargs="?", help="Path to input audio file (WAV, MP3, FLAC)")
    parser.add_argument("-o", "--output", default="output.mp4", help="Output video path")

    # Time selection
    parser.add_argument("-s", "--start", type=float, default=0, help="Start time in seconds")
    parser.add_argument("-d", "--duration", type=float, help="Duration in seconds (default: entire file)")

    # Video settings
    parser.add_argument("--width", type=int, default=1920, help="Output width (default: 1920)")
    parser.add_argument("--height", type=int, default=1080, help="Output height (default: 1080)")
    parser.add_argument("--fps", type=int, default=60, help="Frame rate (default: 60)")
    parser.add_argument("--4k", dest="use_4k", action="store_true", help="Use 4K resolution (3840x2160)")

    # Quality
    parser.add_argument("--quality", type=int, default=18, choices=range(0, 52),
                        metavar="0-51", help="Video quality (lower=better, default: 18)")
    parser.add_argument("--preset", default="slow",
                        choices=["ultrafast", "superfast", "veryfast", "faster", "fast",
                                 "medium", "slow", "slower", "veryslow"],
                        help="Encoding preset (default: slow)")

    # AI features (Phase 2)
    parser.add_argument("--ai-overlay", action="store_true", help="Enable AI classification overlay")
    parser.add_argument("--instrument-model", help="Path to instrument classification model")
    parser.add_argument("--show-attention", action="store_true", help="Show attention heatmap overlay")

    # Demo mode
    parser.add_argument("--demo", action="store_true", help="Generate demo with synthetic audio")
    parser.add_argument("--demo-duration", type=float, default=10,
                        help="Demo duration in seconds (default: 10)")

    # Debug
    parser.add_argument("--keep-frames", action="store_true", help="Keep rendered frames after encoding")
    parser.add_argument("--test-frame", action="store_true", help="Generate single test frame only")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Print banner
    print_banner()

    # Import modules (delayed to speed up --help)
    from video_generator import VideoGenerator, VideoConfig, generate_demo_video
    from spiral_renderer import render_test_frame

    # Handle test frame mode
    if args.test_frame:
        print("Generating test frame...")
        output = args.output.replace(".mp4", ".png").replace(".mov", ".png")
        render_test_frame(output)
        print(f"Test frame saved to: {output}")
        return 0

    # Handle demo mode
    if args.demo:
        print(f"Generating {args.demo_duration}s demo video...")
        generate_demo_video(args.output, duration_seconds=args.demo_duration)
        print(f"Demo video saved to: {args.output}")
        return 0

    # Require audio file for normal operation
    if not args.audio_file:
        parser.error("Audio file required (or use --demo)")

    if not os.path.exists(args.audio_file):
        print(f"Error: Audio file not found: {args.audio_file}")
        return 1

    # Configure video generation
    config = VideoConfig(
        output_width=3840 if args.use_4k else args.width,
        output_height=2160 if args.use_4k else args.height,
        frame_rate=args.fps,
        video_crf=args.quality,
        video_preset=args.preset,
        keep_frames=args.keep_frames,
        enable_ai_overlay=args.ai_overlay,
        ai_model_path=args.instrument_model
    )

    # Progress callback
    def progress(current, total, stage):
        if args.verbose or current % 100 == 0:
            pct = (current / total) * 100 if total > 0 else 0
            print(f"\r{stage} [{current}/{total}] {pct:.1f}%", end="", flush=True)
        if current == total:
            print()

    # Generate video
    print(f"Input:  {args.audio_file}")
    print(f"Output: {args.output}")
    print(f"Resolution: {config.output_width}x{config.output_height} @ {config.frame_rate}fps")
    if args.start > 0:
        print(f"Start time: {args.start}s")
    if args.duration:
        print(f"Duration: {args.duration}s")
    print()

    try:
        generator = VideoGenerator(video_config=config)
        generator.generate(
            audio_path=args.audio_file,
            output_path=args.output,
            start_time=args.start,
            duration=args.duration,
            progress_callback=progress if args.verbose else None
        )
        print(f"\n✅ Video generated successfully: {args.output}")
        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
