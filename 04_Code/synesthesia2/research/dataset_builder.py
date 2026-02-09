#!/usr/bin/env python3
"""
SYNESTHESIA Research - Dataset Builder
=======================================
Tools for building, downloading, and managing audio datasets for
visualization-classification research.

Supports:
- NSynth (Google Magenta) - Instrument classification
- Synthetic generation - Controlled experiments
- Audio augmentation - Data expansion
- Metadata management - Labels and splits
"""

import os
import json
import hashlib
import subprocess
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple, Callable
import numpy as np
from scipy.io import wavfile
import warnings

warnings.filterwarnings('ignore')


@dataclass
class AudioSample:
    """Metadata for a single audio sample."""
    sample_id: str
    file_path: str
    duration: float
    sample_rate: int

    # Labels
    instrument: Optional[str] = None
    instrument_family: Optional[str] = None
    genre: Optional[str] = None
    emotion: Optional[str] = None

    # Audio properties
    pitch: Optional[int] = None  # MIDI note number
    velocity: Optional[int] = None
    tempo: Optional[float] = None

    # Dataset info
    dataset_source: str = "unknown"
    split: str = "train"  # train/val/test

    # Computed features (optional)
    features: Dict = field(default_factory=dict)


@dataclass
class DatasetConfig:
    """Configuration for dataset building."""
    name: str
    root_dir: str
    sample_rate: int = 16000
    duration: float = 4.0  # seconds

    # Splits
    train_ratio: float = 0.7
    val_ratio: float = 0.15
    test_ratio: float = 0.15

    # Augmentation
    augment_train: bool = True
    augment_factor: int = 3  # How many augmented versions per sample


class SyntheticDatasetGenerator:
    """
    Generate synthetic audio samples with controlled parameters.
    Perfect for isolated experiments on specific visualization aspects.
    """

    def __init__(self, output_dir: str, sample_rate: int = 16000):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.sample_rate = sample_rate
        self.samples: List[AudioSample] = []

    def generate_single_tone(self,
                            frequency: float,
                            duration: float = 2.0,
                            amplitude: float = 0.8,
                            waveform: str = "sine") -> Tuple[np.ndarray, AudioSample]:
        """Generate a single tone with specified parameters."""
        t = np.linspace(0, duration, int(self.sample_rate * duration))

        if waveform == "sine":
            audio = amplitude * np.sin(2 * np.pi * frequency * t)
        elif waveform == "square":
            audio = amplitude * np.sign(np.sin(2 * np.pi * frequency * t))
        elif waveform == "sawtooth":
            audio = amplitude * (2 * (t * frequency % 1) - 1)
        elif waveform == "triangle":
            audio = amplitude * (2 * np.abs(2 * (t * frequency % 1) - 1) - 1)
        else:
            raise ValueError(f"Unknown waveform: {waveform}")

        # Apply envelope
        attack = int(0.01 * self.sample_rate)
        release = int(0.05 * self.sample_rate)
        envelope = np.ones_like(audio)
        envelope[:attack] = np.linspace(0, 1, attack)
        envelope[-release:] = np.linspace(1, 0, release)
        audio *= envelope

        # Create metadata
        midi_note = int(12 * np.log2(frequency / 440) + 69)
        sample_id = f"tone_{waveform}_{midi_note}_{hashlib.md5(str(frequency).encode()).hexdigest()[:8]}"

        sample = AudioSample(
            sample_id=sample_id,
            file_path=str(self.output_dir / f"{sample_id}.wav"),
            duration=duration,
            sample_rate=self.sample_rate,
            instrument=waveform,
            instrument_family="synthetic",
            pitch=midi_note,
            dataset_source="synthetic_tones"
        )

        return audio, sample

    def generate_instrument_family(self,
                                   instrument: str,
                                   pitch_range: Tuple[int, int] = (48, 84),
                                   num_samples: int = 50) -> List[AudioSample]:
        """
        Generate synthetic instrument samples using additive synthesis.
        """
        samples = []

        # Instrument-specific harmonic profiles
        harmonic_profiles = {
            "piano": [1.0, 0.5, 0.3, 0.2, 0.15, 0.1, 0.08, 0.05],
            "guitar": [1.0, 0.7, 0.5, 0.35, 0.2, 0.15, 0.1],
            "violin": [1.0, 0.8, 0.6, 0.5, 0.4, 0.3, 0.25, 0.2, 0.15],
            "flute": [1.0, 0.3, 0.1, 0.05],
            "clarinet": [1.0, 0.1, 0.75, 0.1, 0.5, 0.1, 0.25],  # Odd harmonics
            "trumpet": [1.0, 0.9, 0.8, 0.7, 0.5, 0.4, 0.3, 0.2],
            "bass": [1.0, 0.8, 0.5, 0.3, 0.2],
            "organ": [1.0, 0.8, 0.6, 0.5, 0.4, 0.35, 0.3, 0.25],
        }

        harmonics = harmonic_profiles.get(instrument, [1.0, 0.5, 0.25])

        for i in range(num_samples):
            # Random pitch within range
            midi_note = np.random.randint(pitch_range[0], pitch_range[1] + 1)
            frequency = 440 * 2 ** ((midi_note - 69) / 12)

            # Random duration and velocity
            duration = np.random.uniform(1.0, 4.0)
            velocity = np.random.randint(60, 127)
            amplitude = velocity / 127.0

            # Generate audio with harmonics
            t = np.linspace(0, duration, int(self.sample_rate * duration))
            audio = np.zeros_like(t)

            for h_idx, h_amp in enumerate(harmonics):
                h_freq = frequency * (h_idx + 1)
                if h_freq < self.sample_rate / 2:  # Nyquist
                    audio += h_amp * amplitude * np.sin(2 * np.pi * h_freq * t)

            # Normalize
            audio = audio / np.max(np.abs(audio) + 1e-8) * 0.9

            # Apply ADSR envelope
            audio = self._apply_adsr(audio, instrument)

            # Create sample
            sample_id = f"{instrument}_{midi_note}_{i:04d}"
            file_path = self.output_dir / f"{sample_id}.wav"

            # Save
            wavfile.write(str(file_path), self.sample_rate,
                         (audio * 32767).astype(np.int16))

            sample = AudioSample(
                sample_id=sample_id,
                file_path=str(file_path),
                duration=duration,
                sample_rate=self.sample_rate,
                instrument=instrument,
                instrument_family=self._get_family(instrument),
                pitch=midi_note,
                velocity=velocity,
                dataset_source="synthetic_instruments"
            )

            samples.append(sample)

        self.samples.extend(samples)
        return samples

    def _apply_adsr(self, audio: np.ndarray, instrument: str) -> np.ndarray:
        """Apply instrument-specific ADSR envelope."""
        adsr_profiles = {
            "piano": (0.01, 0.1, 0.7, 0.3),
            "guitar": (0.005, 0.05, 0.6, 0.4),
            "violin": (0.1, 0.1, 0.9, 0.2),
            "flute": (0.05, 0.1, 0.8, 0.15),
            "clarinet": (0.03, 0.05, 0.85, 0.1),
            "trumpet": (0.02, 0.05, 0.8, 0.15),
            "bass": (0.01, 0.05, 0.7, 0.25),
            "organ": (0.02, 0.01, 1.0, 0.1),
        }

        attack, decay, sustain, release = adsr_profiles.get(instrument, (0.01, 0.1, 0.8, 0.2))

        n_samples = len(audio)
        envelope = np.ones(n_samples)

        attack_samples = int(attack * self.sample_rate)
        decay_samples = int(decay * self.sample_rate)
        release_samples = int(release * self.sample_rate)
        sustain_samples = n_samples - attack_samples - decay_samples - release_samples

        if sustain_samples < 0:
            # Short sample, simplify envelope
            envelope[:n_samples//10] = np.linspace(0, 1, n_samples//10)
            envelope[-n_samples//5:] = np.linspace(1, 0, n_samples//5)
        else:
            idx = 0
            envelope[idx:idx+attack_samples] = np.linspace(0, 1, attack_samples)
            idx += attack_samples
            envelope[idx:idx+decay_samples] = np.linspace(1, sustain, decay_samples)
            idx += decay_samples
            envelope[idx:idx+sustain_samples] = sustain
            idx += sustain_samples
            envelope[idx:] = np.linspace(sustain, 0, len(envelope) - idx)

        return audio * envelope

    def _get_family(self, instrument: str) -> str:
        """Get instrument family."""
        families = {
            "piano": "keyboard",
            "organ": "keyboard",
            "guitar": "string",
            "violin": "string",
            "bass": "string",
            "flute": "woodwind",
            "clarinet": "woodwind",
            "trumpet": "brass",
        }
        return families.get(instrument, "other")

    def generate_chord_progressions(self,
                                   num_progressions: int = 50,
                                   duration_per_chord: float = 2.0) -> List[AudioSample]:
        """Generate chord progressions for harmony analysis."""
        samples = []

        # Common chord progressions (in Roman numerals, converted to semitones from root)
        progressions = [
            [(0, 4, 7), (5, 9, 12), (7, 11, 14), (0, 4, 7)],  # I-IV-V-I
            [(0, 4, 7), (9, 12, 16), (5, 9, 12), (7, 11, 14)],  # I-vi-IV-V
            [(0, 3, 7), (5, 8, 12), (7, 10, 14), (0, 3, 7)],  # i-iv-v-i (minor)
            [(0, 4, 7), (7, 11, 14), (9, 12, 16), (5, 9, 12)],  # I-V-vi-IV
        ]

        chord_names = ["I-IV-V-I", "I-vi-IV-V", "i-iv-v-i", "I-V-vi-IV"]

        for prog_idx in range(num_progressions):
            # Random root note and progression
            root_midi = np.random.randint(48, 72)
            prog_choice = prog_idx % len(progressions)
            progression = progressions[prog_choice]

            root_freq = 440 * 2 ** ((root_midi - 69) / 12)

            # Generate audio
            total_duration = duration_per_chord * len(progression)
            t = np.linspace(0, total_duration, int(self.sample_rate * total_duration))
            audio = np.zeros_like(t)

            for chord_idx, chord in enumerate(progression):
                start_sample = int(chord_idx * duration_per_chord * self.sample_rate)
                end_sample = int((chord_idx + 1) * duration_per_chord * self.sample_rate)

                chord_t = t[start_sample:end_sample]

                for semitone in chord:
                    freq = root_freq * 2 ** (semitone / 12)
                    audio[start_sample:end_sample] += 0.3 * np.sin(2 * np.pi * freq * chord_t)

                # Apply per-chord envelope
                chord_len = end_sample - start_sample
                envelope = np.ones(chord_len)
                attack = int(0.02 * self.sample_rate)
                release = int(0.1 * self.sample_rate)
                envelope[:attack] = np.linspace(0, 1, attack)
                envelope[-release:] = np.linspace(1, 0.3, release)
                audio[start_sample:end_sample] *= envelope

            # Normalize
            audio = audio / np.max(np.abs(audio) + 1e-8) * 0.9

            # Save
            sample_id = f"chord_prog_{chord_names[prog_choice]}_{root_midi}_{prog_idx:04d}"
            file_path = self.output_dir / f"{sample_id}.wav"
            wavfile.write(str(file_path), self.sample_rate,
                         (audio * 32767).astype(np.int16))

            sample = AudioSample(
                sample_id=sample_id,
                file_path=str(file_path),
                duration=total_duration,
                sample_rate=self.sample_rate,
                instrument="chord",
                instrument_family="harmony",
                pitch=root_midi,
                dataset_source="synthetic_chords",
                features={"progression": chord_names[prog_choice]}
            )

            samples.append(sample)

        self.samples.extend(samples)
        return samples

    def generate_rhythm_patterns(self,
                                num_patterns: int = 50,
                                duration: float = 4.0) -> List[AudioSample]:
        """Generate rhythmic patterns for rhythm analysis."""
        samples = []

        # Common rhythm patterns (as beat positions in a 4-beat measure)
        patterns = {
            "four_on_floor": [0, 1, 2, 3],
            "backbeat": [1, 3],
            "offbeat": [0.5, 1.5, 2.5, 3.5],
            "syncopated": [0, 0.5, 1.5, 2, 3, 3.5],
            "shuffle": [0, 0.67, 1, 1.67, 2, 2.67, 3, 3.67],
            "reggae": [0.5, 2.5],
        }

        for pat_idx in range(num_patterns):
            # Random tempo
            tempo = np.random.uniform(80, 140)
            beat_duration = 60.0 / tempo

            # Select pattern
            pattern_name = list(patterns.keys())[pat_idx % len(patterns)]
            beat_positions = patterns[pattern_name]

            # Generate audio
            t = np.linspace(0, duration, int(self.sample_rate * duration))
            audio = np.zeros_like(t)

            # Add drum hits
            for measure in range(int(duration / (4 * beat_duration)) + 1):
                for beat_pos in beat_positions:
                    hit_time = measure * 4 * beat_duration + beat_pos * beat_duration
                    if hit_time < duration:
                        hit_sample = int(hit_time * self.sample_rate)

                        # Drum sound (noise burst with pitch)
                        drum_len = int(0.1 * self.sample_rate)
                        drum_t = np.linspace(0, 0.1, drum_len)
                        drum_sound = np.random.randn(drum_len) * np.exp(-30 * drum_t)
                        drum_sound += 0.5 * np.sin(2 * np.pi * 80 * drum_t) * np.exp(-20 * drum_t)

                        end_sample = min(hit_sample + drum_len, len(audio))
                        audio[hit_sample:end_sample] += drum_sound[:end_sample - hit_sample]

            # Normalize
            audio = audio / np.max(np.abs(audio) + 1e-8) * 0.9

            # Save
            sample_id = f"rhythm_{pattern_name}_{int(tempo)}bpm_{pat_idx:04d}"
            file_path = self.output_dir / f"{sample_id}.wav"
            wavfile.write(str(file_path), self.sample_rate,
                         (audio * 32767).astype(np.int16))

            sample = AudioSample(
                sample_id=sample_id,
                file_path=str(file_path),
                duration=duration,
                sample_rate=self.sample_rate,
                instrument="drums",
                instrument_family="percussion",
                tempo=tempo,
                dataset_source="synthetic_rhythms",
                features={"pattern": pattern_name}
            )

            samples.append(sample)

        self.samples.extend(samples)
        return samples

    def save_metadata(self, output_file: str = "dataset_metadata.json"):
        """Save all sample metadata to JSON."""
        metadata = {
            "num_samples": len(self.samples),
            "sample_rate": self.sample_rate,
            "samples": [asdict(s) for s in self.samples]
        }

        output_path = self.output_dir / output_file
        with open(output_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"Saved metadata for {len(self.samples)} samples to {output_path}")
        return output_path


class AudioAugmenter:
    """Audio augmentation for dataset expansion."""

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate

    def pitch_shift(self, audio: np.ndarray, semitones: float) -> np.ndarray:
        """Shift pitch by semitones (simple resampling method)."""
        factor = 2 ** (semitones / 12)
        indices = np.round(np.arange(0, len(audio), factor)).astype(int)
        indices = indices[indices < len(audio)]
        return audio[indices]

    def time_stretch(self, audio: np.ndarray, factor: float) -> np.ndarray:
        """Time stretch by factor (simple interpolation)."""
        new_length = int(len(audio) / factor)
        indices = np.linspace(0, len(audio) - 1, new_length)
        return np.interp(indices, np.arange(len(audio)), audio)

    def add_noise(self, audio: np.ndarray, snr_db: float = 20) -> np.ndarray:
        """Add white noise at specified SNR."""
        signal_power = np.mean(audio ** 2)
        noise_power = signal_power / (10 ** (snr_db / 10))
        noise = np.sqrt(noise_power) * np.random.randn(len(audio))
        return audio + noise

    def add_reverb(self, audio: np.ndarray, decay: float = 0.3, delay_ms: float = 50) -> np.ndarray:
        """Add simple reverb effect."""
        delay_samples = int(delay_ms * self.sample_rate / 1000)
        reverb = np.zeros(len(audio) + delay_samples)
        reverb[:len(audio)] = audio
        reverb[delay_samples:delay_samples + len(audio)] += decay * audio
        return reverb[:len(audio)]

    def augment_sample(self, audio: np.ndarray, augmentation_type: str) -> np.ndarray:
        """Apply a specific augmentation."""
        augmentations = {
            "pitch_up": lambda x: self.pitch_shift(x, 2),
            "pitch_down": lambda x: self.pitch_shift(x, -2),
            "time_slow": lambda x: self.time_stretch(x, 0.9),
            "time_fast": lambda x: self.time_stretch(x, 1.1),
            "noise_light": lambda x: self.add_noise(x, 30),
            "noise_heavy": lambda x: self.add_noise(x, 15),
            "reverb": lambda x: self.add_reverb(x, 0.3, 50),
        }

        if augmentation_type in augmentations:
            return augmentations[augmentation_type](audio)
        else:
            return audio


class DatasetManager:
    """Manage datasets for research experiments."""

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.samples: List[AudioSample] = []

    def load_metadata(self, metadata_file: str) -> List[AudioSample]:
        """Load samples from metadata file."""
        with open(metadata_file, 'r') as f:
            data = json.load(f)

        samples = [AudioSample(**s) for s in data['samples']]
        self.samples.extend(samples)
        return samples

    def create_splits(self,
                      train_ratio: float = 0.7,
                      val_ratio: float = 0.15,
                      test_ratio: float = 0.15,
                      stratify_by: str = "instrument") -> Dict[str, List[AudioSample]]:
        """Create train/val/test splits, optionally stratified."""
        np.random.shuffle(self.samples)

        # Group by stratification key
        groups = {}
        for sample in self.samples:
            key = getattr(sample, stratify_by, "unknown")
            if key not in groups:
                groups[key] = []
            groups[key].append(sample)

        splits = {"train": [], "val": [], "test": []}

        for key, group_samples in groups.items():
            n = len(group_samples)
            n_train = int(n * train_ratio)
            n_val = int(n * val_ratio)

            for i, sample in enumerate(group_samples):
                if i < n_train:
                    sample.split = "train"
                    splits["train"].append(sample)
                elif i < n_train + n_val:
                    sample.split = "val"
                    splits["val"].append(sample)
                else:
                    sample.split = "test"
                    splits["test"].append(sample)

        print(f"Created splits: train={len(splits['train'])}, "
              f"val={len(splits['val'])}, test={len(splits['test'])}")

        return splits

    def get_statistics(self) -> Dict:
        """Get dataset statistics."""
        stats = {
            "total_samples": len(self.samples),
            "total_duration_hours": sum(s.duration for s in self.samples) / 3600,
            "instruments": {},
            "instrument_families": {},
            "pitch_range": {"min": 127, "max": 0},
            "tempo_range": {"min": 999, "max": 0},
        }

        for sample in self.samples:
            # Instrument counts
            if sample.instrument:
                stats["instruments"][sample.instrument] = \
                    stats["instruments"].get(sample.instrument, 0) + 1

            if sample.instrument_family:
                stats["instrument_families"][sample.instrument_family] = \
                    stats["instrument_families"].get(sample.instrument_family, 0) + 1

            # Pitch range
            if sample.pitch:
                stats["pitch_range"]["min"] = min(stats["pitch_range"]["min"], sample.pitch)
                stats["pitch_range"]["max"] = max(stats["pitch_range"]["max"], sample.pitch)

            # Tempo range
            if sample.tempo:
                stats["tempo_range"]["min"] = min(stats["tempo_range"]["min"], sample.tempo)
                stats["tempo_range"]["max"] = max(stats["tempo_range"]["max"], sample.tempo)

        return stats


def build_research_dataset(output_dir: str,
                           samples_per_instrument: int = 100,
                           num_chord_progressions: int = 50,
                           num_rhythm_patterns: int = 50) -> str:
    """
    Build a complete research dataset with controlled samples.

    Returns path to metadata file.
    """
    print("=" * 60)
    print("  SYNESTHESIA Research Dataset Builder")
    print("=" * 60)

    generator = SyntheticDatasetGenerator(output_dir)

    # Generate instrument samples
    instruments = ["piano", "guitar", "violin", "flute", "clarinet", "trumpet", "bass", "organ"]

    for instrument in instruments:
        print(f"\nGenerating {samples_per_instrument} {instrument} samples...")
        generator.generate_instrument_family(instrument, num_samples=samples_per_instrument)

    # Generate chord progressions
    print(f"\nGenerating {num_chord_progressions} chord progressions...")
    generator.generate_chord_progressions(num_progressions=num_chord_progressions)

    # Generate rhythm patterns
    print(f"\nGenerating {num_rhythm_patterns} rhythm patterns...")
    generator.generate_rhythm_patterns(num_patterns=num_rhythm_patterns)

    # Save metadata
    metadata_path = generator.save_metadata()

    # Print statistics
    manager = DatasetManager(output_dir)
    manager.load_metadata(str(metadata_path))
    stats = manager.get_statistics()

    print("\n" + "=" * 60)
    print("  Dataset Statistics")
    print("=" * 60)
    print(f"  Total samples: {stats['total_samples']}")
    print(f"  Total duration: {stats['total_duration_hours']:.2f} hours")
    print(f"  Instruments: {list(stats['instruments'].keys())}")
    print(f"  Pitch range: MIDI {stats['pitch_range']['min']}-{stats['pitch_range']['max']}")
    print("=" * 60)

    return str(metadata_path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build SYNESTHESIA research dataset")
    parser.add_argument("--output", "-o", default="./research_dataset",
                       help="Output directory")
    parser.add_argument("--samples", "-n", type=int, default=50,
                       help="Samples per instrument")
    parser.add_argument("--chords", type=int, default=30,
                       help="Number of chord progressions")
    parser.add_argument("--rhythms", type=int, default=30,
                       help="Number of rhythm patterns")

    args = parser.parse_args()

    build_research_dataset(
        args.output,
        samples_per_instrument=args.samples,
        num_chord_progressions=args.chords,
        num_rhythm_patterns=args.rhythms
    )
