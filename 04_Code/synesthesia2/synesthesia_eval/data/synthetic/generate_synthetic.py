"""Generate synthetic evaluation samples for testing.

Creates 10 samples (5 good sync, 5 poor sync) with WAV audio files,
placeholder video files, and ground truth annotations.

Usage:
    python -m synesthesia_eval.data.synthetic.generate_synthetic
"""

import json
import struct
import wave
from pathlib import Path

import numpy as np


def _write_wav(path: str, samples: np.ndarray, sample_rate: int = 22050) -> None:
    """Write a mono WAV file from float samples in [-1, 1]."""
    samples = np.clip(samples, -1.0, 1.0)
    int_samples = (samples * 32767).astype(np.int16)

    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int_samples.tobytes())


def _generate_good_audio(duration: float = 2.0, sr: int = 22050, seed: int = 0) -> np.ndarray:
    """Generate audio with clear rhythmic structure (good for sync testing)."""
    rng = np.random.RandomState(seed)
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # Strong beat at ~120 BPM
    beat_freq = 2.0  # Hz = 120 BPM
    beat = np.sin(2 * np.pi * beat_freq * t) * 0.5
    # Add pitched content
    melody = 0.3 * np.sin(2 * np.pi * 440 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * beat_freq * t))
    # Slight noise
    noise = 0.05 * rng.randn(len(t))
    return beat + melody + noise


def _generate_poor_audio(duration: float = 2.0, sr: int = 22050, seed: int = 0) -> np.ndarray:
    """Generate noisy audio with weak rhythmic structure."""
    rng = np.random.RandomState(seed)
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # Random frequencies, no clear beat
    noise = 0.4 * rng.randn(len(t))
    sweep = 0.3 * np.sin(2 * np.pi * (200 + 800 * t / duration) * t)
    return noise + sweep


def _create_placeholder_video(path: str) -> None:
    """Create a minimal placeholder file (not a real video).

    For real testing, use actual synesthesia-generated videos.
    """
    Path(path).write_text("PLACEHOLDER_VIDEO")


def generate_dataset(output_dir: str) -> None:
    """Generate the full synthetic dataset.

    Args:
        output_dir: Root directory for the synthetic dataset.
    """
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)

    samples = []

    # --- 5 good sync samples ---
    for i in range(5):
        sample_id = f"good_sync_{i:03d}"
        sample_dir = root / sample_id
        sample_dir.mkdir(exist_ok=True)

        audio = _generate_good_audio(duration=2.0, seed=i)
        audio_path = sample_dir / "audio.wav"
        _write_wav(str(audio_path), audio)

        video_path = sample_dir / "video.mp4"
        _create_placeholder_video(str(video_path))

        annotation = {
            "sync_score": round(0.75 + 0.05 * i, 2),
            "alignment_score": round(0.70 + 0.06 * i, 2),
            "aesthetic_score": round(0.65 + 0.07 * i, 2),
            "annotator_ids": ["ann_synthetic_1", "ann_synthetic_2"],
            "confidence": 0.9,
            "split": "train" if i < 3 else "val",
            "metadata": {
                "genre": "synthetic_tonal",
                "tempo": 120,
                "complexity": "medium",
                "quality": "good",
            },
        }
        with open(sample_dir / "annotation.json", "w") as f:
            json.dump(annotation, f, indent=2)

        samples.append({"id": sample_id, "quality": "good", **annotation})

    # --- 5 poor sync samples ---
    for i in range(5):
        sample_id = f"poor_sync_{i:03d}"
        sample_dir = root / sample_id
        sample_dir.mkdir(exist_ok=True)

        audio = _generate_poor_audio(duration=2.0, seed=i + 100)
        audio_path = sample_dir / "audio.wav"
        _write_wav(str(audio_path), audio)

        video_path = sample_dir / "video.mp4"
        _create_placeholder_video(str(video_path))

        annotation = {
            "sync_score": round(0.15 + 0.05 * i, 2),
            "alignment_score": round(0.20 + 0.04 * i, 2),
            "aesthetic_score": round(0.25 + 0.05 * i, 2),
            "annotator_ids": ["ann_synthetic_1", "ann_synthetic_2"],
            "confidence": 0.85,
            "split": "train" if i < 3 else "test",
            "metadata": {
                "genre": "synthetic_noise",
                "tempo": 0,
                "complexity": "low",
                "quality": "poor",
            },
        }
        with open(sample_dir / "annotation.json", "w") as f:
            json.dump(annotation, f, indent=2)

        samples.append({"id": sample_id, "quality": "poor", **annotation})

    # Write manifest
    manifest = {
        "description": "Synthetic evaluation dataset for testing",
        "n_samples": len(samples),
        "samples": samples,
    }
    with open(root / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Generated {len(samples)} synthetic samples in {root}")


if __name__ == "__main__":
    script_dir = Path(__file__).parent
    generate_dataset(str(script_dir))
