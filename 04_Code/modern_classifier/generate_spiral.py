"""
Spiral Cochlear Visualization Generator

Converts audio files to spiral visualizations based on the cochlear model
from the original project. This replaces the MATLAB implementation with
a pure Python version.

The spiral visualization maps:
- Frequency -> Angular position on spiral (tonotopic organization)
- Amplitude -> Circle size at that position
- Frequency -> Color (HSV hue mapping)

Usage:
    # Single file
    python generate_spiral.py --input audio.wav --output frames/

    # Batch processing
    python generate_spiral.py --input_dir audio/ --output_dir visualizations/

    # Generate dataset structure
    python generate_spiral.py --input_dir audio/ --output_dir data/ --create_dataset
"""

import argparse
import os
from pathlib import Path
from typing import Optional, Tuple, List
import numpy as np
from PIL import Image, ImageDraw
import colorsys

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    print("Warning: librosa not installed. Run: pip install librosa")


class SpiralVisualizer:
    """
    Generates spiral cochlear visualizations from audio.

    Based on the Fermat spiral model: r(φ) = a√φ
    """

    def __init__(
        self,
        image_size: int = 224,
        num_frequency_bins: int = 128,
        min_freq: float = 20.0,
        max_freq: float = 8000.0,
        spiral_turns: float = 3.0,
        background_color: Tuple[int, int, int] = (0, 0, 0),
        sample_rate: int = 22050,
        hop_length: int = 512,
        n_fft: int = 2048
    ):
        """
        Args:
            image_size: Output image size (square)
            num_frequency_bins: Number of frequency bins to visualize
            min_freq: Minimum frequency (Hz)
            max_freq: Maximum frequency (Hz)
            spiral_turns: Number of spiral turns
            background_color: RGB background color
            sample_rate: Audio sample rate
            hop_length: STFT hop length
            n_fft: FFT size
        """
        self.image_size = image_size
        self.num_frequency_bins = num_frequency_bins
        self.min_freq = min_freq
        self.max_freq = max_freq
        self.spiral_turns = spiral_turns
        self.background_color = background_color
        self.sample_rate = sample_rate
        self.hop_length = hop_length
        self.n_fft = n_fft

        # Pre-compute spiral coordinates for each frequency bin
        self._compute_spiral_coordinates()

    def _compute_spiral_coordinates(self):
        """Pre-compute spiral coordinates for efficiency."""
        center = self.image_size // 2
        max_radius = center * 0.9  # Leave margin

        # Fermat spiral: r = a * sqrt(phi)
        # We want the spiral to make spiral_turns rotations
        phi_max = self.spiral_turns * 2 * np.pi

        # Map frequency bins to spiral positions
        # Lower frequencies at center (like cochlea apex)
        # Higher frequencies at outside (like cochlea base)
        self.spiral_coords = []
        self.spiral_colors = []

        for i in range(self.num_frequency_bins):
            # Normalized position (0 = low freq, 1 = high freq)
            t = i / (self.num_frequency_bins - 1)

            # Spiral angle (more turns for higher frequencies)
            phi = t * phi_max

            # Spiral radius (Fermat spiral)
            r = max_radius * np.sqrt(t)

            # Convert to Cartesian
            x = center + r * np.cos(phi)
            y = center + r * np.sin(phi)

            self.spiral_coords.append((x, y))

            # Color mapping: frequency to hue
            # Low freq = red, high freq = violet (like visible spectrum)
            hue = t * 0.75  # 0 to 0.75 covers red to violet
            rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            color = tuple(int(c * 255) for c in rgb)
            self.spiral_colors.append(color)

    def _get_frequency_bins(self) -> np.ndarray:
        """Get frequency values for each bin (mel-scale)."""
        # Use mel scale for perceptually uniform spacing
        mel_min = 2595 * np.log10(1 + self.min_freq / 700)
        mel_max = 2595 * np.log10(1 + self.max_freq / 700)

        mel_points = np.linspace(mel_min, mel_max, self.num_frequency_bins)
        freq_points = 700 * (10 ** (mel_points / 2595) - 1)

        return freq_points

    def audio_to_spectrogram(self, audio_path: str) -> np.ndarray:
        """
        Convert audio file to spectrogram.

        Args:
            audio_path: Path to audio file

        Returns:
            Spectrogram array (frequency_bins, time_frames)
        """
        if not LIBROSA_AVAILABLE:
            raise ImportError("librosa required. Install: pip install librosa")

        # Load audio
        y, sr = librosa.load(audio_path, sr=self.sample_rate)

        # Compute mel spectrogram
        mel_spec = librosa.feature.melspectrogram(
            y=y,
            sr=sr,
            n_mels=self.num_frequency_bins,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            fmin=self.min_freq,
            fmax=self.max_freq
        )

        # Convert to dB scale
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)

        # Normalize to 0-1
        mel_spec_norm = (mel_spec_db - mel_spec_db.min()) / (mel_spec_db.max() - mel_spec_db.min() + 1e-8)

        return mel_spec_norm

    def spectrum_to_image(self, spectrum: np.ndarray) -> Image.Image:
        """
        Convert a single spectrum (one time frame) to spiral image.

        Args:
            spectrum: 1D array of frequency magnitudes (num_frequency_bins,)

        Returns:
            PIL Image of spiral visualization
        """
        # Create image
        img = Image.new('RGB', (self.image_size, self.image_size), self.background_color)
        draw = ImageDraw.Draw(img)

        # Draw circles for each frequency bin
        max_circle_radius = self.image_size / (self.num_frequency_bins * 0.3)

        for i, (coord, color) in enumerate(zip(self.spiral_coords, self.spiral_colors)):
            x, y = coord
            magnitude = spectrum[i]

            # Scale circle size by magnitude
            radius = magnitude * max_circle_radius

            if radius > 0.5:  # Only draw visible circles
                # Adjust color brightness by magnitude
                h, s, v = colorsys.rgb_to_hsv(color[0]/255, color[1]/255, color[2]/255)
                v = max(0.3, magnitude)  # Minimum brightness
                r, g, b = colorsys.hsv_to_rgb(h, s, v)
                adjusted_color = (int(r*255), int(g*255), int(b*255))

                draw.ellipse(
                    [x - radius, y - radius, x + radius, y + radius],
                    fill=adjusted_color
                )

        return img

    def generate_frames(
        self,
        audio_path: str,
        output_dir: str,
        max_frames: Optional[int] = None,
        frame_prefix: str = "frame"
    ) -> List[str]:
        """
        Generate spiral visualization frames from audio file.

        Args:
            audio_path: Path to audio file
            output_dir: Directory to save frames
            max_frames: Maximum number of frames (None for all)
            frame_prefix: Prefix for frame filenames

        Returns:
            List of saved frame paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Get spectrogram
        spectrogram = self.audio_to_spectrogram(audio_path)
        num_frames = spectrogram.shape[1]

        if max_frames:
            num_frames = min(num_frames, max_frames)

        saved_paths = []

        for i in range(num_frames):
            spectrum = spectrogram[:, i]
            img = self.spectrum_to_image(spectrum)

            # Save frame
            frame_path = output_dir / f"{frame_prefix}_{i:05d}.jpg"
            img.save(frame_path, quality=95)
            saved_paths.append(str(frame_path))

        print(f"Generated {len(saved_paths)} frames in {output_dir}")
        return saved_paths

    def generate_single_image(
        self,
        audio_path: str,
        output_path: str,
        aggregation: str = "mean"
    ) -> str:
        """
        Generate a single aggregated spiral image from audio.

        Args:
            audio_path: Path to audio file
            output_path: Path to save image
            aggregation: How to aggregate frames ("mean", "max", "median")

        Returns:
            Path to saved image
        """
        spectrogram = self.audio_to_spectrogram(audio_path)

        # Aggregate across time
        if aggregation == "mean":
            spectrum = spectrogram.mean(axis=1)
        elif aggregation == "max":
            spectrum = spectrogram.max(axis=1)
        elif aggregation == "median":
            spectrum = np.median(spectrogram, axis=1)
        else:
            raise ValueError(f"Unknown aggregation: {aggregation}")

        img = self.spectrum_to_image(spectrum)
        img.save(output_path, quality=95)

        return output_path


def generate_synthetic_demo_data(
    output_dir: str,
    num_classes: int = 5,
    samples_per_class: int = 50,
    image_size: int = 224
):
    """
    Generate synthetic spiral-like images for testing the pipeline.

    This creates fake data that resembles spiral visualizations
    so you can test the training pipeline before having real audio data.
    """
    output_dir = Path(output_dir)

    # Class names (simulating instruments)
    class_names = ["piano", "guitar", "violin", "flute", "drums"][:num_classes]

    # Each class will have a different characteristic pattern
    class_patterns = {
        "piano": {"freq_range": (0.2, 0.8), "brightness": 0.9, "spread": 0.3},
        "guitar": {"freq_range": (0.3, 0.7), "brightness": 0.8, "spread": 0.4},
        "violin": {"freq_range": (0.4, 0.9), "brightness": 0.85, "spread": 0.2},
        "flute": {"freq_range": (0.5, 0.95), "brightness": 0.75, "spread": 0.15},
        "drums": {"freq_range": (0.1, 0.5), "brightness": 0.95, "spread": 0.5},
    }

    visualizer = SpiralVisualizer(image_size=image_size)

    for split in ["train", "val"]:
        split_samples = samples_per_class if split == "train" else samples_per_class // 5

        for class_name in class_names:
            class_dir = output_dir / split / class_name
            class_dir.mkdir(parents=True, exist_ok=True)

            pattern = class_patterns[class_name]

            for i in range(split_samples):
                # Generate synthetic spectrum with class-specific characteristics
                spectrum = np.zeros(visualizer.num_frequency_bins)

                # Add characteristic frequency range
                freq_start = int(pattern["freq_range"][0] * visualizer.num_frequency_bins)
                freq_end = int(pattern["freq_range"][1] * visualizer.num_frequency_bins)

                # Create peaks in characteristic range
                num_peaks = np.random.randint(3, 8)
                for _ in range(num_peaks):
                    peak_pos = np.random.randint(freq_start, freq_end)
                    peak_width = int(pattern["spread"] * 20) + np.random.randint(5, 15)
                    peak_height = pattern["brightness"] * (0.7 + 0.3 * np.random.random())

                    for j in range(max(0, peak_pos - peak_width), min(visualizer.num_frequency_bins, peak_pos + peak_width)):
                        distance = abs(j - peak_pos) / peak_width
                        spectrum[j] = max(spectrum[j], peak_height * np.exp(-distance**2 * 2))

                # Add some noise
                spectrum += np.random.random(visualizer.num_frequency_bins) * 0.1
                spectrum = np.clip(spectrum, 0, 1)

                # Generate image
                img = visualizer.spectrum_to_image(spectrum)
                img.save(class_dir / f"sample_{i:04d}.jpg", quality=95)

            print(f"Generated {split_samples} samples for {split}/{class_name}")

    print(f"\nSynthetic dataset created at {output_dir}")
    print(f"Classes: {class_names}")
    print(f"Train samples per class: {samples_per_class}")
    print(f"Val samples per class: {samples_per_class // 5}")


def process_audio_directory(
    input_dir: str,
    output_dir: str,
    create_dataset: bool = True,
    max_frames_per_file: int = 100,
    train_split: float = 0.8
):
    """
    Process a directory of audio files organized by class.

    Expected structure:
        input_dir/
            piano/
                song1.wav
                song2.wav
            guitar/
                song1.wav
                ...

    Output structure:
        output_dir/
            train/
                piano/
                    frame_00001.jpg
                    ...
            val/
                piano/
                    ...
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    visualizer = SpiralVisualizer()

    # Find all class directories
    class_dirs = [d for d in input_dir.iterdir() if d.is_dir()]

    for class_dir in class_dirs:
        class_name = class_dir.name
        print(f"\nProcessing class: {class_name}")

        # Find audio files
        audio_files = list(class_dir.glob("*.wav")) + list(class_dir.glob("*.mp3"))

        if not audio_files:
            print(f"  No audio files found in {class_dir}")
            continue

        # Split files into train/val
        np.random.shuffle(audio_files)
        split_idx = int(len(audio_files) * train_split)
        train_files = audio_files[:split_idx]
        val_files = audio_files[split_idx:]

        for split, files in [("train", train_files), ("val", val_files)]:
            split_dir = output_dir / split / class_name
            split_dir.mkdir(parents=True, exist_ok=True)

            frame_idx = 0
            for audio_file in files:
                try:
                    frames = visualizer.generate_frames(
                        str(audio_file),
                        str(split_dir),
                        max_frames=max_frames_per_file,
                        frame_prefix=f"{audio_file.stem}"
                    )
                    frame_idx += len(frames)
                except Exception as e:
                    print(f"  Error processing {audio_file}: {e}")

            print(f"  {split}: {frame_idx} frames from {len(files)} files")


def main():
    parser = argparse.ArgumentParser(description="Generate spiral visualizations from audio")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Single file command
    single_parser = subparsers.add_parser("single", help="Process single audio file")
    single_parser.add_argument("--input", type=str, required=True, help="Input audio file")
    single_parser.add_argument("--output", type=str, required=True, help="Output directory or file")
    single_parser.add_argument("--frames", action="store_true", help="Generate frames (default: single image)")
    single_parser.add_argument("--max_frames", type=int, default=None, help="Max frames to generate")

    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Process directory of audio files")
    batch_parser.add_argument("--input_dir", type=str, required=True, help="Input directory")
    batch_parser.add_argument("--output_dir", type=str, required=True, help="Output directory")
    batch_parser.add_argument("--max_frames", type=int, default=100, help="Max frames per file")

    # Demo data command
    demo_parser = subparsers.add_parser("demo", help="Generate synthetic demo data")
    demo_parser.add_argument("--output_dir", type=str, default="data", help="Output directory")
    demo_parser.add_argument("--num_classes", type=int, default=5, help="Number of classes")
    demo_parser.add_argument("--samples", type=int, default=100, help="Samples per class")

    args = parser.parse_args()

    if args.command == "single":
        visualizer = SpiralVisualizer()
        if args.frames:
            visualizer.generate_frames(args.input, args.output, args.max_frames)
        else:
            visualizer.generate_single_image(args.input, args.output)

    elif args.command == "batch":
        process_audio_directory(args.input_dir, args.output_dir, max_frames_per_file=args.max_frames)

    elif args.command == "demo":
        generate_synthetic_demo_data(args.output_dir, args.num_classes, args.samples)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
