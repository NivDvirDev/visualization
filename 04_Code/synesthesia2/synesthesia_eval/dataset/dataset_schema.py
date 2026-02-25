"""Data models for the synesthesia evaluation dataset.

Defines the core schema for video samples, ground truth annotations,
and dataset splits used throughout the evaluation pipeline.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class DatasetSplit(Enum):
    """Dataset partition identifier."""

    TRAIN = "train"
    VAL = "val"
    TEST = "test"


@dataclass
class GroundTruth:
    """Human-annotated ground truth scores for a video sample.

    All scores are normalized to [0, 1] where 1.0 is best.

    Attributes:
        sync_score: Audio-visual temporal synchronization quality.
        alignment_score: Semantic/feature alignment quality.
        aesthetic_score: Overall visual aesthetic quality.
        annotator_ids: List of annotator identifiers who rated this sample.
        confidence: Mean annotator confidence in their ratings (0-1).
    """

    sync_score: float
    alignment_score: float
    aesthetic_score: float
    annotator_ids: List[str] = field(default_factory=list)
    confidence: float = 1.0

    def __post_init__(self) -> None:
        for attr in ("sync_score", "alignment_score", "aesthetic_score", "confidence"):
            val = getattr(self, attr)
            if not 0.0 <= val <= 1.0:
                raise ValueError(f"{attr} must be in [0, 1], got {val}")

    @property
    def composite_score(self) -> float:
        """Weighted average of all sub-scores."""
        return (
            0.4 * self.sync_score
            + 0.35 * self.alignment_score
            + 0.25 * self.aesthetic_score
        )


@dataclass
class VideoSample:
    """A single evaluation sample linking video, audio, and metadata.

    Attributes:
        sample_id: Unique identifier for this sample.
        video_path: Path to the video file.
        audio_path: Path to the source audio file.
        metadata: Arbitrary metadata (genre, tempo, complexity, etc.).
        ground_truth: Optional human annotations.
        split: Dataset partition this sample belongs to.
    """

    sample_id: str
    video_path: str
    audio_path: str
    metadata: Dict[str, object] = field(default_factory=dict)
    ground_truth: Optional[GroundTruth] = None
    split: DatasetSplit = DatasetSplit.TRAIN

    def has_ground_truth(self) -> bool:
        """Return True if this sample has ground truth annotations."""
        return self.ground_truth is not None
