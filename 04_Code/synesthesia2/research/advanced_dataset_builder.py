#!/usr/bin/env python3
"""
SYNESTHESIA Research Framework - Advanced Dataset Builder
=========================================================
Creates comprehensive audio datasets with edge cases, noise conditions,
and complex real-world scenarios for robust visualization research.

Key Features:
- Edge case generation (extreme frequencies, dynamics, transients)
- Noise injection (white, pink, brown, environmental)
- Polyphonic complexity layers
- Real-world artifact simulation (clipping, compression, reverb)
- Melodic pattern library for trail analysis
"""

import numpy as np
import os
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Tuple, Optional, Callable
from pathlib import Path
import scipy.io.wavfile as wav
from scipy import signal
from scipy.ndimage import gaussian_filter1d
import warnings
warnings.filterwarnings('ignore')

# Constants
SAMPLE_RATE = 22050
NYQUIST = SAMPLE_RATE // 2


@dataclass
class AdvancedSample:
    """Extended audio sample with edge case metadata."""
    filename: str
    category: str
    subcategory: str
    duration: float
    sample_rate: int
    label: str

    # Edge case flags
    has_noise: bool = False
    noise_type: Optional[str] = None
    noise_snr_db: Optional[float] = None

    has_clipping: bool = False
    clipping_threshold: Optional[float] = None

    has_reverb: bool = False
    reverb_decay: Optional[float] = None

    is_polyphonic: bool = False
    polyphony_count: int = 1

    frequency_range: Tuple[float, float] = (20, 8000)
    dynamic_range_db: float = 40.0

    # Melodic characteristics
    melodic_contour: Optional[str] = None  # ascending, descending, arch, wave
    note_density: Optional[float] = None   # notes per second
    interval_complexity: Optional[float] = None  # average interval size

    metadata: Dict = field(default_factory=dict)


class NoiseGenerator:
    """Generate various noise types for robustness testing."""

    @staticmethod
    def white_noise(duration: float, amplitude: float = 1.0) -> np.ndarray:
        """Pure white noise - flat spectrum."""
        samples = int(duration * SAMPLE_RATE)
        return np.random.randn(samples) * amplitude

    @staticmethod
    def pink_noise(duration: float, amplitude: float = 1.0) -> np.ndarray:
        """Pink noise - 1/f spectrum, more natural sounding."""
        samples = int(duration * SAMPLE_RATE)
        white = np.random.randn(samples)

        # Apply 1/f filter using cumulative sum technique
        b = np.array([0.049922035, -0.095993537, 0.050612699, -0.004408786])
        a = np.array([1, -2.494956002, 2.017265875, -0.522189400])
        pink = signal.lfilter(b, a, white) * amplitude
        return pink

    @staticmethod
    def brown_noise(duration: float, amplitude: float = 1.0) -> np.ndarray:
        """Brown/red noise - 1/f² spectrum, very bassy."""
        samples = int(duration * SAMPLE_RATE)
        white = np.random.randn(samples)
        brown = np.cumsum(white)
        brown = brown / np.max(np.abs(brown)) * amplitude
        return brown

    @staticmethod
    def environmental_noise(duration: float, noise_type: str = 'room') -> np.ndarray:
        """Simulate environmental noise conditions."""
        samples = int(duration * SAMPLE_RATE)

        if noise_type == 'room':
            # Low rumble + high frequency hiss
            low = NoiseGenerator.brown_noise(duration, 0.3)
            high = NoiseGenerator.white_noise(duration, 0.1)
            high = signal.lfilter(*signal.butter(4, 0.3, 'high'), high)
            return low + high

        elif noise_type == 'street':
            # Broadband with occasional bursts
            base = NoiseGenerator.pink_noise(duration, 0.4)
            # Add random bursts
            burst_times = np.random.randint(0, samples, size=int(duration * 2))
            for bt in burst_times:
                burst_len = min(int(SAMPLE_RATE * 0.1), samples - bt)
                base[bt:bt+burst_len] += np.random.randn(burst_len) * 0.3
            return base

        elif noise_type == 'vinyl':
            # Crackle + low frequency rumble
            crackle = np.random.randn(samples) * 0.05
            crackle[np.random.rand(samples) > 0.995] *= 10  # Pops
            rumble = NoiseGenerator.brown_noise(duration, 0.1)
            return crackle + rumble

        else:
            return NoiseGenerator.white_noise(duration, 0.2)

    @staticmethod
    def add_noise_at_snr(audio: np.ndarray, noise: np.ndarray, snr_db: float) -> np.ndarray:
        """Mix noise with audio at specified SNR."""
        # Calculate signal power
        signal_power = np.mean(audio ** 2)
        noise_power = np.mean(noise ** 2)

        if noise_power == 0:
            return audio

        # Calculate required noise scale
        target_noise_power = signal_power / (10 ** (snr_db / 10))
        noise_scale = np.sqrt(target_noise_power / noise_power)

        return audio + noise[:len(audio)] * noise_scale


class AudioEffects:
    """Audio effects for simulating real-world recording artifacts."""

    @staticmethod
    def apply_clipping(audio: np.ndarray, threshold: float = 0.8) -> np.ndarray:
        """Simulate digital clipping/distortion."""
        return np.clip(audio, -threshold, threshold)

    @staticmethod
    def apply_compression(audio: np.ndarray, threshold: float = 0.5,
                          ratio: float = 4.0) -> np.ndarray:
        """Dynamic range compression."""
        compressed = audio.copy()
        above_threshold = np.abs(audio) > threshold
        compressed[above_threshold] = (
            np.sign(audio[above_threshold]) *
            (threshold + (np.abs(audio[above_threshold]) - threshold) / ratio)
        )
        return compressed

    @staticmethod
    def apply_reverb(audio: np.ndarray, decay: float = 0.3,
                     delay_ms: float = 50) -> np.ndarray:
        """Simple reverb simulation."""
        delay_samples = int(delay_ms * SAMPLE_RATE / 1000)
        reverb = np.zeros(len(audio) + delay_samples * 5)
        reverb[:len(audio)] = audio

        for i in range(1, 6):
            offset = delay_samples * i
            reverb[offset:offset+len(audio)] += audio * (decay ** i)

        return reverb[:len(audio)]

    @staticmethod
    def apply_eq_boost(audio: np.ndarray, center_freq: float,
                       gain_db: float = 6, q: float = 2.0) -> np.ndarray:
        """Parametric EQ boost/cut."""
        nyq = SAMPLE_RATE / 2
        freq_normalized = center_freq / nyq

        if freq_normalized >= 1:
            return audio

        # Design peaking filter
        bandwidth = freq_normalized / q
        b, a = signal.iirpeak(freq_normalized, q)

        filtered = signal.lfilter(b, a, audio)
        gain_linear = 10 ** (gain_db / 20)

        return audio + (filtered - audio) * (gain_linear - 1)


class MelodicPatternGenerator:
    """Generate melodic patterns for trail visualization research."""

    # Common melodic contours
    CONTOURS = {
        'ascending': lambda n: np.linspace(0, 1, n),
        'descending': lambda n: np.linspace(1, 0, n),
        'arch': lambda n: np.sin(np.linspace(0, np.pi, n)),
        'inverted_arch': lambda n: 1 - np.sin(np.linspace(0, np.pi, n)),
        'wave': lambda n: (np.sin(np.linspace(0, 2*np.pi, n)) + 1) / 2,
        'zigzag': lambda n: np.abs(np.linspace(-1, 1, n) * (np.arange(n) % 2 * 2 - 1)),
        'step_up': lambda n: np.floor(np.linspace(0, 4, n)) / 4,
        'step_down': lambda n: 1 - np.floor(np.linspace(0, 4, n)) / 4,
    }

    # Musical scales (semitone patterns)
    SCALES = {
        'major': [0, 2, 4, 5, 7, 9, 11],
        'minor': [0, 2, 3, 5, 7, 8, 10],
        'pentatonic': [0, 2, 4, 7, 9],
        'blues': [0, 3, 5, 6, 7, 10],
        'chromatic': list(range(12)),
        'whole_tone': [0, 2, 4, 6, 8, 10],
    }

    @classmethod
    def generate_melody(cls, base_midi: int = 60, num_notes: int = 8,
                       contour: str = 'arch', scale: str = 'major',
                       note_duration: float = 0.3,
                       legato: float = 0.8) -> Tuple[np.ndarray, Dict]:
        """
        Generate a melodic sequence with specific contour and scale.

        Returns:
            audio: Generated audio
            metadata: Melodic characteristics
        """
        # Get contour shape
        contour_fn = cls.CONTOURS.get(contour, cls.CONTOURS['arch'])
        contour_values = contour_fn(num_notes)

        # Get scale
        scale_degrees = cls.SCALES.get(scale, cls.SCALES['major'])
        scale_range = len(scale_degrees) * 2  # Two octaves

        # Map contour to scale degrees
        scale_indices = (contour_values * (scale_range - 1)).astype(int)
        midi_notes = []
        for idx in scale_indices:
            octave = idx // len(scale_degrees)
            degree = idx % len(scale_degrees)
            midi_notes.append(base_midi + octave * 12 + scale_degrees[degree])

        # Generate audio
        total_duration = num_notes * note_duration
        samples_per_note = int(note_duration * SAMPLE_RATE)
        audio = np.zeros(int(total_duration * SAMPLE_RATE))

        intervals = []
        for i, midi in enumerate(midi_notes):
            freq = 440 * (2 ** ((midi - 69) / 12))
            start = i * samples_per_note

            # Generate note with envelope
            t = np.linspace(0, note_duration * legato, int(samples_per_note * legato))
            envelope = np.exp(-t * 3)  # Decay
            note = np.sin(2 * np.pi * freq * t) * envelope

            # Add harmonics for richness
            note += 0.3 * np.sin(4 * np.pi * freq * t) * envelope
            note += 0.15 * np.sin(6 * np.pi * freq * t) * envelope

            end = min(start + len(note), len(audio))
            audio[start:end] += note[:end-start]

            if i > 0:
                intervals.append(abs(midi_notes[i] - midi_notes[i-1]))

        # Normalize
        audio = audio / np.max(np.abs(audio)) * 0.8

        metadata = {
            'contour': contour,
            'scale': scale,
            'base_midi': base_midi,
            'num_notes': num_notes,
            'note_duration': note_duration,
            'midi_sequence': midi_notes,
            'interval_complexity': np.mean(intervals) if intervals else 0,
            'note_density': num_notes / total_duration,
            'pitch_range': max(midi_notes) - min(midi_notes),
        }

        return audio, metadata

    @classmethod
    def generate_complex_melody(cls, duration: float = 4.0,
                                layers: int = 2,
                                base_midi: int = 60) -> Tuple[np.ndarray, Dict]:
        """Generate polyphonic melody with multiple voice layers."""
        audio = np.zeros(int(duration * SAMPLE_RATE))
        all_metadata = []

        contours = list(cls.CONTOURS.keys())
        scales = list(cls.SCALES.keys())

        for layer in range(layers):
            # Vary parameters per layer
            contour = contours[layer % len(contours)]
            scale = scales[layer % len(scales)]
            layer_base = base_midi + layer * 7  # Offset by fifth
            num_notes = 6 + layer * 2

            layer_audio, metadata = cls.generate_melody(
                base_midi=layer_base,
                num_notes=num_notes,
                contour=contour,
                scale=scale,
                note_duration=duration / num_notes * 0.9,
            )

            # Pad or trim to match duration
            if len(layer_audio) < len(audio):
                audio[:len(layer_audio)] += layer_audio * (0.8 ** layer)
            else:
                audio += layer_audio[:len(audio)] * (0.8 ** layer)

            metadata['layer'] = layer
            all_metadata.append(metadata)

        audio = audio / np.max(np.abs(audio)) * 0.8

        return audio, {'layers': all_metadata, 'polyphony': layers}


class EdgeCaseGenerator:
    """Generate audio edge cases for robustness testing."""

    @staticmethod
    def extreme_frequency_sweep(duration: float = 3.0,
                                 f_start: float = 20,
                                 f_end: float = 15000) -> np.ndarray:
        """Logarithmic frequency sweep across audible range."""
        t = np.linspace(0, duration, int(duration * SAMPLE_RATE))

        # Logarithmic sweep
        phase = 2 * np.pi * f_start * duration / np.log(f_end/f_start) * \
                (np.exp(t/duration * np.log(f_end/f_start)) - 1)

        audio = np.sin(phase) * 0.8
        return audio

    @staticmethod
    def extreme_dynamics(duration: float = 4.0) -> np.ndarray:
        """Audio with extreme dynamic range (pp to ff)."""
        t = np.linspace(0, duration, int(duration * SAMPLE_RATE))

        # Base tone
        freq = 440
        audio = np.sin(2 * np.pi * freq * t)

        # Extreme envelope: very quiet to very loud
        envelope = np.exp(np.linspace(-6, 0, len(t)))  # ~48dB range

        return audio * envelope

    @staticmethod
    def rapid_transients(duration: float = 3.0,
                         transients_per_second: float = 8) -> np.ndarray:
        """Rapid attack/decay transients (percussion-like)."""
        samples = int(duration * SAMPLE_RATE)
        audio = np.zeros(samples)

        num_transients = int(duration * transients_per_second)
        transient_spacing = samples // num_transients

        for i in range(num_transients):
            pos = i * transient_spacing

            # Quick attack, decay envelope
            transient_len = min(int(SAMPLE_RATE * 0.1), samples - pos)
            t = np.linspace(0, 0.1, transient_len)
            envelope = np.exp(-t * 30)

            # Random frequency for each transient
            freq = 200 + np.random.rand() * 800
            transient = np.sin(2 * np.pi * freq * t) * envelope

            # Add some harmonics
            transient += 0.5 * np.sin(4 * np.pi * freq * t) * envelope

            audio[pos:pos+transient_len] += transient

        return audio / np.max(np.abs(audio)) * 0.8

    @staticmethod
    def silence_gaps(duration: float = 4.0,
                     num_gaps: int = 3) -> np.ndarray:
        """Audio with silence gaps (tests trail persistence)."""
        samples = int(duration * SAMPLE_RATE)
        t = np.linspace(0, duration, samples)

        # Base melody
        freq = 440
        audio = np.sin(2 * np.pi * freq * t) * 0.5
        audio += 0.3 * np.sin(2 * np.pi * freq * 2 * t)

        # Insert silence gaps
        gap_duration = int(SAMPLE_RATE * 0.3)
        for i in range(num_gaps):
            gap_start = int((i + 1) * samples / (num_gaps + 1))
            gap_end = min(gap_start + gap_duration, samples)
            audio[gap_start:gap_end] = 0

        return audio

    @staticmethod
    def frequency_collision(duration: float = 3.0) -> np.ndarray:
        """Multiple frequencies very close together (beating)."""
        t = np.linspace(0, duration, int(duration * SAMPLE_RATE))

        base_freq = 440
        # Frequencies within 5Hz of each other
        freqs = [base_freq, base_freq + 2, base_freq + 5]

        audio = np.zeros_like(t)
        for freq in freqs:
            audio += np.sin(2 * np.pi * freq * t) * 0.3

        return audio

    @staticmethod
    def microtonal_content(duration: float = 3.0) -> np.ndarray:
        """Quarter-tone and microtonal intervals."""
        t = np.linspace(0, duration, int(duration * SAMPLE_RATE))

        # A4 and A4 + 50 cents (quarter tone)
        f1 = 440
        f2 = 440 * (2 ** (0.5/12))  # Quarter tone up
        f3 = 440 * (2 ** (0.25/12))  # Eighth tone up

        audio = np.sin(2 * np.pi * f1 * t) * 0.4
        audio += np.sin(2 * np.pi * f2 * t) * 0.3
        audio += np.sin(2 * np.pi * f3 * t) * 0.2

        return audio

    @staticmethod
    def extreme_polyphony(duration: float = 3.0,
                          voices: int = 12) -> np.ndarray:
        """Dense polyphonic texture."""
        t = np.linspace(0, duration, int(duration * SAMPLE_RATE))
        audio = np.zeros_like(t)

        # Create cluster of voices
        base_midi = 48  # C3
        for v in range(voices):
            # Distribute across 2 octaves
            midi = base_midi + (v * 24 // voices) + np.random.randint(-2, 3)
            freq = 440 * (2 ** ((midi - 69) / 12))

            # Slightly detuned for richness
            detune = 1 + (np.random.rand() - 0.5) * 0.01

            # Random phase
            phase = np.random.rand() * 2 * np.pi

            voice = np.sin(2 * np.pi * freq * detune * t + phase)

            # Individual envelope
            attack = int(SAMPLE_RATE * np.random.rand() * 0.2)
            env = np.ones_like(t)
            env[:attack] = np.linspace(0, 1, attack)

            audio += voice * env * (1 / voices)

        return audio / np.max(np.abs(audio)) * 0.8


class AdvancedDatasetBuilder:
    """Build comprehensive dataset with edge cases for research."""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.samples: List[AdvancedSample] = []

        self.noise_gen = NoiseGenerator()
        self.effects = AudioEffects()
        self.melody_gen = MelodicPatternGenerator()
        self.edge_gen = EdgeCaseGenerator()

    def _save_audio(self, audio: np.ndarray, filename: str) -> str:
        """Save audio to file."""
        filepath = self.output_dir / filename

        # Normalize and convert to int16
        audio = audio / np.max(np.abs(audio) + 1e-8) * 0.9
        audio_int = (audio * 32767).astype(np.int16)

        wav.write(str(filepath), SAMPLE_RATE, audio_int)
        return str(filepath)

    def generate_melodic_dataset(self, num_per_contour: int = 10):
        """Generate melody samples for trail analysis."""
        print("\n🎵 Generating Melodic Dataset for Trail Analysis...")

        contours = list(MelodicPatternGenerator.CONTOURS.keys())
        scales = ['major', 'minor', 'pentatonic', 'blues']

        for contour in contours:
            for scale in scales:
                for i in range(num_per_contour):
                    # Vary parameters
                    base_midi = 48 + np.random.randint(0, 24)
                    num_notes = np.random.randint(6, 16)
                    note_duration = 0.2 + np.random.rand() * 0.4

                    audio, metadata = self.melody_gen.generate_melody(
                        base_midi=base_midi,
                        num_notes=num_notes,
                        contour=contour,
                        scale=scale,
                        note_duration=note_duration,
                    )

                    filename = f"melody_{contour}_{scale}_{i:04d}.wav"
                    self._save_audio(audio, filename)

                    sample = AdvancedSample(
                        filename=filename,
                        category='melody',
                        subcategory=f'{contour}_{scale}',
                        duration=len(audio) / SAMPLE_RATE,
                        sample_rate=SAMPLE_RATE,
                        label=contour,
                        melodic_contour=contour,
                        note_density=metadata['note_density'],
                        interval_complexity=metadata['interval_complexity'],
                        metadata=metadata,
                    )
                    self.samples.append(sample)

        print(f"   Generated {len(contours) * len(scales) * num_per_contour} melody samples")

    def generate_polyphonic_dataset(self, num_samples: int = 50):
        """Generate polyphonic complexity samples."""
        print("\n🎹 Generating Polyphonic Dataset...")

        for i in range(num_samples):
            layers = np.random.randint(2, 5)
            duration = 3.0 + np.random.rand() * 2
            base_midi = 48 + np.random.randint(0, 12)

            audio, metadata = self.melody_gen.generate_complex_melody(
                duration=duration,
                layers=layers,
                base_midi=base_midi,
            )

            filename = f"polyphonic_{layers}voices_{i:04d}.wav"
            self._save_audio(audio, filename)

            sample = AdvancedSample(
                filename=filename,
                category='polyphonic',
                subcategory=f'{layers}_voices',
                duration=duration,
                sample_rate=SAMPLE_RATE,
                label=f'poly_{layers}',
                is_polyphonic=True,
                polyphony_count=layers,
                metadata=metadata,
            )
            self.samples.append(sample)

        print(f"   Generated {num_samples} polyphonic samples")

    def generate_edge_cases(self, num_each: int = 20):
        """Generate edge case samples."""
        print("\n⚠️ Generating Edge Cases...")

        edge_cases = {
            'freq_sweep': lambda: self.edge_gen.extreme_frequency_sweep(),
            'extreme_dynamics': lambda: self.edge_gen.extreme_dynamics(),
            'rapid_transients': lambda: self.edge_gen.rapid_transients(),
            'silence_gaps': lambda: self.edge_gen.silence_gaps(),
            'freq_collision': lambda: self.edge_gen.frequency_collision(),
            'microtonal': lambda: self.edge_gen.microtonal_content(),
            'extreme_polyphony': lambda: self.edge_gen.extreme_polyphony(),
        }

        for case_name, generator in edge_cases.items():
            for i in range(num_each):
                audio = generator()

                filename = f"edge_{case_name}_{i:04d}.wav"
                self._save_audio(audio, filename)

                sample = AdvancedSample(
                    filename=filename,
                    category='edge_case',
                    subcategory=case_name,
                    duration=len(audio) / SAMPLE_RATE,
                    sample_rate=SAMPLE_RATE,
                    label=case_name,
                    metadata={'edge_type': case_name},
                )
                self.samples.append(sample)

        print(f"   Generated {len(edge_cases) * num_each} edge case samples")

    def generate_noise_variants(self, num_base: int = 30):
        """Generate clean samples with various noise conditions."""
        print("\n🔊 Generating Noise Variant Dataset...")

        noise_types = ['white', 'pink', 'brown', 'room', 'street', 'vinyl']
        snr_levels = [30, 20, 10, 5]  # dB

        for i in range(num_base):
            # Generate base melody
            contour = np.random.choice(list(MelodicPatternGenerator.CONTOURS.keys()))
            base_audio, _ = self.melody_gen.generate_melody(
                contour=contour,
                num_notes=8,
            )

            for noise_type in noise_types:
                for snr in snr_levels:
                    # Generate noise
                    if noise_type in ['white', 'pink', 'brown']:
                        noise_fn = getattr(self.noise_gen, f'{noise_type}_noise')
                        noise = noise_fn(len(base_audio) / SAMPLE_RATE)
                    else:
                        noise = self.noise_gen.environmental_noise(
                            len(base_audio) / SAMPLE_RATE, noise_type
                        )

                    # Mix at SNR
                    noisy_audio = self.noise_gen.add_noise_at_snr(base_audio, noise, snr)

                    filename = f"noisy_{noise_type}_snr{snr}_{i:04d}.wav"
                    self._save_audio(noisy_audio, filename)

                    sample = AdvancedSample(
                        filename=filename,
                        category='noisy',
                        subcategory=f'{noise_type}_snr{snr}',
                        duration=len(noisy_audio) / SAMPLE_RATE,
                        sample_rate=SAMPLE_RATE,
                        label=noise_type,
                        has_noise=True,
                        noise_type=noise_type,
                        noise_snr_db=float(snr),
                        metadata={'base_contour': contour},
                    )
                    self.samples.append(sample)

        total = num_base * len(noise_types) * len(snr_levels)
        print(f"   Generated {total} noise variant samples")

    def generate_effect_variants(self, num_base: int = 30):
        """Generate samples with audio effects (clipping, reverb, compression)."""
        print("\n🎚️ Generating Effect Variant Dataset...")

        effects_config = [
            ('clipped_light', lambda a: self.effects.apply_clipping(a, 0.9)),
            ('clipped_heavy', lambda a: self.effects.apply_clipping(a, 0.5)),
            ('reverb_short', lambda a: self.effects.apply_reverb(a, 0.2, 30)),
            ('reverb_long', lambda a: self.effects.apply_reverb(a, 0.5, 100)),
            ('compressed', lambda a: self.effects.apply_compression(a, 0.4, 6)),
            ('eq_bass_boost', lambda a: self.effects.apply_eq_boost(a, 100, 8)),
            ('eq_presence', lambda a: self.effects.apply_eq_boost(a, 3000, 6)),
        ]

        for i in range(num_base):
            # Generate base content
            audio, _ = self.melody_gen.generate_melody(
                num_notes=np.random.randint(6, 12),
                contour=np.random.choice(list(MelodicPatternGenerator.CONTOURS.keys())),
            )

            for effect_name, effect_fn in effects_config:
                processed = effect_fn(audio)

                filename = f"effect_{effect_name}_{i:04d}.wav"
                self._save_audio(processed, filename)

                sample = AdvancedSample(
                    filename=filename,
                    category='effects',
                    subcategory=effect_name,
                    duration=len(processed) / SAMPLE_RATE,
                    sample_rate=SAMPLE_RATE,
                    label=effect_name.split('_')[0],
                    has_clipping='clipped' in effect_name,
                    has_reverb='reverb' in effect_name,
                    metadata={'effect': effect_name},
                )
                self.samples.append(sample)

        total = num_base * len(effects_config)
        print(f"   Generated {total} effect variant samples")

    def generate_full_dataset(self,
                              melodic_per_contour: int = 10,
                              polyphonic: int = 50,
                              edge_cases_each: int = 20,
                              noise_base: int = 30,
                              effects_base: int = 30):
        """Generate complete research dataset."""
        print("\n" + "="*60)
        print("  SYNESTHESIA Advanced Dataset Builder")
        print("="*60)

        self.generate_melodic_dataset(melodic_per_contour)
        self.generate_polyphonic_dataset(polyphonic)
        self.generate_edge_cases(edge_cases_each)
        self.generate_noise_variants(noise_base)
        self.generate_effect_variants(effects_base)

        # Helper to convert numpy types to native Python types
        def convert_to_native(obj):
            if isinstance(obj, dict):
                return {k: convert_to_native(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_native(v) for v in obj]
            elif isinstance(obj, tuple):
                return tuple(convert_to_native(v) for v in obj)
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj

        # Save metadata
        metadata = {
            'total_samples': len(self.samples),
            'categories': {},
            'samples': [convert_to_native(asdict(s)) for s in self.samples],
        }

        # Count by category
        for sample in self.samples:
            cat = sample.category
            if cat not in metadata['categories']:
                metadata['categories'][cat] = 0
            metadata['categories'][cat] += 1

        metadata_path = self.output_dir / 'advanced_dataset_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        print("\n" + "="*60)
        print("  Dataset Statistics")
        print("="*60)
        print(f"  Total samples: {len(self.samples)}")
        for cat, count in metadata['categories'].items():
            print(f"  - {cat}: {count}")
        print(f"  Metadata saved to: {metadata_path}")
        print("="*60)

        return metadata


def main():
    """Build advanced dataset."""
    import argparse

    parser = argparse.ArgumentParser(description='Build advanced research dataset')
    parser.add_argument('-o', '--output', default='./advanced_dataset',
                       help='Output directory')
    parser.add_argument('--melodic', type=int, default=10,
                       help='Samples per melodic contour')
    parser.add_argument('--polyphonic', type=int, default=50,
                       help='Polyphonic samples')
    parser.add_argument('--edge', type=int, default=20,
                       help='Edge cases per type')
    parser.add_argument('--noise', type=int, default=30,
                       help='Base samples for noise variants')
    parser.add_argument('--effects', type=int, default=30,
                       help='Base samples for effect variants')

    args = parser.parse_args()

    builder = AdvancedDatasetBuilder(args.output)
    builder.generate_full_dataset(
        melodic_per_contour=args.melodic,
        polyphonic=args.polyphonic,
        edge_cases_each=args.edge,
        noise_base=args.noise,
        effects_base=args.effects,
    )


if __name__ == '__main__':
    main()
