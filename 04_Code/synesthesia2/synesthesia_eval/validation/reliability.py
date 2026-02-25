"""Reliability validation for the synesthesia scoring model.

Provides inter-rater agreement, model-human correlation, cross-validation,
and bootstrap confidence interval computation.
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy import stats
from sklearn.model_selection import KFold

from synesthesia_eval.dataset.dataset_schema import VideoSample
from synesthesia_eval.pipeline.results import EvaluationResult
from synesthesia_eval.pipeline.scoring_model import ScoringModel

logger = logging.getLogger(__name__)


class ReliabilityValidator:
    """Validate scoring model reliability against human annotations.

    Provides statistical measures of agreement, correlation,
    cross-validation performance, and bootstrap confidence intervals.
    """

    def compute_inter_rater_agreement(
        self,
        samples: List[VideoSample],
    ) -> Dict[str, float]:
        """Compute inter-rater agreement from multiple annotators.

        Uses Krippendorff's alpha and Intraclass Correlation Coefficient (ICC)
        to measure consistency among human raters.

        Args:
            samples: VideoSample list with ground_truth containing
                annotator_ids. For this computation, each sample needs
                per-annotator scores stored in metadata['annotator_scores']
                as a dict mapping annotator_id -> score.

        Returns:
            Dict with keys:
                - 'krippendorff_alpha': Agreement coefficient (-1 to 1, >0.67 acceptable).
                - 'icc': Intraclass correlation coefficient (0-1).
                - 'n_annotators': Number of unique annotators.
                - 'n_samples': Number of samples with multi-annotator data.
        """
        # Collect per-annotator score matrices
        annotator_scores: Dict[str, List[Optional[float]]] = {}
        valid_samples = []

        for s in samples:
            if not s.has_ground_truth():
                continue
            per_annotator = s.metadata.get("annotator_scores", {})
            if len(per_annotator) < 2:
                continue
            valid_samples.append(s)
            for ann_id, score in per_annotator.items():
                if ann_id not in annotator_scores:
                    annotator_scores[ann_id] = []

        if not valid_samples or not annotator_scores:
            return {
                "krippendorff_alpha": 0.0,
                "icc": 0.0,
                "n_annotators": 0,
                "n_samples": 0,
            }

        # Build rating matrix (annotators x samples)
        annotator_list = sorted(annotator_scores.keys())
        n_ann = len(annotator_list)
        n_samp = len(valid_samples)
        rating_matrix = np.full((n_ann, n_samp), np.nan)

        for j, s in enumerate(valid_samples):
            per_annotator = s.metadata.get("annotator_scores", {})
            for i, ann_id in enumerate(annotator_list):
                if ann_id in per_annotator:
                    rating_matrix[i, j] = per_annotator[ann_id]

        alpha = self._krippendorff_alpha(rating_matrix)
        icc = self._icc(rating_matrix)

        return {
            "krippendorff_alpha": alpha,
            "icc": icc,
            "n_annotators": n_ann,
            "n_samples": n_samp,
        }

    def compute_model_human_correlation(
        self,
        predictions: np.ndarray,
        ground_truth: np.ndarray,
    ) -> Dict[str, float]:
        """Compute correlation between model predictions and human scores.

        Args:
            predictions: 1-D array of model-predicted scores.
            ground_truth: 1-D array of human ground truth scores.

        Returns:
            Dict with keys:
                - 'pearson_r': Pearson correlation coefficient.
                - 'pearson_p': p-value for Pearson.
                - 'spearman_rho': Spearman rank correlation.
                - 'spearman_p': p-value for Spearman.
                - 'rmse': Root mean squared error.
                - 'mae': Mean absolute error.
        """
        predictions = np.asarray(predictions).ravel()
        ground_truth = np.asarray(ground_truth).ravel()

        if len(predictions) < 2 or len(predictions) != len(ground_truth):
            return {
                "pearson_r": 0.0,
                "pearson_p": 1.0,
                "spearman_rho": 0.0,
                "spearman_p": 1.0,
                "rmse": float("inf"),
                "mae": float("inf"),
            }

        pearson_r, pearson_p = stats.pearsonr(predictions, ground_truth)
        spearman_rho, spearman_p = stats.spearmanr(predictions, ground_truth)
        rmse = float(np.sqrt(np.mean((predictions - ground_truth) ** 2)))
        mae = float(np.mean(np.abs(predictions - ground_truth)))

        return {
            "pearson_r": float(pearson_r),
            "pearson_p": float(pearson_p),
            "spearman_rho": float(spearman_rho),
            "spearman_p": float(spearman_p),
            "rmse": rmse,
            "mae": mae,
        }

    def cross_validation(
        self,
        model: ScoringModel,
        results: List[EvaluationResult],
        samples: List[VideoSample],
        k: int = 5,
    ) -> Dict[str, object]:
        """K-fold cross-validation of the scoring model.

        Args:
            model: ScoringModel to evaluate (will be re-fitted per fold).
            results: All evaluation results.
            samples: All corresponding samples with ground truth.
            k: Number of folds.

        Returns:
            Dict with keys:
                - 'fold_scores': list of per-fold Pearson-r values.
                - 'mean_r': mean Pearson-r across folds.
                - 'std_r': std of Pearson-r across folds.
                - 'mean_rmse': mean RMSE across folds.
                - 'ci_95': 95% confidence interval for mean_r.
        """
        # Filter to annotated samples only
        annotated_pairs = [
            (r, s) for r, s in zip(results, samples) if s.has_ground_truth()
        ]
        if len(annotated_pairs) < k:
            logger.warning(
                "Only %d annotated samples, need >= %d for %d-fold CV",
                len(annotated_pairs), k, k,
            )
            k = max(2, len(annotated_pairs))

        indices = np.arange(len(annotated_pairs))
        kf = KFold(n_splits=k, shuffle=True, random_state=42)

        fold_pearson: List[float] = []
        fold_rmse: List[float] = []

        for train_idx, test_idx in kf.split(indices):
            train_results = [annotated_pairs[i][0] for i in train_idx]
            train_samples = [annotated_pairs[i][1] for i in train_idx]
            test_results = [annotated_pairs[i][0] for i in test_idx]
            test_samples = [annotated_pairs[i][1] for i in test_idx]

            fold_model = ScoringModel(alpha=model.alpha)
            try:
                fold_model.fit(train_results, train_samples)
            except ValueError:
                continue

            preds = fold_model.predict_batch(test_results)
            gt = np.array([s.ground_truth.composite_score for s in test_samples])

            corr = self.compute_model_human_correlation(preds, gt)
            fold_pearson.append(corr["pearson_r"])
            fold_rmse.append(corr["rmse"])

        if not fold_pearson:
            return {
                "fold_scores": [],
                "mean_r": 0.0,
                "std_r": 0.0,
                "mean_rmse": float("inf"),
                "ci_95": (0.0, 0.0),
            }

        mean_r = float(np.mean(fold_pearson))
        std_r = float(np.std(fold_pearson))
        se = std_r / np.sqrt(len(fold_pearson))
        ci_95 = (mean_r - 1.96 * se, mean_r + 1.96 * se)

        return {
            "fold_scores": fold_pearson,
            "mean_r": mean_r,
            "std_r": std_r,
            "mean_rmse": float(np.mean(fold_rmse)),
            "ci_95": ci_95,
        }

    def bootstrap_confidence(
        self,
        predictions: np.ndarray,
        ground_truth: np.ndarray,
        n: int = 1000,
        confidence: float = 0.95,
    ) -> Dict[str, object]:
        """Bootstrap confidence intervals for model-human correlation.

        Args:
            predictions: 1-D array of model predictions.
            ground_truth: 1-D array of human scores.
            n: Number of bootstrap resamples.
            confidence: Confidence level (default 0.95).

        Returns:
            Dict with keys:
                - 'pearson_ci': (lower, upper) CI for Pearson r.
                - 'spearman_ci': (lower, upper) CI for Spearman rho.
                - 'rmse_ci': (lower, upper) CI for RMSE.
                - 'n_resamples': actual number of bootstrap samples used.
        """
        predictions = np.asarray(predictions).ravel()
        ground_truth = np.asarray(ground_truth).ravel()
        m = len(predictions)

        if m < 3:
            return {
                "pearson_ci": (0.0, 0.0),
                "spearman_ci": (0.0, 0.0),
                "rmse_ci": (0.0, 0.0),
                "n_resamples": 0,
            }

        rng = np.random.RandomState(42)
        pearsons: List[float] = []
        spearmans: List[float] = []
        rmses: List[float] = []

        for _ in range(n):
            idx = rng.choice(m, size=m, replace=True)
            p = predictions[idx]
            g = ground_truth[idx]

            if np.std(p) < 1e-10 or np.std(g) < 1e-10:
                continue

            pr, _ = stats.pearsonr(p, g)
            sr, _ = stats.spearmanr(p, g)
            rmse = float(np.sqrt(np.mean((p - g) ** 2)))

            pearsons.append(float(pr))
            spearmans.append(float(sr))
            rmses.append(rmse)

        alpha = (1.0 - confidence) / 2.0

        def _ci(values: List[float]) -> Tuple[float, float]:
            if not values:
                return (0.0, 0.0)
            arr = np.array(values)
            return (
                float(np.percentile(arr, 100 * alpha)),
                float(np.percentile(arr, 100 * (1 - alpha))),
            )

        return {
            "pearson_ci": _ci(pearsons),
            "spearman_ci": _ci(spearmans),
            "rmse_ci": _ci(rmses),
            "n_resamples": len(pearsons),
        }

    # ------------------------------------------------------------------
    # Internal statistics
    # ------------------------------------------------------------------

    @staticmethod
    def _krippendorff_alpha(matrix: np.ndarray) -> float:
        """Compute Krippendorff's alpha for interval data.

        Args:
            matrix: (n_annotators, n_samples) with NaN for missing ratings.

        Returns:
            Alpha coefficient in [-1, 1].
        """
        # Pairs-based computation for interval data
        n_ann, n_samp = matrix.shape
        valid_pairs_within = 0.0
        disagreement_within = 0.0

        for j in range(n_samp):
            ratings = matrix[:, j]
            valid = ratings[~np.isnan(ratings)]
            n_j = len(valid)
            if n_j < 2:
                continue
            for a in range(n_j):
                for b in range(a + 1, n_j):
                    disagreement_within += (valid[a] - valid[b]) ** 2
                    valid_pairs_within += 1

        if valid_pairs_within == 0:
            return 0.0

        # Expected disagreement across all ratings
        all_ratings = matrix[~np.isnan(matrix)]
        n_total = len(all_ratings)
        if n_total < 2:
            return 0.0

        disagreement_expected = 0.0
        n_pairs_total = 0
        for a in range(n_total):
            for b in range(a + 1, n_total):
                disagreement_expected += (all_ratings[a] - all_ratings[b]) ** 2
                n_pairs_total += 1

        if n_pairs_total == 0 or disagreement_expected == 0:
            return 1.0

        d_o = disagreement_within / valid_pairs_within
        d_e = disagreement_expected / n_pairs_total

        return float(1.0 - d_o / d_e)

    @staticmethod
    def _icc(matrix: np.ndarray) -> float:
        """Compute ICC(3,1) - two-way mixed, single measures, consistency.

        Args:
            matrix: (n_annotators, n_samples) with NaN for missing ratings.

        Returns:
            ICC value in [0, 1].
        """
        # Drop samples with any missing ratings for ICC
        valid_cols = ~np.any(np.isnan(matrix), axis=0)
        data = matrix[:, valid_cols]

        if data.shape[1] < 2 or data.shape[0] < 2:
            return 0.0

        k, n = data.shape  # k annotators, n samples
        grand_mean = np.mean(data)
        row_means = np.mean(data, axis=1)
        col_means = np.mean(data, axis=0)

        ss_total = np.sum((data - grand_mean) ** 2)
        ss_rows = n * np.sum((row_means - grand_mean) ** 2)
        ss_cols = k * np.sum((col_means - grand_mean) ** 2)
        ss_error = ss_total - ss_rows - ss_cols

        ms_cols = ss_cols / max(1, n - 1)
        ms_error = ss_error / max(1, (k - 1) * (n - 1))

        if (ms_cols + (k - 1) * ms_error) == 0:
            return 0.0

        icc = (ms_cols - ms_error) / (ms_cols + (k - 1) * ms_error)
        return float(np.clip(icc, 0.0, 1.0))
