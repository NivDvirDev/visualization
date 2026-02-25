"""Semantic and feature alignment metrics between audio and video.

Measures how well visual properties (brightness, color, complexity)
correspond to audio properties (energy, spectrum, harmonics).
"""

from typing import Callable, Dict, Optional

import numpy as np
from scipy import stats


class AlignmentMetrics:
    """Measure semantic/feature alignment between audio and video.

    Supports configurable alignment strategies via custom correlation
    functions.

    Args:
        correlation_fn: A callable that takes two 1-D arrays and returns
            a correlation coefficient in [-1, 1]. Defaults to Pearson
            correlation.
    """

    def __init__(
        self,
        correlation_fn: Optional[Callable[[np.ndarray, np.ndarray], float]] = None,
    ):
        self.correlation_fn = correlation_fn or self._pearson

    @staticmethod
    def _pearson(a: np.ndarray, b: np.ndarray) -> float:
        """Pearson correlation with constant-input handling."""
        if len(a) < 2 or np.std(a) < 1e-10 or np.std(b) < 1e-10:
            return 0.0
        r, _ = stats.pearsonr(a, b)
        return float(r)

    @staticmethod
    def _align_lengths(a: np.ndarray, b: np.ndarray) -> tuple:
        """Truncate to the shorter of two 1-D arrays."""
        min_len = min(len(a), len(b))
        return a[:min_len], b[:min_len]

    def energy_alignment(
        self,
        audio_rms: np.ndarray,
        visual_brightness: np.ndarray,
    ) -> Dict[str, float]:
        """Correlation between audio RMS energy and visual brightness.

        Args:
            audio_rms: 1-D array of per-frame RMS energy values.
            visual_brightness: 1-D array of per-frame mean brightness.

        Returns:
            Dict with keys:
                - 'score': alignment score in [0, 1].
                - 'correlation': raw correlation coefficient.
        """
        audio_rms = np.asarray(audio_rms, dtype=np.float64).ravel()
        visual_brightness = np.asarray(visual_brightness, dtype=np.float64).ravel()
        a, v = self._align_lengths(audio_rms, visual_brightness)

        if len(a) < 2:
            return {"score": 0.0, "correlation": 0.0}

        corr = self.correlation_fn(a, v)
        # Map correlation [-1, 1] -> score [0, 1]
        score = float(np.clip((corr + 1.0) / 2.0, 0.0, 1.0))

        return {"score": score, "correlation": corr}

    def frequency_color_mapping(
        self,
        audio_spectrum: np.ndarray,
        visual_colors: np.ndarray,
        frequency_bins: Optional[np.ndarray] = None,
    ) -> Dict[str, float]:
        """Evaluate frequency-to-color correspondence.

        Checks whether lower frequencies map to warmer colors and higher
        frequencies to cooler colors (or any consistent mapping).

        The method computes the correlation between the spectral centroid
        over time and the dominant hue over time, plus the correlation
        between spectral spread and color spread.

        Args:
            audio_spectrum: 2-D array of shape (n_freq_bins, n_frames) with
                magnitude values.
            visual_colors: 2-D array of shape (n_frames, 3) with mean RGB
                values per frame (values in [0, 1] or [0, 255]).
            frequency_bins: 1-D array of frequency values for each bin.
                If None, uses linear indices.

        Returns:
            Dict with keys:
                - 'score': overall frequency-color alignment in [0, 1].
                - 'centroid_hue_corr': correlation between spectral centroid
                    and dominant hue.
                - 'spread_corr': correlation between spectral spread and
                    color spread.
        """
        audio_spectrum = np.asarray(audio_spectrum, dtype=np.float64)
        visual_colors = np.asarray(visual_colors, dtype=np.float64)

        if audio_spectrum.ndim != 2 or visual_colors.ndim != 2:
            return {"score": 0.0, "centroid_hue_corr": 0.0, "spread_corr": 0.0}

        n_bins, n_frames_a = audio_spectrum.shape
        n_frames_v, n_channels = visual_colors.shape

        if n_channels < 3:
            return {"score": 0.0, "centroid_hue_corr": 0.0, "spread_corr": 0.0}

        # Align frame counts
        n_frames = min(n_frames_a, n_frames_v)
        if n_frames < 2:
            return {"score": 0.0, "centroid_hue_corr": 0.0, "spread_corr": 0.0}

        spectrum = audio_spectrum[:, :n_frames]
        colors = visual_colors[:n_frames, :3]

        # Normalize colors to [0, 1]
        if colors.max() > 1.0:
            colors = colors / 255.0

        if frequency_bins is None:
            frequency_bins = np.arange(n_bins, dtype=np.float64)
        else:
            frequency_bins = np.asarray(frequency_bins, dtype=np.float64)

        # Spectral centroid per frame
        total_energy = spectrum.sum(axis=0)
        total_energy = np.where(total_energy < 1e-10, 1.0, total_energy)
        spectral_centroid = (frequency_bins[:, None] * spectrum).sum(axis=0) / total_energy

        # Spectral spread per frame
        centroid_diff = frequency_bins[:, None] - spectral_centroid[None, :]
        spectral_spread = np.sqrt(
            (centroid_diff ** 2 * spectrum).sum(axis=0) / total_energy
        )

        # Dominant hue approximation: use (R - B) as a warm-cool axis
        hue_proxy = colors[:, 0] - colors[:, 2]  # R - B

        # Color spread: standard deviation across channels per frame
        color_spread = colors.std(axis=1)

        centroid_hue_corr = self.correlation_fn(spectral_centroid, hue_proxy)
        spread_corr = self.correlation_fn(spectral_spread, color_spread)

        # Combine: take absolute values (consistent mapping matters, not direction)
        score = float(np.clip(
            (abs(centroid_hue_corr) + abs(spread_corr)) / 2.0, 0.0, 1.0
        ))

        return {
            "score": score,
            "centroid_hue_corr": centroid_hue_corr,
            "spread_corr": spread_corr,
        }

    def harmonic_visual_complexity(
        self,
        harmonic_features: np.ndarray,
        visual_complexity: np.ndarray,
    ) -> Dict[str, float]:
        """Correlate harmonic richness with visual detail.

        Harmonic richness can be represented as the number of active
        harmonics, spectral flatness, or chroma entropy over time.

        Args:
            harmonic_features: 1-D array of per-frame harmonic richness
                values (e.g., spectral flatness or chroma entropy).
            visual_complexity: 1-D array of per-frame visual complexity
                values (e.g., edge density or spatial frequency energy).

        Returns:
            Dict with keys:
                - 'score': alignment score in [0, 1].
                - 'correlation': raw correlation coefficient.
        """
        harmonic_features = np.asarray(harmonic_features, dtype=np.float64).ravel()
        visual_complexity = np.asarray(visual_complexity, dtype=np.float64).ravel()
        h, v = self._align_lengths(harmonic_features, visual_complexity)

        if len(h) < 2:
            return {"score": 0.0, "correlation": 0.0}

        corr = self.correlation_fn(h, v)
        score = float(np.clip((corr + 1.0) / 2.0, 0.0, 1.0))

        return {"score": score, "correlation": corr}
