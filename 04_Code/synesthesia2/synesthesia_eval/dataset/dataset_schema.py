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
    """Human or AI-annotated ground truth scores for a video sample.

    Scores are on a 1-5 integer scale matching the labeling interface.

    Attributes:
        sync_score: Audio-visual temporal synchronization quality (1-5).
        alignment_score: Semantic/feature alignment quality (1-5).
        aesthetic_score: Overall visual aesthetic quality (1-5).
        motion_smoothness_score: Fluidity and smoothness of motion (1-5).
        annotator_ids: List of annotator identifiers who rated this sample.
        confidence: Mean annotator confidence in their ratings (0-1).
    """

    sync_score: float
    alignment_score: float
    aesthetic_score: float
    motion_smoothness_score: float = 3.0
    annotator_ids: List[str] = field(default_factory=list)
    confidence: float = 1.0

    def __post_init__(self) -> None:
        for attr in ("sync_score", "alignment_score", "aesthetic_score", "motion_smoothness_score"):
            val = getattr(self, attr)
            if not 1.0 <= val <= 5.0:
                raise ValueError(f"{attr} must be in [1, 5], got {val}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be in [0, 1], got {self.confidence}")

    @property
    def composite_score(self) -> float:
        """Weighted average of all sub-scores, normalized to [0, 1]."""
        raw = (
            0.30 * self.sync_score
            + 0.30 * self.alignment_score
            + 0.20 * self.aesthetic_score
            + 0.20 * self.motion_smoothness_score
        )
        return (raw - 1.0) / 4.0  # Map 1-5 to 0-1


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
