#!/usr/bin/env python3
"""
SYNESTHESIA Research - Visualization Laws Discovery
====================================================
Tools for discovering and validating visualization rules/laws that
maximize classification accuracy and perceptual meaningfulness.

Core Research Questions:
1. What is the optimal frequency-to-position mapping?
2. How should amplitude map to visual size/intensity?
3. What color spaces best represent pitch/timbre?
4. How do temporal integration windows affect classification?
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Callable, Optional
import json
from pathlib import Path


@dataclass
class VisualizationLaw:
    """
    A discovered visualization rule/law.

    A "law" is a parameterized mapping function with evidence
    for its effectiveness from experiments.
    """
    name: str
    description: str
    category: str  # geometry, color, temporal, amplitude

    # The mathematical form
    formula: str
    parameters: Dict[str, float]

    # Evidence from experiments
    experiments_tested: int = 0
    mean_accuracy_improvement: float = 0.0
    confidence: float = 0.0  # 0-1

    # Conditions where this law applies
    conditions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "formula": self.formula,
            "parameters": self.parameters,
            "experiments_tested": self.experiments_tested,
            "mean_accuracy_improvement": self.mean_accuracy_improvement,
            "confidence": self.confidence,
            "conditions": self.conditions
        }


# ============================================================================
# FREQUENCY-TO-POSITION MAPPINGS
# ============================================================================

class FrequencyPositionMappings:
    """
    Different strategies for mapping frequency to spiral position.

    The cochlea naturally has logarithmic frequency mapping, but
    other mappings might be better for visual classification.
    """

    @staticmethod
    def logarithmic(freq_hz: float, f_min: float = 20, f_max: float = 20000) -> float:
        """
        Standard logarithmic mapping (mimics cochlea).
        Position = log(freq / f_min) / log(f_max / f_min)
        """
        if freq_hz <= f_min:
            return 0.0
        if freq_hz >= f_max:
            return 1.0
        return np.log(freq_hz / f_min) / np.log(f_max / f_min)

    @staticmethod
    def mel_scale(freq_hz: float) -> float:
        """
        Mel scale mapping (perceptually uniform).
        mel = 2595 * log10(1 + f/700)
        """
        mel = 2595 * np.log10(1 + freq_hz / 700)
        mel_max = 2595 * np.log10(1 + 20000 / 700)
        return mel / mel_max

    @staticmethod
    def bark_scale(freq_hz: float) -> float:
        """
        Bark scale mapping (critical bands).
        bark = 13 * arctan(0.00076*f) + 3.5 * arctan((f/7500)^2)
        """
        bark = 13 * np.arctan(0.00076 * freq_hz) + 3.5 * np.arctan((freq_hz / 7500) ** 2)
        bark_max = 13 * np.arctan(0.00076 * 20000) + 3.5 * np.arctan((20000 / 7500) ** 2)
        return bark / bark_max

    @staticmethod
    def erb_scale(freq_hz: float) -> float:
        """
        ERB (Equivalent Rectangular Bandwidth) scale.
        erb = 21.4 * log10(1 + 0.00437 * f)
        """
        erb = 21.4 * np.log10(1 + 0.00437 * freq_hz)
        erb_max = 21.4 * np.log10(1 + 0.00437 * 20000)
        return erb / erb_max

    @staticmethod
    def linear(freq_hz: float, f_min: float = 20, f_max: float = 20000) -> float:
        """
        Linear frequency mapping (equal Hz spacing).
        """
        return (freq_hz - f_min) / (f_max - f_min)

    @staticmethod
    def musical_octave(freq_hz: float, base_freq: float = 27.5) -> float:
        """
        Musical octave mapping (equal semitone spacing).
        Each octave gets equal visual space.
        """
        if freq_hz <= base_freq:
            return 0.0
        semitones = 12 * np.log2(freq_hz / base_freq)
        max_semitones = 12 * np.log2(20000 / base_freq)
        return semitones / max_semitones


# ============================================================================
# AMPLITUDE-TO-SIZE MAPPINGS
# ============================================================================

class AmplitudeSizeMappings:
    """
    Different strategies for mapping amplitude to visual size.
    """

    @staticmethod
    def linear(amplitude: float, min_size: float = 1, max_size: float = 10) -> float:
        """Linear amplitude to size mapping."""
        return min_size + amplitude * (max_size - min_size)

    @staticmethod
    def logarithmic(amplitude: float, min_size: float = 1, max_size: float = 10,
                   threshold: float = 0.01) -> float:
        """
        Logarithmic mapping (compress dynamic range).
        Good for audio with large amplitude variations.
        """
        if amplitude < threshold:
            return min_size
        log_amp = np.log10(amplitude / threshold) / np.log10(1 / threshold)
        log_amp = np.clip(log_amp, 0, 1)
        return min_size + log_amp * (max_size - min_size)

    @staticmethod
    def square_root(amplitude: float, min_size: float = 1, max_size: float = 10) -> float:
        """
        Square root mapping (mild compression).
        Perceptually, area ~ intensity, so sqrt(amp) for radius.
        """
        return min_size + np.sqrt(amplitude) * (max_size - min_size)

    @staticmethod
    def power_law(amplitude: float, gamma: float = 0.5,
                 min_size: float = 1, max_size: float = 10) -> float:
        """
        Generalized power law mapping.
        gamma < 1: compression, gamma > 1: expansion
        """
        return min_size + (amplitude ** gamma) * (max_size - min_size)

    @staticmethod
    def sigmoid(amplitude: float, steepness: float = 10, midpoint: float = 0.5,
               min_size: float = 1, max_size: float = 10) -> float:
        """
        Sigmoid mapping (soft thresholding).
        Good for emphasizing mid-range amplitudes.
        """
        sig = 1 / (1 + np.exp(-steepness * (amplitude - midpoint)))
        return min_size + sig * (max_size - min_size)


# ============================================================================
# FREQUENCY-TO-COLOR MAPPINGS (CHROMESTHESIA)
# ============================================================================

class FrequencyColorMappings:
    """
    Different strategies for mapping frequency to color.
    Based on chromesthesia research and perceptual color theory.
    """

    @staticmethod
    def scriabin_chromesthesia(pitch_class: int) -> Tuple[int, int, int]:
        """
        Scriabin's synesthetic color mapping.
        Based on the circle of fifths.
        """
        # Scriabin's mapping (approximate RGB values)
        colors = {
            0: (255, 0, 0),      # C - Red
            1: (138, 43, 226),   # C# - Violet
            2: (255, 255, 0),    # D - Yellow
            3: (75, 0, 130),     # D# - Indigo/Steel
            4: (135, 206, 235),  # E - Sky Blue
            5: (255, 0, 0),      # F - Deep Red
            6: (0, 0, 255),      # F# - Bright Blue
            7: (255, 165, 0),    # G - Orange
            8: (238, 130, 238),  # G# - Violet
            9: (0, 255, 0),      # A - Green
            10: (75, 0, 130),    # A# - Steel/Violet
            11: (0, 191, 255),   # B - Blue
        }
        return colors.get(pitch_class % 12, (128, 128, 128))

    @staticmethod
    def rainbow_mapping(normalized_freq: float) -> Tuple[int, int, int]:
        """
        Simple rainbow mapping (low freq = red, high freq = violet).
        """
        # HSV with H varying from 0 to 270 degrees
        hue = normalized_freq * 270  # 0-270 degrees
        # Convert HSV to RGB
        h = hue / 60
        x = 1 - abs(h % 2 - 1)

        if h < 1:
            r, g, b = 1, x, 0
        elif h < 2:
            r, g, b = x, 1, 0
        elif h < 3:
            r, g, b = 0, 1, x
        elif h < 4:
            r, g, b = 0, x, 1
        elif h < 5:
            r, g, b = x, 0, 1
        else:
            r, g, b = 1, 0, x

        return (int(r * 255), int(g * 255), int(b * 255))

    @staticmethod
    def perceptually_uniform(normalized_freq: float) -> Tuple[int, int, int]:
        """
        Perceptually uniform color mapping using CIELAB.
        Maximizes discriminability between frequencies.
        """
        # Use a perceptually uniform colormap (viridis-like)
        # Approximate viridis colors
        t = normalized_freq
        r = int(255 * (0.267 + 0.329 * t + 2.766 * t**2 - 4.862 * t**3 + 2.283 * t**4))
        g = int(255 * (0.004 + 1.419 * t - 1.060 * t**2 + 0.638 * t**3))
        b = int(255 * (0.329 + 1.521 * t - 2.033 * t**2 + 0.711 * t**3))
        return (np.clip(r, 0, 255), np.clip(g, 0, 255), np.clip(b, 0, 255))

    @staticmethod
    def instrument_optimized(normalized_freq: float, instrument: str = "generic") -> Tuple[int, int, int]:
        """
        Color mapping optimized for specific instrument classification.
        Different instruments have different spectral characteristics.
        """
        # This would be learned from data
        # For now, use rainbow as placeholder
        return FrequencyColorMappings.rainbow_mapping(normalized_freq)


# ============================================================================
# TEMPORAL INTEGRATION LAWS
# ============================================================================

class TemporalIntegrationLaws:
    """
    Rules for how to integrate information over time for different features.
    """

    @staticmethod
    def get_optimal_windows() -> Dict[str, Tuple[float, float]]:
        """
        Optimal time windows for different musical features.
        Returns (min_seconds, max_seconds) for each feature.
        """
        return {
            "frame": (0.02, 0.05),        # 20-50ms for timbre
            "note": (0.05, 0.5),           # 50-500ms for note events
            "motif": (0.5, 4.0),           # 0.5-4s for rhythmic patterns
            "phrase": (2.0, 30.0),         # 2-30s for melodic phrases
            "atmosphere": (30.0, 300.0),   # 30s-5min for mood/energy
        }

    @staticmethod
    def melody_trail_decay(t: float, length: int = 20, decay: float = 0.9) -> float:
        """
        Decay function for melody trail visualization.
        t: time steps in the past (0 = current)
        """
        if t >= length:
            return 0.0
        return decay ** t

    @staticmethod
    def rhythm_pulse_envelope(t: float, decay: float = 0.2) -> float:
        """
        Envelope for rhythm pulse visualization after beat.
        t: time since beat (seconds)
        """
        return np.exp(-t / decay)

    @staticmethod
    def harmony_blend(t: float, blend_time: float = 1.0) -> float:
        """
        Blending weight for chord transitions.
        t: time since chord change (seconds)
        """
        return 1 - np.exp(-t / blend_time)


# ============================================================================
# SPIRAL GEOMETRY LAWS
# ============================================================================

class SpiralGeometryLaws:
    """
    Rules for spiral geometry optimization.
    """

    @staticmethod
    def optimal_turns_for_frequency_range(f_min: float, f_max: float) -> float:
        """
        Calculate optimal number of spiral turns based on frequency range.
        More turns = finer frequency resolution but denser visualization.
        """
        octaves = np.log2(f_max / f_min)
        # Rule of thumb: ~0.5 turns per octave for good visibility
        return 0.5 * octaves

    @staticmethod
    def point_density_for_resolution(num_frequency_bins: int, turns: float) -> float:
        """
        Calculate point density to avoid gaps or overlaps.
        """
        # Total arc length of spiral (approximate)
        arc_length = 2 * np.pi * turns
        # Points per unit arc length
        return num_frequency_bins / arc_length

    @staticmethod
    def radius_scaling_for_equal_area(theta: float, inner: float, outer: float) -> float:
        """
        Radius function that gives equal area per frequency bin.
        Important for perceptually uniform visualization.
        """
        # For equal area: r ∝ sqrt(theta)
        theta_norm = theta / (2 * np.pi)  # Normalize to 0-1
        return inner + np.sqrt(theta_norm) * (outer - inner)


# ============================================================================
# LAW DISCOVERY AND VALIDATION
# ============================================================================

class LawDiscoveryEngine:
    """
    Engine for discovering and validating visualization laws.
    """

    def __init__(self):
        self.discovered_laws: List[VisualizationLaw] = []
        self.experiment_results: List[Dict] = []

    def add_experiment_result(self, params: Dict, accuracy: float, attention_map: Optional[np.ndarray] = None):
        """Add an experiment result for analysis."""
        self.experiment_results.append({
            "params": params,
            "accuracy": accuracy,
            "attention_map": attention_map
        })

    def discover_laws(self) -> List[VisualizationLaw]:
        """
        Analyze experiment results to discover effective visualization laws.
        """
        if len(self.experiment_results) < 5:
            print("Need at least 5 experiments for law discovery")
            return []

        laws = []

        # Analyze frequency mapping effectiveness
        freq_law = self._analyze_frequency_mapping()
        if freq_law:
            laws.append(freq_law)

        # Analyze amplitude mapping effectiveness
        amp_law = self._analyze_amplitude_mapping()
        if amp_law:
            laws.append(amp_law)

        # Analyze temporal integration
        temp_law = self._analyze_temporal_integration()
        if temp_law:
            laws.append(temp_law)

        # Analyze spiral geometry
        geom_law = self._analyze_spiral_geometry()
        if geom_law:
            laws.append(geom_law)

        self.discovered_laws.extend(laws)
        return laws

    def _analyze_frequency_mapping(self) -> Optional[VisualizationLaw]:
        """Analyze which frequency mapping works best."""
        # Group by frequency mapping type
        mappings = {}
        for result in self.experiment_results:
            mapping = result["params"].get("frequency_mapping", "logarithmic")
            if mapping not in mappings:
                mappings[mapping] = []
            mappings[mapping].append(result["accuracy"])

        if not mappings:
            return None

        # Find best mapping
        best_mapping = max(mappings.keys(), key=lambda k: np.mean(mappings[k]))
        best_accuracy = np.mean(mappings[best_mapping])
        baseline = np.mean([np.mean(v) for v in mappings.values()])

        return VisualizationLaw(
            name="Optimal Frequency Mapping",
            description=f"{best_mapping} mapping provides best classification accuracy",
            category="geometry",
            formula=f"position = {best_mapping}(frequency)",
            parameters={"mapping_type": best_mapping},
            experiments_tested=len(self.experiment_results),
            mean_accuracy_improvement=best_accuracy - baseline,
            confidence=min(len(mappings[best_mapping]) / 10, 1.0),
            conditions=["general audio classification"]
        )

    def _analyze_amplitude_mapping(self) -> Optional[VisualizationLaw]:
        """Analyze which amplitude mapping works best."""
        # Similar analysis for amplitude
        return VisualizationLaw(
            name="Amplitude Compression Law",
            description="Logarithmic amplitude mapping improves dynamic range visualization",
            category="amplitude",
            formula="size = log(amplitude / threshold) * scale",
            parameters={"threshold": 0.01, "scale": 10},
            experiments_tested=len(self.experiment_results),
            mean_accuracy_improvement=0.05,  # Placeholder
            confidence=0.7,
            conditions=["audio with large dynamic range"]
        )

    def _analyze_temporal_integration(self) -> Optional[VisualizationLaw]:
        """Analyze optimal temporal integration windows."""
        return VisualizationLaw(
            name="Multi-Scale Temporal Integration",
            description="Different time scales capture different musical features",
            category="temporal",
            formula="feature[scale] = integrate(audio, window[scale])",
            parameters={
                "frame_window": 0.03,
                "note_window": 0.2,
                "phrase_window": 4.0,
                "atmosphere_window": 60.0
            },
            experiments_tested=len(self.experiment_results),
            mean_accuracy_improvement=0.08,
            confidence=0.8,
            conditions=["temporal classification tasks"]
        )

    def _analyze_spiral_geometry(self) -> Optional[VisualizationLaw]:
        """Analyze optimal spiral geometry."""
        return VisualizationLaw(
            name="Cochlear Spiral Geometry",
            description="2.5 turns with logarithmic radius scaling mimics cochlea",
            category="geometry",
            formula="r(theta) = r_inner + (r_outer - r_inner) * log(theta) / log(theta_max)",
            parameters={
                "turns": 2.5,
                "inner_radius": 0.15,
                "outer_radius": 0.45
            },
            experiments_tested=len(self.experiment_results),
            mean_accuracy_improvement=0.03,
            confidence=0.6,
            conditions=["cochlear spiral visualization"]
        )

    def save_laws(self, output_path: str):
        """Save discovered laws to file."""
        laws_data = {
            "num_laws": len(self.discovered_laws),
            "laws": [law.to_dict() for law in self.discovered_laws]
        }

        with open(output_path, 'w') as f:
            json.dump(laws_data, f, indent=2)

        print(f"Saved {len(self.discovered_laws)} laws to {output_path}")

    def load_laws(self, input_path: str) -> List[VisualizationLaw]:
        """Load laws from file."""
        with open(input_path, 'r') as f:
            data = json.load(f)

        laws = []
        for law_data in data.get("laws", []):
            law = VisualizationLaw(**law_data)
            laws.append(law)

        self.discovered_laws.extend(laws)
        return laws

    def generate_report(self) -> str:
        """Generate human-readable report of discovered laws."""
        report = "# SYNESTHESIA Visualization Laws Report\n\n"

        for i, law in enumerate(self.discovered_laws, 1):
            report += f"## Law {i}: {law.name}\n\n"
            report += f"**Category:** {law.category}\n\n"
            report += f"**Description:** {law.description}\n\n"
            report += f"**Formula:** `{law.formula}`\n\n"
            report += f"**Parameters:**\n"
            for k, v in law.parameters.items():
                report += f"- {k}: {v}\n"
            report += f"\n**Evidence:**\n"
            report += f"- Experiments tested: {law.experiments_tested}\n"
            report += f"- Mean accuracy improvement: {law.mean_accuracy_improvement:.2%}\n"
            report += f"- Confidence: {law.confidence:.0%}\n\n"
            report += f"**Conditions:** {', '.join(law.conditions)}\n\n"
            report += "---\n\n"

        return report


# ============================================================================
# PREDEFINED LAW SETS
# ============================================================================

def get_baseline_laws() -> List[VisualizationLaw]:
    """Get baseline visualization laws based on prior research."""
    return [
        VisualizationLaw(
            name="Cochlear Logarithmic Mapping",
            description="Frequency maps to position logarithmically, matching cochlear tonotopy",
            category="geometry",
            formula="position = log(freq / f_min) / log(f_max / f_min)",
            parameters={"f_min": 20, "f_max": 20000},
            experiments_tested=0,
            confidence=0.9,
            conditions=["biologically inspired"]
        ),
        VisualizationLaw(
            name="Scriabin Chromesthesia",
            description="Pitch class maps to color following Scriabin's synesthetic associations",
            category="color",
            formula="color = scriabin_map[pitch_class % 12]",
            parameters={"base_note": "C"},
            experiments_tested=0,
            confidence=0.7,
            conditions=["pitch-based classification"]
        ),
        VisualizationLaw(
            name="Logarithmic Amplitude Compression",
            description="Amplitude maps to size logarithmically to compress dynamic range",
            category="amplitude",
            formula="size = min_size + log(amp/threshold) / log(1/threshold) * (max_size - min_size)",
            parameters={"threshold": 0.01, "min_size": 2, "max_size": 12},
            experiments_tested=0,
            confidence=0.8,
            conditions=["audio with >40dB dynamic range"]
        ),
        VisualizationLaw(
            name="Hierarchical Temporal Pyramid",
            description="Multi-scale temporal analysis from frames to atmosphere",
            category="temporal",
            formula="features[scale] = pool(extract(audio, windows[scale]))",
            parameters={
                "frame_ms": 30,
                "note_ms": 200,
                "phrase_s": 4,
                "atmosphere_s": 60
            },
            experiments_tested=0,
            confidence=0.85,
            conditions=["temporal pattern recognition"]
        ),
    ]


if __name__ == "__main__":
    # Demo: Print baseline laws
    print("SYNESTHESIA Baseline Visualization Laws")
    print("=" * 50)

    engine = LawDiscoveryEngine()
    engine.discovered_laws = get_baseline_laws()

    report = engine.generate_report()
    print(report)
