#!/usr/bin/env python3
"""
SYNESTHESIA Research - Experiment Runner
=========================================
Systematic experimentation framework for visualization-classification optimization.

Features:
- Parameter grid/random search
- Automated visualization generation
- Classification training and evaluation
- Attention analysis
- Result logging and comparison
"""

import os
import sys
import json
import time
import hashlib
import itertools
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import numpy as np
import warnings

warnings.filterwarnings('ignore')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class VisualizationParams:
    """Parameters controlling visualization generation."""
    # Spiral geometry
    spiral_turns: float = 2.5
    inner_radius: float = 0.15
    outer_radius: float = 0.45
    point_size_min: int = 2
    point_size_max: int = 12

    # Color mapping
    color_mapping: str = "chromesthesia"  # chromesthesia, rainbow, perceptual
    saturation: float = 0.85
    brightness_min: float = 0.3
    brightness_max: float = 1.0

    # Temporal features
    melody_trail_length: int = 20
    melody_trail_decay: float = 0.9
    rhythm_pulse_intensity: float = 0.3
    rhythm_pulse_decay: float = 0.2
    harmony_blend_time: float = 1.0
    atmosphere_window: float = 60.0

    # Amplitude mapping
    amplitude_scale: str = "log"  # linear, log, sqrt
    amplitude_threshold: float = 0.05

    def to_dict(self) -> Dict:
        return asdict(self)

    def get_hash(self) -> str:
        """Get unique hash for this parameter set."""
        return hashlib.md5(json.dumps(self.to_dict(), sort_keys=True).encode()).hexdigest()[:12]


@dataclass
class ClassifierParams:
    """Parameters for the classification model."""
    model_type: str = "SimpleCNN"  # SimpleCNN, ViT, ResNet
    input_size: int = 224
    num_classes: int = 8
    learning_rate: float = 1e-4
    batch_size: int = 32
    epochs: int = 50
    augmentation: bool = True


@dataclass
class ExperimentConfig:
    """Full experiment configuration."""
    experiment_id: str
    visualization_params: VisualizationParams
    classifier_params: ClassifierParams
    dataset_path: str
    output_dir: str
    description: str = ""

    def to_dict(self) -> Dict:
        return {
            "experiment_id": self.experiment_id,
            "visualization_params": self.visualization_params.to_dict(),
            "classifier_params": asdict(self.classifier_params),
            "dataset_path": self.dataset_path,
            "output_dir": self.output_dir,
            "description": self.description
        }


@dataclass
class ExperimentResult:
    """Results from a single experiment."""
    experiment_id: str
    timestamp: str
    duration_seconds: float

    # Classification metrics
    train_accuracy: float = 0.0
    val_accuracy: float = 0.0
    test_accuracy: float = 0.0
    per_class_accuracy: Dict[str, float] = field(default_factory=dict)

    # Attention analysis
    attention_entropy: float = 0.0  # Higher = more distributed attention
    attention_center_ratio: float = 0.0  # Attention on spiral center (low freq)
    attention_edge_ratio: float = 0.0  # Attention on spiral edge (high freq)

    # Feature analysis
    feature_separability: float = 0.0  # Between-class / within-class variance

    # Additional metrics
    confusion_matrix: List[List[int]] = field(default_factory=list)
    training_history: Dict[str, List[float]] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)


class ParameterSearchSpace:
    """Define parameter search spaces for experiments."""

    @staticmethod
    def get_spiral_geometry_space() -> Dict[str, List]:
        """Parameters for spiral geometry experiments."""
        return {
            "spiral_turns": [1.5, 2.0, 2.5, 3.0, 3.5],
            "inner_radius": [0.1, 0.15, 0.2],
            "outer_radius": [0.4, 0.45, 0.5],
        }

    @staticmethod
    def get_color_mapping_space() -> Dict[str, List]:
        """Parameters for color mapping experiments."""
        return {
            "color_mapping": ["chromesthesia", "rainbow", "perceptual"],
            "saturation": [0.7, 0.85, 1.0],
            "brightness_min": [0.2, 0.3, 0.4],
        }

    @staticmethod
    def get_temporal_features_space() -> Dict[str, List]:
        """Parameters for temporal feature experiments."""
        return {
            "melody_trail_length": [10, 20, 30, 50],
            "rhythm_pulse_intensity": [0.2, 0.3, 0.4],
            "harmony_blend_time": [0.5, 1.0, 2.0],
            "atmosphere_window": [30, 60, 120],
        }

    @staticmethod
    def get_amplitude_mapping_space() -> Dict[str, List]:
        """Parameters for amplitude mapping experiments."""
        return {
            "amplitude_scale": ["linear", "log", "sqrt"],
            "amplitude_threshold": [0.01, 0.05, 0.1],
            "point_size_min": [1, 2, 3],
            "point_size_max": [8, 12, 16],
        }

    @staticmethod
    def get_full_search_space() -> Dict[str, List]:
        """Combined parameter space (use with care - many combinations!)."""
        space = {}
        space.update(ParameterSearchSpace.get_spiral_geometry_space())
        space.update(ParameterSearchSpace.get_color_mapping_space())
        space.update(ParameterSearchSpace.get_temporal_features_space())
        space.update(ParameterSearchSpace.get_amplitude_mapping_space())
        return space


class ExperimentRunner:
    """
    Run visualization-classification experiments systematically.
    """

    def __init__(self, base_output_dir: str, dataset_path: str):
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        self.dataset_path = dataset_path

        self.experiments: List[ExperimentConfig] = []
        self.results: List[ExperimentResult] = []

        # Create experiment log
        self.log_path = self.base_output_dir / "experiment_log.json"

    def generate_grid_experiments(self,
                                  param_space: Dict[str, List],
                                  base_params: Optional[VisualizationParams] = None,
                                  max_experiments: int = 100) -> List[ExperimentConfig]:
        """Generate experiments from parameter grid."""
        if base_params is None:
            base_params = VisualizationParams()

        # Get all combinations
        keys = list(param_space.keys())
        values = list(param_space.values())
        combinations = list(itertools.product(*values))

        if len(combinations) > max_experiments:
            print(f"Warning: {len(combinations)} combinations, sampling {max_experiments}")
            indices = np.random.choice(len(combinations), max_experiments, replace=False)
            combinations = [combinations[i] for i in indices]

        experiments = []
        for i, combo in enumerate(combinations):
            # Create params from base + overrides
            params_dict = base_params.to_dict()
            for key, value in zip(keys, combo):
                params_dict[key] = value

            viz_params = VisualizationParams(**params_dict)
            exp_id = f"exp_{viz_params.get_hash()}_{i:04d}"

            config = ExperimentConfig(
                experiment_id=exp_id,
                visualization_params=viz_params,
                classifier_params=ClassifierParams(),
                dataset_path=self.dataset_path,
                output_dir=str(self.base_output_dir / exp_id),
                description=f"Grid search: {dict(zip(keys, combo))}"
            )

            experiments.append(config)

        self.experiments.extend(experiments)
        return experiments

    def generate_random_experiments(self,
                                    param_space: Dict[str, List],
                                    num_experiments: int = 20) -> List[ExperimentConfig]:
        """Generate random experiments from parameter space."""
        experiments = []

        for i in range(num_experiments):
            params_dict = {}
            for key, values in param_space.items():
                params_dict[key] = np.random.choice(values)

            viz_params = VisualizationParams(**params_dict)
            exp_id = f"rand_{viz_params.get_hash()}_{i:04d}"

            config = ExperimentConfig(
                experiment_id=exp_id,
                visualization_params=viz_params,
                classifier_params=ClassifierParams(),
                dataset_path=self.dataset_path,
                output_dir=str(self.base_output_dir / exp_id),
                description=f"Random search #{i}"
            )

            experiments.append(config)

        self.experiments.extend(experiments)
        return experiments

    def run_single_experiment(self, config: ExperimentConfig) -> ExperimentResult:
        """Run a single experiment and return results."""
        print(f"\n{'='*60}")
        print(f"Running experiment: {config.experiment_id}")
        print(f"{'='*60}")

        start_time = time.time()

        # Create output directory
        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save config
        with open(output_dir / "config.json", 'w') as f:
            json.dump(config.to_dict(), f, indent=2)

        try:
            # Step 1: Generate visualizations with these parameters
            print("Step 1: Generating visualizations...")
            viz_dir = output_dir / "visualizations"
            self._generate_visualizations(config, viz_dir)

            # Step 2: Train classifier on visualizations
            print("Step 2: Training classifier...")
            train_result = self._train_classifier(config, viz_dir)

            # Step 3: Analyze attention patterns
            print("Step 3: Analyzing attention...")
            attention_result = self._analyze_attention(config, viz_dir)

            # Step 4: Compute feature separability
            print("Step 4: Computing feature separability...")
            separability = self._compute_separability(config, viz_dir)

            duration = time.time() - start_time

            result = ExperimentResult(
                experiment_id=config.experiment_id,
                timestamp=datetime.now().isoformat(),
                duration_seconds=duration,
                train_accuracy=train_result.get("train_acc", 0),
                val_accuracy=train_result.get("val_acc", 0),
                test_accuracy=train_result.get("test_acc", 0),
                per_class_accuracy=train_result.get("per_class", {}),
                attention_entropy=attention_result.get("entropy", 0),
                attention_center_ratio=attention_result.get("center_ratio", 0),
                attention_edge_ratio=attention_result.get("edge_ratio", 0),
                feature_separability=separability,
                confusion_matrix=train_result.get("confusion_matrix", []),
                training_history=train_result.get("history", {})
            )

        except Exception as e:
            print(f"Error in experiment: {e}")
            duration = time.time() - start_time
            result = ExperimentResult(
                experiment_id=config.experiment_id,
                timestamp=datetime.now().isoformat(),
                duration_seconds=duration,
            )

        # Save result
        with open(output_dir / "result.json", 'w') as f:
            json.dump(result.to_dict(), f, indent=2)

        self.results.append(result)
        return result

    def _generate_visualizations(self, config: ExperimentConfig, output_dir: Path):
        """Generate visualization frames for all samples in dataset."""
        output_dir.mkdir(parents=True, exist_ok=True)

        # Load dataset metadata
        with open(config.dataset_path, 'r') as f:
            dataset = json.load(f)

        # For now, generate a subset for speed
        samples = dataset['samples'][:100]  # Limit for testing

        for sample in samples:
            # Generate single frame visualization
            # (In full implementation, this would use the temporal renderer)
            viz_path = output_dir / f"{sample['sample_id']}.png"

            # Placeholder: Create dummy visualization
            # In real implementation, call the renderer with config.visualization_params
            self._render_sample_visualization(
                sample['file_path'],
                str(viz_path),
                config.visualization_params
            )

    def _render_sample_visualization(self, audio_path: str, output_path: str, params: VisualizationParams):
        """Render a single visualization frame."""
        # Import here to avoid circular imports
        try:
            from spiral_renderer_2d import FastSpiralRenderer, Render2DConfig
            from audio_analyzer import AudioAnalyzer, AudioAnalysisConfig

            # Configure renderer based on params
            render_config = Render2DConfig(
                frame_width=224,
                frame_height=224,
            )

            # Analyze audio
            analyzer = AudioAnalyzer(AudioAnalysisConfig())
            result = analyzer.analyze(audio_path, duration=2.0)

            if result.amplitude_data is not None and len(result.amplitude_data) > 0:
                # Render middle frame
                mid_idx = len(result.amplitude_data) // 2
                renderer = FastSpiralRenderer(render_config)
                renderer.render_frame(
                    result.amplitude_data[mid_idx],
                    result.phase_data[mid_idx] if result.phase_data is not None else None,
                    result.brightness_data[mid_idx] if result.brightness_data is not None else 0.5
                )
                renderer.save_frame(output_path)
            else:
                # Create placeholder
                import PIL.Image as Image
                img = Image.new('RGB', (224, 224), color='black')
                img.save(output_path)

        except Exception as e:
            print(f"  Warning: Could not render {audio_path}: {e}")
            # Create placeholder
            try:
                import PIL.Image as Image
                img = Image.new('RGB', (224, 224), color='black')
                img.save(output_path)
            except:
                pass

    def _train_classifier(self, config: ExperimentConfig, viz_dir: Path) -> Dict:
        """Train classifier on visualizations."""
        # Placeholder implementation
        # In real implementation, this would:
        # 1. Load visualization images
        # 2. Split into train/val/test
        # 3. Train CNN/ViT model
        # 4. Return metrics

        # Simulated results for framework testing
        return {
            "train_acc": np.random.uniform(0.7, 0.95),
            "val_acc": np.random.uniform(0.65, 0.90),
            "test_acc": np.random.uniform(0.60, 0.88),
            "per_class": {},
            "confusion_matrix": [],
            "history": {"loss": [], "accuracy": []}
        }

    def _analyze_attention(self, config: ExperimentConfig, viz_dir: Path) -> Dict:
        """Analyze attention patterns from trained model."""
        # Placeholder implementation
        # In real implementation, this would:
        # 1. Load trained model
        # 2. Generate attention/saliency maps
        # 3. Analyze spatial distribution

        return {
            "entropy": np.random.uniform(0.5, 2.0),
            "center_ratio": np.random.uniform(0.2, 0.6),
            "edge_ratio": np.random.uniform(0.1, 0.4)
        }

    def _compute_separability(self, config: ExperimentConfig, viz_dir: Path) -> float:
        """Compute feature separability metric."""
        # Fisher's discriminant ratio: between-class / within-class variance
        # Placeholder implementation
        return np.random.uniform(0.5, 3.0)

    def run_all_experiments(self, parallel: bool = False) -> List[ExperimentResult]:
        """Run all queued experiments."""
        print(f"\nRunning {len(self.experiments)} experiments...")

        for i, config in enumerate(self.experiments):
            print(f"\n[{i+1}/{len(self.experiments)}]")
            result = self.run_single_experiment(config)
            self._save_log()

        return self.results

    def _save_log(self):
        """Save experiment log."""
        log_data = {
            "num_experiments": len(self.results),
            "last_updated": datetime.now().isoformat(),
            "results": [r.to_dict() for r in self.results]
        }

        with open(self.log_path, 'w') as f:
            json.dump(log_data, f, indent=2)

    def analyze_results(self) -> Dict:
        """Analyze experiment results to find best parameters."""
        if not self.results:
            return {}

        # Sort by test accuracy
        sorted_results = sorted(self.results, key=lambda r: r.test_accuracy, reverse=True)

        analysis = {
            "best_experiment": sorted_results[0].experiment_id,
            "best_accuracy": sorted_results[0].test_accuracy,
            "worst_accuracy": sorted_results[-1].test_accuracy,
            "mean_accuracy": np.mean([r.test_accuracy for r in self.results]),
            "std_accuracy": np.std([r.test_accuracy for r in self.results]),
            "top_5_experiments": [r.experiment_id for r in sorted_results[:5]],
        }

        # Parameter importance analysis
        # (Would correlate params with accuracy in full implementation)

        return analysis

    def generate_report(self, output_file: str = "experiment_report.md"):
        """Generate markdown report of results."""
        analysis = self.analyze_results()

        report = f"""# SYNESTHESIA Experiment Report
Generated: {datetime.now().isoformat()}

## Summary
- Total experiments: {len(self.results)}
- Best accuracy: {analysis.get('best_accuracy', 0):.2%}
- Mean accuracy: {analysis.get('mean_accuracy', 0):.2%}
- Std accuracy: {analysis.get('std_accuracy', 0):.4f}

## Best Experiment
ID: {analysis.get('best_experiment', 'N/A')}

## Top 5 Experiments
"""
        for exp_id in analysis.get('top_5_experiments', []):
            result = next((r for r in self.results if r.experiment_id == exp_id), None)
            if result:
                report += f"- {exp_id}: {result.test_accuracy:.2%}\n"

        report += """
## Recommendations
Based on the experiments, consider:
1. Parameters from top-performing experiments
2. Attention analysis insights
3. Feature separability correlations
"""

        report_path = self.base_output_dir / output_file
        with open(report_path, 'w') as f:
            f.write(report)

        print(f"Report saved to {report_path}")
        return report


def run_quick_study(dataset_path: str, output_dir: str, num_experiments: int = 10):
    """Run a quick parameter study."""
    print("=" * 60)
    print("  SYNESTHESIA Quick Parameter Study")
    print("=" * 60)

    runner = ExperimentRunner(output_dir, dataset_path)

    # Test spiral geometry variations
    print("\nGenerating spiral geometry experiments...")
    space = ParameterSearchSpace.get_spiral_geometry_space()
    runner.generate_random_experiments(space, num_experiments=num_experiments)

    # Run experiments
    runner.run_all_experiments()

    # Analyze and report
    analysis = runner.analyze_results()
    print("\n" + "=" * 60)
    print("  Results Summary")
    print("=" * 60)
    print(f"  Best accuracy: {analysis.get('best_accuracy', 0):.2%}")
    print(f"  Mean accuracy: {analysis.get('mean_accuracy', 0):.2%}")
    print(f"  Best experiment: {analysis.get('best_experiment', 'N/A')}")

    runner.generate_report()

    return runner


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run SYNESTHESIA experiments")
    parser.add_argument("--dataset", "-d", required=True, help="Path to dataset metadata JSON")
    parser.add_argument("--output", "-o", default="./experiments", help="Output directory")
    parser.add_argument("--num", "-n", type=int, default=10, help="Number of experiments")

    args = parser.parse_args()

    run_quick_study(args.dataset, args.output, args.num)
