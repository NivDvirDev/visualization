"""Temporal pattern analysis for audio-visual synchronization.

Provides tools for extracting visual onsets, estimating visual tempo,
and analyzing time-lag and phase relationships between audio and visual signals.
"""

from typing import Dict, Optional

import numpy as np
from scipy import signal


class TemporalAnalyzer:
    """Analyze temporal patterns in audio-visual streams.

    Args:
        frame_rate: Video frame rate in FPS. Used to convert between
            frame indices and seconds. Defaults to 30.0.
        hop_length: Audio hop length in samples for frame alignment.
            Defaults to 512.
        sample_rate: Audio sample rate. Defaults to 22050.
    """

    def __init__(
        self,
        frame_rate: float = 30.0,
        hop_length: int = 512,
        sample_rate: int = 22050,
    ):
        self.frame_rate = frame_rate
        self.hop_length = hop_length
        self.sample_rate = sample_rate

    def extract_visual_onsets(
        self,
        frames: np.ndarray,
        threshold: Optional[float] = None,
    ) -> np.ndarray:
        """Detect visual change points from a sequence of frames.

        Computes the absolute frame-to-frame difference in mean intensity
        and returns the times at which that difference exceeds a threshold.

        Args:
            frames: Array of shape (T, H, W, C) or (T, H, W) with pixel
                values, or a pre-computed 1-D brightness curve of length T.
            threshold: Minimum intensity change to count as an onset. If
                None, uses mean + 1 std of the difference signal.

        Returns:
            1-D array of onset times in seconds.
        """
        brightness = self._to_brightness(frames)
        if len(brightness) < 2:
            return np.array([], dtype=np.float64)

        diff = np.abs(np.diff(brightness))

        if threshold is None:
            threshold = float(np.mean(diff) + np.std(diff))

        onset_frames = np.where(diff > threshold)[0] + 1  # +1 because diff shifts
        return onset_frames.astype(np.float64) / self.frame_rate

    def extract_visual_rhythm(
        self,
        frames: np.ndarray,
    ) -> Dict[str, float]:
        """Estimate visual tempo and periodicity from a frame sequence.

        Uses autocorrelation of the brightness curve to find the dominant
        period.

        Args:
            frames: Array of shape (T, H, W, C) or (T, H, W), or a
                pre-computed 1-D brightness curve.

        Returns:
            Dict with keys:
                - 'tempo_bpm': estimated visual tempo in BPM.
                - 'periodicity': strength of the dominant period (0-1).
        """
        brightness = self._to_brightness(frames)
        if len(brightness) < 4:
            return {"tempo_bpm": 0.0, "periodicity": 0.0}

        # Remove DC and normalize
        b = brightness - np.mean(brightness)
        b_std = np.std(b)
        if b_std < 1e-10:
            return {"tempo_bpm": 0.0, "periodicity": 0.0}
        b = b / b_std

        # Autocorrelation via FFT
        n = len(b)
        fft = np.fft.rfft(b, n=2 * n)
        acf = np.fft.irfft(fft * np.conj(fft))[:n]
        acf = acf / acf[0]  # Normalize so lag-0 = 1.0

        # Find peaks in autocorrelation (skip lag 0)
        # Minimum lag: ~40 BPM at frame_rate -> frame_rate * 60/40
        min_lag = max(2, int(self.frame_rate * 60.0 / 300.0))  # up to 300 BPM
        max_lag = min(n - 1, int(self.frame_rate * 60.0 / 30.0))  # down to 30 BPM

        if min_lag >= max_lag or max_lag >= n:
            return {"tempo_bpm": 0.0, "periodicity": 0.0}

        acf_search = acf[min_lag : max_lag + 1]
        peak_idx = int(np.argmax(acf_search)) + min_lag

        periodicity = float(np.clip(acf[peak_idx], 0.0, 1.0))
        period_seconds = peak_idx / self.frame_rate
        tempo_bpm = 60.0 / period_seconds if period_seconds > 0 else 0.0

        return {"tempo_bpm": tempo_bpm, "periodicity": periodicity}

    def lag_analysis(
        self,
        audio_signal: np.ndarray,
        visual_signal: np.ndarray,
        max_lag: Optional[int] = None,
    ) -> Dict[str, float]:
        """Find the optimal time lag between audio and visual signals.

        Positive lag means visual leads audio; negative means visual lags.

        Args:
            audio_signal: 1-D audio envelope or feature curve.
            visual_signal: 1-D visual envelope or feature curve (same
                temporal resolution as audio_signal).
            max_lag: Maximum lag in samples to search. Defaults to 10%
                of signal length.

        Returns:
            Dict with keys:
                - 'optimal_lag': lag in samples that maximizes correlation.
                - 'optimal_lag_seconds': lag converted to seconds using frame_rate.
                - 'peak_correlation': cross-correlation at optimal lag.
                - 'score': normalized score in [0, 1].
        """
        a = np.asarray(audio_signal, dtype=np.float64).ravel()
        v = np.asarray(visual_signal, dtype=np.float64).ravel()

        min_len = min(len(a), len(v))
        if min_len < 2:
            return {
                "optimal_lag": 0,
                "optimal_lag_seconds": 0.0,
                "peak_correlation": 0.0,
                "score": 0.0,
            }

        a = a[:min_len]
        v = v[:min_len]

        # Z-score normalize
        a_std, v_std = np.std(a), np.std(v)
        if a_std < 1e-10 or v_std < 1e-10:
            return {
                "optimal_lag": 0,
                "optimal_lag_seconds": 0.0,
                "peak_correlation": 0.0,
                "score": 0.0,
            }

        a = (a - np.mean(a)) / a_std
        v = (v - np.mean(v)) / v_std

        corr = signal.correlate(a, v, mode="full") / min_len
        lags = signal.correlation_lags(len(a), len(v), mode="full")

        if max_lag is None:
            max_lag = max(1, min_len // 10)

        mask = np.abs(lags) <= max_lag
        if not np.any(mask):
            mask = np.ones_like(lags, dtype=bool)

        corr_w = corr[mask]
        lags_w = lags[mask]

        best_idx = int(np.argmax(corr_w))
        optimal_lag = int(lags_w[best_idx])
        peak_corr = float(corr_w[best_idx])

        # Convert lag to seconds (assuming signals are at frame_rate)
        optimal_lag_seconds = optimal_lag / self.frame_rate

        score = float(np.clip((peak_corr + 1.0) / 2.0, 0.0, 1.0))

        return {
            "optimal_lag": optimal_lag,
            "optimal_lag_seconds": optimal_lag_seconds,
            "peak_correlation": peak_corr,
            "score": score,
        }

    def phase_coherence(
        self,
        audio_phase: np.ndarray,
        visual_phase: np.ndarray,
    ) -> Dict[str, float]:
        """Measure phase alignment between audio and visual signals.

        Computes the mean resultant length (circular mean) of the phase
        difference, which indicates how consistently the two signals
        maintain a fixed phase relationship.

        Args:
            audio_phase: 1-D array of instantaneous phase values (radians).
            visual_phase: 1-D array of instantaneous phase values (radians).

        Returns:
            Dict with keys:
                - 'score': phase coherence in [0, 1] (1 = perfectly locked).
                - 'mean_phase_diff': circular mean of phase difference (radians).
        """
        a = np.asarray(audio_phase, dtype=np.float64).ravel()
        v = np.asarray(visual_phase, dtype=np.float64).ravel()

        min_len = min(len(a), len(v))
        if min_len < 1:
            return {"score": 0.0, "mean_phase_diff": 0.0}

        a = a[:min_len]
        v = v[:min_len]

        phase_diff = a - v

        # Mean resultant length
        mean_vec = np.mean(np.exp(1j * phase_diff))
        coherence = float(np.abs(mean_vec))
        mean_phase_diff = float(np.angle(mean_vec))

        return {
            "score": float(np.clip(coherence, 0.0, 1.0)),
            "mean_phase_diff": mean_phase_diff,
        }

    @staticmethod
    def _to_brightness(frames: np.ndarray) -> np.ndarray:
        """Convert frames to a 1-D brightness curve.

        Args:
            frames: (T, H, W, C), (T, H, W), or already 1-D brightness.

        Returns:
            1-D array of mean brightness per frame.
        """
        frames = np.asarray(frames, dtype=np.float64)
        if frames.ndim == 1:
            return frames
        if frames.ndim == 4:
            # (T, H, W, C) -> mean over spatial + channels
            return frames.mean(axis=(1, 2, 3))
        if frames.ndim == 3:
            # (T, H, W) -> mean over spatial
            return frames.mean(axis=(1, 2))
        if frames.ndim == 2:
            # Ambiguous: treat as (T, features) -> mean over features
            return frames.mean(axis=1)
        return frames.ravel()
