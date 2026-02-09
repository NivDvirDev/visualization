"""
SYNESTHESIA 3.0 - Temporal Audio Analyzer
==========================================
Extracts multi-scale temporal features for breakthrough visualization:
- Melody: Pitch contours over 1-10 seconds
- Rhythm: Beat patterns over 0.5-4 seconds
- Harmony: Chord progressions over 2-30 seconds
- Atmosphere: Energy/emotion trajectory over 30-300 seconds

This extends audio_analyzer.py to capture what makes music MUSICAL.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict
from collections import deque
import warnings

# Try to import librosa for advanced audio analysis
try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False
    warnings.warn("librosa not found. Install with: pip install librosa")


@dataclass
class TemporalConfig:
    """Configuration for multi-scale temporal analysis."""
    # Frame-level (existing)
    frame_rate: int = 30

    # Note-level (50-500ms)
    pitch_fmin: float = 50.0  # Minimum pitch to track
    pitch_fmax: float = 2000.0  # Maximum pitch to track

    # Motif-level (0.5-4s)
    beat_tracking: bool = True

    # Phrase-level (2-30s)
    chord_detection: bool = True
    segment_detection: bool = True

    # Atmosphere-level (30-300s)
    energy_smoothing_window: float = 2.0  # seconds
    atmosphere_window: float = 30.0  # seconds for mood estimation


@dataclass
class TemporalFeatures:
    """Multi-scale temporal analysis results."""
    # Basic info
    sample_rate: int
    total_frames: int
    duration_seconds: float

    # Frame-level (from existing audio_analyzer.py)
    amplitude_data: np.ndarray = None  # [num_freqs, num_frames]
    frequencies: np.ndarray = None

    # Note-level - MELODY
    pitch_contour: np.ndarray = None  # [num_frames] - F0 in Hz (0 = unvoiced)
    pitch_confidence: np.ndarray = None  # [num_frames] - confidence of pitch estimate
    onset_frames: np.ndarray = None  # Frame indices of note onsets
    onset_strengths: np.ndarray = None  # Strength of each onset

    # Motif-level - RHYTHM
    tempo: float = 0.0  # Estimated BPM
    beat_frames: np.ndarray = None  # Frame indices of beats
    beat_strength: np.ndarray = None  # [num_frames] - rhythmic emphasis
    downbeat_frames: np.ndarray = None  # Frame indices of downbeats (measure starts)

    # Phrase-level - HARMONY
    chroma: np.ndarray = None  # [12, num_frames] - pitch class energy
    chord_frames: np.ndarray = None  # Frame indices of chord changes
    chord_labels: List[str] = field(default_factory=list)  # Chord label for each segment
    segment_boundaries: np.ndarray = None  # Structural segment boundaries

    # Atmosphere-level - MOOD
    energy_curve: np.ndarray = None  # [num_frames] - smoothed RMS energy
    spectral_centroid: np.ndarray = None  # [num_frames] - brightness
    spectral_contrast: np.ndarray = None  # [num_bands, num_frames] - texture
    tension_curve: np.ndarray = None  # [num_frames] - harmonic tension estimate


class TemporalAudioAnalyzer:
    """
    Extracts multi-scale temporal features for musical visualization.

    Analyzes audio at multiple time scales to capture:
    - What note is playing (frame-level, existing)
    - What melody is being played (note sequences)
    - What rhythm drives the music (beat patterns)
    - What harmony underlies the music (chord progressions)
    - What atmosphere pervades the piece (long-term mood)
    """

    def __init__(self, config: Optional[TemporalConfig] = None):
        self.config = config or TemporalConfig()

        if not HAS_LIBROSA:
            raise ImportError("librosa is required for temporal analysis. Install with: pip install librosa")

    def analyze(self, audio_path: str,
                start_time: float = 0,
                duration: Optional[float] = None) -> TemporalFeatures:
        """
        Perform multi-scale temporal analysis on audio file.

        Args:
            audio_path: Path to audio file
            start_time: Start time in seconds
            duration: Duration to analyze (None = entire file)

        Returns:
            TemporalFeatures containing all extracted features
        """
        print(f"Loading audio: {audio_path}")

        # Load audio with librosa
        y, sr = librosa.load(audio_path, sr=None, offset=start_time, duration=duration)

        # Calculate basic parameters
        hop_length = int(sr / self.config.frame_rate)
        total_frames = len(y) // hop_length
        duration_seconds = len(y) / sr

        print(f"Audio: {duration_seconds:.2f}s, {sr}Hz, {total_frames} frames")

        # Initialize features
        features = TemporalFeatures(
            sample_rate=sr,
            total_frames=total_frames,
            duration_seconds=duration_seconds
        )

        # Extract features at each level
        print("Extracting frame-level features...")
        self._extract_frame_features(y, sr, hop_length, features)

        print("Extracting note-level features (melody)...")
        self._extract_note_features(y, sr, hop_length, features)

        print("Extracting motif-level features (rhythm)...")
        self._extract_motif_features(y, sr, hop_length, features)

        print("Extracting phrase-level features (harmony)...")
        self._extract_phrase_features(y, sr, hop_length, features)

        print("Extracting atmosphere-level features (mood)...")
        self._extract_atmosphere_features(y, sr, hop_length, features)

        print("Temporal analysis complete!")
        return features

    def _extract_frame_features(self, y: np.ndarray, sr: int, hop_length: int,
                                features: TemporalFeatures):
        """Extract frame-level spectral features."""
        # Mel spectrogram for frequency representation
        mel_spec = librosa.feature.melspectrogram(
            y=y, sr=sr, hop_length=hop_length,
            n_mels=128, fmin=20, fmax=8000
        )
        features.amplitude_data = librosa.power_to_db(mel_spec, ref=np.max)
        features.frequencies = librosa.mel_frequencies(n_mels=128, fmin=20, fmax=8000)

    def _extract_note_features(self, y: np.ndarray, sr: int, hop_length: int,
                               features: TemporalFeatures):
        """Extract note-level features - MELODY."""
        # Pitch tracking with pyin (probabilistic YIN)
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y, sr=sr, hop_length=hop_length,
            fmin=self.config.pitch_fmin,
            fmax=self.config.pitch_fmax
        )

        # Replace NaN with 0 for unvoiced frames
        f0 = np.nan_to_num(f0, nan=0.0)

        features.pitch_contour = f0
        features.pitch_confidence = voiced_probs

        # Onset detection
        onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
        features.onset_strengths = onset_env

        onset_frames = librosa.onset.onset_detect(
            onset_envelope=onset_env, sr=sr, hop_length=hop_length
        )
        features.onset_frames = onset_frames

    def _extract_motif_features(self, y: np.ndarray, sr: int, hop_length: int,
                                features: TemporalFeatures):
        """Extract motif-level features - RHYTHM."""
        if not self.config.beat_tracking:
            return

        # Beat tracking
        tempo, beat_frames = librosa.beat.beat_track(
            y=y, sr=sr, hop_length=hop_length
        )

        features.tempo = float(tempo)
        features.beat_frames = beat_frames

        # Beat strength at each frame
        onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
        features.beat_strength = onset_env

        # Estimate downbeats (simplified - every 4th beat for 4/4 time)
        if len(beat_frames) > 0:
            features.downbeat_frames = beat_frames[::4]

    def _extract_phrase_features(self, y: np.ndarray, sr: int, hop_length: int,
                                 features: TemporalFeatures):
        """Extract phrase-level features - HARMONY."""
        # Chromagram (pitch class distribution)
        chroma = librosa.feature.chroma_cqt(
            y=y, sr=sr, hop_length=hop_length
        )
        features.chroma = chroma

        if self.config.chord_detection:
            # Simple chord detection using chroma templates
            features.chord_frames, features.chord_labels = self._detect_chords(chroma, sr, hop_length)

        if self.config.segment_detection:
            # Structural segmentation
            features.segment_boundaries = self._detect_segments(y, sr, hop_length)

    def _detect_chords(self, chroma: np.ndarray, sr: int, hop_length: int
                       ) -> Tuple[np.ndarray, List[str]]:
        """Simple chord detection from chroma features."""
        # Major and minor chord templates
        major_template = np.array([1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0])  # Root, M3, P5
        minor_template = np.array([1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0])  # Root, m3, P5

        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

        # Smooth chroma over time
        chroma_smooth = librosa.decompose.nn_filter(
            chroma, aggregate=np.median, metric='cosine'
        )

        chord_frames = []
        chord_labels = []

        # Analyze every N frames (~ 0.5 seconds)
        segment_length = int(0.5 * sr / hop_length)

        prev_chord = None
        for i in range(0, chroma.shape[1], segment_length):
            segment = chroma_smooth[:, i:i+segment_length]
            if segment.size == 0:
                continue

            # Get mean chroma for segment
            mean_chroma = np.mean(segment, axis=1)

            # Find best matching chord
            best_score = -np.inf
            best_chord = "N"  # No chord

            for root in range(12):
                # Roll templates to each root
                maj_template_shifted = np.roll(major_template, root)
                min_template_shifted = np.roll(minor_template, root)

                maj_score = np.dot(mean_chroma, maj_template_shifted)
                min_score = np.dot(mean_chroma, min_template_shifted)

                if maj_score > best_score:
                    best_score = maj_score
                    best_chord = note_names[root]
                if min_score > best_score:
                    best_score = min_score
                    best_chord = note_names[root] + "m"

            # Record chord changes
            if best_chord != prev_chord:
                chord_frames.append(i)
                chord_labels.append(best_chord)
                prev_chord = best_chord

        return np.array(chord_frames), chord_labels

    def _detect_segments(self, y: np.ndarray, sr: int, hop_length: int) -> np.ndarray:
        """Detect structural segment boundaries."""
        # Use spectral clustering on self-similarity matrix
        # Simplified version using onset envelope changes

        onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)

        # Compute self-similarity
        mfcc = librosa.feature.mfcc(y=y, sr=sr, hop_length=hop_length, n_mfcc=13)

        # Use librosa's segmentation
        try:
            bounds = librosa.segment.agglomerative(mfcc, k=None)
            return bounds
        except Exception:
            # Fallback: return evenly spaced segments
            num_segments = max(1, int(len(y) / sr / 10))  # One segment per ~10 seconds
            return np.linspace(0, mfcc.shape[1], num_segments + 1, dtype=int)

    def _extract_atmosphere_features(self, y: np.ndarray, sr: int, hop_length: int,
                                     features: TemporalFeatures):
        """Extract atmosphere-level features - MOOD."""
        # RMS energy
        rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]

        # Smooth energy over time
        smooth_window = int(self.config.energy_smoothing_window * sr / hop_length)
        if smooth_window > 1:
            kernel = np.ones(smooth_window) / smooth_window
            features.energy_curve = np.convolve(rms, kernel, mode='same')
        else:
            features.energy_curve = rms

        # Spectral centroid (brightness)
        features.spectral_centroid = librosa.feature.spectral_centroid(
            y=y, sr=sr, hop_length=hop_length
        )[0]

        # Spectral contrast (texture)
        features.spectral_contrast = librosa.feature.spectral_contrast(
            y=y, sr=sr, hop_length=hop_length
        )

        # Tension estimate (based on dissonance - simplified)
        # High spectral flatness = more noise/tension
        spectral_flatness = librosa.feature.spectral_flatness(y=y, hop_length=hop_length)[0]
        features.tension_curve = spectral_flatness


class MelodyTrailRenderer:
    """
    Renders melodic trails on the spiral visualization.

    Shows the last N seconds of pitch as a glowing trail,
    making the melody contour visible.
    """

    def __init__(self,
                 trail_duration: float = 3.0,  # seconds
                 frame_rate: int = 30,
                 decay_rate: float = 0.92):
        self.trail_length = int(trail_duration * frame_rate)
        self.decay_rate = decay_rate
        self.pitch_history = deque(maxlen=self.trail_length)

        # Pitch to spiral position mapping
        self.freq_min = 50.0
        self.freq_max = 2000.0

    def update(self, pitch_hz: float, confidence: float = 1.0):
        """Add current pitch to the trail."""
        self.pitch_history.append((pitch_hz, confidence))

    def get_trail_points(self, spiral_params: dict) -> List[Tuple[float, float, float, float]]:
        """
        Get trail points for rendering.

        Returns:
            List of (x, y, alpha, size) tuples for each trail point
        """
        points = []

        for i, (pitch, confidence) in enumerate(self.pitch_history):
            if pitch <= 0 or confidence < 0.3:
                continue

            # Map pitch to spiral position
            x, y = self._pitch_to_spiral_coords(pitch, spiral_params)

            # Alpha decays with age
            age = len(self.pitch_history) - i - 1
            alpha = (self.decay_rate ** age) * confidence

            # Size based on confidence
            size = 3 + confidence * 5

            points.append((x, y, alpha, size))

        return points

    def _pitch_to_spiral_coords(self, pitch_hz: float, spiral_params: dict
                                ) -> Tuple[float, float]:
        """Map a pitch frequency to spiral coordinates."""
        center_x = spiral_params.get('center_x', 320)
        center_y = spiral_params.get('center_y', 240)
        max_radius = spiral_params.get('max_radius', 200)
        num_turns = spiral_params.get('num_turns', 7)
        rotation = spiral_params.get('rotation', 0)

        # Logarithmic mapping of frequency to radius
        if pitch_hz <= self.freq_min:
            rel_freq = 0
        elif pitch_hz >= self.freq_max:
            rel_freq = 1
        else:
            rel_freq = (np.log(pitch_hz) - np.log(self.freq_min)) / \
                       (np.log(self.freq_max) - np.log(self.freq_min))

        # Fermat spiral
        theta = rel_freq * num_turns * 2 * np.pi + rotation
        r = np.sqrt(rel_freq) * max_radius

        x = center_x + r * np.cos(theta)
        y = center_y + r * np.sin(theta)

        return x, y


class RhythmPulseRenderer:
    """
    Modulates spiral visualization based on beat.

    Makes the spiral "breathe" with the rhythm.
    """

    def __init__(self,
                 pulse_scale: float = 0.15,  # Max scale change on beat
                 pulse_decay: float = 0.85):  # How fast pulse decays
        self.pulse_scale = pulse_scale
        self.pulse_decay = pulse_decay
        self.current_pulse = 0.0

    def on_beat(self, strength: float = 1.0):
        """Called when a beat occurs."""
        self.current_pulse = min(1.0, self.current_pulse + strength)

    def update(self) -> float:
        """
        Update and return current pulse amount.

        Returns:
            Scale multiplier (1.0 = no change, 1.15 = 15% larger on beat)
        """
        scale = 1.0 + self.current_pulse * self.pulse_scale
        self.current_pulse *= self.pulse_decay
        return scale

    def get_brightness_boost(self) -> float:
        """Get brightness boost based on current pulse."""
        return self.current_pulse * 0.3


class HarmonicAuraRenderer:
    """
    Maps chord/harmony to background color.

    Creates emotional atmosphere based on harmonic content.
    """

    # Circle of fifths color mapping
    # C -> C# -> D -> ... following chromatic order
    # Colors follow a gradual shift around the color wheel
    CHORD_COLORS = {
        'C': (255, 80, 80),      # Red
        'C#': (255, 120, 80),    # Red-orange
        'D': (255, 160, 80),     # Orange
        'D#': (255, 200, 80),    # Orange-yellow
        'E': (255, 255, 80),     # Yellow
        'F': (160, 255, 80),     # Yellow-green
        'F#': (80, 255, 80),     # Green
        'G': (80, 255, 160),     # Green-cyan
        'G#': (80, 255, 255),    # Cyan
        'A': (80, 160, 255),     # Cyan-blue
        'A#': (80, 80, 255),     # Blue
        'B': (160, 80, 255),     # Blue-purple
        'N': (60, 60, 80),       # No chord - dark gray
    }

    def __init__(self, transition_speed: float = 0.1):
        self.transition_speed = transition_speed
        self.current_color = np.array([60, 60, 80], dtype=float)
        self.target_color = np.array([60, 60, 80], dtype=float)

    def set_chord(self, chord_label: str):
        """Set target color based on chord."""
        # Extract root note from chord label (e.g., "Am" -> "A")
        root = chord_label.rstrip('m').rstrip('7').rstrip('maj').rstrip('dim')

        base_color = np.array(self.CHORD_COLORS.get(root, self.CHORD_COLORS['N']), dtype=float)

        # Minor chords: cooler (shift toward blue)
        if 'm' in chord_label and 'maj' not in chord_label:
            base_color = base_color * 0.7 + np.array([0, 0, 80])

        self.target_color = np.clip(base_color, 0, 255)

    def update(self) -> Tuple[int, int, int]:
        """
        Update and return current background color.

        Returns:
            RGB tuple for background color
        """
        # Smooth transition
        self.current_color += (self.target_color - self.current_color) * self.transition_speed

        return tuple(self.current_color.astype(int))


def demo_temporal_analysis():
    """Demonstrate temporal analysis capabilities."""
    print("=" * 60)
    print("SYNESTHESIA 3.0 - Temporal Analysis Demo")
    print("=" * 60)

    if not HAS_LIBROSA:
        print("\n❌ librosa not installed. Install with: pip install librosa")
        print("   Skipping demo.")
        return

    # Create synthetic audio for demo
    print("\nGenerating synthetic musical phrase...")

    sr = 22050
    duration = 4.0
    t = np.linspace(0, duration, int(sr * duration))

    # Create a simple melody: C4 -> E4 -> G4 -> C5 (arpeggiated chord)
    frequencies = [261.63, 329.63, 392.00, 523.25]  # C4, E4, G4, C5
    note_duration = duration / len(frequencies)

    audio = np.zeros_like(t)
    for i, freq in enumerate(frequencies):
        start_idx = int(i * note_duration * sr)
        end_idx = int((i + 1) * note_duration * sr)
        note_t = t[start_idx:end_idx] - t[start_idx]

        # Note with envelope
        envelope = np.exp(-3 * note_t / note_duration)
        note = envelope * np.sin(2 * np.pi * freq * note_t)

        # Add harmonics
        for h in range(2, 5):
            note += envelope * (0.5 ** h) * np.sin(2 * np.pi * freq * h * note_t)

        audio[start_idx:end_idx] = note

    # Normalize
    audio = audio / np.max(np.abs(audio)) * 0.8

    # Save temporary file
    import tempfile
    import soundfile as sf

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        sf.write(f.name, audio, sr)
        temp_path = f.name

    # Analyze
    print("\nAnalyzing audio...")
    analyzer = TemporalAudioAnalyzer()
    features = analyzer.analyze(temp_path)

    # Report results
    print("\n" + "=" * 60)
    print("ANALYSIS RESULTS")
    print("=" * 60)

    print(f"\n📊 Basic Info:")
    print(f"   Duration: {features.duration_seconds:.2f}s")
    print(f"   Sample rate: {features.sample_rate} Hz")
    print(f"   Total frames: {features.total_frames}")

    print(f"\n🎵 Melody (Note-level):")
    valid_pitches = features.pitch_contour[features.pitch_contour > 0]
    if len(valid_pitches) > 0:
        print(f"   Pitch range: {valid_pitches.min():.1f} - {valid_pitches.max():.1f} Hz")
        print(f"   Mean pitch: {valid_pitches.mean():.1f} Hz")
    print(f"   Detected onsets: {len(features.onset_frames)}")

    print(f"\n🥁 Rhythm (Motif-level):")
    print(f"   Estimated tempo: {features.tempo:.1f} BPM")
    print(f"   Detected beats: {len(features.beat_frames)}")

    print(f"\n🎹 Harmony (Phrase-level):")
    print(f"   Detected chords: {features.chord_labels}")
    print(f"   Segment boundaries: {len(features.segment_boundaries)}")

    print(f"\n🌈 Atmosphere (Mood-level):")
    print(f"   Energy range: {features.energy_curve.min():.3f} - {features.energy_curve.max():.3f}")
    print(f"   Brightness range: {features.spectral_centroid.min():.0f} - {features.spectral_centroid.max():.0f} Hz")

    # Cleanup
    import os
    os.unlink(temp_path)

    print("\n✅ Temporal analysis demo complete!")

    # Demo the renderers
    print("\n" + "=" * 60)
    print("RENDERER DEMOS")
    print("=" * 60)

    # Melody Trail
    melody_trail = MelodyTrailRenderer(trail_duration=2.0)
    for pitch in [261.63, 293.66, 329.63, 349.23]:  # C, D, E, F
        melody_trail.update(pitch, confidence=0.9)

    spiral_params = {'center_x': 320, 'center_y': 240, 'max_radius': 200}
    trail_points = melody_trail.get_trail_points(spiral_params)
    print(f"\n🎵 Melody Trail: {len(trail_points)} points in trail")

    # Rhythm Pulse
    rhythm_pulse = RhythmPulseRenderer()
    rhythm_pulse.on_beat(strength=1.0)
    scale = rhythm_pulse.update()
    print(f"🥁 Rhythm Pulse: scale={scale:.3f} after beat")

    # Harmonic Aura
    harmonic_aura = HarmonicAuraRenderer()
    harmonic_aura.set_chord("Am")
    for _ in range(5):
        color = harmonic_aura.update()
    print(f"🎹 Harmonic Aura: background color for Am = {color}")

    print("\n✅ All renderer demos complete!")


if __name__ == "__main__":
    demo_temporal_analysis()
