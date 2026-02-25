"""Unit tests for cross-modal alignment and synchronization metrics."""

import numpy as np
import pytest

from synesthesia_eval.metrics import (
    AlignmentMetrics,
    SynchronizationMetrics,
    TemporalAnalyzer,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FRAME_RATE = 30.0
SAMPLE_RATE = 22050
NUM_FRAMES = 300  # 10 seconds at 30 fps


def _make_sine(freq: float, n: int, phase: float = 0.0) -> np.ndarray:
    """Generate a 1-D sinusoidal signal."""
    t = np.arange(n, dtype=np.float64)
    return np.sin(2 * np.pi * freq * t / n + phase)


def _make_beats(tempo_bpm: float, duration: float) -> np.ndarray:
    """Generate beat times for a given tempo and duration."""
    interval = 60.0 / tempo_bpm
    return np.arange(0, duration, interval)


def _make_frames_with_flash(
    n_frames: int,
    flash_frames: np.ndarray,
    height: int = 16,
    width: int = 16,
) -> np.ndarray:
    """Create synthetic video frames with brightness flashes at given indices."""
    frames = np.full((n_frames, height, width, 3), 30.0, dtype=np.float64)
    for idx in flash_frames:
        if 0 <= idx < n_frames:
            frames[idx] = 220.0
    return frames


# ===========================================================================
# SynchronizationMetrics Tests
# ===========================================================================


class TestSynchronizationMetrics:
    """Tests for SynchronizationMetrics."""

    @pytest.fixture()
    def sync(self) -> SynchronizationMetrics:
        return SynchronizationMetrics(tolerance=0.05)

    # --- onset_visual_alignment ---

    def test_onset_perfect_alignment(self, sync: SynchronizationMetrics) -> None:
        onsets = np.array([0.5, 1.0, 1.5, 2.0])
        visual = np.array([0.5, 1.0, 1.5, 2.0])
        result = sync.onset_visual_alignment(onsets, visual)
        assert result["score"] == 1.0
        assert result["precision"] == 1.0
        assert result["mean_error"] == 0.0

    def test_onset_no_alignment(self, sync: SynchronizationMetrics) -> None:
        onsets = np.array([0.5, 1.0, 1.5])
        visual = np.array([5.0, 6.0, 7.0])
        result = sync.onset_visual_alignment(onsets, visual)
        assert result["score"] == 0.0

    def test_onset_partial_alignment(self, sync: SynchronizationMetrics) -> None:
        onsets = np.array([0.5, 1.0, 1.5, 2.0])
        visual = np.array([0.5, 1.0, 5.0, 6.0])  # 2 of 4 match
        result = sync.onset_visual_alignment(onsets, visual)
        assert 0.0 < result["score"] < 1.0
        assert result["score"] == pytest.approx(0.5)

    def test_onset_empty_inputs(self, sync: SynchronizationMetrics) -> None:
        result = sync.onset_visual_alignment(np.array([]), np.array([1.0]))
        assert result["score"] == 0.0
        result = sync.onset_visual_alignment(np.array([1.0]), np.array([]))
        assert result["score"] == 0.0

    # --- beat_sync_score ---

    def test_beat_sync_perfect(self, sync: SynchronizationMetrics) -> None:
        beats = _make_beats(120, 4.0)
        result = sync.beat_sync_score(beats, beats)
        assert result["score"] == 1.0
        assert result["f1"] == 1.0

    def test_beat_sync_with_lag(self, sync: SynchronizationMetrics) -> None:
        beats = _make_beats(120, 4.0)
        visual = beats + 0.2  # 200ms lag, beyond tolerance
        result = sync.beat_sync_score(beats, visual, tolerance=0.05)
        assert result["score"] == 0.0

    def test_beat_sync_empty(self, sync: SynchronizationMetrics) -> None:
        result = sync.beat_sync_score(np.array([]), np.array([1.0]))
        assert result["score"] == 0.0

    def test_beat_sync_score_range(self, sync: SynchronizationMetrics) -> None:
        beats = _make_beats(120, 4.0)
        visual = beats + np.random.default_rng(42).uniform(-0.03, 0.03, len(beats))
        result = sync.beat_sync_score(beats, visual)
        assert 0.0 <= result["score"] <= 1.0
        assert 0.0 <= result["f1"] <= 1.0

    # --- tempo_consistency ---

    def test_tempo_perfect_match(self, sync: SynchronizationMetrics) -> None:
        result = sync.tempo_consistency(120.0, 120.0)
        assert result["score"] > 0.9
        assert result["ratio"] == pytest.approx(1.0)

    def test_tempo_double(self, sync: SynchronizationMetrics) -> None:
        result = sync.tempo_consistency(120.0, 240.0)
        assert result["score"] > 0.5  # Double tempo should get partial credit
        assert result["ratio"] == pytest.approx(2.0)

    def test_tempo_half(self, sync: SynchronizationMetrics) -> None:
        result = sync.tempo_consistency(120.0, 60.0)
        assert result["score"] > 0.5
        assert result["ratio"] == pytest.approx(0.5)

    def test_tempo_zero(self, sync: SynchronizationMetrics) -> None:
        result = sync.tempo_consistency(0.0, 120.0)
        assert result["score"] == 0.0
        result = sync.tempo_consistency(120.0, 0.0)
        assert result["score"] == 0.0

    def test_tempo_score_range(self, sync: SynchronizationMetrics) -> None:
        result = sync.tempo_consistency(120.0, 77.0)  # unrelated tempo
        assert 0.0 <= result["score"] <= 1.0

    # --- cross_correlation ---

    def test_cross_corr_identical(self, sync: SynchronizationMetrics) -> None:
        sig = _make_sine(3.0, 200)
        result = sync.cross_correlation(sig, sig)
        assert result["score"] > 0.9
        assert result["best_lag"] == 0

    def test_cross_corr_shifted(self, sync: SynchronizationMetrics) -> None:
        sig = _make_sine(3.0, 200)
        shifted = np.roll(sig, 5)
        result = sync.cross_correlation(sig, shifted, max_lag=20)
        assert result["score"] > 0.7
        assert abs(result["best_lag"]) <= 10

    def test_cross_corr_uncorrelated(self, sync: SynchronizationMetrics) -> None:
        rng = np.random.default_rng(42)
        a = rng.standard_normal(200)
        b = rng.standard_normal(200)
        result = sync.cross_correlation(a, b)
        assert 0.0 <= result["score"] <= 1.0

    def test_cross_corr_constant(self, sync: SynchronizationMetrics) -> None:
        result = sync.cross_correlation(np.ones(100), np.ones(100))
        assert result["score"] == 0.0  # constant signals -> zero std

    def test_cross_corr_short(self, sync: SynchronizationMetrics) -> None:
        result = sync.cross_correlation(np.array([1.0]), np.array([2.0]))
        assert result["score"] == 0.0


# ===========================================================================
# AlignmentMetrics Tests
# ===========================================================================


class TestAlignmentMetrics:
    """Tests for AlignmentMetrics."""

    @pytest.fixture()
    def align(self) -> AlignmentMetrics:
        return AlignmentMetrics()

    # --- energy_alignment ---

    def test_energy_perfect_correlation(self, align: AlignmentMetrics) -> None:
        rms = _make_sine(2.0, NUM_FRAMES) + 1.0  # ensure positive
        brightness = rms * 100  # linearly scaled
        result = align.energy_alignment(rms, brightness)
        assert result["score"] > 0.9
        assert result["correlation"] > 0.9

    def test_energy_inverse_correlation(self, align: AlignmentMetrics) -> None:
        rms = _make_sine(2.0, NUM_FRAMES) + 1.0
        brightness = -rms + 3.0  # inverse
        result = align.energy_alignment(rms, brightness)
        assert result["score"] < 0.1
        assert result["correlation"] < -0.9

    def test_energy_no_correlation(self, align: AlignmentMetrics) -> None:
        rng = np.random.default_rng(42)
        rms = rng.standard_normal(NUM_FRAMES)
        brightness = rng.standard_normal(NUM_FRAMES)
        result = align.energy_alignment(rms, brightness)
        assert 0.0 <= result["score"] <= 1.0

    def test_energy_different_lengths(self, align: AlignmentMetrics) -> None:
        rms = np.ones(100)
        brightness = np.ones(200)
        result = align.energy_alignment(rms, brightness)
        # Constant signals => correlation 0
        assert result["score"] == 0.5  # (0 + 1) / 2

    def test_energy_short_input(self, align: AlignmentMetrics) -> None:
        result = align.energy_alignment(np.array([1.0]), np.array([2.0]))
        assert result["score"] == 0.0

    # --- frequency_color_mapping ---

    def test_freq_color_basic(self, align: AlignmentMetrics) -> None:
        n_bins, n_frames = 64, 100
        rng = np.random.default_rng(42)
        spectrum = rng.uniform(0, 1, (n_bins, n_frames))
        colors = rng.uniform(0, 1, (n_frames, 3))
        result = align.frequency_color_mapping(spectrum, colors)
        assert 0.0 <= result["score"] <= 1.0
        assert "centroid_hue_corr" in result
        assert "spread_corr" in result

    def test_freq_color_consistent_mapping(self, align: AlignmentMetrics) -> None:
        """Higher frequencies -> bluer colors should give high centroid_hue_corr."""
        n_bins, n_frames = 64, 100
        # Gradually shift spectrum from low to high freqs
        spectrum = np.zeros((n_bins, n_frames))
        for t in range(n_frames):
            center = int(t / n_frames * (n_bins - 1))
            spectrum[max(0, center - 2) : center + 3, t] = 1.0

        # Colors shift from red (warm) to blue (cool)
        colors = np.zeros((n_frames, 3))
        for t in range(n_frames):
            frac = t / (n_frames - 1)
            colors[t] = [1.0 - frac, 0.0, frac]  # R decreases, B increases

        result = align.frequency_color_mapping(spectrum, colors)
        # Centroid goes up, R-B goes down (negative correlation)
        assert abs(result["centroid_hue_corr"]) > 0.5

    def test_freq_color_wrong_dims(self, align: AlignmentMetrics) -> None:
        result = align.frequency_color_mapping(np.ones(10), np.ones(10))
        assert result["score"] == 0.0

    def test_freq_color_255_colors(self, align: AlignmentMetrics) -> None:
        n_bins, n_frames = 32, 50
        rng = np.random.default_rng(42)
        spectrum = rng.uniform(0, 1, (n_bins, n_frames))
        colors = rng.integers(0, 256, (n_frames, 3)).astype(np.float64)
        result = align.frequency_color_mapping(spectrum, colors)
        assert 0.0 <= result["score"] <= 1.0

    # --- harmonic_visual_complexity ---

    def test_harmonic_complexity_correlated(self, align: AlignmentMetrics) -> None:
        harmonics = _make_sine(2.0, NUM_FRAMES) + 1.0
        complexity = harmonics * 2.0 + 0.5
        result = align.harmonic_visual_complexity(harmonics, complexity)
        assert result["score"] > 0.9
        assert result["correlation"] > 0.9

    def test_harmonic_complexity_uncorrelated(self, align: AlignmentMetrics) -> None:
        rng = np.random.default_rng(42)
        harmonics = rng.standard_normal(NUM_FRAMES)
        complexity = rng.standard_normal(NUM_FRAMES)
        result = align.harmonic_visual_complexity(harmonics, complexity)
        assert 0.0 <= result["score"] <= 1.0

    def test_harmonic_complexity_short(self, align: AlignmentMetrics) -> None:
        result = align.harmonic_visual_complexity(np.array([1.0]), np.array([2.0]))
        assert result["score"] == 0.0

    # --- custom correlation function ---

    def test_custom_correlation_fn(self) -> None:
        def spearman(a: np.ndarray, b: np.ndarray) -> float:
            from scipy.stats import spearmanr
            r, _ = spearmanr(a, b)
            return float(r)

        align = AlignmentMetrics(correlation_fn=spearman)
        rms = _make_sine(2.0, NUM_FRAMES) + 1.0
        brightness = rms ** 2  # monotone transform -> high Spearman
        result = align.energy_alignment(rms, brightness)
        assert result["score"] > 0.9


# ===========================================================================
# TemporalAnalyzer Tests
# ===========================================================================


class TestTemporalAnalyzer:
    """Tests for TemporalAnalyzer."""

    @pytest.fixture()
    def analyzer(self) -> TemporalAnalyzer:
        return TemporalAnalyzer(frame_rate=FRAME_RATE)

    # --- extract_visual_onsets ---

    def test_visual_onsets_from_flashes(self, analyzer: TemporalAnalyzer) -> None:
        flash_indices = np.array([30, 60, 90, 120])
        frames = _make_frames_with_flash(150, flash_indices)
        onsets = analyzer.extract_visual_onsets(frames)
        assert len(onsets) > 0
        # Each flash should produce an onset near its time
        for idx in flash_indices:
            expected_time = idx / FRAME_RATE
            assert np.any(np.abs(onsets - expected_time) < 0.1)

    def test_visual_onsets_from_1d(self, analyzer: TemporalAnalyzer) -> None:
        brightness = np.zeros(100)
        brightness[20] = 10.0
        brightness[50] = 10.0
        onsets = analyzer.extract_visual_onsets(brightness)
        assert len(onsets) >= 2

    def test_visual_onsets_static_video(self, analyzer: TemporalAnalyzer) -> None:
        frames = np.full((100, 8, 8, 3), 128.0)
        onsets = analyzer.extract_visual_onsets(frames)
        assert len(onsets) == 0  # no changes

    def test_visual_onsets_single_frame(self, analyzer: TemporalAnalyzer) -> None:
        frames = np.zeros((1, 8, 8, 3))
        onsets = analyzer.extract_visual_onsets(frames)
        assert len(onsets) == 0

    # --- extract_visual_rhythm ---

    def test_visual_rhythm_periodic(self, analyzer: TemporalAnalyzer) -> None:
        # 2 Hz oscillation at 30 fps -> 120 BPM
        t = np.arange(300)
        brightness = np.sin(2 * np.pi * 2.0 * t / FRAME_RATE)
        result = analyzer.extract_visual_rhythm(brightness)
        assert result["tempo_bpm"] > 0
        assert abs(result["tempo_bpm"] - 120.0) < 20.0  # within 20 BPM
        assert result["periodicity"] > 0.5

    def test_visual_rhythm_static(self, analyzer: TemporalAnalyzer) -> None:
        brightness = np.ones(100)
        result = analyzer.extract_visual_rhythm(brightness)
        assert result["tempo_bpm"] == 0.0
        assert result["periodicity"] == 0.0

    def test_visual_rhythm_short(self, analyzer: TemporalAnalyzer) -> None:
        result = analyzer.extract_visual_rhythm(np.array([1.0, 2.0, 3.0]))
        assert result["tempo_bpm"] == 0.0

    # --- lag_analysis ---

    def test_lag_identical_signals(self, analyzer: TemporalAnalyzer) -> None:
        sig = _make_sine(3.0, 200)
        result = analyzer.lag_analysis(sig, sig)
        assert result["optimal_lag"] == 0
        assert result["score"] > 0.9

    def test_lag_shifted_signal(self, analyzer: TemporalAnalyzer) -> None:
        sig = _make_sine(3.0, 200)
        shifted = np.roll(sig, 5)
        result = analyzer.lag_analysis(sig, shifted, max_lag=20)
        assert abs(result["optimal_lag"]) <= 10
        assert result["score"] > 0.7

    def test_lag_constant_signal(self, analyzer: TemporalAnalyzer) -> None:
        result = analyzer.lag_analysis(np.ones(100), np.ones(100))
        assert result["score"] == 0.0

    def test_lag_short_signal(self, analyzer: TemporalAnalyzer) -> None:
        result = analyzer.lag_analysis(np.array([1.0]), np.array([2.0]))
        assert result["score"] == 0.0

    def test_lag_score_range(self, analyzer: TemporalAnalyzer) -> None:
        rng = np.random.default_rng(42)
        a = rng.standard_normal(200)
        b = rng.standard_normal(200)
        result = analyzer.lag_analysis(a, b)
        assert 0.0 <= result["score"] <= 1.0

    # --- phase_coherence ---

    def test_phase_perfect_lock(self, analyzer: TemporalAnalyzer) -> None:
        phase = np.linspace(0, 4 * np.pi, 200)
        result = analyzer.phase_coherence(phase, phase)
        assert result["score"] > 0.99
        assert abs(result["mean_phase_diff"]) < 0.01

    def test_phase_constant_offset(self, analyzer: TemporalAnalyzer) -> None:
        phase = np.linspace(0, 4 * np.pi, 200)
        result = analyzer.phase_coherence(phase, phase + np.pi / 4)
        assert result["score"] > 0.99  # consistent offset = high coherence
        # phase_diff = audio - visual = -pi/4
        assert abs(result["mean_phase_diff"] + np.pi / 4) < 0.05

    def test_phase_random(self, analyzer: TemporalAnalyzer) -> None:
        rng = np.random.default_rng(42)
        a = rng.uniform(-np.pi, np.pi, 1000)
        b = rng.uniform(-np.pi, np.pi, 1000)
        result = analyzer.phase_coherence(a, b)
        assert result["score"] < 0.2  # random phases -> low coherence

    def test_phase_empty(self, analyzer: TemporalAnalyzer) -> None:
        result = analyzer.phase_coherence(np.array([]), np.array([]))
        assert result["score"] == 0.0

    def test_phase_score_range(self, analyzer: TemporalAnalyzer) -> None:
        rng = np.random.default_rng(42)
        a = rng.standard_normal(100)
        b = rng.standard_normal(100)
        result = analyzer.phase_coherence(a, b)
        assert 0.0 <= result["score"] <= 1.0

    # --- _to_brightness ---

    def test_brightness_4d(self, analyzer: TemporalAnalyzer) -> None:
        frames = np.random.default_rng(42).uniform(0, 255, (10, 8, 8, 3))
        b = TemporalAnalyzer._to_brightness(frames)
        assert b.shape == (10,)

    def test_brightness_3d(self, analyzer: TemporalAnalyzer) -> None:
        frames = np.random.default_rng(42).uniform(0, 255, (10, 8, 8))
        b = TemporalAnalyzer._to_brightness(frames)
        assert b.shape == (10,)

    def test_brightness_1d_passthrough(self, analyzer: TemporalAnalyzer) -> None:
        signal = np.array([1.0, 2.0, 3.0])
        b = TemporalAnalyzer._to_brightness(signal)
        np.testing.assert_array_equal(b, signal)


# ===========================================================================
# Integration / Cross-class Tests
# ===========================================================================


class TestCrossClassIntegration:
    """Test that TemporalAnalyzer outputs feed into SynchronizationMetrics."""

    def test_extracted_onsets_feed_sync(self) -> None:
        analyzer = TemporalAnalyzer(frame_rate=FRAME_RATE)
        sync = SynchronizationMetrics(tolerance=0.1)

        # Create video with periodic flashes
        flash_indices = np.arange(0, 150, 15)
        frames = _make_frames_with_flash(150, flash_indices)

        visual_onsets = analyzer.extract_visual_onsets(frames)
        audio_onsets = flash_indices.astype(np.float64) / FRAME_RATE

        result = sync.onset_visual_alignment(audio_onsets, visual_onsets)
        assert result["score"] > 0.5

    def test_extracted_rhythm_feeds_tempo(self) -> None:
        analyzer = TemporalAnalyzer(frame_rate=FRAME_RATE)
        sync = SynchronizationMetrics()

        # 2 Hz oscillation = 120 BPM
        t = np.arange(300)
        brightness = np.sin(2 * np.pi * 2.0 * t / FRAME_RATE)

        rhythm = analyzer.extract_visual_rhythm(brightness)
        result = sync.tempo_consistency(120.0, rhythm["tempo_bpm"])
        assert result["score"] > 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
