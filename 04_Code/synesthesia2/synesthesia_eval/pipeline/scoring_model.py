"""Learnable scoring model for combining metric outputs into a final score.

Fits a regression model on ground truth annotations to learn optimal
metric weights, with calibration and feature importance analysis.
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from synesthesia_eval.dataset.dataset_schema import VideoSample
from synesthesia_eval.pipeline.results import EvaluationResult

logger = logging.getLogger(__name__)


class ScoringModel:
    """Learn optimal weights for combining evaluation metrics into a score.

    Uses Ridge regression to map metric feature vectors to ground truth
    composite scores. Supports calibration for score distribution matching
    and feature importance analysis.

    Args:
        alpha: Ridge regression regularization strength. Default 1.0.
    """

    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha
        self._model: Optional[Ridge] = None
        self._scaler: Optional[StandardScaler] = None
        self._feature_names: Optional[List[str]] = None
        self._calibration_shift: float = 0.0
        self._calibration_scale: float = 1.0
        self._is_fitted: bool = False

    def fit(
        self,
        results: List[EvaluationResult],
        samples: List[VideoSample],
    ) -> "ScoringModel":
        """Learn optimal weights from evaluation results and ground truth.

        Args:
            results: EvaluationResult list with computed metrics.
            samples: Corresponding VideoSample list with ground_truth.

        Returns:
            self, for chaining.

        Raises:
            ValueError: If no annotated samples are provided.
        """
        X, y = self._build_dataset(results, samples)
        if len(X) == 0:
            raise ValueError("No annotated samples found for fitting")

        self._scaler = StandardScaler()
        X_scaled = self._scaler.fit_transform(X)

        self._model = Ridge(alpha=self.alpha)
        self._model.fit(X_scaled, y)
        self._is_fitted = True

        # Store feature names from the first result
        self._feature_names = self._get_feature_names(results[0])

        logger.info(
            "ScoringModel fitted on %d samples, R^2=%.3f",
            len(X),
            self._model.score(X_scaled, y),
        )
        return self

    def predict(self, result: EvaluationResult) -> float:
        """Predict a composite score for a single evaluation result.

        Args:
            result: EvaluationResult with computed metrics.

        Returns:
            Predicted score in [0, 1].

        Raises:
            RuntimeError: If the model has not been fitted.
        """
        if not self._is_fitted:
            raise RuntimeError("ScoringModel must be fitted before prediction")

        features = result.to_feature_vector().reshape(1, -1)
        # Pad or truncate to match training feature count
        expected = self._scaler.n_features_in_
        if features.shape[1] < expected:
            features = np.pad(
                features, ((0, 0), (0, expected - features.shape[1]))
            )
        elif features.shape[1] > expected:
            features = features[:, :expected]

        features_scaled = self._scaler.transform(features)
        raw = float(self._model.predict(features_scaled)[0])

        # Apply calibration
        calibrated = raw * self._calibration_scale + self._calibration_shift
        return float(np.clip(calibrated, 0.0, 1.0))

    def predict_batch(self, results: List[EvaluationResult]) -> np.ndarray:
        """Predict scores for multiple evaluation results.

        Args:
            results: List of EvaluationResult instances.

        Returns:
            1-D array of predicted scores.
        """
        return np.array([self.predict(r) for r in results])

    def calibrate(
        self,
        results: List[EvaluationResult],
        samples: List[VideoSample],
    ) -> "ScoringModel":
        """Calibrate predictions to match ground truth distribution.

        Adjusts the mean and scale of predictions to align with
        the validation set's ground truth distribution.

        Args:
            results: Validation set evaluation results.
            samples: Corresponding samples with ground truth.

        Returns:
            self, for chaining.
        """
        _, y_true = self._build_dataset(results, samples)
        if len(y_true) == 0:
            logger.warning("No annotated samples for calibration")
            return self

        y_pred = np.array([self.predict(r) for r in results if self._has_gt(r, samples)])

        if len(y_pred) == 0 or np.std(y_pred) < 1e-10:
            return self

        # Linear calibration: match mean and std
        self._calibration_scale = float(np.std(y_true) / np.std(y_pred))
        self._calibration_shift = float(
            np.mean(y_true) - self._calibration_scale * np.mean(y_pred)
        )

        logger.info(
            "Calibration: scale=%.3f, shift=%.3f",
            self._calibration_scale,
            self._calibration_shift,
        )
        return self

    def get_feature_importance(self) -> Dict[str, float]:
        """Return feature importance based on model coefficients.

        Returns:
            Dict mapping feature names to their absolute importance scores,
            sorted by importance descending.

        Raises:
            RuntimeError: If the model has not been fitted.
        """
        if not self._is_fitted:
            raise RuntimeError("ScoringModel must be fitted before querying importance")

        coefs = np.abs(self._model.coef_)
        names = self._feature_names or [f"feature_{i}" for i in range(len(coefs))]

        # Ensure names match coefs length
        if len(names) < len(coefs):
            names.extend(f"feature_{i}" for i in range(len(names), len(coefs)))
        names = names[: len(coefs)]

        importance = dict(zip(names, coefs.tolist()))
        return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_dataset(
        self,
        results: List[EvaluationResult],
        samples: List[VideoSample],
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Build feature matrix X and target vector y from annotated samples."""
        sample_map = {s.sample_id: s for s in samples}
        X_list: List[np.ndarray] = []
        y_list: List[float] = []

        for r in results:
            sample = sample_map.get(r.sample_id)
            if sample is None or not sample.has_ground_truth():
                continue
            features = r.to_feature_vector()
            if len(features) == 0:
                continue
            X_list.append(features)
            y_list.append(sample.ground_truth.composite_score)

        if not X_list:
            return np.empty((0, 0)), np.empty(0)

        # Pad to uniform feature length
        max_len = max(len(x) for x in X_list)
        X = np.zeros((len(X_list), max_len))
        for i, x in enumerate(X_list):
            X[i, : len(x)] = x

        return X, np.array(y_list)

    def _has_gt(self, result: EvaluationResult, samples: List[VideoSample]) -> bool:
        """Check if a result's corresponding sample has ground truth."""
        for s in samples:
            if s.sample_id == result.sample_id and s.has_ground_truth():
                return True
        return False

    @staticmethod
    def _get_feature_names(result: EvaluationResult) -> List[str]:
        """Extract feature names from an EvaluationResult's metric structure."""
        names: List[str] = []
        for group_name, metrics_dict in [
            ("sync", result.sync_metrics),
            ("alignment", result.alignment_metrics),
            ("temporal", result.temporal_metrics),
        ]:
            for metric_name, sub_result in metrics_dict.items():
                if isinstance(sub_result, dict):
                    for key, val in sub_result.items():
                        if isinstance(val, (int, float)) and np.isfinite(val):
                            names.append(f"{group_name}.{metric_name}.{key}")
        return names
