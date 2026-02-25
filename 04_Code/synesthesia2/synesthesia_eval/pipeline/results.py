"""Result containers for the evaluation pipeline.

Provides dataclasses for per-sample and aggregate evaluation outputs,
with serialization to CSV and JSON.
"""

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np


@dataclass
class EvaluationResult:
    """Evaluation output for a single video sample.

    Attributes:
        sample_id: Unique identifier matching the source VideoSample.
        sync_metrics: Raw output dicts from SynchronizationMetrics methods.
        alignment_metrics: Raw output dicts from AlignmentMetrics methods.
        temporal_metrics: Raw output dicts from TemporalAnalyzer methods.
        composite_score: Final weighted score in [0, 1].
        timestamps: Dict of timing info (processing durations, etc.).
    """

    sample_id: str
    sync_metrics: Dict[str, Dict[str, float]] = field(default_factory=dict)
    alignment_metrics: Dict[str, Dict[str, float]] = field(default_factory=dict)
    temporal_metrics: Dict[str, Dict[str, float]] = field(default_factory=dict)
    composite_score: Optional[float] = None
    timestamps: Dict[str, float] = field(default_factory=dict)

    def get_sync_score(self) -> float:
        """Aggregate synchronization score across sub-metrics."""
        scores = [
            m["score"] for m in self.sync_metrics.values() if "score" in m
        ]
        return float(np.mean(scores)) if scores else 0.0

    def get_alignment_score(self) -> float:
        """Aggregate alignment score across sub-metrics."""
        scores = [
            m["score"] for m in self.alignment_metrics.values() if "score" in m
        ]
        return float(np.mean(scores)) if scores else 0.0

    def get_temporal_score(self) -> float:
        """Aggregate temporal score across sub-metrics."""
        scores = [
            m["score"] for m in self.temporal_metrics.values() if "score" in m
        ]
        return float(np.mean(scores)) if scores else 0.0

    def to_feature_vector(self) -> np.ndarray:
        """Flatten all metric scores into a single feature vector for the scoring model."""
        features: List[float] = []
        for metrics_dict in (
            self.sync_metrics,
            self.alignment_metrics,
            self.temporal_metrics,
        ):
            for sub_result in metrics_dict.values():
                if isinstance(sub_result, dict):
                    for v in sub_result.values():
                        if isinstance(v, (int, float)) and np.isfinite(v):
                            features.append(float(v))
        return np.array(features, dtype=np.float64)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dict."""
        return {
            "sample_id": self.sample_id,
            "sync_metrics": self.sync_metrics,
            "alignment_metrics": self.alignment_metrics,
            "temporal_metrics": self.temporal_metrics,
            "composite_score": self.composite_score,
            "sync_score": self.get_sync_score(),
            "alignment_score": self.get_alignment_score(),
            "temporal_score": self.get_temporal_score(),
            "timestamps": self.timestamps,
        }


@dataclass
class DatasetResults:
    """Aggregate evaluation results for an entire dataset.

    Attributes:
        results: Per-sample EvaluationResult list.
        aggregates: Summary statistics computed over all samples.
    """

    results: List[EvaluationResult] = field(default_factory=list)
    aggregates: Dict[str, Any] = field(default_factory=dict)

    def compute_aggregates(self) -> Dict[str, Any]:
        """Compute mean, std, min, max, and percentiles over all samples."""
        if not self.results:
            self.aggregates = {}
            return self.aggregates

        composites = np.array([
            r.composite_score for r in self.results
            if r.composite_score is not None
        ])
        sync_scores = np.array([r.get_sync_score() for r in self.results])
        align_scores = np.array([r.get_alignment_score() for r in self.results])
        temporal_scores = np.array([r.get_temporal_score() for r in self.results])

        def _stats(arr: np.ndarray) -> Dict[str, float]:
            if len(arr) == 0:
                return {}
            return {
                "mean": float(np.mean(arr)),
                "std": float(np.std(arr)),
                "min": float(np.min(arr)),
                "max": float(np.max(arr)),
                "p25": float(np.percentile(arr, 25)),
                "p50": float(np.percentile(arr, 50)),
                "p75": float(np.percentile(arr, 75)),
            }

        self.aggregates = {
            "n_samples": len(self.results),
            "composite": _stats(composites),
            "sync": _stats(sync_scores),
            "alignment": _stats(align_scores),
            "temporal": _stats(temporal_scores),
        }
        return self.aggregates

    def export_to_csv(self, path: str) -> None:
        """Write per-sample results to a CSV file.

        Args:
            path: Output CSV file path.
        """
        if not self.results:
            return

        rows = [r.to_dict() for r in self.results]
        # Flatten nested dicts into columns
        flat_rows: List[Dict[str, Any]] = []
        for row in rows:
            flat: Dict[str, Any] = {
                "sample_id": row["sample_id"],
                "composite_score": row["composite_score"],
                "sync_score": row["sync_score"],
                "alignment_score": row["alignment_score"],
                "temporal_score": row["temporal_score"],
            }
            flat_rows.append(flat)

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(flat_rows[0].keys())
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flat_rows)

    def export_to_json(self, path: str) -> None:
        """Write full results (per-sample + aggregates) to a JSON file.

        Args:
            path: Output JSON file path.
        """
        if not self.aggregates:
            self.compute_aggregates()

        output = {
            "aggregates": self.aggregates,
            "samples": [r.to_dict() for r in self.results],
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(output, f, indent=2, default=str)
