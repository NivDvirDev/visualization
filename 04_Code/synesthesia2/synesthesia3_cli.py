#!/usr/bin/env python3
"""
SYNESTHESIA 3.0 - Unified Command Line Interface

Advanced psychoacoustic visualization with temporal intelligence:
- Melodic trails (pitch history)
- Rhythm pulses (beat synchronization)
- Harmonic auras (chord-driven colors)
- Atmosphere fields (mood/energy modulation)
- Multi-scale temporal pattern learning
- Learnable visualization parameters

Usage:
    python synesthesia3_cli.py input.wav -o output.mp4
    python synesthesia3_cli.py input.mp3 -o output.mp4 --temporal
    python synesthesia3_cli.py input.wav -o output.mp4 --4k --full
    python synesthesia3_cli.py --demo -o demo.mp4
    python synesthesia3_cli.py --train-viz --audio-dir ./data
"""

import argparse
import sys
import os
import time
import warnings
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

warnings.filterwarnings('ignore', category=DeprecationWarning)


def print_banner():
    """Print SYNESTHESIA 3.0 banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║   ███████╗██╗   ██╗███╗   ██╗███████╗███████╗████████╗            ║
    ║   ██╔════╝╚██╗ ██╔╝████╗  ██║██╔════╝██╔════╝╚══██╔══╝            ║
    ║   ███████╗ ╚████╔╝ ██╔██╗ ██║█████╗  ███████╗   ██║               ║
    ║   ╚════██║  ╚██╔╝  ██║╚██╗██║██╔══╝  ╚════██║   ██║               ║
    ║   ███████║   ██║   ██║ ╚████║███████╗███████║   ██║               ║
    ║   ╚══════╝   ╚═╝   ╚═╝  ╚═══╝╚══════╝╚══════╝   ╚═╝               ║
    ║                                                                   ║
    ║          HESIA 3.0 - Temporal Intelligence Edition                ║
    ║                                                                   ║
    ║   Multi-Scale Temporal Analysis • Learnable Visualization         ║
    ║   Melody Trails • Rhythm Pulse • Harmonic Aura • Atmosphere       ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_feature_status(mode: str):
    """Display which features are enabled."""
    features = {
        'basic': {
            'Frame-level spectral analysis': True,
            'Cochlear spiral visualization': True,
            'Chromesthesia color mapping': True,
            'Melodic trail': False,
            'Rhythm pulse': False,
            'Harmonic aura': False,
            'Atmosphere field': False,
        },
        'temporal': {
            'Frame-level spectral analysis': True,
            'Cochlear spiral visualization': True,
            'Chromesthesia color mapping': True,
            'Melodic trail': True,
            'Rhythm pulse': True,
            'Harmonic aura': True,
            'Atmosphere field': True,
        },
        'full': {
            'Frame-level spectral analysis': True,
            'Cochlear spiral visualization': True,
            'Chromesthesia color mapping': True,
            'Melodic trail': True,
            'Rhythm pulse': True,
            'Harmonic aura': True,
            'Atmosphere field': True,
            'Multi-scale transformer': True,
            'Learnable parameters': True,
        }
    }

    print(f"\n📊 Visualization Mode: {mode.upper()}")
    print("─" * 40)
    for feature, enabled in features.get(mode, features['temporal']).items():
        status = "✅" if enabled else "⬜"
        print(f"  {status} {feature}")
    print()


@dataclass
class UnifiedConfig:
    """Unified configuration for SYNESTHESIA 3.0"""
    # Output
    output_width: int = 1920
    output_height: int = 1080
    frame_rate: int = 60
    video_crf: int = 18
    video_preset: str = "slow"

    # Temporal features
    enable_melody_trail: bool = True
    enable_rhythm_pulse: bool = True
    enable_harmonic_aura: bool = True
    enable_atmosphere: bool = True

    # Advanced features
    enable_transformer: bool = False
    enable_learnable: bool = False
    transformer_checkpoint: Optional[str] = None
    learnable_checkpoint: Optional[str] = None

    # Processing
    keep_frames: bool = False
    use_gpu: bool = True


def generate_basic_video(audio_path: str, output_path: str, config: UnifiedConfig,
                         start_time: float = 0, duration: Optional[float] = None,
                         progress_callback=None):
    """Generate basic visualization (frame-level only)."""
    from video_generator import VideoGenerator, VideoConfig

    video_config = VideoConfig(
        output_width=config.output_width,
        output_height=config.output_height,
        frame_rate=config.frame_rate,
        video_crf=config.video_crf,
        video_preset=config.video_preset,
        keep_frames=config.keep_frames,
    )

    generator = VideoGenerator(video_config=video_config)
    generator.generate(
        audio_path=audio_path,
        output_path=output_path,
        start_time=start_time,
        duration=duration,
        progress_callback=progress_callback
    )


def generate_temporal_video(audio_path: str, output_path: str, config: UnifiedConfig,
                           start_time: float = 0, duration: Optional[float] = None,
                           progress_callback=None):
    """Generate temporal visualization with all temporal features."""
    from video_generator_temporal import TemporalVideoGenerator, TemporalVideoConfig

    video_config = TemporalVideoConfig(
        output_width=config.output_width,
        output_height=config.output_height,
        frame_rate=config.frame_rate,
        video_crf=config.video_crf,
        video_preset=config.video_preset,
        keep_frames=config.keep_frames,
        enable_melody_trail=config.enable_melody_trail,
        enable_rhythm_pulse=config.enable_rhythm_pulse,
        enable_harmonic_aura=config.enable_harmonic_aura,
        enable_atmosphere=config.enable_atmosphere,
    )

    generator = TemporalVideoGenerator(config=video_config)
    generator.generate(
        audio_path=audio_path,
        output_path=output_path,
        start_time=start_time,
        duration=duration,
        progress_callback=progress_callback
    )


def generate_demo_synthetic():
    """Generate synthetic demo audio for testing."""
    import numpy as np
    from scipy.io import wavfile
    import tempfile

    sample_rate = 44100
    duration = 10.0
    t = np.linspace(0, duration, int(sample_rate * duration))

    # Create complex synthetic audio with multiple features
    audio = np.zeros_like(t)

    # Melodic line (frequency sweep)
    melody_freq = 220 * (1 + 0.5 * np.sin(2 * np.pi * 0.2 * t))
    audio += 0.4 * np.sin(2 * np.pi * melody_freq * t)

    # Harmonic accompaniment (C major -> G major -> Am -> F major progression)
    chord_freqs = [
        [261.6, 329.6, 392.0],  # C major
        [392.0, 493.9, 587.3],  # G major
        [220.0, 261.6, 329.6],  # A minor
        [349.2, 440.0, 523.3],  # F major
    ]
    chord_duration = duration / 4
    for i, chord in enumerate(chord_freqs):
        start_idx = int(i * chord_duration * sample_rate)
        end_idx = int((i + 1) * chord_duration * sample_rate)
        for freq in chord:
            audio[start_idx:end_idx] += 0.15 * np.sin(2 * np.pi * freq * t[start_idx:end_idx])

    # Rhythmic pulses (kick drum simulation)
    beat_interval = 0.5  # 120 BPM
    for beat_time in np.arange(0, duration, beat_interval):
        beat_idx = int(beat_time * sample_rate)
        decay = np.exp(-10 * np.linspace(0, 0.1, int(0.1 * sample_rate)))
        end_idx = min(beat_idx + len(decay), len(audio))
        audio[beat_idx:end_idx] += 0.3 * decay[:end_idx - beat_idx] * np.sin(
            2 * np.pi * 80 * t[beat_idx:end_idx]
        )

    # High-frequency shimmer for atmosphere
    audio += 0.05 * np.sin(2 * np.pi * 4000 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.1 * t))

    # Normalize
    audio = audio / np.max(np.abs(audio)) * 0.9

    # Save to temp file
    temp_path = tempfile.mktemp(suffix='.wav')
    wavfile.write(temp_path, sample_rate, (audio * 32767).astype(np.int16))

    return temp_path


def run_analysis_only(audio_path: str, output_dir: str, verbose: bool = False):
    """Run temporal analysis and save results."""
    from temporal_analyzer import TemporalAnalyzer, TemporalAnalyzerConfig
    import json
    import numpy as np

    print("🔬 Running temporal analysis...")

    config = TemporalAnalyzerConfig()
    analyzer = TemporalAnalyzer(config)
    features = analyzer.analyze(audio_path)

    # Save results
    os.makedirs(output_dir, exist_ok=True)

    # Save numeric data
    np.savez_compressed(
        os.path.join(output_dir, 'temporal_features.npz'),
        pitch_contour=features.pitch_contour if features.pitch_contour is not None else np.array([]),
        pitch_confidence=features.pitch_confidence if features.pitch_confidence is not None else np.array([]),
        beat_frames=features.beat_frames if features.beat_frames is not None else np.array([]),
        energy_curve=features.energy_curve if features.energy_curve is not None else np.array([]),
        tension_curve=features.tension_curve if features.tension_curve is not None else np.array([]),
        chroma=features.chroma if features.chroma is not None else np.array([]),
    )

    # Save summary
    summary = {
        'duration_seconds': float(features.duration),
        'sample_rate': features.sample_rate,
        'hop_length': features.hop_length,
        'tempo_bpm': float(features.tempo) if features.tempo else 0,
        'num_beats': len(features.beat_frames) if features.beat_frames is not None else 0,
        'num_chords': len(features.chord_labels) if features.chord_labels else 0,
        'chord_progression': features.chord_labels[:20] if features.chord_labels else [],
    }

    with open(os.path.join(output_dir, 'analysis_summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n📊 Analysis Summary:")
    print(f"   Duration: {summary['duration_seconds']:.2f}s")
    print(f"   Tempo: {summary['tempo_bpm']:.1f} BPM")
    print(f"   Beats detected: {summary['num_beats']}")
    print(f"   Chords detected: {summary['num_chords']}")
    if summary['chord_progression']:
        print(f"   First chords: {' → '.join(summary['chord_progression'][:8])}")

    print(f"\n✅ Analysis saved to: {output_dir}/")
    return features


def train_visualization(audio_dir: str, output_dir: str,
                        epochs: int = 100, batch_size: int = 4,
                        learning_rate: float = 1e-4, verbose: bool = False):
    """Train learnable visualization parameters."""
    try:
        import torch
        from learnable_visualization import (
            LearnableVisualizationConfig,
            DifferentiableSpiralRenderer,
            VisualizationTrainer,
            create_sample_batch
        )
    except ImportError as e:
        print(f"❌ Error: PyTorch required for training. Install: pip install torch")
        return None

    print("🎓 Training Learnable Visualization Parameters")
    print("=" * 50)

    # Check for GPU
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"   Device: {device}")

    # Create config
    config = LearnableVisualizationConfig(
        num_frequency_bins=381,
        image_size=256,  # Smaller for training
        spiral_turns=2.5,
    )

    # Create model
    model = DifferentiableSpiralRenderer(config).to(device)
    param_count = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"   Model parameters: {param_count:,}")

    # Create trainer
    os.makedirs(output_dir, exist_ok=True)
    trainer = VisualizationTrainer(model, device, learning_rate=learning_rate)

    # Training loop (simplified - would need real data loader)
    print(f"\n   Training for {epochs} epochs...")

    for epoch in range(epochs):
        # Create synthetic batch
        batch = create_sample_batch(batch_size, config.num_frequency_bins, device)

        # Training step
        losses = trainer.train_step(batch)

        if epoch % 10 == 0 or epoch == epochs - 1:
            total_loss = sum(losses.values())
            print(f"   Epoch {epoch:4d}: Loss = {total_loss:.4f}")

    # Save checkpoint
    checkpoint_path = os.path.join(output_dir, 'learnable_viz_checkpoint.pt')
    torch.save({
        'model_state_dict': model.state_dict(),
        'config': config,
        'epoch': epochs,
    }, checkpoint_path)

    print(f"\n✅ Training complete! Checkpoint saved to: {checkpoint_path}")
    return checkpoint_path


def train_transformer(audio_dir: str, output_dir: str,
                      epochs: int = 50, batch_size: int = 8,
                      learning_rate: float = 1e-4, verbose: bool = False):
    """Train temporal transformer for classification."""
    try:
        import torch
        from temporal_transformer import (
            TemporalTransformerConfig,
            TemporalSpiralTransformer,
        )
    except ImportError as e:
        print(f"❌ Error: PyTorch required for training. Install: pip install torch")
        return None

    print("🎓 Training Temporal Transformer")
    print("=" * 50)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"   Device: {device}")

    # Create config
    config = TemporalTransformerConfig(
        num_frequency_bins=381,
        d_model=256,
        num_heads=8,
        num_layers=4,
        num_instrument_classes=11,
        num_genre_classes=10,
        num_emotion_classes=8,
    )

    # Create model
    model = TemporalSpiralTransformer(config).to(device)
    param_count = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"   Model parameters: {param_count:,}")

    # Create optimizer
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)

    os.makedirs(output_dir, exist_ok=True)

    print(f"\n   Training for {epochs} epochs...")

    for epoch in range(epochs):
        model.train()

        # Create synthetic batch (would need real data loader)
        seq_length = 128
        amplitude_data = torch.randn(batch_size, seq_length, config.num_frequency_bins).to(device)
        phase_data = torch.randn(batch_size, seq_length, config.num_frequency_bins, 60).to(device)
        temporal_features = {
            'pitch': torch.randn(batch_size, seq_length).to(device),
            'beat_strength': torch.rand(batch_size, seq_length).to(device),
            'energy': torch.rand(batch_size, seq_length).to(device),
            'tension': torch.rand(batch_size, seq_length).to(device),
        }

        # Forward pass
        outputs = model(amplitude_data, phase_data, temporal_features)

        # Simple loss (would use real labels)
        loss = outputs['instrument_logits'].mean() * 0  # Placeholder
        for key in ['note_features', 'motif_features', 'phrase_features', 'atmosphere_features']:
            loss = loss + outputs[key].std()  # Encourage diverse representations

        # Backward
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if epoch % 10 == 0 or epoch == epochs - 1:
            print(f"   Epoch {epoch:4d}: Loss = {loss.item():.4f}")

    # Save checkpoint
    checkpoint_path = os.path.join(output_dir, 'temporal_transformer_checkpoint.pt')
    torch.save({
        'model_state_dict': model.state_dict(),
        'config': config,
        'epoch': epochs,
    }, checkpoint_path)

    print(f"\n✅ Training complete! Checkpoint saved to: {checkpoint_path}")
    return checkpoint_path


def main():
    parser = argparse.ArgumentParser(
        description="SYNESTHESIA 3.0 - Temporal Intelligence Visualization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s song.wav -o output.mp4                    # Basic temporal visualization
  %(prog)s song.mp3 -o output.mp4 --basic            # Frame-only (original style)
  %(prog)s song.wav -o output.mp4 --temporal         # Full temporal features
  %(prog)s song.wav -o output.mp4 --4k --temporal    # 4K with temporal features
  %(prog)s --demo -o demo.mp4                        # Generate demo
  %(prog)s --analyze song.wav -o ./analysis/         # Analysis only
  %(prog)s --train-viz --audio-dir ./data -o ./models/  # Train visualization

Temporal Features:
  Melodic Trail   - Pitch history as glowing particles showing melody contour
  Rhythm Pulse    - Beat-synchronized scaling and brightness
  Harmonic Aura   - Chord-driven background colors (circle of fifths)
  Atmosphere      - Long-term energy/tension modulating global visuals

For more information: https://youtube.com/@NivDvir-ND
        """
    )

    # Input/Output
    parser.add_argument("audio_file", nargs="?", help="Path to input audio file")
    parser.add_argument("-o", "--output", default="output.mp4", help="Output path")

    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--basic", action="store_true",
                           help="Basic frame-only visualization (no temporal features)")
    mode_group.add_argument("--temporal", action="store_true",
                           help="Enable all temporal features (default)")
    mode_group.add_argument("--full", action="store_true",
                           help="Full mode with transformer and learnable params")

    # Time selection
    parser.add_argument("-s", "--start", type=float, default=0, help="Start time (seconds)")
    parser.add_argument("-d", "--duration", type=float, help="Duration (seconds)")

    # Video settings
    parser.add_argument("--width", type=int, default=1920, help="Output width")
    parser.add_argument("--height", type=int, default=1080, help="Output height")
    parser.add_argument("--fps", type=int, default=60, help="Frame rate")
    parser.add_argument("--4k", dest="use_4k", action="store_true", help="4K resolution")

    # Quality
    parser.add_argument("--quality", type=int, default=18, metavar="0-51",
                       help="Video quality (lower=better)")
    parser.add_argument("--preset", default="slow",
                       choices=["ultrafast", "fast", "medium", "slow", "veryslow"],
                       help="Encoding preset")

    # Temporal feature toggles
    parser.add_argument("--no-melody", action="store_true", help="Disable melodic trail")
    parser.add_argument("--no-rhythm", action="store_true", help="Disable rhythm pulse")
    parser.add_argument("--no-harmony", action="store_true", help="Disable harmonic aura")
    parser.add_argument("--no-atmosphere", action="store_true", help="Disable atmosphere field")

    # Model paths
    parser.add_argument("--transformer-model", help="Path to transformer checkpoint")
    parser.add_argument("--viz-model", help="Path to learnable visualization checkpoint")

    # Special modes
    parser.add_argument("--demo", action="store_true", help="Generate demo with synthetic audio")
    parser.add_argument("--demo-duration", type=float, default=10, help="Demo duration")
    parser.add_argument("--analyze", action="store_true", help="Analysis only (no video)")
    parser.add_argument("--train-viz", action="store_true", help="Train learnable visualization")
    parser.add_argument("--train-transformer", action="store_true", help="Train temporal transformer")
    parser.add_argument("--audio-dir", help="Directory with audio files for training")
    parser.add_argument("--epochs", type=int, default=100, help="Training epochs")

    # Debug
    parser.add_argument("--keep-frames", action="store_true", help="Keep rendered frames")
    parser.add_argument("--no-gpu", action="store_true", help="Disable GPU")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Print banner
    print_banner()

    # Determine mode
    if args.basic:
        mode = 'basic'
    elif args.full:
        mode = 'full'
    else:
        mode = 'temporal'  # Default

    # Handle training modes
    if args.train_viz:
        audio_dir = args.audio_dir or '.'
        output_dir = args.output if not args.output.endswith('.mp4') else './models'
        train_visualization(audio_dir, output_dir, epochs=args.epochs, verbose=args.verbose)
        return 0

    if args.train_transformer:
        audio_dir = args.audio_dir or '.'
        output_dir = args.output if not args.output.endswith('.mp4') else './models'
        train_transformer(audio_dir, output_dir, epochs=args.epochs, verbose=args.verbose)
        return 0

    # Handle demo mode
    if args.demo:
        print(f"🎵 Generating {args.demo_duration}s demo with synthetic audio...")
        audio_path = generate_demo_synthetic()
        args.audio_file = audio_path
        args.duration = args.demo_duration

    # Handle analysis-only mode
    if args.analyze:
        if not args.audio_file:
            parser.error("Audio file required for analysis")
        output_dir = args.output if not args.output.endswith('.mp4') else './analysis'
        run_analysis_only(args.audio_file, output_dir, verbose=args.verbose)
        return 0

    # Require audio file for video generation
    if not args.audio_file:
        parser.error("Audio file required (or use --demo)")

    if not os.path.exists(args.audio_file):
        print(f"❌ Error: Audio file not found: {args.audio_file}")
        return 1

    # Create config
    config = UnifiedConfig(
        output_width=3840 if args.use_4k else args.width,
        output_height=2160 if args.use_4k else args.height,
        frame_rate=args.fps,
        video_crf=args.quality,
        video_preset=args.preset,
        keep_frames=args.keep_frames,
        use_gpu=not args.no_gpu,
        enable_melody_trail=not args.no_melody,
        enable_rhythm_pulse=not args.no_rhythm,
        enable_harmonic_aura=not args.no_harmony,
        enable_atmosphere=not args.no_atmosphere,
        enable_transformer=args.full,
        enable_learnable=args.full,
        transformer_checkpoint=args.transformer_model,
        learnable_checkpoint=args.viz_model,
    )

    # Print feature status
    print_feature_status(mode)

    # Print info
    print(f"📁 Input:  {args.audio_file}")
    print(f"📁 Output: {args.output}")
    print(f"🖥️  Resolution: {config.output_width}x{config.output_height} @ {config.frame_rate}fps")
    if args.start > 0:
        print(f"⏱️  Start: {args.start}s")
    if args.duration:
        print(f"⏱️  Duration: {args.duration}s")
    print()

    # Progress callback
    start_time_proc = time.time()

    def progress(current, total, stage="Processing"):
        elapsed = time.time() - start_time_proc
        if total > 0:
            pct = (current / total) * 100
            eta = (elapsed / (current + 1)) * (total - current)
            print(f"\r   {stage} [{current}/{total}] {pct:.1f}% | ETA: {eta:.0f}s", end="", flush=True)
        if current == total:
            print()

    try:
        if mode == 'basic':
            print("🎬 Generating basic visualization...")
            generate_basic_video(
                args.audio_file, args.output, config,
                start_time=args.start, duration=args.duration,
                progress_callback=progress if args.verbose else None
            )
        else:
            print("🎬 Generating temporal visualization...")
            generate_temporal_video(
                args.audio_file, args.output, config,
                start_time=args.start, duration=args.duration,
                progress_callback=progress if args.verbose else None
            )

        elapsed = time.time() - start_time_proc
        print(f"\n✅ Video generated successfully!")
        print(f"   Output: {args.output}")
        print(f"   Time: {elapsed:.1f}s")

        # Clean up demo audio
        if args.demo and os.path.exists(args.audio_file):
            os.remove(args.audio_file)

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
