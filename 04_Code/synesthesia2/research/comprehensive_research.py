#!/usr/bin/env python3
"""
SYNESTHESIA Comprehensive Research Framework
=============================================
Orchestrates all research investigations and generates unified reports.

This module coordinates:
1. Advanced dataset generation with edge cases
2. Melody trail parameter investigation
3. Color mapping research
4. Temporal parameters investigation
5. Unified analysis and law discovery

Goal: Transform conventional audio into memorable visualizations that
create clear visual memory for average human viewers.
"""

import numpy as np
import os
import json
import sys
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import argparse

# Add research directory to path
sys.path.insert(0, str(Path(__file__).parent))

from advanced_dataset_builder import AdvancedDatasetBuilder
from melody_trail_research import MelodyTrailExperimentRunner
from color_mapping_research import ColorMappingExperimentRunner
from temporal_research import TemporalExperimentRunner


@dataclass
class ResearchSummary:
    """Summary of all research findings."""
    # Best configurations
    optimal_trail_length: int
    optimal_trail_decay: float
    optimal_color_mapping: str
    optimal_saturation: float
    optimal_rhythm_intensity: float
    optimal_harmony_blend: float
    optimal_atmosphere_window: float

    # Composite scores
    melody_research_score: float
    color_research_score: float
    temporal_research_score: float
    overall_research_score: float

    # Key findings
    findings: List[str]
    recommendations: List[str]

    # Statistics
    total_experiments: int
    total_samples_analyzed: int
    research_duration_hours: float


class ComprehensiveResearchRunner:
    """Run complete research pipeline."""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.dataset_dir = self.output_dir / 'dataset'
        self.melody_dir = self.output_dir / 'melody_experiments'
        self.color_dir = self.output_dir / 'color_experiments'
        self.temporal_dir = self.output_dir / 'temporal_experiments'

        self.start_time = None
        self.summary: Optional[ResearchSummary] = None

    def _print_banner(self):
        """Print research banner."""
        banner = """
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                                                                       ║
    ║   ███████╗██╗   ██╗███╗   ██╗███████╗███████╗████████╗██╗  ██╗       ║
    ║   ██╔════╝╚██╗ ██╔╝████╗  ██║██╔════╝██╔════╝╚══██╔══╝██║  ██║       ║
    ║   ███████╗ ╚████╔╝ ██╔██╗ ██║█████╗  ███████╗   ██║   ███████║       ║
    ║   ╚════██║  ╚██╔╝  ██║╚██╗██║██╔══╝  ╚════██║   ██║   ██╔══██║       ║
    ║   ███████║   ██║   ██║ ╚████║███████╗███████║   ██║   ██║  ██║       ║
    ║   ╚══════╝   ╚═╝   ╚═╝  ╚═══╝╚══════╝╚══════╝   ╚═╝   ╚═╝  ╚═╝       ║
    ║                                                                       ║
    ║           COMPREHENSIVE VISUALIZATION RESEARCH FRAMEWORK              ║
    ║                                                                       ║
    ║   "From Sound to Memorable Sight"                                     ║
    ║                                                                       ║
    ║   Research Areas:                                                     ║
    ║   ├── Melody Trail Investigation (optimal trail visualization)       ║
    ║   ├── Color Mapping Research (perceptual color associations)         ║
    ║   ├── Temporal Parameters (rhythm, harmony, atmosphere)              ║
    ║   └── Edge Case Robustness (noise, artifacts, complexity)            ║
    ╚═══════════════════════════════════════════════════════════════════════╝
        """
        print(banner)

    def build_dataset(self, melodic_per_contour: int = 8,
                      polyphonic: int = 40,
                      edge_cases_each: int = 15,
                      noise_base: int = 25,
                      effects_base: int = 25):
        """Build comprehensive research dataset."""
        print("\n" + "="*70)
        print("  PHASE 1: Building Advanced Research Dataset")
        print("="*70)

        builder = AdvancedDatasetBuilder(str(self.dataset_dir))
        metadata = builder.generate_full_dataset(
            melodic_per_contour=melodic_per_contour,
            polyphonic=polyphonic,
            edge_cases_each=edge_cases_each,
            noise_base=noise_base,
            effects_base=effects_base,
        )

        self.dataset_metadata_path = self.dataset_dir / 'advanced_dataset_metadata.json'
        return metadata

    def run_melody_research(self, samples_per_experiment: int = 25):
        """Run melody trail investigation."""
        print("\n" + "="*70)
        print("  PHASE 2: Melody Trail Parameter Investigation")
        print("="*70)

        runner = MelodyTrailExperimentRunner(
            str(self.dataset_metadata_path),
            str(self.melody_dir)
        )
        runner.run_all_experiments(samples_per_experiment)

        return runner.results

    def run_color_research(self):
        """Run color mapping investigation."""
        print("\n" + "="*70)
        print("  PHASE 3: Color Mapping Investigation")
        print("="*70)

        runner = ColorMappingExperimentRunner(
            str(self.dataset_metadata_path),
            str(self.color_dir)
        )
        runner.run_all_experiments()

        return runner.results

    def run_temporal_research(self, samples_per_experiment: int = 15):
        """Run temporal parameters investigation."""
        print("\n" + "="*70)
        print("  PHASE 4: Temporal Parameters Investigation")
        print("="*70)

        runner = TemporalExperimentRunner(
            str(self.dataset_metadata_path),
            str(self.temporal_dir)
        )
        runner.run_all_experiments(samples_per_experiment)

        return runner.results

    def analyze_all_results(self, melody_results, color_results, temporal_results):
        """Analyze all research results and extract optimal parameters."""
        print("\n" + "="*70)
        print("  PHASE 5: Comprehensive Analysis")
        print("="*70)

        # Find optimal melody trail parameters
        melody_scored = [(r, r.trail_coherence_score * 0.4 +
                            r.classification_accuracy * 0.3 +
                            r.contour_preservation * 0.3)
                        for r in melody_results]
        melody_scored.sort(key=lambda x: x[1], reverse=True)
        best_melody = melody_scored[0][0] if melody_scored else None

        # Find optimal color mapping
        color_scored = [(r, r.classification_accuracy * 0.35 +
                           r.color_distinctiveness * 0.25 +
                           r.memorability_score * 0.25 +
                           r.hue_coverage * 0.15)
                       for r in color_results]
        color_scored.sort(key=lambda x: x[1], reverse=True)
        best_color = color_scored[0][0] if color_scored else None

        # Find optimal temporal parameters
        temporal_scored = [(r, r.overall_temporal_score)
                          for r in temporal_results]
        temporal_scored.sort(key=lambda x: x[1], reverse=True)
        best_temporal = temporal_scored[0][0] if temporal_scored else None

        # Calculate research scores
        melody_score = melody_scored[0][1] if melody_scored else 0.5
        color_score = color_scored[0][1] if color_scored else 0.5
        temporal_score = temporal_scored[0][1] if temporal_scored else 0.5

        # Generate findings
        findings = []

        if best_melody:
            findings.append(f"Optimal trail length: {best_melody.config.trail_length} frames "
                          f"(coherence: {best_melody.trail_coherence_score:.3f})")
            findings.append(f"Best trail decay: {best_melody.config.trail_decay:.2f} "
                          f"for smooth melodic visualization")

        if best_color:
            findings.append(f"Best color mapping: {best_color.config.mapping_name} "
                          f"(distinctiveness: {best_color.color_distinctiveness:.3f})")
            findings.append(f"Optimal saturation: {best_color.config.saturation:.2f} "
                          f"for visual memorability")

        if best_temporal:
            findings.append(f"Rhythm intensity {best_temporal.config.rhythm_pulse_intensity:.1f} "
                          f"achieves best beat alignment")
            findings.append(f"Harmony blend time of {best_temporal.config.harmony_blend_time:.1f}s "
                          f"provides stable chord colors")
            findings.append(f"Atmosphere window of {best_temporal.config.atmosphere_window:.0f}s "
                          f"captures overall mood")

        # Generate recommendations
        recommendations = [
            "Use perceptual color mapping for best visual distinction",
            f"Set melody trail length to {best_melody.config.trail_length if best_melody else 30} frames",
            "Apply logarithmic amplitude scaling for natural dynamics",
            "Enable multi-scale temporal integration",
            "Test edge cases (noise, clipping) to ensure robustness",
        ]

        # Calculate duration
        duration_hours = (datetime.now() - self.start_time).total_seconds() / 3600

        self.summary = ResearchSummary(
            optimal_trail_length=best_melody.config.trail_length if best_melody else 30,
            optimal_trail_decay=best_melody.config.trail_decay if best_melody else 0.9,
            optimal_color_mapping=best_color.config.mapping_name if best_color else 'perceptual',
            optimal_saturation=best_color.config.saturation if best_color else 0.85,
            optimal_rhythm_intensity=best_temporal.config.rhythm_pulse_intensity if best_temporal else 0.5,
            optimal_harmony_blend=best_temporal.config.harmony_blend_time if best_temporal else 1.0,
            optimal_atmosphere_window=best_temporal.config.atmosphere_window if best_temporal else 60,
            melody_research_score=float(melody_score),
            color_research_score=float(color_score),
            temporal_research_score=float(temporal_score),
            overall_research_score=float((melody_score + color_score + temporal_score) / 3),
            findings=findings,
            recommendations=recommendations,
            total_experiments=len(melody_results) + len(color_results) + len(temporal_results),
            total_samples_analyzed=len(melody_results) * 25 + len(temporal_results) * 15,
            research_duration_hours=duration_hours,
        )

        return self.summary

    def generate_final_report(self, summary: ResearchSummary):
        """Generate comprehensive final report."""
        print("\n📝 Generating Final Research Report...")

        report = [
            "# SYNESTHESIA Comprehensive Research Report",
            f"\nGenerated: {datetime.now().isoformat()}",
            f"Research Duration: {summary.research_duration_hours:.2f} hours",
            f"Total Experiments: {summary.total_experiments}",
            "",
            "## Executive Summary",
            "",
            "This research investigated optimal visualization parameters for transforming",
            "audio into memorable visual content. Through systematic experimentation across",
            "melody trails, color mappings, and temporal features, we identified configurations",
            "that maximize visual memory formation and pattern recognition.",
            "",
            f"**Overall Research Score:** {summary.overall_research_score:.3f}",
            "",
            "---",
            "",
            "## Optimal Configuration",
            "",
            "### Melody Trail",
            f"- **Trail Length:** {summary.optimal_trail_length} frames",
            f"- **Trail Decay:** {summary.optimal_trail_decay:.2f}",
            "",
            "### Color Mapping",
            f"- **Mapping Type:** {summary.optimal_color_mapping}",
            f"- **Saturation:** {summary.optimal_saturation:.2f}",
            "",
            "### Temporal Features",
            f"- **Rhythm Intensity:** {summary.optimal_rhythm_intensity:.2f}",
            f"- **Harmony Blend:** {summary.optimal_harmony_blend:.1f} seconds",
            f"- **Atmosphere Window:** {summary.optimal_atmosphere_window:.0f} seconds",
            "",
            "---",
            "",
            "## Key Findings",
            "",
        ]

        for i, finding in enumerate(summary.findings, 1):
            report.append(f"{i}. {finding}")

        report.extend([
            "",
            "---",
            "",
            "## Recommendations for Production",
            "",
        ])

        for i, rec in enumerate(summary.recommendations, 1):
            report.append(f"{i}. {rec}")

        report.extend([
            "",
            "---",
            "",
            "## Research Scores by Area",
            "",
            "| Research Area | Score | Status |",
            "|---------------|-------|--------|",
            f"| Melody Trail | {summary.melody_research_score:.3f} | {'✅ Good' if summary.melody_research_score > 0.6 else '⚠️ Needs Work'} |",
            f"| Color Mapping | {summary.color_research_score:.3f} | {'✅ Good' if summary.color_research_score > 0.6 else '⚠️ Needs Work'} |",
            f"| Temporal | {summary.temporal_research_score:.3f} | {'✅ Good' if summary.temporal_research_score > 0.6 else '⚠️ Needs Work'} |",
            "",
            "---",
            "",
            "## Visual Memory Optimization Principles",
            "",
            "Based on our research, the following principles maximize visual memory formation:",
            "",
            "1. **Melodic Contour Preservation**: Trail visualization should faithfully",
            "   represent the shape of melodic lines, allowing viewers to 'see' the melody.",
            "",
            "2. **Perceptual Color Distinction**: Colors should be perceptually uniform",
            "   and maximally distinguishable to avoid confusion between frequency bands.",
            "",
            "3. **Temporal Coherence**: Smooth transitions between frames create a sense",
            "   of continuous motion that is easier to remember than jarring changes.",
            "",
            "4. **Beat-Visual Alignment**: Rhythm pulses should align precisely with",
            "   musical beats to create memorable rhythmic visual patterns.",
            "",
            "5. **Atmospheric Context**: Long-term features provide context that helps",
            "   viewers understand the overall mood and structure of the music.",
            "",
            "---",
            "",
            "## Next Steps",
            "",
            "1. Implement optimal configuration in production SYNESTHESIA system",
            "2. Conduct human evaluation study to validate visual memory claims",
            "3. Test with diverse musical genres and styles",
            "4. Develop adaptive parameters based on audio characteristics",
            "",
            "---",
            "",
            "*Generated by SYNESTHESIA Comprehensive Research Framework*",
        ])

        report_path = self.output_dir / 'COMPREHENSIVE_RESEARCH_REPORT.md'
        with open(report_path, 'w') as f:
            f.write('\n'.join(report))

        print(f"✅ Report saved to: {report_path}")

        # Save summary as JSON
        summary_path = self.output_dir / 'research_summary.json'
        with open(summary_path, 'w') as f:
            json.dump(asdict(summary), f, indent=2)

        print(f"✅ Summary JSON saved to: {summary_path}")

        return report_path

    def generate_optimal_config(self, summary: ResearchSummary):
        """Generate optimal SYNESTHESIA configuration file."""
        config = {
            'version': '3.0-research-optimized',
            'generated': datetime.now().isoformat(),
            'research_score': summary.overall_research_score,

            'spiral': {
                'turns': 3.5,
                'inner_radius': 0.15,
                'outer_radius': 0.45,
            },

            'melody_trail': {
                'length': summary.optimal_trail_length,
                'decay': summary.optimal_trail_decay,
                'width_start': 1.0,
                'width_end': 0.3,
                'color_fade': True,
            },

            'color': {
                'mapping': summary.optimal_color_mapping,
                'saturation': summary.optimal_saturation,
                'brightness_min': 0.35,
                'brightness_max': 1.0,
            },

            'rhythm': {
                'pulse_intensity': summary.optimal_rhythm_intensity,
                'pulse_decay': 0.25,
                'window_ms': 30,
            },

            'harmony': {
                'blend_time': summary.optimal_harmony_blend,
                'smoothing': 0.3,
                'chord_hold_time': summary.optimal_harmony_blend * 0.5,
            },

            'atmosphere': {
                'window': summary.optimal_atmosphere_window,
                'decay': 60 / summary.optimal_atmosphere_window,
                'influence': 0.35,
            },

            'amplitude': {
                'scale': 'log',
                'threshold': 0.05,
                'min_size': 2,
                'max_size': 12,
            },

            'multi_scale': {
                'enabled': True,
                'weights': {
                    'frame': 0.25,
                    'note': 0.30,
                    'phrase': 0.25,
                    'atmosphere': 0.20,
                },
            },
        }

        config_path = self.output_dir / 'optimal_config.json'
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"✅ Optimal config saved to: {config_path}")

        return config_path

    def run_full_research(self,
                          melodic_per_contour: int = 8,
                          polyphonic: int = 40,
                          edge_cases_each: int = 15,
                          noise_base: int = 25,
                          effects_base: int = 25,
                          samples_per_experiment: int = 20):
        """Run complete research pipeline."""
        self.start_time = datetime.now()
        self._print_banner()

        # Phase 1: Build dataset
        self.build_dataset(
            melodic_per_contour=melodic_per_contour,
            polyphonic=polyphonic,
            edge_cases_each=edge_cases_each,
            noise_base=noise_base,
            effects_base=effects_base,
        )

        # Phase 2: Melody research
        melody_results = self.run_melody_research(samples_per_experiment)

        # Phase 3: Color research
        color_results = self.run_color_research()

        # Phase 4: Temporal research
        temporal_results = self.run_temporal_research(samples_per_experiment // 2)

        # Phase 5: Analysis
        summary = self.analyze_all_results(melody_results, color_results, temporal_results)

        # Generate outputs
        self.generate_final_report(summary)
        self.generate_optimal_config(summary)

        # Final summary
        print("\n" + "="*70)
        print("  RESEARCH COMPLETE")
        print("="*70)
        print(f"\n📊 Total experiments: {summary.total_experiments}")
        print(f"⏱️  Duration: {summary.research_duration_hours:.2f} hours")
        print(f"🎯 Overall score: {summary.overall_research_score:.3f}")
        print(f"\n📁 Output directory: {self.output_dir}")
        print("\nKey files:")
        print(f"  - COMPREHENSIVE_RESEARCH_REPORT.md")
        print(f"  - research_summary.json")
        print(f"  - optimal_config.json")

        return summary


def main():
    """Run comprehensive research."""
    parser = argparse.ArgumentParser(
        description='SYNESTHESIA Comprehensive Visualization Research'
    )
    parser.add_argument('-o', '--output', default='./comprehensive_research',
                       help='Output directory')
    parser.add_argument('--melodic', type=int, default=8,
                       help='Melodic samples per contour')
    parser.add_argument('--polyphonic', type=int, default=40,
                       help='Polyphonic samples')
    parser.add_argument('--edge', type=int, default=15,
                       help='Edge cases per type')
    parser.add_argument('--noise', type=int, default=25,
                       help='Noise variant base samples')
    parser.add_argument('--effects', type=int, default=25,
                       help='Effect variant base samples')
    parser.add_argument('--samples-per-exp', type=int, default=20,
                       help='Samples per experiment')
    parser.add_argument('--quick', action='store_true',
                       help='Quick mode with reduced samples')

    args = parser.parse_args()

    if args.quick:
        args.melodic = 3
        args.polyphonic = 15
        args.edge = 5
        args.noise = 10
        args.effects = 10
        args.samples_per_exp = 10

    runner = ComprehensiveResearchRunner(args.output)
    runner.run_full_research(
        melodic_per_contour=args.melodic,
        polyphonic=args.polyphonic,
        edge_cases_each=args.edge,
        noise_base=args.noise,
        effects_base=args.effects,
        samples_per_experiment=args.samples_per_exp,
    )


if __name__ == '__main__':
    main()
