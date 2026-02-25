"""Benchmarking framework for comparing scoring models.

Runs standardized evaluations and generates comparative reports.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from synesthesia_eval.dataset.dataset_schema import VideoSample
from synesthesia_eval.pipeline.results import DatasetResults, EvaluationResult
from synesthesia_eval.pipeline.scoring_model import ScoringModel
from synesthesia_eval.validation.reliability import ReliabilityValidator

logger = logging.getLogger(__name__)


class BenchmarkReport:
    """Container for benchmark results with report generation.

    Attributes:
        model_results: Dict mapping model names to their benchmark metrics.
        dataset_info: Summary of the benchmark dataset.
        timestamp: When the benchmark was run.
    """

    def __init__(self) -> None:
        self.model_results: Dict[str, Dict[str, Any]] = {}
        self.dataset_info: Dict[str, Any] = {}
        self.timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "dataset_info": self.dataset_info,
            "model_results": self.model_results,
        }

    def save_json(self, path: str) -> None:
        """Save report to JSON file."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

    def to_markdown(self) -> str:
        """Generate a markdown report string."""
        lines = [
            "# Synesthesia Scoring Model Benchmark Report",
            "",
            f"**Run at:** {self.timestamp}",
            "",
            "## Dataset",
            "",
            f"- Total samples: {self.dataset_info.get('n_samples', 'N/A')}",
            f"- Annotated samples: {self.dataset_info.get('n_annotated', 'N/A')}",
            "",
            "## Model Comparison",
            "",
            "| Model | Pearson r | Spearman rho | RMSE | MAE | CV Mean r |",
            "|-------|-----------|-------------|------|-----|-----------|",
        ]

        for name, metrics in self.model_results.items():
            corr = metrics.get("correlation", {})
            cv = metrics.get("cross_validation", {})
            lines.append(
                f"| {name} "
                f"| {corr.get('pearson_r', 'N/A'):.3f} "
                f"| {corr.get('spearman_rho', 'N/A'):.3f} "
                f"| {corr.get('rmse', 'N/A'):.3f} "
                f"| {corr.get('mae', 'N/A'):.3f} "
                f"| {cv.get('mean_r', 'N/A'):.3f} |"
            )

        lines.extend([
            "",
            "## Feature Importance (Top Model)",
            "",
        ])

        # Show feature importance for the best model
        best_model = None
        best_r = -1.0
        for name, metrics in self.model_results.items():
            r = metrics.get("correlation", {}).get("pearson_r", -1)
            if r > best_r:
                best_r = r
                best_model = name

        if best_model:
            importance = self.model_results[best_model].get("feature_importance", {})
            if importance:
                lines.append(f"**Best model: {best_model}**")
                lines.append("")
                lines.append("| Feature | Importance |")
                lines.append("|---------|-----------|")
                for feat, imp in list(importance.items())[:10]:
                    lines.append(f"| {feat} | {imp:.4f} |")

        return "\n".join(lines)


class Benchmark:
    """Run standardized benchmarks on scoring models.

    Args:
        validator: ReliabilityValidator instance for computing metrics.
    """

    def __init__(
        self,
        validator: Optional[ReliabilityValidator] = None,
    ):
        self.validator = validator or ReliabilityValidator()

    def run_full_benchmark(
        self,
        model: ScoringModel,
        results: List[EvaluationResult],
        samples: List[VideoSample],
        model_name: str = "default",
    ) -> BenchmarkReport:
        """Run a complete benchmark on a single model.

        Args:
            model: Fitted ScoringModel to evaluate.
            results: Evaluation results for the dataset.
            samples: Corresponding VideoSample list with ground truth.
            model_name: Name for this model in the report.

        Returns:
            BenchmarkReport with full results.
        """
        report = BenchmarkReport()
        report.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        report.dataset_info = {
            "n_samples": len(samples),
            "n_annotated": sum(1 for s in samples if s.has_ground_truth()),
        }

        report.model_results[model_name] = self._evaluate_model(
            model, results, samples
        )

        return report

    def compare_models(
        self,
        models: Dict[str, ScoringModel],
        results: List[EvaluationResult],
        samples: List[VideoSample],
    ) -> BenchmarkReport:
        """Compare multiple models side-by-side.

        Args:
            models: Dict mapping model name to fitted ScoringModel.
            results: Shared evaluation results.
            samples: Shared samples with ground truth.

        Returns:
            BenchmarkReport with comparative results.
        """
        report = BenchmarkReport()
        report.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        report.dataset_info = {
            "n_samples": len(samples),
            "n_annotated": sum(1 for s in samples if s.has_ground_truth()),
        }

        for name, model in models.items():
            logger.info("Benchmarking model: %s", name)
            report.model_results[name] = self._evaluate_model(
                model, results, samples
            )

        return report

    def generate_report(
        self,
        report: BenchmarkReport,
        output_dir: str,
    ) -> str:
        """Generate markdown and JSON reports to the output directory.

        Args:
            report: BenchmarkReport to write.
            output_dir: Directory for output files.

        Returns:
            Path to the generated markdown report.
        """
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        md_path = out / "benchmark_report.md"
        json_path = out / "benchmark_report.json"

        md_content = report.to_markdown()
        with open(md_path, "w") as f:
            f.write(md_content)

        report.save_json(str(json_path))

        logger.info("Reports saved to %s", output_dir)
        return str(md_path)

    def _evaluate_model(
        self,
        model: ScoringModel,
        results: List[EvaluationResult],
        samples: List[VideoSample],
    ) -> Dict[str, Any]:
        """Run all evaluation metrics for a single model."""
        # Get predictions and ground truth
        sample_map = {s.sample_id: s for s in samples}
        annotated_results = [
            r for r in results
            if r.sample_id in sample_map and sample_map[r.sample_id].has_ground_truth()
        ]
        annotated_samples = [sample_map[r.sample_id] for r in annotated_results]

        if not annotated_results:
            return {"error": "No annotated samples found"}

        predictions = model.predict_batch(annotated_results)
        ground_truth = np.array([
            s.ground_truth.composite_score for s in annotated_samples
        ])

        # Correlation
        correlation = self.validator.compute_model_human_correlation(
            predictions, ground_truth
        )

        # Cross-validation
        cv = self.validator.cross_validation(
            model, results, samples, k=min(5, len(annotated_results))
        )

        # Bootstrap CI
        bootstrap = self.validator.bootstrap_confidence(
            predictions, ground_truth, n=1000
        )

        # Feature importance
        try:
            importance = model.get_feature_importance()
        except RuntimeError:
            importance = {}

        return {
            "correlation": correlation,
            "cross_validation": cv,
            "bootstrap": bootstrap,
            "feature_importance": importance,
            "n_predictions": len(predictions),
        }
