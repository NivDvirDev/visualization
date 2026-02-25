"""Audio-video synchronization quality metrics.

Measures how well visual changes align with audio events such as
onsets, beats, and tempo patterns.
"""

from typing import Dict, Optional

import numpy as np
from scipy import signal


class SynchronizationMetrics:
    """Compute audio-video synchronization quality scores.

    All public methods return scores normalized to [0, 1] where 1.0
    indicates perfect synchronization.

    Args:
        tolerance: Maximum time difference (seconds) for an onset/beat
            to be considered aligned with a visual event. Defaults to 0.05.
        sample_rate: Sample rate used to convert between samples and
            seconds when needed. Defaults to 22050.
    """

    def __init__(
        self,
        tolerance: float = 0.05,
        sample_rate: int = 22050,
    ):
        self.tolerance = tolerance
        self.sample_rate = sample_rate

    def onset_visual_alignment(
        self,
        audio_onsets: np.ndarray,
        visual_changes: np.ndarray,
        tolerance: Optional[float] = None,
    ) -> Dict[str, float]:
        """Correlate audio onsets with visual intensity changes.

        For each audio onset, checks whether a visual change occurs within
        the tolerance window. Also computes the mean absolute time error
        for matched pairs.

        Args:
            audio_onsets: 1-D array of audio onset times in seconds.
            visual_changes: 1-D array of visual change-point times in seconds.
            tolerance: Override instance tolerance for this call.

        Returns:
            Dict with keys:
                - 'score': fraction of audio onsets matched to visual changes.
                - 'precision': fraction of visual changes matched to an audio onset.
                - 'mean_error': mean absolute timing error of matched pairs (seconds).
        """
        tol = tolerance if tolerance is not None else self.tolerance
        audio_onsets = np.asarray(audio_onsets, dtype=np.float64).ravel()
        visual_changes = np.asarray(visual_changes, dtype=np.float64).ravel()

        if len(audio_onsets) == 0 or len(visual_changes) == 0:
            return {"score": 0.0, "precision": 0.0, "mean_error": float("inf")}

        matched = 0
        errors = []
        vis_matched = set()

        for onset in audio_onsets:
            diffs = np.abs(visual_changes - onset)
            best_idx = int(np.argmin(diffs))
            if diffs[best_idx] <= tol:
                matched += 1
                errors.append(diffs[best_idx])
                vis_matched.add(best_idx)

        score = matched / len(audio_onsets)
        precision = len(vis_matched) / len(visual_changes)
        mean_error = float(np.mean(errors)) if errors else float("inf")

        return {"score": score, "precision": precision, "mean_error": mean_error}

    def beat_sync_score(
        self,
        beat_times: np.ndarray,
        visual_peaks: np.ndarray,
        tolerance: Optional[float] = None,
    ) -> Dict[str, float]:
        """Measure how well visual peaks align with beats.

        Args:
            beat_times: 1-D array of beat times in seconds.
            visual_peaks: 1-D array of visual peak times in seconds.
            tolerance: Override instance tolerance for this call.

        Returns:
            Dict with keys:
                - 'score': fraction of beats matched to a visual peak.
                - 'f1': harmonic mean of beat-recall and peak-precision.
                - 'mean_lag': mean signed lag (visual - audio) in seconds.
        """
        tol = tolerance if tolerance is not None else self.tolerance
        beat_times = np.asarray(beat_times, dtype=np.float64).ravel()
        visual_peaks = np.asarray(visual_peaks, dtype=np.float64).ravel()

        if len(beat_times) == 0 or len(visual_peaks) == 0:
            return {"score": 0.0, "f1": 0.0, "mean_lag": 0.0}

        beat_matched = 0
        peak_matched_set = set()
        lags = []

        for bt in beat_times:
            diffs = visual_peaks - bt
            abs_diffs = np.abs(diffs)
            best_idx = int(np.argmin(abs_diffs))
            if abs_diffs[best_idx] <= tol:
                beat_matched += 1
                peak_matched_set.add(best_idx)
                lags.append(diffs[best_idx])

        recall = beat_matched / len(beat_times)
        precision = len(peak_matched_set) / len(visual_peaks)
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )
        mean_lag = float(np.mean(lags)) if lags else 0.0

        return {"score": recall, "f1": f1, "mean_lag": mean_lag}

    def tempo_consistency(
        self,
        audio_tempo: float,
        visual_tempo: float,
    ) -> Dict[str, float]:
        """Compare audio and visual rhythmic tempo.

        Handles integer-ratio relationships (e.g., visual tempo is
        half or double the audio tempo) as partial matches.

        Args:
            audio_tempo: Audio tempo in BPM.
            visual_tempo: Visual tempo in BPM (estimated from visual periodicity).

        Returns:
            Dict with keys:
                - 'score': tempo consistency score in [0, 1].
                - 'ratio': visual_tempo / audio_tempo.
        """
        if audio_tempo <= 0 or visual_tempo <= 0:
            return {"score": 0.0, "ratio": 0.0}

        ratio = visual_tempo / audio_tempo

        # Check simple integer ratios: 1:1, 1:2, 2:1, 1:3, 3:1
        best_score = 0.0
        for target_ratio in [1.0, 0.5, 2.0, 1.0 / 3.0, 3.0]:
            deviation = abs(ratio - target_ratio) / target_ratio
            # Gaussian-like scoring around each target ratio
            s = np.exp(-0.5 * (deviation / 0.1) ** 2)
            best_score = max(best_score, float(s))

        return {"score": best_score, "ratio": ratio}

    def cross_correlation(
        self,
        audio_envelope: np.ndarray,
        visual_envelope: np.ndarray,
        max_lag: Optional[int] = None,
    ) -> Dict[str, float]:
        """Compute time-lagged cross-correlation between audio and visual envelopes.

        Both envelopes are z-score normalized before correlation.

        Args:
            audio_envelope: 1-D audio amplitude envelope.
            visual_envelope: 1-D visual intensity envelope (same length or
                resampled to match).
            max_lag: Maximum lag in samples to search. Defaults to 10% of
                signal length.

        Returns:
            Dict with keys:
                - 'score': peak normalized cross-correlation in [0, 1].
                - 'best_lag': lag (in samples) that maximizes correlation.
                - 'correlation_at_zero': correlation at zero lag.
        """
        audio_envelope = np.asarray(audio_envelope, dtype=np.float64).ravel()
        visual_envelope = np.asarray(visual_envelope, dtype=np.float64).ravel()

        # Align lengths by truncating to the shorter signal
        min_len = min(len(audio_envelope), len(visual_envelope))
        if min_len < 2:
            return {"score": 0.0, "best_lag": 0, "correlation_at_zero": 0.0}

        a = audio_envelope[:min_len]
        v = visual_envelope[:min_len]

        # Z-score normalize
        a_std = np.std(a)
        v_std = np.std(v)
        if a_std < 1e-10 or v_std < 1e-10:
            return {"score": 0.0, "best_lag": 0, "correlation_at_zero": 0.0}

        a = (a - np.mean(a)) / a_std
        v = (v - np.mean(v)) / v_std

        # Full cross-correlation
        corr = signal.correlate(a, v, mode="full") / min_len
        lags = signal.correlation_lags(len(a), len(v), mode="full")

        if max_lag is None:
            max_lag = max(1, min_len // 10)

        # Restrict to max_lag window
        mask = np.abs(lags) <= max_lag
        if not np.any(mask):
            mask = np.ones_like(lags, dtype=bool)

        corr_windowed = corr[mask]
        lags_windowed = lags[mask]

        best_idx = int(np.argmax(corr_windowed))
        peak_corr = float(corr_windowed[best_idx])
        best_lag = int(lags_windowed[best_idx])

        # Correlation at zero lag
        zero_idx = np.where(lags == 0)[0]
        corr_at_zero = float(corr[zero_idx[0]]) if len(zero_idx) > 0 else 0.0

        # Normalize score to [0, 1]
        score = float(np.clip((peak_corr + 1.0) / 2.0, 0.0, 1.0))

        return {
            "score": score,
            "best_lag": best_lag,
            "correlation_at_zero": corr_at_zero,
        }
