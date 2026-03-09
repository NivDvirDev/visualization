"""Dataset loading and management for the synesthesia evaluation pipeline.

Supports loading from directory structures with JSON annotations and
from CSV files. Provides dataset splitting, validation, and statistics.
"""

import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from synesthesia_eval.dataset.dataset_schema import (
    DatasetSplit,
    GroundTruth,
    VideoSample,
)

logger = logging.getLogger(__name__)


class DatasetLoader:
    """Load and manage evaluation datasets.

    Stores a collection of :class:`VideoSample` instances and provides
    methods for splitting, validation, and summary statistics.
    """

    def __init__(self) -> None:
        self.samples: List[VideoSample] = []

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_from_directory(self, path: str) -> "DatasetLoader":
        """Scan a directory for video/audio pairs with JSON annotations.

        Expected structure::

            path/
              sample_001/
                video.mp4
                audio.wav
                annotation.json
              sample_002/
                ...

        Each ``annotation.json`` should follow the annotation schema.

        Args:
            path: Root directory to scan.

        Returns:
            self, for chaining.
        """
        root = Path(path)
        if not root.is_dir():
            raise FileNotFoundError(f"Dataset directory not found: {path}")

        for sample_dir in sorted(root.iterdir()):
            if not sample_dir.is_dir():
                continue

            video_files = list(sample_dir.glob("*.mp4")) + list(
                sample_dir.glob("*.avi")
            )
            audio_files = list(sample_dir.glob("*.wav")) + list(
                sample_dir.glob("*.mp3")
            )
            annotation_file = sample_dir / "annotation.json"

            if not video_files or not audio_files:
                logger.warning("Skipping %s: missing video or audio", sample_dir.name)
                continue

            video_path = str(video_files[0])
            audio_path = str(audio_files[0])

            ground_truth = None
            metadata: Dict[str, object] = {}
            split = DatasetSplit.TRAIN

            if annotation_file.exists():
                with open(annotation_file) as f:
                    ann = json.load(f)
                ground_truth = GroundTruth(
                    sync_score=ann.get("sync_score", 3.0),
                    alignment_score=ann.get("alignment_score", 3.0),
                    aesthetic_score=ann.get("aesthetic_score", 3.0),
                    motion_smoothness_score=ann.get("motion_smoothness_score", 3.0),
                    annotator_ids=ann.get("annotator_ids", []),
                    confidence=ann.get("confidence", 1.0),
                )
                metadata = ann.get("metadata", {})
                split_str = ann.get("split", "train")
                split = DatasetSplit(split_str)

            self.samples.append(
                VideoSample(
                    sample_id=sample_dir.name,
                    video_path=video_path,
                    audio_path=audio_path,
                    metadata=metadata,
                    ground_truth=ground_truth,
                    split=split,
                )
            )

        logger.info("Loaded %d samples from %s", len(self.samples), path)
        return self

    def load_from_csv(self, csv_path: str) -> "DatasetLoader":
        """Load dataset from a CSV file.

        Required columns: sample_id, video_path, audio_path.
        Optional columns: sync_score, alignment_score, aesthetic_score,
        confidence, annotator_ids, split, genre, tempo, complexity.

        Args:
            csv_path: Path to the CSV file.

        Returns:
            self, for chaining.
        """
        csv_file = Path(csv_path)
        if not csv_file.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        with open(csv_file, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ground_truth = None
                if "sync_score" in row and row["sync_score"]:
                    annotator_ids = (
                        row.get("annotator_ids", "").split(";")
                        if row.get("annotator_ids")
                        else []
                    )
                    ground_truth = GroundTruth(
                        sync_score=float(row["sync_score"]),
                        alignment_score=float(row.get("alignment_score", 3)),
                        aesthetic_score=float(row.get("aesthetic_score", 3)),
                        motion_smoothness_score=float(row.get("motion_smoothness_score", 3)),
                        annotator_ids=annotator_ids,
                        confidence=float(row.get("confidence", 1.0)),
                    )

                metadata: Dict[str, object] = {}
                for key in ("genre", "tempo", "complexity"):
                    if key in row and row[key]:
                        metadata[key] = row[key]

                split_str = row.get("split", "train")
                split = DatasetSplit(split_str)

                self.samples.append(
                    VideoSample(
                        sample_id=row["sample_id"],
                        video_path=row["video_path"],
                        audio_path=row["audio_path"],
                        metadata=metadata,
                        ground_truth=ground_truth,
                        split=split,
                    )
                )

        logger.info("Loaded %d samples from %s", len(self.samples), csv_path)
        return self

    def load_from_clips_dir(
        self, clips_dir: str, labels_file: str, metadata_file: Optional[str] = None
    ) -> "DatasetLoader":
        """Load from the synesthesia_eval local format: clips/*.mp4 + labels JSON.

        This bridges the actual data format (auto_labels.json or unified_labels.json)
        with the evaluation pipeline.

        Args:
            clips_dir: Directory containing .mp4 clip files.
            labels_file: Path to labels JSON (auto_labels.json format).
            metadata_file: Optional path to metadata.json for clip descriptions.

        Returns:
            self, for chaining.
        """
        clips_path = Path(clips_dir)
        labels_path = Path(labels_file)

        if not clips_path.is_dir():
            raise FileNotFoundError(f"Clips directory not found: {clips_dir}")
        if not labels_path.exists():
            raise FileNotFoundError(f"Labels file not found: {labels_file}")

        with open(labels_path) as f:
            labels = json.load(f)

        # Load optional metadata
        clip_metadata: Dict[str, dict] = {}
        if metadata_file:
            meta_path = Path(metadata_file)
            if meta_path.exists():
                with open(meta_path) as f:
                    meta = json.load(f)
                for clip in meta.get("clips", []):
                    clip_metadata[clip.get("id", "")] = clip

        # Find video files and match with labels
        video_files = sorted(clips_path.glob("*.mp4"))
        for video_path in video_files:
            # Extract clip ID from filename (e.g., "001_something.mp4" -> "001")
            import re
            match = re.match(r"^(\d+)", video_path.name)
            clip_id = match.group(1) if match else video_path.stem

            ground_truth = None
            if clip_id in labels:
                entry = labels[clip_id]
                ground_truth = GroundTruth(
                    sync_score=float(entry.get("sync_quality", 3)),
                    alignment_score=float(entry.get("visual_audio_alignment", 3)),
                    aesthetic_score=float(entry.get("aesthetic_quality", 3)),
                    motion_smoothness_score=float(entry.get("motion_smoothness", 3)),
                    annotator_ids=[entry.get("model", "unknown")],
                    confidence=1.0,
                )

            metadata = clip_metadata.get(clip_id, {})

            self.samples.append(
                VideoSample(
                    sample_id=clip_id,
                    video_path=str(video_path),
                    audio_path="",  # Audio extracted from video at processing time
                    metadata=metadata,
                    ground_truth=ground_truth,
                    split=DatasetSplit.TRAIN,
                )
            )

        logger.info("Loaded %d samples from %s (%d labeled)", len(self.samples), clips_dir,
                     sum(1 for s in self.samples if s.has_ground_truth()))
        return self

    def load_from_huggingface(
        self, dataset_id: str = "NivDvir/synesthesia-eval", token: Optional[str] = None
    ) -> "DatasetLoader":
        """Load clips and labels from a HuggingFace dataset.

        Fetches clip list, auto_labels.json, and community_labels.json from HF.
        Videos are referenced by HF URL (not downloaded).

        Args:
            dataset_id: HuggingFace dataset identifier.
            token: Optional HF API token for private datasets.

        Returns:
            self, for chaining.
        """
        import urllib.request

        hf_base = f"https://huggingface.co/datasets/{dataset_id}"
        api_base = f"https://huggingface.co/api/datasets/{dataset_id}"

        def _fetch_json(url: str) -> Optional[dict]:
            req = urllib.request.Request(url)
            if token:
                req.add_header("Authorization", f"Bearer {token}")
            try:
                with urllib.request.urlopen(req) as resp:
                    return json.loads(resp.read().decode())
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return None
                raise

        # Fetch file list from HF API
        tree = _fetch_json(f"{api_base}/tree/main/data/clips")
        if not tree:
            raise RuntimeError(f"Could not fetch clip list from {dataset_id}")

        clip_files = [
            f for f in tree
            if f.get("type") == "file" and f["path"].lower().endswith(".mp4")
        ]

        # Fetch labels
        auto_labels = _fetch_json(f"{hf_base}/resolve/main/data/auto_labels.json") or {}
        community_raw = _fetch_json(f"{hf_base}/resolve/main/data/community_labels.json") or []

        # Index community labels by clip_id (may have multiple per clip)
        community_by_clip: Dict[str, List[dict]] = {}
        for entry in community_raw:
            cid = entry.get("clip_id", "")
            community_by_clip.setdefault(cid, []).append(entry)

        # Build samples
        import re
        for f in clip_files:
            filename = f["path"].split("/")[-1]
            match = re.match(r"^(\d+)", filename)
            clip_id = match.group(1) if match else filename.rsplit(".", 1)[0]

            video_url = f"{hf_base}/resolve/main/{f['path']}"

            # Prefer human labels over auto labels
            ground_truth = None
            source = "none"

            human_entries = community_by_clip.get(clip_id, [])
            if human_entries:
                # Average human ratings if multiple
                scores = {"sync_quality": [], "visual_audio_alignment": [],
                          "aesthetic_quality": [], "motion_smoothness": []}
                annotators = []
                for he in human_entries:
                    s = he.get("scores", he)
                    for k in scores:
                        if k in s:
                            scores[k].append(float(s[k]))
                    annotators.append(he.get("user", "human"))

                ground_truth = GroundTruth(
                    sync_score=np.mean(scores["sync_quality"]) if scores["sync_quality"] else 3.0,
                    alignment_score=np.mean(scores["visual_audio_alignment"]) if scores["visual_audio_alignment"] else 3.0,
                    aesthetic_score=np.mean(scores["aesthetic_quality"]) if scores["aesthetic_quality"] else 3.0,
                    motion_smoothness_score=np.mean(scores["motion_smoothness"]) if scores["motion_smoothness"] else 3.0,
                    annotator_ids=annotators,
                    confidence=1.0,
                )
                source = "human"

            elif clip_id in auto_labels:
                entry = auto_labels[clip_id]
                ground_truth = GroundTruth(
                    sync_score=float(entry.get("sync_quality", 3)),
                    alignment_score=float(entry.get("visual_audio_alignment", 3)),
                    aesthetic_score=float(entry.get("aesthetic_quality", 3)),
                    motion_smoothness_score=float(entry.get("motion_smoothness", 3)),
                    annotator_ids=[entry.get("model", "gemini")],
                    confidence=0.8,  # Lower confidence for AI labels
                )
                source = "auto"

            self.samples.append(
                VideoSample(
                    sample_id=clip_id,
                    video_path=video_url,
                    audio_path="",
                    metadata={"source": source, "filename": filename},
                    ground_truth=ground_truth,
                    split=DatasetSplit.TRAIN,
                )
            )

        logger.info("Loaded %d samples from HuggingFace %s (%d labeled)",
                     len(self.samples), dataset_id,
                     sum(1 for s in self.samples if s.has_ground_truth()))
        return self

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def get_split(self, split: DatasetSplit) -> List[VideoSample]:
        """Return samples belonging to the given split.

        Args:
            split: The dataset partition to retrieve.

        Returns:
            List of matching VideoSample instances.
        """
        return [s for s in self.samples if s.split == split]

    def get_annotated_samples(self) -> List[VideoSample]:
        """Return only samples that have ground truth annotations."""
        return [s for s in self.samples if s.has_ground_truth()]

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_dataset(self) -> Dict[str, object]:
        """Check dataset integrity and report issues.

        Returns:
            Dict with keys:
                - 'total_samples': number of samples loaded.
                - 'missing_video': list of sample IDs with missing video files.
                - 'missing_audio': list of sample IDs with missing audio files.
                - 'missing_ground_truth': list of sample IDs without annotations.
                - 'valid': True if no files are missing.
        """
        missing_video: List[str] = []
        missing_audio: List[str] = []
        missing_gt: List[str] = []

        for s in self.samples:
            if not Path(s.video_path).exists():
                missing_video.append(s.sample_id)
            if not Path(s.audio_path).exists():
                missing_audio.append(s.sample_id)
            if not s.has_ground_truth():
                missing_gt.append(s.sample_id)

        report = {
            "total_samples": len(self.samples),
            "missing_video": missing_video,
            "missing_audio": missing_audio,
            "missing_ground_truth": missing_gt,
            "valid": len(missing_video) == 0 and len(missing_audio) == 0,
        }

        if missing_video:
            logger.warning("Missing video files: %s", missing_video)
        if missing_audio:
            logger.warning("Missing audio files: %s", missing_audio)

        return report

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def get_statistics(self) -> Dict[str, object]:
        """Compute summary statistics over the dataset.

        Returns:
            Dict with distribution info for scores, splits, and metadata.
        """
        stats: Dict[str, object] = {
            "total_samples": len(self.samples),
            "annotated_samples": sum(1 for s in self.samples if s.has_ground_truth()),
        }

        # Split distribution
        split_counts = {}
        for split in DatasetSplit:
            split_counts[split.value] = len(self.get_split(split))
        stats["split_distribution"] = split_counts

        # Score distributions for annotated samples
        annotated = self.get_annotated_samples()
        if annotated:
            sync = np.array([s.ground_truth.sync_score for s in annotated])
            align = np.array([s.ground_truth.alignment_score for s in annotated])
            aesthetic = np.array([s.ground_truth.aesthetic_score for s in annotated])
            motion = np.array([s.ground_truth.motion_smoothness_score for s in annotated])

            def _dist(arr: np.ndarray) -> Dict[str, float]:
                return {
                    "mean": float(np.mean(arr)),
                    "std": float(np.std(arr)),
                    "min": float(np.min(arr)),
                    "max": float(np.max(arr)),
                    "median": float(np.median(arr)),
                }

            stats["sync_score"] = _dist(sync)
            stats["alignment_score"] = _dist(align)
            stats["aesthetic_score"] = _dist(aesthetic)
            stats["motion_smoothness_score"] = _dist(motion)

        # Genre distribution
        genres: Dict[str, int] = {}
        for s in self.samples:
            genre = s.metadata.get("genre", "unknown")
            genres[genre] = genres.get(genre, 0) + 1
        stats["genre_distribution"] = genres

        return stats

    def __len__(self) -> int:
        return len(self.samples)

    def __repr__(self) -> str:
        return f"DatasetLoader({len(self.samples)} samples)"
