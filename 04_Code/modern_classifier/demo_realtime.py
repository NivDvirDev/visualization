"""
Real-time Instrument Classification Demo

Captures audio from microphone, generates spiral visualization,
and classifies the instrument in real-time.

Usage:
    python demo_realtime.py --checkpoint checkpoints/best_model_simple.pt

Requirements:
    pip install pyaudio sounddevice matplotlib numpy torch pillow

Controls:
    - Press 'q' to quit
    - Press 's' to save current frame
    - Press 'r' to reset visualization
"""

import argparse
import sys
import time
import threading
import queue
from pathlib import Path
from typing import Optional, List, Tuple
from collections import deque

import numpy as np
import torch
import torch.nn as nn
from PIL import Image

# Visualization imports
try:
    import matplotlib
    matplotlib.use('TkAgg')  # Use TkAgg backend for interactive display
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not available. Install: pip install matplotlib")

# Audio imports
try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    print("Warning: sounddevice not available. Install: pip install sounddevice")

# Import our modules
from generate_spiral import SpiralVisualizer
from train_simple import SimpleCNN


class AudioBuffer:
    """Thread-safe audio buffer for real-time processing."""

    def __init__(self, sample_rate: int = 22050, buffer_seconds: float = 1.0):
        self.sample_rate = sample_rate
        self.buffer_size = int(sample_rate * buffer_seconds)
        self.buffer = np.zeros(self.buffer_size, dtype=np.float32)
        self.lock = threading.Lock()

    def add_samples(self, samples: np.ndarray):
        """Add new samples to buffer (FIFO)."""
        with self.lock:
            samples = samples.flatten()
            if len(samples) >= self.buffer_size:
                self.buffer = samples[-self.buffer_size:]
            else:
                self.buffer = np.roll(self.buffer, -len(samples))
                self.buffer[-len(samples):] = samples

    def get_buffer(self) -> np.ndarray:
        """Get current buffer contents."""
        with self.lock:
            return self.buffer.copy()


class RealtimeClassifier:
    """Real-time audio classification with visualization."""

    def __init__(
        self,
        model_path: str,
        sample_rate: int = 22050,
        hop_length: int = 512,
        n_fft: int = 2048,
        device: str = "cpu"
    ):
        self.sample_rate = sample_rate
        self.hop_length = hop_length
        self.n_fft = n_fft
        self.device = device

        # Load model
        print(f"Loading model from {model_path}...")
        checkpoint = torch.load(model_path, map_location=device)

        self.classes = checkpoint.get('classes', ['drums', 'flute', 'guitar', 'piano', 'violin'])
        num_classes = len(self.classes)

        self.model = SimpleCNN(num_classes=num_classes)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.to(device)
        self.model.eval()

        print(f"Model loaded. Classes: {self.classes}")

        # Spiral visualizer
        self.visualizer = SpiralVisualizer(
            image_size=224,
            sample_rate=sample_rate,
            hop_length=hop_length,
            n_fft=n_fft
        )

        # Image transform
        self.transform = self._get_transform()

        # Audio buffer
        self.audio_buffer = AudioBuffer(sample_rate, buffer_seconds=1.0)

        # Prediction history for smoothing
        self.prediction_history = deque(maxlen=10)

        # State
        self.is_running = False
        self.current_frame = None
        self.current_prediction = None
        self.current_confidence = 0.0

    def _get_transform(self):
        """Get image transform."""
        from torchvision import transforms
        return transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

    def _compute_spectrum(self, audio: np.ndarray) -> np.ndarray:
        """Compute spectrum from audio buffer."""
        # Simple FFT-based spectrum
        if len(audio) < self.n_fft:
            audio = np.pad(audio, (0, self.n_fft - len(audio)))

        # Window and FFT
        window = np.hanning(self.n_fft)
        windowed = audio[-self.n_fft:] * window
        spectrum = np.abs(np.fft.rfft(windowed))

        # Convert to mel-like scale (approximate)
        num_bins = self.visualizer.num_frequency_bins
        spectrum_resampled = np.zeros(num_bins)

        # Simple linear interpolation to target bins
        for i in range(num_bins):
            start_idx = int(i * len(spectrum) / num_bins)
            end_idx = int((i + 1) * len(spectrum) / num_bins)
            if start_idx < len(spectrum):
                spectrum_resampled[i] = np.mean(spectrum[start_idx:max(start_idx+1, end_idx)])

        # Normalize
        if spectrum_resampled.max() > 0:
            spectrum_resampled = spectrum_resampled / spectrum_resampled.max()

        return spectrum_resampled

    def process_audio(self, audio: np.ndarray) -> Tuple[Image.Image, str, float]:
        """
        Process audio and return visualization + prediction.

        Args:
            audio: Audio samples

        Returns:
            (spiral_image, predicted_class, confidence)
        """
        # Compute spectrum
        spectrum = self._compute_spectrum(audio)

        # Generate spiral visualization
        spiral_image = self.visualizer.spectrum_to_image(spectrum)

        # Prepare for model
        image_tensor = self.transform(spiral_image).unsqueeze(0).to(self.device)

        # Predict
        with torch.no_grad():
            output = self.model(image_tensor)
            probs = torch.softmax(output, dim=1)[0]
            confidence, predicted_idx = probs.max(0)

        predicted_class = self.classes[predicted_idx.item()]
        confidence = confidence.item()

        # Add to history for smoothing
        self.prediction_history.append((predicted_class, confidence))

        # Smoothed prediction (majority vote)
        if len(self.prediction_history) >= 3:
            class_counts = {}
            for cls, conf in self.prediction_history:
                class_counts[cls] = class_counts.get(cls, 0) + conf
            predicted_class = max(class_counts, key=class_counts.get)
            confidence = class_counts[predicted_class] / len(self.prediction_history)

        return spiral_image, predicted_class, confidence

    def audio_callback(self, indata, frames, time_info, status):
        """Callback for audio stream."""
        if status:
            print(f"Audio status: {status}")
        self.audio_buffer.add_samples(indata[:, 0])

    def run_terminal(self):
        """Run in terminal mode (no GUI)."""
        if not SOUNDDEVICE_AVAILABLE:
            print("Error: sounddevice required. Install: pip install sounddevice")
            return

        print("\n" + "="*50)
        print("Real-time Instrument Classification")
        print("="*50)
        print("Listening... Press Ctrl+C to stop\n")

        self.is_running = True

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                callback=self.audio_callback,
                blocksize=self.hop_length
            ):
                while self.is_running:
                    # Get current audio
                    audio = self.audio_buffer.get_buffer()

                    # Check if there's significant audio
                    rms = np.sqrt(np.mean(audio**2))
                    if rms < 0.01:
                        print("\r[Silence]                                    ", end="")
                        time.sleep(0.1)
                        continue

                    # Process
                    _, predicted_class, confidence = self.process_audio(audio)

                    # Display
                    bar = "█" * int(confidence * 20)
                    print(f"\r{predicted_class:15s} [{bar:20s}] {confidence*100:.1f}%", end="")

                    time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n\nStopped.")
            self.is_running = False

    def run_gui(self):
        """Run with GUI visualization."""
        if not MATPLOTLIB_AVAILABLE:
            print("Warning: matplotlib not available, falling back to terminal mode")
            self.run_terminal()
            return

        if not SOUNDDEVICE_AVAILABLE:
            print("Error: sounddevice required. Install: pip install sounddevice")
            return

        print("\n" + "="*50)
        print("Real-time Instrument Classification (GUI)")
        print("="*50)
        print("Close window to stop\n")

        self.is_running = True

        # Setup figure
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        fig.suptitle("Real-time Instrument Classification", fontsize=14)

        # Spiral visualization
        ax_spiral = axes[0]
        ax_spiral.set_title("Spiral Visualization")
        ax_spiral.axis('off')

        # Create initial black image
        initial_img = np.zeros((224, 224, 3), dtype=np.uint8)
        img_display = ax_spiral.imshow(initial_img)

        # Prediction bar chart
        ax_pred = axes[1]
        ax_pred.set_title("Class Probabilities")
        bars = ax_pred.barh(self.classes, [0] * len(self.classes), color='steelblue')
        ax_pred.set_xlim(0, 1)
        ax_pred.set_xlabel("Confidence")

        # Text annotation
        pred_text = ax_pred.text(0.5, -0.1, "", transform=ax_pred.transAxes,
                                  ha='center', fontsize=12, fontweight='bold')

        def update(frame):
            if not self.is_running:
                return img_display, *bars, pred_text

            # Get current audio
            audio = self.audio_buffer.get_buffer()

            # Check for silence
            rms = np.sqrt(np.mean(audio**2))
            if rms < 0.01:
                pred_text.set_text("[Silence]")
                return img_display, *bars, pred_text

            # Process audio
            spiral_image, predicted_class, confidence = self.process_audio(audio)

            # Update spiral display
            img_display.set_array(np.array(spiral_image))

            # Update probability bars (use uniform for now, could compute actual probs)
            probs = [0.1] * len(self.classes)
            pred_idx = self.classes.index(predicted_class)
            probs[pred_idx] = confidence
            for bar, prob in zip(bars, probs):
                bar.set_width(prob)
                bar.set_color('green' if prob == confidence else 'steelblue')

            # Update text
            pred_text.set_text(f"Prediction: {predicted_class} ({confidence*100:.1f}%)")

            return img_display, *bars, pred_text

        # Start audio stream
        stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            callback=self.audio_callback,
            blocksize=self.hop_length
        )
        stream.start()

        # Animation
        ani = FuncAnimation(fig, update, interval=100, blit=False)

        plt.tight_layout()

        try:
            plt.show()
        except KeyboardInterrupt:
            pass
        finally:
            self.is_running = False
            stream.stop()
            stream.close()

        print("Stopped.")


def run_demo_without_audio(model_path: str, data_dir: str):
    """
    Run demo using saved images (no microphone needed).

    Useful for testing without audio hardware.
    """
    print("\n" + "="*50)
    print("Demo Mode (Using saved images)")
    print("="*50)

    # Load model
    device = "cpu"
    checkpoint = torch.load(model_path, map_location=device)
    classes = checkpoint.get('classes', ['drums', 'flute', 'guitar', 'piano', 'violin'])

    model = SimpleCNN(num_classes=len(classes))
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()

    # Find test images
    from torchvision import transforms
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    data_path = Path(data_dir)
    test_images = []

    for class_dir in data_path.iterdir():
        if class_dir.is_dir():
            for img_path in list(class_dir.glob("*.jpg"))[:5]:
                test_images.append((img_path, class_dir.name))

    if not test_images:
        print(f"No images found in {data_dir}")
        return

    print(f"\nTesting on {len(test_images)} images...\n")

    correct = 0
    for img_path, true_class in test_images:
        # Load and transform
        image = Image.open(img_path).convert('RGB')
        image_tensor = transform(image).unsqueeze(0)

        # Predict
        with torch.no_grad():
            output = model(image_tensor)
            probs = torch.softmax(output, dim=1)[0]
            confidence, pred_idx = probs.max(0)

        pred_class = classes[pred_idx.item()]
        is_correct = pred_class == true_class
        correct += int(is_correct)

        status = "✓" if is_correct else "✗"
        print(f"{status} {img_path.name}: True={true_class}, Pred={pred_class} ({confidence.item()*100:.1f}%)")

    print(f"\nAccuracy: {correct}/{len(test_images)} ({100*correct/len(test_images):.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="Real-time instrument classification demo")

    parser.add_argument("--checkpoint", type=str, default="checkpoints/best_model_simple.pt",
                        help="Path to model checkpoint")
    parser.add_argument("--mode", type=str, default="gui",
                        choices=["gui", "terminal", "demo"],
                        help="Display mode (gui=visual, terminal=text, demo=test images)")
    parser.add_argument("--data_dir", type=str, default="data/val",
                        help="Data directory for demo mode")
    parser.add_argument("--sample_rate", type=int, default=22050,
                        help="Audio sample rate")

    args = parser.parse_args()

    # Check model exists
    if not Path(args.checkpoint).exists():
        print(f"Error: Model not found at {args.checkpoint}")
        print("\nTo create a model, run:")
        print("  python train_simple.py --data_dir data --epochs 10")
        sys.exit(1)

    if args.mode == "demo":
        run_demo_without_audio(args.checkpoint, args.data_dir)
    else:
        classifier = RealtimeClassifier(
            model_path=args.checkpoint,
            sample_rate=args.sample_rate
        )

        if args.mode == "gui":
            classifier.run_gui()
        else:
            classifier.run_terminal()


if __name__ == "__main__":
    main()
