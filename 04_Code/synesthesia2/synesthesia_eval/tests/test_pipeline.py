"""Integration tests for the Stage 3 evaluation pipeline.

Tests the full pipeline on synthetic data: dataset loading, evaluation,
scoring model training/prediction, and reliability metrics.
"""

import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pytest

from synesthesia_eval.dataset.dataset_schema import (
    DatasetSplit,
    GroundTruth,
    VideoSample,
)
from synesthesia_eval.dataset.dataset_loader import DatasetLoader
from synesthesia_eval.pipeline.results import DatasetResults, EvaluationResult
from synesthesia_eval.pipeline.scoring_model import ScoringModel
from synesthesia_eval.validation.reliability import ReliabilityValidator
from synesthesia_eval.validation.benchmark import Benchmark, BenchmarkReport


# ==========================================================================
# Fixtures
# ==========================================================================


def _make_synced_signals(n: int = 200, seed: int = 0) -> tuple:
    """Create correlated audio/visual signals simulating good sync."""
    rng = np.random.RandomState(seed)
    t = np.linspace(0, 4 * np.pi, n)
    base = np.sin(t) + 0.3 * np.sin(3 * t)
    audio = base + 0.1 * rng.randn(n)
    visual = base + 0.1 * rng.randn(n)
    return audio, visual


def _make_unsynced_signals(n: int = 200, seed: int = 1) -> tuple:
    """Create uncorrelated audio/visual signals simulating poor sync."""
    rng = np.random.RandomState(seed)
    audio = rng.randn(n)
    visual = rng.randn(n)
    return audio, visual


def _make_eval_result(
    sample_id: str,
    quality: str = "good",
    seed: int = 0,
) -> EvaluationResult:
    """Build a synthetic EvaluationResult with populated metrics."""
    if quality == "good":
        audio, visual = _make_synced_signals(seed=seed)
    else:
        audio, visual = _make_unsynced_signals(seed=seed)

    from synesthesia_eval.metrics.sync_metrics import SynchronizationMetrics
    from synesthesia_eval.metrics.alignment_metrics import AlignmentMetrics
    from synesthesia_eval.metrics.temporal_analysis import TemporalAnalyzer

    sync = SynchronizationMetrics()
    align = AlignmentMetrics()
    temporal = TemporalAnalyzer(frame_rate=30.0)

    # Derive onsets from threshold crossings
    diff = np.abs(np.diff(visual))
    threshold = np.mean(diff) + np.std(diff)
    visual_onsets = np.where(diff > threshold)[0].astype(float) / 30.0

    audio_diff = np.abs(np.diff(audio))
    a_threshold = np.mean(audio_diff) + np.std(audio_diff)
    audio_onsets = np.where(audio_diff > a_threshold)[0].astype(float) / 30.0

    result = EvaluationResult(sample_id=sample_id)
    result.sync_metrics = {
        "onset_alignment": sync.onset_visual_alignment(audio_onsets, visual_onsets),
        "beat_sync": sync.beat_sync_score(audio_onsets, visual_onsets),
        "tempo_consistency": sync.tempo_consistency(120.0, 120.0 if quality == "good" else 80.0),
        "cross_correlation": sync.cross_correlation(audio, visual),
    }
    result.alignment_metrics = {
        "energy_alignment": align.energy_alignment(np.abs(audio), np.abs(visual)),
        "harmonic_complexity": align.harmonic_visual_complexity(audio, visual),
    }
    result.temporal_metrics = {
        "lag_analysis": temporal.lag_analysis(audio, visual),
        "phase_coherence": temporal.phase_coherence(
            np.angle(np.fft.fft(audio)), np.angle(np.fft.fft(visual))
        ),
    }
    result.composite_score = (
        0.4 * result.get_sync_score()
        + 0.35 * result.get_alignment_score()
        + 0.25 * result.get_temporal_score()
    )
    return result


def _make_sample(
    sample_id: str,
    quality: str = "good",
    split: DatasetSplit = DatasetSplit.TRAIN,
) -> VideoSample:
    """Build a synthetic VideoSample with ground truth."""
    if quality == "good":
        gt = GroundTruth(
            sync_score=0.85,
            alignment_score=0.80,
            aesthetic_score=0.75,
            annotator_ids=["ann1", "ann2"],
            confidence=0.9,
        )
    else:
        gt = GroundTruth(
            sync_score=0.25,
            alignment_score=0.30,
            aesthetic_score=0.35,
            annotator_ids=["ann1", "ann2"],
            confidence=0.9,
        )
    return VideoSample(
        sample_id=sample_id,
        video_path=f"/tmp/fake/{sample_id}/video.mp4",
        audio_path=f"/tmp/fake/{sample_id}/audio.wav",
        metadata={"genre": "synthetic", "tempo": 120},
        ground_truth=gt,
        split=split,
    )


@pytest.fixture
def synthetic_dataset():
    """Create a dataset of 10 samples: 5 good + 5 poor."""
    results = []
    samples = []
    for i in range(5):
        sid = f"good_{i:03d}"
        results.append(_make_eval_result(sid, "good", seed=i))
        samples.append(_make_sample(sid, "good", DatasetSplit.TRAIN))
    for i in range(5):
        sid = f"poor_{i:03d}"
        results.append(_make_eval_result(sid, "poor", seed=i + 100))
        samples.append(_make_sample(sid, "poor", DatasetSplit.TRAIN))
    return results, samples


# ==========================================================================
# Tests: Dataset Schema & Loader
# ==========================================================================


class TestDatasetSchema:
    def test_ground_truth_validation(self):
        gt = GroundTruth(sync_score=0.5, alignment_score=0.6, aesthetic_score=0.7)
        assert 0.0 <= gt.composite_score <= 1.0

    def test_ground_truth_score_range_error(self):
        with pytest.raises(ValueError):
            GroundTruth(sync_score=1.5, alignment_score=0.5, aesthetic_score=0.5)

    def test_video_sample_has_ground_truth(self):
        s = VideoSample(sample_id="a", video_path="v", audio_path="a")
        assert not s.has_ground_truth()

        s.ground_truth = GroundTruth(
            sync_score=0.5, alignment_score=0.5, aesthetic_score=0.5
        )
        assert s.has_ground_truth()

    def test_composite_score_weights(self):
        gt = GroundTruth(sync_score=1.0, alignment_score=1.0, aesthetic_score=1.0)
        assert abs(gt.composite_score - 1.0) < 1e-6

        gt2 = GroundTruth(sync_score=0.0, alignment_score=0.0, aesthetic_score=0.0)
        assert abs(gt2.composite_score - 0.0) < 1e-6


class TestDatasetLoader:
    def test_load_from_directory(self, tmp_path):
        # Create mock directory structure
        for i in range(3):
            d = tmp_path / f"sample_{i:03d}"
            d.mkdir()
            (d / "video.mp4").write_text("fake")
            (d / "audio.wav").write_text("fake")
            ann = {
                "sync_score": 0.5 + i * 0.1,
                "alignment_score": 0.6,
                "aesthetic_score": 0.7,
                "annotator_ids": ["ann1"],
                "confidence": 0.9,
                "split": "train",
                "metadata": {"genre": "test"},
            }
            (d / "annotation.json").write_text(json.dumps(ann))

        loader = DatasetLoader()
        loader.load_from_directory(str(tmp_path))
        assert len(loader) == 3
        assert all(s.has_ground_truth() for s in loader.samples)

    def test_load_from_csv(self, tmp_path):
        csv_file = tmp_path / "dataset.csv"
        csv_file.write_text(
            "sample_id,video_path,audio_path,sync_score,alignment_score,aesthetic_score,split\n"
            "s1,v1.mp4,a1.wav,0.8,0.7,0.6,train\n"
            "s2,v2.mp4,a2.wav,0.3,0.4,0.5,val\n"
        )

        loader = DatasetLoader()
        loader.load_from_csv(str(csv_file))
        assert len(loader) == 2
        assert loader.get_split(DatasetSplit.VAL)[0].sample_id == "s2"

    def test_validate_dataset(self, tmp_path):
        d = tmp_path / "sample_001"
        d.mkdir()
        (d / "video.mp4").write_text("fake")
        (d / "audio.wav").write_text("fake")
        ann = {"sync_score": 0.5, "alignment_score": 0.5, "aesthetic_score": 0.5}
        (d / "annotation.json").write_text(json.dumps(ann))

        loader = DatasetLoader().load_from_directory(str(tmp_path))
        report = loader.validate_dataset()
        assert report["total_samples"] == 1
        assert report["valid"] is True

    def test_get_statistics(self, tmp_path):
        loader = DatasetLoader()
        loader.samples = [
            _make_sample("s1", "good"),
            _make_sample("s2", "poor"),
        ]
        stats = loader.get_statistics()
        assert stats["total_samples"] == 2
        assert stats["annotated_samples"] == 2
        assert "sync_score" in stats


# ==========================================================================
# Tests: Evaluation Results
# ==========================================================================


class TestEvaluationResult:
    def test_to_feature_vector(self):
        result = _make_eval_result("test", "good")
        features = result.to_feature_vector()
        assert features.ndim == 1
        assert len(features) > 0
        assert np.all(np.isfinite(features))

    def test_aggregate_scores(self):
        result = _make_eval_result("test", "good")
        assert 0.0 <= result.get_sync_score() <= 1.0
        assert 0.0 <= result.get_alignment_score() <= 1.0
        assert 0.0 <= result.get_temporal_score() <= 1.0

    def test_to_dict(self):
        result = _make_eval_result("test", "good")
        d = result.to_dict()
        assert d["sample_id"] == "test"
        assert "sync_metrics" in d
        assert "composite_score" in d


class TestDatasetResults:
    def test_compute_aggregates(self, synthetic_dataset):
        results, _ = synthetic_dataset
        dr = DatasetResults(results=results)
        agg = dr.compute_aggregates()
        assert agg["n_samples"] == 10
        assert "composite" in agg
        assert "mean" in agg["composite"]

    def test_export_csv(self, synthetic_dataset, tmp_path):
        results, _ = synthetic_dataset
        dr = DatasetResults(results=results)
        csv_path = str(tmp_path / "results.csv")
        dr.export_to_csv(csv_path)
        assert Path(csv_path).exists()
        with open(csv_path) as f:
            lines = f.readlines()
        assert len(lines) == 11  # header + 10 rows

    def test_export_json(self, synthetic_dataset, tmp_path):
        results, _ = synthetic_dataset
        dr = DatasetResults(results=results)
        json_path = str(tmp_path / "results.json")
        dr.export_to_json(json_path)
        assert Path(json_path).exists()
        with open(json_path) as f:
            data = json.load(f)
        assert "aggregates" in data
        assert "samples" in data


# ==========================================================================
# Tests: Scoring Model
# ==========================================================================


class TestScoringModel:
    def test_fit_and_predict(self, synthetic_dataset):
        results, samples = synthetic_dataset
        model = ScoringModel(alpha=1.0)
        model.fit(results, samples)

        # Predict on the same data (overfitting is fine for this test)
        for r in results:
            score = model.predict(r)
            assert 0.0 <= score <= 1.0

    def test_predict_batch(self, synthetic_dataset):
        results, samples = synthetic_dataset
        model = ScoringModel(alpha=1.0)
        model.fit(results, samples)

        predictions = model.predict_batch(results)
        assert len(predictions) == 10
        assert all(0.0 <= p <= 1.0 for p in predictions)

    def test_feature_importance(self, synthetic_dataset):
        results, samples = synthetic_dataset
        model = ScoringModel(alpha=1.0)
        model.fit(results, samples)

        importance = model.get_feature_importance()
        assert isinstance(importance, dict)
        assert len(importance) > 0
        # Values should be non-negative (absolute coefficients)
        assert all(v >= 0 for v in importance.values())

    def test_predict_before_fit_raises(self):
        model = ScoringModel()
        result = _make_eval_result("test", "good")
        with pytest.raises(RuntimeError):
            model.predict(result)

    def test_calibrate(self, synthetic_dataset):
        results, samples = synthetic_dataset
        model = ScoringModel(alpha=1.0)
        model.fit(results, samples)
        model.calibrate(results, samples)

        # After calibration, predictions should still be valid
        for r in results:
            score = model.predict(r)
            assert 0.0 <= score <= 1.0

    def test_good_scores_higher_than_poor(self, synthetic_dataset):
        results, samples = synthetic_dataset
        model = ScoringModel(alpha=1.0)
        model.fit(results, samples)

        good_preds = [model.predict(r) for r in results[:5]]
        poor_preds = [model.predict(r) for r in results[5:]]
        # On average, good should score higher
        assert np.mean(good_preds) > np.mean(poor_preds)


# ==========================================================================
# Tests: Reliability Validation
# ==========================================================================


class TestReliabilityValidator:
    def test_model_human_correlation(self, synthetic_dataset):
        results, samples = synthetic_dataset
        model = ScoringModel(alpha=1.0)
        model.fit(results, samples)

        predictions = model.predict_batch(results)
        ground_truth = np.array([s.ground_truth.composite_score for s in samples])

        validator = ReliabilityValidator()
        corr = validator.compute_model_human_correlation(predictions, ground_truth)

        assert "pearson_r" in corr
        assert "spearman_rho" in corr
        assert "rmse" in corr
        assert "mae" in corr
        # Model should correlate positively with ground truth
        assert corr["pearson_r"] > 0

    def test_cross_validation(self, synthetic_dataset):
        results, samples = synthetic_dataset
        model = ScoringModel(alpha=1.0)
        model.fit(results, samples)

        validator = ReliabilityValidator()
        cv = validator.cross_validation(model, results, samples, k=3)

        assert "fold_scores" in cv
        assert "mean_r" in cv
        assert "ci_95" in cv
        assert len(cv["fold_scores"]) == 3

    def test_bootstrap_confidence(self, synthetic_dataset):
        results, samples = synthetic_dataset
        model = ScoringModel(alpha=1.0)
        model.fit(results, samples)

        predictions = model.predict_batch(results)
        ground_truth = np.array([s.ground_truth.composite_score for s in samples])

        validator = ReliabilityValidator()
        boot = validator.bootstrap_confidence(predictions, ground_truth, n=100)

        assert "pearson_ci" in boot
        assert "spearman_ci" in boot
        assert "rmse_ci" in boot
        lo, hi = boot["pearson_ci"]
        assert lo <= hi

    def test_inter_rater_agreement(self):
        """Test ICC and Krippendorff with multi-annotator data."""
        samples = []
        for i in range(5):
            s = _make_sample(f"s{i}", "good")
            s.metadata["annotator_scores"] = {
                "ann1": 0.7 + 0.05 * i,
                "ann2": 0.72 + 0.05 * i,
                "ann3": 0.68 + 0.05 * i,
            }
            samples.append(s)

        validator = ReliabilityValidator()
        agreement = validator.compute_inter_rater_agreement(samples)

        assert agreement["n_annotators"] == 3
        assert agreement["n_samples"] == 5
        # With very consistent raters, alpha and ICC should be high
        assert agreement["krippendorff_alpha"] > 0.5
        assert agreement["icc"] > 0.5


# ==========================================================================
# Tests: Benchmark
# ==========================================================================


class TestBenchmark:
    def test_run_full_benchmark(self, synthetic_dataset):
        results, samples = synthetic_dataset
        model = ScoringModel(alpha=1.0)
        model.fit(results, samples)

        benchmark = Benchmark()
        report = benchmark.run_full_benchmark(model, results, samples)

        assert isinstance(report, BenchmarkReport)
        assert "default" in report.model_results
        assert "correlation" in report.model_results["default"]

    def test_compare_models(self, synthetic_dataset):
        results, samples = synthetic_dataset

        model_a = ScoringModel(alpha=0.1)
        model_a.fit(results, samples)
        model_b = ScoringModel(alpha=10.0)
        model_b.fit(results, samples)

        benchmark = Benchmark()
        report = benchmark.compare_models(
            {"low_reg": model_a, "high_reg": model_b},
            results,
            samples,
        )

        assert "low_reg" in report.model_results
        assert "high_reg" in report.model_results

    def test_generate_report(self, synthetic_dataset, tmp_path):
        results, samples = synthetic_dataset
        model = ScoringModel(alpha=1.0)
        model.fit(results, samples)

        benchmark = Benchmark()
        report = benchmark.run_full_benchmark(model, results, samples)
        md_path = benchmark.generate_report(report, str(tmp_path / "output"))

        assert Path(md_path).exists()
        assert (tmp_path / "output" / "benchmark_report.json").exists()

    def test_markdown_report_content(self, synthetic_dataset):
        results, samples = synthetic_dataset
        model = ScoringModel(alpha=1.0)
        model.fit(results, samples)

        benchmark = Benchmark()
        report = benchmark.run_full_benchmark(model, results, samples)
        md = report.to_markdown()

        assert "Benchmark Report" in md
        assert "Pearson r" in md
        assert "Feature Importance" in md


# ==========================================================================
# Tests: Full Pipeline Integration
# ==========================================================================


class TestFullPipeline:
    """End-to-end test: dataset -> evaluate -> score -> validate."""

    def test_end_to_end(self, synthetic_dataset):
        results, samples = synthetic_dataset

        # 1. Check dataset results
        dr = DatasetResults(results=results)
        agg = dr.compute_aggregates()
        assert agg["n_samples"] == 10

        # 2. Fit scoring model
        model = ScoringModel(alpha=1.0)
        model.fit(results, samples)

        # 3. Predict
        predictions = model.predict_batch(results)
        assert len(predictions) == 10
        assert all(0.0 <= p <= 1.0 for p in predictions)

        # 4. Validate
        gt = np.array([s.ground_truth.composite_score for s in samples])
        validator = ReliabilityValidator()
        corr = validator.compute_model_human_correlation(predictions, gt)
        assert corr["pearson_r"] > 0  # Should be positively correlated

        # 5. Benchmark
        benchmark = Benchmark()
        report = benchmark.run_full_benchmark(model, results, samples)
        assert "default" in report.model_results

    def test_good_vs_poor_discrimination(self, synthetic_dataset):
        """The pipeline should discriminate good from poor samples."""
        results, samples = synthetic_dataset
        model = ScoringModel(alpha=1.0)
        model.fit(results, samples)

        good_scores = [model.predict(r) for r in results[:5]]
        poor_scores = [model.predict(r) for r in results[5:]]

        assert np.mean(good_scores) > np.mean(poor_scores), (
            f"Good mean ({np.mean(good_scores):.3f}) should exceed "
            f"poor mean ({np.mean(poor_scores):.3f})"
        )
