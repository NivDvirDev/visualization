#!/usr/bin/env python3
"""
SYNESTHESIA Research CLI
========================
Command-line interface for running visualization-classification research.

Usage:
    python research_cli.py build-dataset --output ./data
    python research_cli.py run-study --dataset ./data/metadata.json --output ./experiments
    python research_cli.py analyze --experiments ./experiments
    python research_cli.py full-pipeline --output ./research
"""

import argparse
import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))


def print_banner():
    """Print research banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║   ███████╗██╗   ██╗███╗   ██╗███████╗███████╗████████╗            ║
    ║   ██╔════╝╚██╗ ██╔╝████╗  ██║██╔════╝██╔════╝╚══██╔══╝            ║
    ║   ███████╗ ╚████╔╝ ██╔██╗ ██║█████╗  ███████╗   ██║               ║
    ║   ╚════██║  ╚██╔╝  ██║╚██╗██║██╔══╝  ╚════██║   ██║               ║
    ║   ███████║   ██║   ██║ ╚████║███████╗███████║   ██║               ║
    ║   ╚══════╝   ╚═╝   ╚═╝  ╚═══╝╚══════╝╚══════╝   ╚═╝               ║
    ║                                                                   ║
    ║              HESIA RESEARCH FRAMEWORK                             ║
    ║                                                                   ║
    ║   Visualization → Classification → Analysis → Optimization        ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def cmd_build_dataset(args):
    """Build research dataset."""
    from dataset_builder import build_research_dataset

    print("\n📊 Building Research Dataset")
    print("=" * 50)

    metadata_path = build_research_dataset(
        args.output,
        samples_per_instrument=args.samples,
        num_chord_progressions=args.chords,
        num_rhythm_patterns=args.rhythms
    )

    print(f"\n✅ Dataset built: {metadata_path}")
    return metadata_path


def cmd_run_study(args):
    """Run parameter study experiments."""
    from experiment_runner import ExperimentRunner, ParameterSearchSpace

    print("\n🔬 Running Parameter Study")
    print("=" * 50)

    runner = ExperimentRunner(args.output, args.dataset)

    # Select parameter space
    if args.space == "spiral":
        space = ParameterSearchSpace.get_spiral_geometry_space()
    elif args.space == "color":
        space = ParameterSearchSpace.get_color_mapping_space()
    elif args.space == "temporal":
        space = ParameterSearchSpace.get_temporal_features_space()
    elif args.space == "amplitude":
        space = ParameterSearchSpace.get_amplitude_mapping_space()
    else:
        space = ParameterSearchSpace.get_spiral_geometry_space()

    # Generate experiments
    if args.search == "grid":
        runner.generate_grid_experiments(space, max_experiments=args.num)
    else:
        runner.generate_random_experiments(space, num_experiments=args.num)

    print(f"\nGenerated {len(runner.experiments)} experiments")

    # Run experiments
    runner.run_all_experiments()

    # Generate report
    runner.generate_report()

    print(f"\n✅ Study complete. Results in: {args.output}")


def cmd_analyze(args):
    """Analyze experiment results."""
    from visualization_laws import LawDiscoveryEngine, get_baseline_laws
    import json

    print("\n📈 Analyzing Experiment Results")
    print("=" * 50)

    # Load experiment results
    exp_dir = Path(args.experiments)
    log_file = exp_dir / "experiment_log.json"

    if not log_file.exists():
        print(f"Error: No experiment log found at {log_file}")
        return

    with open(log_file, 'r') as f:
        log_data = json.load(f)

    print(f"Loaded {log_data['num_experiments']} experiments")

    # Initialize law discovery engine
    engine = LawDiscoveryEngine()

    # Add baseline laws
    engine.discovered_laws = get_baseline_laws()

    # Add experiment results
    for result in log_data.get('results', []):
        # Load config for this experiment
        exp_dir_path = exp_dir / result['experiment_id']
        config_file = exp_dir_path / "config.json"

        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
            engine.add_experiment_result(
                config.get('visualization_params', {}),
                result.get('test_accuracy', 0)
            )

    # Discover laws from experiments
    if len(engine.experiment_results) >= 5:
        print("\nDiscovering visualization laws...")
        new_laws = engine.discover_laws()
        print(f"Discovered {len(new_laws)} new laws")

    # Generate report
    report = engine.generate_report()
    report_path = exp_dir / "laws_report.md"
    with open(report_path, 'w') as f:
        f.write(report)

    print(f"\n✅ Analysis complete. Report: {report_path}")

    # Save laws
    laws_path = exp_dir / "discovered_laws.json"
    engine.save_laws(str(laws_path))


def cmd_full_pipeline(args):
    """Run full research pipeline."""
    print("\n🚀 Running Full Research Pipeline")
    print("=" * 50)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Build dataset
    print("\n[Step 1/4] Building dataset...")
    from dataset_builder import build_research_dataset

    data_dir = output_dir / "dataset"
    metadata_path = build_research_dataset(
        str(data_dir),
        samples_per_instrument=args.samples,
        num_chord_progressions=30,
        num_rhythm_patterns=30
    )

    # Step 2: Run spiral geometry experiments
    print("\n[Step 2/4] Running spiral geometry study...")
    from experiment_runner import ExperimentRunner, ParameterSearchSpace

    exp_dir = output_dir / "experiments"
    runner = ExperimentRunner(str(exp_dir), metadata_path)

    space = ParameterSearchSpace.get_spiral_geometry_space()
    runner.generate_random_experiments(space, num_experiments=args.num_experiments)
    runner.run_all_experiments()

    # Step 3: Analyze results
    print("\n[Step 3/4] Analyzing results...")
    from visualization_laws import LawDiscoveryEngine, get_baseline_laws

    engine = LawDiscoveryEngine()
    engine.discovered_laws = get_baseline_laws()

    for result in runner.results:
        exp_config_path = exp_dir / result.experiment_id / "config.json"
        if exp_config_path.exists():
            import json
            with open(exp_config_path, 'r') as f:
                config = json.load(f)
            engine.add_experiment_result(
                config.get('visualization_params', {}),
                result.test_accuracy
            )

    if len(engine.experiment_results) >= 5:
        engine.discover_laws()

    # Step 4: Generate reports
    print("\n[Step 4/4] Generating reports...")

    # Experiment report
    runner.generate_report("experiment_report.md")

    # Laws report
    laws_report = engine.generate_report()
    with open(output_dir / "visualization_laws.md", 'w') as f:
        f.write(laws_report)

    # Save laws
    engine.save_laws(str(output_dir / "discovered_laws.json"))

    # Summary
    analysis = runner.analyze_results()

    summary = f"""
# SYNESTHESIA Research Summary
Generated: {datetime.now().isoformat()}

## Dataset
- Location: {data_dir}
- Metadata: {metadata_path}

## Experiments
- Total experiments: {len(runner.results)}
- Best accuracy: {analysis.get('best_accuracy', 0):.2%}
- Mean accuracy: {analysis.get('mean_accuracy', 0):.2%}
- Best experiment: {analysis.get('best_experiment', 'N/A')}

## Discovered Laws
- Total laws: {len(engine.discovered_laws)}

## Output Files
- experiments/: Individual experiment results
- experiment_report.md: Detailed experiment analysis
- visualization_laws.md: Discovered visualization laws
- discovered_laws.json: Machine-readable laws

## Next Steps
1. Review top-performing visualization parameters
2. Validate discovered laws with new experiments
3. Implement best parameters in SYNESTHESIA 3.0
4. Run classification benchmarks
"""

    with open(output_dir / "SUMMARY.md", 'w') as f:
        f.write(summary)

    print("\n" + "=" * 50)
    print("  ✅ RESEARCH PIPELINE COMPLETE")
    print("=" * 50)
    print(f"\n  Output directory: {output_dir}")
    print(f"  Best accuracy: {analysis.get('best_accuracy', 0):.2%}")
    print(f"  Discovered {len(engine.discovered_laws)} visualization laws")
    print(f"\n  See SUMMARY.md for details")


def cmd_visualize_laws(args):
    """Visualize discovered laws."""
    from visualization_laws import LawDiscoveryEngine

    print("\n📊 Visualizing Laws")
    print("=" * 50)

    engine = LawDiscoveryEngine()
    laws = engine.load_laws(args.laws)

    print(f"Loaded {len(laws)} laws")

    # Print detailed report
    report = engine.generate_report()
    print(report)


def main():
    parser = argparse.ArgumentParser(
        description="SYNESTHESIA Research Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s build-dataset -o ./data -n 100
  %(prog)s run-study -d ./data/metadata.json -o ./experiments --space spiral
  %(prog)s analyze -e ./experiments
  %(prog)s full-pipeline -o ./research --num-experiments 20

Research Workflow:
  1. Build dataset with synthetic audio samples
  2. Run parameter studies to test visualization rules
  3. Analyze results to discover effective laws
  4. Apply best parameters to improve classification
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Build dataset
    build_parser = subparsers.add_parser("build-dataset", help="Build research dataset")
    build_parser.add_argument("-o", "--output", default="./research_dataset",
                             help="Output directory")
    build_parser.add_argument("-n", "--samples", type=int, default=50,
                             help="Samples per instrument")
    build_parser.add_argument("--chords", type=int, default=30,
                             help="Number of chord progressions")
    build_parser.add_argument("--rhythms", type=int, default=30,
                             help="Number of rhythm patterns")

    # Run study
    study_parser = subparsers.add_parser("run-study", help="Run parameter study")
    study_parser.add_argument("-d", "--dataset", required=True,
                             help="Path to dataset metadata")
    study_parser.add_argument("-o", "--output", default="./experiments",
                             help="Output directory")
    study_parser.add_argument("-n", "--num", type=int, default=20,
                             help="Number of experiments")
    study_parser.add_argument("--space", choices=["spiral", "color", "temporal", "amplitude"],
                             default="spiral", help="Parameter space to search")
    study_parser.add_argument("--search", choices=["grid", "random"], default="random",
                             help="Search strategy")

    # Analyze
    analyze_parser = subparsers.add_parser("analyze", help="Analyze experiment results")
    analyze_parser.add_argument("-e", "--experiments", required=True,
                               help="Path to experiments directory")

    # Full pipeline
    full_parser = subparsers.add_parser("full-pipeline", help="Run full research pipeline")
    full_parser.add_argument("-o", "--output", default="./research",
                            help="Output directory")
    full_parser.add_argument("-n", "--num-experiments", type=int, default=15,
                            help="Number of experiments per study")
    full_parser.add_argument("--samples", type=int, default=30,
                            help="Samples per instrument")

    # Visualize laws
    viz_parser = subparsers.add_parser("visualize-laws", help="Visualize discovered laws")
    viz_parser.add_argument("-l", "--laws", required=True,
                           help="Path to laws JSON file")

    args = parser.parse_args()

    print_banner()

    if args.command == "build-dataset":
        cmd_build_dataset(args)
    elif args.command == "run-study":
        cmd_run_study(args)
    elif args.command == "analyze":
        cmd_analyze(args)
    elif args.command == "full-pipeline":
        cmd_full_pipeline(args)
    elif args.command == "visualize-laws":
        cmd_visualize_laws(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
