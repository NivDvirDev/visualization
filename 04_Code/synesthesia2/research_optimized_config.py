#!/usr/bin/env python3
"""
SYNESTHESIA 3.0 - Research-Optimized Configuration
===================================================
Configuration parameters derived from comprehensive research:
- 1,704 audio samples analyzed
- 210 experiments conducted
- 90 melody trail experiments
- 96 color mapping experiments
- 24 temporal parameter experiments

Research Score: 0.869
Date: January 2026
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any


@dataclass
class ResearchOptimizedConfig:
    """
    Research-optimized visualization parameters.

    These values were determined through systematic experimentation
    to maximize visual memory formation and pattern recognition.
    """

    # === SPIRAL GEOMETRY ===
    # Based on cochlear tonotopy research
    spiral_turns: float = 3.5
    spiral_inner_radius: float = 0.15
    spiral_outer_radius: float = 0.45

    # === MELODY TRAIL (Score: 0.925) ===
    # Optimal: L=10, D=0.70, Style=glow
    # Research finding: Shorter trails with fast decay create crisp visuals
    trail_length_frames: int = 10  # Was 90 (3s @ 30fps)
    trail_decay_rate: float = 0.70  # Was 0.92 - faster decay
    trail_glow_radius: int = 10
    trail_width_start: float = 1.0
    trail_width_end: float = 0.3
    trail_color_fade: bool = True
    trail_style: str = "glow"  # solid, gradient, glow

    # === COLOR MAPPING (Score: 0.996) ===
    # Rainbow with high saturation performed best
    color_mapping: str = "rainbow"  # scriabin, rainbow, mel_rainbow, perceptual
    color_saturation: float = 0.95  # Was 0.85 - higher saturation
    color_brightness_min: float = 0.35
    color_brightness_max: float = 1.0
    use_amplitude_brightness: bool = True

    # === RHYTHM PULSE (Score: 0.685) ===
    # Moderate intensity for balanced beat visualization
    rhythm_pulse_intensity: float = 0.5  # Was variable
    rhythm_pulse_decay: float = 0.25
    rhythm_window_ms: float = 30.0
    pulse_scale_amount: float = 0.12
    pulse_brightness_amount: float = 0.25

    # === HARMONY (Score: 0.685) ===
    # Longer blend time for stable chord colors
    harmony_blend_time: float = 4.0  # Was 1.0 - smoother transitions
    harmony_smoothing: float = 0.3
    chord_hold_time: float = 2.0
    aura_saturation: float = 0.4
    aura_brightness: float = 0.15
    aura_transition_speed: float = 0.05  # Slower for stability

    # === ATMOSPHERE ===
    # 60-second window captures overall mood effectively
    atmosphere_window: float = 60.0
    atmosphere_decay: float = 1.0
    atmosphere_influence: float = 0.35
    atmosphere_particle_density: float = 0.3

    # === AMPLITUDE MAPPING ===
    # Logarithmic scaling for natural perception
    amplitude_scale: str = "log"  # linear, log, sqrt, sigmoid
    amplitude_threshold: float = 0.05
    amplitude_min_size: int = 2
    amplitude_max_size: int = 12

    # === MULTI-SCALE TEMPORAL ===
    # Balanced weights across temporal scales
    multi_scale_enabled: bool = True
    weight_frame: float = 0.25
    weight_note: float = 0.30
    weight_phrase: float = 0.25
    weight_atmosphere: float = 0.20

    @classmethod
    def load_from_json(cls, json_path: str) -> 'ResearchOptimizedConfig':
        """Load configuration from research output JSON."""
        with open(json_path, 'r') as f:
            data = json.load(f)

        config = cls()

        # Map JSON structure to config
        if 'spiral' in data:
            config.spiral_turns = data['spiral'].get('turns', config.spiral_turns)
            config.spiral_inner_radius = data['spiral'].get('inner_radius', config.spiral_inner_radius)
            config.spiral_outer_radius = data['spiral'].get('outer_radius', config.spiral_outer_radius)

        if 'melody_trail' in data:
            config.trail_length_frames = data['melody_trail'].get('length', config.trail_length_frames)
            config.trail_decay_rate = data['melody_trail'].get('decay', config.trail_decay_rate)
            config.trail_width_start = data['melody_trail'].get('width_start', config.trail_width_start)
            config.trail_width_end = data['melody_trail'].get('width_end', config.trail_width_end)
            config.trail_color_fade = data['melody_trail'].get('color_fade', config.trail_color_fade)

        if 'color' in data:
            config.color_mapping = data['color'].get('mapping', config.color_mapping)
            config.color_saturation = data['color'].get('saturation', config.color_saturation)
            config.color_brightness_min = data['color'].get('brightness_min', config.color_brightness_min)
            config.color_brightness_max = data['color'].get('brightness_max', config.color_brightness_max)

        if 'rhythm' in data:
            config.rhythm_pulse_intensity = data['rhythm'].get('pulse_intensity', config.rhythm_pulse_intensity)
            config.rhythm_pulse_decay = data['rhythm'].get('pulse_decay', config.rhythm_pulse_decay)
            config.rhythm_window_ms = data['rhythm'].get('window_ms', config.rhythm_window_ms)

        if 'harmony' in data:
            config.harmony_blend_time = data['harmony'].get('blend_time', config.harmony_blend_time)
            config.harmony_smoothing = data['harmony'].get('smoothing', config.harmony_smoothing)
            config.chord_hold_time = data['harmony'].get('chord_hold_time', config.chord_hold_time)

        if 'atmosphere' in data:
            config.atmosphere_window = data['atmosphere'].get('window', config.atmosphere_window)
            config.atmosphere_decay = data['atmosphere'].get('decay', config.atmosphere_decay)
            config.atmosphere_influence = data['atmosphere'].get('influence', config.atmosphere_influence)

        if 'amplitude' in data:
            config.amplitude_scale = data['amplitude'].get('scale', config.amplitude_scale)
            config.amplitude_threshold = data['amplitude'].get('threshold', config.amplitude_threshold)
            config.amplitude_min_size = data['amplitude'].get('min_size', config.amplitude_min_size)
            config.amplitude_max_size = data['amplitude'].get('max_size', config.amplitude_max_size)

        if 'multi_scale' in data:
            config.multi_scale_enabled = data['multi_scale'].get('enabled', config.multi_scale_enabled)
            weights = data['multi_scale'].get('weights', {})
            config.weight_frame = weights.get('frame', config.weight_frame)
            config.weight_note = weights.get('note', config.weight_note)
            config.weight_phrase = weights.get('phrase', config.weight_phrase)
            config.weight_atmosphere = weights.get('atmosphere', config.weight_atmosphere)

        return config

    def to_temporal_render_config(self) -> Dict[str, Any]:
        """Convert to TemporalRenderConfig parameters."""
        return {
            'num_turns': self.spiral_turns,
            'trail_duration_seconds': self.trail_length_frames / 30.0,  # Assume 30fps
            'trail_decay_rate': self.trail_decay_rate,
            'trail_glow_radius': self.trail_glow_radius,
            'pulse_scale_amount': self.pulse_scale_amount,
            'pulse_brightness_amount': self.pulse_brightness_amount,
            'pulse_decay_rate': 1.0 - self.rhythm_pulse_decay,
            'aura_transition_speed': self.aura_transition_speed,
            'aura_saturation': self.aura_saturation,
            'aura_brightness': self.aura_brightness,
            'atmosphere_particle_density': self.atmosphere_particle_density,
        }

    def get_color_mapper(self):
        """Get the appropriate color mapping function based on config."""
        from research.color_mapping_research import ColorMappings

        mappers = {
            'scriabin': ColorMappings.scriabin_chromesthesia,
            'rainbow': ColorMappings.rainbow_linear,
            'mel_rainbow': ColorMappings.mel_rainbow,
            'perceptual': ColorMappings.perceptual_uniform,
            'categorical': ColorMappings.categorical_bands,
            'harmonic': ColorMappings.harmonic_colors,
        }

        return mappers.get(self.color_mapping, ColorMappings.rainbow_linear)


def get_default_research_config() -> ResearchOptimizedConfig:
    """Get the default research-optimized configuration."""
    return ResearchOptimizedConfig()


def load_research_config(config_path: Optional[str] = None) -> ResearchOptimizedConfig:
    """
    Load research configuration from file or return defaults.

    Args:
        config_path: Path to optimal_config.json from research output

    Returns:
        ResearchOptimizedConfig instance
    """
    if config_path and Path(config_path).exists():
        return ResearchOptimizedConfig.load_from_json(config_path)

    # Try to find config in standard locations
    search_paths = [
        Path(__file__).parent / 'research' / 'optimal_config.json',
        Path(__file__).parent / 'research' / 'full_research' / 'optimal_config.json',
        Path(__file__).parent / 'research' / 'comprehensive_output' / 'optimal_config.json',
    ]

    for path in search_paths:
        if path.exists():
            print(f"📊 Loading research config from: {path}")
            return ResearchOptimizedConfig.load_from_json(str(path))

    print("📊 Using default research-optimized configuration")
    return ResearchOptimizedConfig()


# Print config summary when module is run
if __name__ == '__main__':
    config = load_research_config()

    print("\n" + "="*60)
    print("  SYNESTHESIA Research-Optimized Configuration")
    print("="*60)

    print("\n📐 Spiral Geometry:")
    print(f"   Turns: {config.spiral_turns}")
    print(f"   Radius: {config.spiral_inner_radius} - {config.spiral_outer_radius}")

    print("\n🎵 Melody Trail (Score: 0.925):")
    print(f"   Length: {config.trail_length_frames} frames")
    print(f"   Decay: {config.trail_decay_rate}")
    print(f"   Style: {config.trail_style}")

    print("\n🎨 Color Mapping (Score: 0.996):")
    print(f"   Mapping: {config.color_mapping}")
    print(f"   Saturation: {config.color_saturation}")
    print(f"   Brightness: {config.color_brightness_min} - {config.color_brightness_max}")

    print("\n🥁 Rhythm Pulse:")
    print(f"   Intensity: {config.rhythm_pulse_intensity}")
    print(f"   Decay: {config.rhythm_pulse_decay}")

    print("\n🎹 Harmony:")
    print(f"   Blend Time: {config.harmony_blend_time}s")
    print(f"   Hold Time: {config.chord_hold_time}s")

    print("\n🌫️ Atmosphere:")
    print(f"   Window: {config.atmosphere_window}s")
    print(f"   Influence: {config.atmosphere_influence}")

    print("\n" + "="*60)
