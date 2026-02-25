"""Synesthesia Evaluation Pipeline.

Stage 3: Dataset management, evaluation pipeline, scoring model,
and reliability validation for audio-visual synchronization assessment.
"""

from synesthesia_eval.dataset.dataset_schema import (
    DatasetSplit,
    GroundTruth,
    VideoSample,
)
from synesthesia_eval.dataset.dataset_loader import DatasetLoader
from synesthesia_eval.pipeline.results import DatasetResults, EvaluationResult
from synesthesia_eval.pipeline.evaluator import SynesthesiaEvaluator
from synesthesia_eval.pipeline.scoring_model import ScoringModel
from synesthesia_eval.validation.reliability import ReliabilityValidator
from synesthesia_eval.validation.benchmark import Benchmark, BenchmarkReport

__all__ = [
    "DatasetSplit",
    "GroundTruth",
    "VideoSample",
    "DatasetLoader",
    "DatasetResults",
    "EvaluationResult",
    "SynesthesiaEvaluator",
    "ScoringModel",
    "ReliabilityValidator",
    "Benchmark",
    "BenchmarkReport",
]
