"""Audio feature extraction for synesthesia evaluation.

Uses librosa for spectral, rhythmic, and harmonic feature extraction
from audio files and raw waveform data.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union

import librosa
import numpy as np
import torch


@dataclass
class AudioFeatures:
    """Container for extracted audio features."""

    mel_spectrogram: np.ndarray  # (n_mels, time)
    mfcc: np.ndarray  # (n_mfcc, time)
    chroma: np.ndarray  # (12, time)
    onset_strength: np.ndarray  # (time,)
    beat_frames: np.ndarray  # (n_beats,)
    tempo: float  # BPM
    sample_rate: int
    duration: float


class AudioFeatureExtractor:
    """Extract audio features using librosa.

    Supports mel spectrograms, MFCCs, chroma, onset/beat detection,
    and tempo estimation. Works on file paths or raw numpy arrays.

    Args:
        sample_rate: Target sample rate for analysis. Defaults to 22050.
        n_fft: FFT window size. Defaults to 2048.
        hop_length: Hop length in samples. Defaults to 512.
        n_mels: Number of mel bands. Defaults to 128.
        n_mfcc: Number of MFCCs. Defaults to 20.
        device: Torch device for GPU operations. Defaults to auto-detect.
    """

    def __init__(
        self,
        sample_rate: int = 22050,
        n_fft: int = 2048,
        hop_length: int = 512,
        n_mels: int = 128,
        n_mfcc: int = 20,
        device: Optional[str] = None,
    ):
        self.sample_rate = sample_rate
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.n_mels = n_mels
        self.n_mfcc = n_mfcc
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

    def _load_audio(
        self, source: Union[str, np.ndarray], sr: Optional[int] = None
    ) -> Tuple[np.ndarray, int]:
        """Load audio from a file path or validate a raw array.

        Args:
            source: File path or numpy array of audio samples.
            sr: Sample rate (required when source is an array).

        Returns:
            Tuple of (audio_array, sample_rate).
        """
        if isinstance(source, (str,)):
            y, sr_loaded = librosa.load(source, sr=self.sample_rate, mono=True)
            return y, sr_loaded
        if isinstance(source, np.ndarray):
            if sr is None:
                sr = self.sample_rate
            if source.ndim > 1:
                source = np.mean(source, axis=0)
            return source.astype(np.float32), sr
        raise TypeError(f"Expected file path or numpy array, got {type(source)}")

    def extract_mel_spectrogram(
        self, source: Union[str, np.ndarray], sr: Optional[int] = None
    ) -> np.ndarray:
        """Extract mel spectrogram.

        Args:
            source: Audio file path or numpy array.
            sr: Sample rate (required when source is an array).

        Returns:
            Log-power mel spectrogram of shape (n_mels, time_frames).
        """
        y, sr_actual = self._load_audio(source, sr)
        mel = librosa.feature.melspectrogram(
            y=y,
            sr=sr_actual,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            n_mels=self.n_mels,
        )
        return librosa.power_to_db(mel, ref=np.max)

    def extract_rhythm_features(
        self, source: Union[str, np.ndarray], sr: Optional[int] = None
    ) -> Dict[str, Union[np.ndarray, float]]:
        """Extract rhythm-related features: onset strength, beat frames, tempo.

        Args:
            source: Audio file path or numpy array.
            sr: Sample rate (required when source is an array).

        Returns:
            Dict with keys 'onset_strength', 'beat_frames', 'tempo'.
        """
        y, sr_actual = self._load_audio(source, sr)
        onset_env = librosa.onset.onset_strength(
            y=y, sr=sr_actual, hop_length=self.hop_length
        )
        tempo, beat_frames = librosa.beat.beat_track(
            onset_envelope=onset_env, sr=sr_actual, hop_length=self.hop_length
        )
        tempo_val = float(tempo) if np.ndim(tempo) == 0 else float(tempo[0])
        return {
            "onset_strength": onset_env,
            "beat_frames": beat_frames,
            "tempo": tempo_val,
        }

    def extract_harmonic_features(
        self, source: Union[str, np.ndarray], sr: Optional[int] = None
    ) -> Dict[str, np.ndarray]:
        """Extract harmonic features: MFCCs and chroma.

        Args:
            source: Audio file path or numpy array.
            sr: Sample rate (required when source is an array).

        Returns:
            Dict with keys 'mfcc' (n_mfcc, time) and 'chroma' (12, time).
        """
        y, sr_actual = self._load_audio(source, sr)
        mfcc = librosa.feature.mfcc(
            y=y,
            sr=sr_actual,
            n_mfcc=self.n_mfcc,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
        )
        chroma = librosa.feature.chroma_stft(
            y=y,
            sr=sr_actual,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
        )
        return {"mfcc": mfcc, "chroma": chroma}

    def extract_all(
        self, source: Union[str, np.ndarray], sr: Optional[int] = None
    ) -> AudioFeatures:
        """Extract all audio features at once.

        Args:
            source: Audio file path or numpy array.
            sr: Sample rate (required when source is an array).

        Returns:
            AudioFeatures dataclass with all extracted features.
        """
        y, sr_actual = self._load_audio(source, sr)
        duration = float(len(y)) / sr_actual

        mel = self.extract_mel_spectrogram(y, sr=sr_actual)
        rhythm = self.extract_rhythm_features(y, sr=sr_actual)
        harmonic = self.extract_harmonic_features(y, sr=sr_actual)

        return AudioFeatures(
            mel_spectrogram=mel,
            mfcc=harmonic["mfcc"],
            chroma=harmonic["chroma"],
            onset_strength=rhythm["onset_strength"],
            beat_frames=rhythm["beat_frames"],
            tempo=rhythm["tempo"],
            sample_rate=sr_actual,
            duration=duration,
        )

    def extract_batch(
        self, sources: List[Union[str, np.ndarray]], sr: Optional[int] = None
    ) -> List[AudioFeatures]:
        """Extract features from multiple audio sources.

        Args:
            sources: List of file paths or numpy arrays.
            sr: Sample rate (required when sources are arrays).

        Returns:
            List of AudioFeatures, one per source.
        """
        return [self.extract_all(s, sr=sr) for s in sources]
