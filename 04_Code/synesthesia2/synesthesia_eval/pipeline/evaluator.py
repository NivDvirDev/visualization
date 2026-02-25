"""Core evaluation pipeline for synesthesia audio-visual scoring.

Orchestrates feature extraction and metric computation across the
Stage 1 & 2 components to produce per-sample and aggregate results.
"""

import logging
import time
from typing import Callable, List, Optional

import librosa
import numpy as np

from synesthesia_eval.dataset.dataset_schema import VideoSample
from synesthesia_eval.extractors.audio_extractor import AudioFeatureExtractor
from synesthesia_eval.metrics.alignment_metrics import AlignmentMetrics
from synesthesia_eval.metrics.sync_metrics import SynchronizationMetrics
from synesthesia_eval.metrics.temporal_analysis import TemporalAnalyzer
from synesthesia_eval.pipeline.results import DatasetResults, EvaluationResult

logger = logging.getLogger(__name__)


class SynesthesiaEvaluator:
    """Evaluate audio-visual synchronization quality.

    Composes extractors and metrics to score how well a video
    visualization aligns with its source audio.

    Args:
        audio_extractor: AudioFeatureExtractor instance.
        sync_metrics: SynchronizationMetrics instance.
        alignment_metrics: AlignmentMetrics instance.
        temporal_analyzer: TemporalAnalyzer instance.
        sync_weight: Weight for sync score in composite (default 0.4).
        alignment_weight: Weight for alignment score in composite (default 0.35).
        temporal_weight: Weight for temporal score in composite (default 0.25).
    """

    def __init__(
        self,
        audio_extractor: Optional[AudioFeatureExtractor] = None,
        sync_metrics: Optional[SynchronizationMetrics] = None,
        alignment_metrics: Optional[AlignmentMetrics] = None,
        temporal_analyzer: Optional[TemporalAnalyzer] = None,
        sync_weight: float = 0.4,
        alignment_weight: float = 0.35,
        temporal_weight: float = 0.25,
    ):
        self.audio_extractor = audio_extractor or AudioFeatureExtractor()
        self.sync_metrics = sync_metrics or SynchronizationMetrics()
        self.alignment_metrics = alignment_metrics or AlignmentMetrics()
        self.temporal_analyzer = temporal_analyzer or TemporalAnalyzer()
        self.sync_weight = sync_weight
        self.alignment_weight = alignment_weight
        self.temporal_weight = temporal_weight

    def evaluate_single(
        self,
        video_path: str,
        audio_path: str,
        sample_id: str = "unknown",
    ) -> EvaluationResult:
        """Evaluate a single video/audio pair.

        Loads the audio, extracts visual brightness from the video,
        and computes all metrics.

        Args:
            video_path: Path to the video file.
            audio_path: Path to the audio file.
            sample_id: Identifier for logging.

        Returns:
            EvaluationResult with all metric outputs.
        """
        t_start = time.time()
        result = EvaluationResult(sample_id=sample_id)

        try:
            audio_features = self.audio_extractor.extract_all(audio_path)
        except Exception as e:
            logger.error("Audio extraction failed for %s: %s", sample_id, e)
            return result

        # Extract visual brightness curve from video
        visual_brightness = self._extract_visual_curve(video_path)

        # --- Synchronization metrics ---
        result.sync_metrics = self.compute_sync_scores(audio_features, visual_brightness)

        # --- Alignment metrics ---
        result.alignment_metrics = self.compute_alignment_scores(
            audio_features, visual_brightness
        )

        # --- Temporal metrics ---
        result.temporal_metrics = self.compute_temporal_scores(
            audio_features, visual_brightness
        )

        # --- Composite ---
        result.composite_score = self.compute_composite_score(result)
        result.timestamps["total_seconds"] = time.time() - t_start

        return result

    def evaluate_dataset(
        self,
        samples: List[VideoSample],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> DatasetResults:
        """Evaluate an entire dataset of samples.

        Args:
            samples: List of VideoSample instances to evaluate.
            progress_callback: Optional callback(current, total) for progress.

        Returns:
            DatasetResults with per-sample and aggregate results.
        """
        dataset_results = DatasetResults()
        total = len(samples)

        for i, sample in enumerate(samples):
            logger.info("Evaluating %d/%d: %s", i + 1, total, sample.sample_id)
            result = self.evaluate_single(
                video_path=sample.video_path,
                audio_path=sample.audio_path,
                sample_id=sample.sample_id,
            )
            dataset_results.results.append(result)

            if progress_callback:
                progress_callback(i + 1, total)

        dataset_results.compute_aggregates()
        return dataset_results

    def compute_sync_scores(
        self, audio_features, visual_brightness: np.ndarray
    ) -> dict:
        """Compute synchronization metrics from extracted features.

        Args:
            audio_features: AudioFeatures from the audio extractor.
            visual_brightness: 1-D visual brightness curve.

        Returns:
            Dict of metric_name -> result_dict.
        """
        results = {}
        hop = self.audio_extractor.hop_length
        sr = audio_features.sample_rate

        # Onset-visual alignment
        onset_times = librosa.frames_to_time(
            np.where(audio_features.onset_strength > np.mean(audio_features.onset_strength))[0],
            sr=sr,
            hop_length=hop,
        )
        visual_onsets = self.temporal_analyzer.extract_visual_onsets(visual_brightness)
        results["onset_alignment"] = self.sync_metrics.onset_visual_alignment(
            onset_times, visual_onsets
        )

        # Beat sync
        beat_times = librosa.frames_to_time(
            audio_features.beat_frames, sr=sr, hop_length=hop
        )
        results["beat_sync"] = self.sync_metrics.beat_sync_score(
            beat_times, visual_onsets
        )

        # Tempo consistency
        visual_rhythm = self.temporal_analyzer.extract_visual_rhythm(visual_brightness)
        results["tempo_consistency"] = self.sync_metrics.tempo_consistency(
            audio_features.tempo, visual_rhythm["tempo_bpm"]
        )

        # Cross-correlation
        audio_env = audio_features.onset_strength
        min_len = min(len(audio_env), len(visual_brightness))
        if min_len > 1:
            results["cross_correlation"] = self.sync_metrics.cross_correlation(
                audio_env[:min_len], visual_brightness[:min_len]
            )
        else:
            results["cross_correlation"] = {"score": 0.0, "best_lag": 0, "correlation_at_zero": 0.0}

        return results

    def compute_alignment_scores(
        self, audio_features, visual_brightness: np.ndarray
    ) -> dict:
        """Compute alignment metrics from extracted features.

        Args:
            audio_features: AudioFeatures from the audio extractor.
            visual_brightness: 1-D visual brightness curve.

        Returns:
            Dict of metric_name -> result_dict.
        """
        results = {}

        # Energy alignment: RMS vs visual brightness
        hop = self.audio_extractor.hop_length
        sr = audio_features.sample_rate
        # Compute RMS from mel spectrogram (mean over frequency bands)
        audio_rms = np.mean(np.abs(audio_features.mel_spectrogram), axis=0)
        min_len = min(len(audio_rms), len(visual_brightness))
        if min_len > 1:
            results["energy_alignment"] = self.alignment_metrics.energy_alignment(
                audio_rms[:min_len], visual_brightness[:min_len]
            )
        else:
            results["energy_alignment"] = {"score": 0.0, "correlation": 0.0}

        # Harmonic-visual complexity
        chroma = audio_features.chroma  # (12, time)
        harmonic_richness = np.std(chroma, axis=0)  # spectral diversity over time
        min_len = min(len(harmonic_richness), len(visual_brightness))
        if min_len > 1:
            results["harmonic_complexity"] = self.alignment_metrics.harmonic_visual_complexity(
                harmonic_richness[:min_len], visual_brightness[:min_len]
            )
        else:
            results["harmonic_complexity"] = {"score": 0.0, "correlation": 0.0}

        return results

    def compute_temporal_scores(
        self, audio_features, visual_brightness: np.ndarray
    ) -> dict:
        """Compute temporal analysis metrics.

        Args:
            audio_features: AudioFeatures from the audio extractor.
            visual_brightness: 1-D visual brightness curve.

        Returns:
            Dict of metric_name -> result_dict.
        """
        results = {}

        audio_env = audio_features.onset_strength
        min_len = min(len(audio_env), len(visual_brightness))
        if min_len > 1:
            results["lag_analysis"] = self.temporal_analyzer.lag_analysis(
                audio_env[:min_len], visual_brightness[:min_len]
            )

            # Phase coherence using Hilbert transform
            from scipy.signal import hilbert

            audio_analytic = hilbert(audio_env[:min_len])
            visual_analytic = hilbert(visual_brightness[:min_len])
            results["phase_coherence"] = self.temporal_analyzer.phase_coherence(
                np.angle(audio_analytic), np.angle(visual_analytic)
            )
        else:
            results["lag_analysis"] = {
                "optimal_lag": 0, "optimal_lag_seconds": 0.0,
                "peak_correlation": 0.0, "score": 0.0,
            }
            results["phase_coherence"] = {"score": 0.0, "mean_phase_diff": 0.0}

        return results

    def compute_composite_score(self, result: EvaluationResult) -> float:
        """Compute weighted composite score from sub-scores.

        Args:
            result: EvaluationResult with populated metric dicts.

        Returns:
            Composite score in [0, 1].
        """
        sync = result.get_sync_score()
        alignment = result.get_alignment_score()
        temporal = result.get_temporal_score()

        composite = (
            self.sync_weight * sync
            + self.alignment_weight * alignment
            + self.temporal_weight * temporal
        )
        return float(np.clip(composite, 0.0, 1.0))

    def _extract_visual_curve(self, video_path: str) -> np.ndarray:
        """Extract a brightness curve from a video file.

        Uses OpenCV to read frames and compute mean brightness per frame.
        Falls back to a synthetic curve if OpenCV is unavailable.

        Args:
            video_path: Path to video file.

        Returns:
            1-D numpy array of per-frame mean brightness values.
        """
        try:
            import cv2

            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.warning("Cannot open video %s, using empty curve", video_path)
                return np.array([0.0])

            brightness = []
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                brightness.append(float(np.mean(frame)))
            cap.release()

            if not brightness:
                return np.array([0.0])
            return np.array(brightness, dtype=np.float64)

        except ImportError:
            logger.warning("OpenCV not available, returning empty visual curve")
            return np.array([0.0])
