"""
SYNESTHESIA 3.0 - Temporal Renderer
====================================
Enhanced spiral renderer with temporal visualization features:
- Melodic Trail: Shows pitch history as glowing particles
- Rhythm Pulse: Spiral breathes with the beat
- Harmonic Aura: Background color reflects chord/key
- Atmosphere Field: Global visual modulation based on mood

This is the breakthrough renderer that visualizes not just WHAT is playing,
but HOW the music unfolds over time.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict
from collections import deque
import colorsys
import math


@dataclass
class TemporalRenderConfig:
    """Configuration for temporal-aware rendering."""
    # Frame dimensions
    frame_width: int = 1280
    frame_height: int = 720

    # Spiral parameters
    num_turns: float = 3.5  # Research-validated (VISUALIZATION_LAWS.md)
    num_frequency_bins: int = 381
    base_point_size: int = 4

    # Melodic Trail
    enable_melody_trail: bool = True
    trail_duration_seconds: float = 3.0
    trail_decay_rate: float = 0.92
    trail_glow_radius: int = 8
    trail_color: Tuple[int, int, int] = (255, 220, 100)  # Golden

    # Rhythm Pulse
    enable_rhythm_pulse: bool = True
    pulse_scale_amount: float = 0.12  # Max 12% scale change
    pulse_brightness_amount: float = 0.25
    pulse_decay_rate: float = 0.85

    # Harmonic Aura
    enable_harmonic_aura: bool = True
    aura_transition_speed: float = 0.08
    aura_saturation: float = 0.4
    aura_brightness: float = 0.15

    # Atmosphere Field
    enable_atmosphere: bool = True
    atmosphere_particle_density: float = 0.3
    atmosphere_blur_amount: float = 0.0

    # Harmonic connections
    enable_harmonic_connections: bool = True

    # Background
    base_background_color: Tuple[int, int, int] = (15, 20, 30)


# Chromesthesia color mapping (solfège-based)
CHROMESTHESIA_COLORS = [
    (0, 0, 255),      # Do - Blue (C)
    (75, 0, 130),     # C# - Indigo
    (255, 105, 180),  # Re - Pink (D)
    (238, 130, 238),  # D# - Violet
    (255, 0, 0),      # Mi - Red (E)
    (255, 165, 0),    # Fa - Orange (F)
    (255, 140, 0),    # F# - Dark Orange
    (255, 255, 0),    # Sol - Yellow (G)
    (173, 255, 47),   # G# - Green Yellow
    (0, 255, 0),      # La - Green (A)
    (0, 206, 209),    # A# - Dark Turquoise
    (0, 255, 255),    # Si - Cyan (B)
]

# Circle of fifths color mapping for harmony
HARMONY_COLORS = {
    'C': (255, 80, 80),      # Red
    'G': (255, 140, 80),     # Orange-red
    'D': (255, 200, 80),     # Orange
    'A': (255, 255, 80),     # Yellow
    'E': (200, 255, 80),     # Yellow-green
    'B': (80, 255, 80),      # Green
    'F#': (80, 255, 160),    # Green-cyan
    'Db': (80, 255, 255),    # Cyan
    'Ab': (80, 160, 255),    # Cyan-blue
    'Eb': (80, 80, 255),     # Blue
    'Bb': (160, 80, 255),    # Blue-purple
    'F': (255, 80, 200),     # Purple-red
    'N': (60, 60, 80),       # No chord
}


class MelodicTrail:
    """Tracks and renders the melodic pitch trail."""

    def __init__(self, config: TemporalRenderConfig, frame_rate: int = 30):
        self.config = config
        self.frame_rate = frame_rate
        self.trail_length = int(config.trail_duration_seconds * frame_rate)
        self.pitch_history: deque = deque(maxlen=self.trail_length)

        # Spiral mapping parameters
        self.freq_min = 50.0
        self.freq_max = 2000.0

    def update(self, pitch_hz: float, confidence: float = 1.0):
        """Add current pitch to the trail."""
        self.pitch_history.append((pitch_hz, confidence))

    def render(self, draw: ImageDraw.Draw, center_x: int, center_y: int,
               max_radius: float, rotation: float):
        """Render the melodic trail as glowing particles."""
        if not self.config.enable_melody_trail or len(self.pitch_history) == 0:
            return

        points = []

        for i, (pitch, confidence) in enumerate(self.pitch_history):
            if pitch <= 0 or confidence < 0.3:
                continue

            # Map pitch to spiral position
            x, y = self._pitch_to_coords(pitch, center_x, center_y, max_radius, rotation)

            # Alpha decays with age
            age = len(self.pitch_history) - i - 1
            alpha = (self.config.trail_decay_rate ** age) * confidence

            if alpha < 0.05:
                continue

            points.append((x, y, alpha, confidence))

        # Render points with glow effect (oldest to newest)
        for x, y, alpha, confidence in points:
            # Glow radius based on confidence
            glow_r = int(self.config.trail_glow_radius * (0.5 + 0.5 * confidence))

            # Draw glow layers
            for layer in range(3, 0, -1):
                layer_alpha = alpha * (0.3 / layer)
                layer_radius = glow_r * layer

                color = tuple(int(c * layer_alpha) for c in self.config.trail_color)

                draw.ellipse(
                    [x - layer_radius, y - layer_radius,
                     x + layer_radius, y + layer_radius],
                    fill=color
                )

            # Draw core
            core_color = tuple(int(c * alpha) for c in self.config.trail_color)
            core_radius = max(2, int(glow_r * 0.4))
            draw.ellipse(
                [x - core_radius, y - core_radius,
                 x + core_radius, y + core_radius],
                fill=core_color
            )

    def _pitch_to_coords(self, pitch_hz: float, center_x: int, center_y: int,
                         max_radius: float, rotation: float) -> Tuple[int, int]:
        """Map pitch frequency to spiral coordinates."""
        # Logarithmic mapping
        if pitch_hz <= self.freq_min:
            rel_freq = 0.05
        elif pitch_hz >= self.freq_max:
            rel_freq = 0.95
        else:
            rel_freq = (np.log(pitch_hz) - np.log(self.freq_min)) / \
                       (np.log(self.freq_max) - np.log(self.freq_min))

        # Fermat spiral
        theta = rel_freq * self.config.num_turns * 2 * np.pi + np.radians(rotation)
        r = np.sqrt(rel_freq) * max_radius * 0.9

        x = int(center_x + r * np.cos(theta))
        y = int(center_y + r * np.sin(theta))

        return x, y


class RhythmPulse:
    """Manages rhythm-synchronized pulsing effects."""

    def __init__(self, config: TemporalRenderConfig):
        self.config = config
        self.current_pulse = 0.0
        self.beat_phase = 0.0

    def on_beat(self, strength: float = 1.0, is_downbeat: bool = False):
        """Called when a beat is detected."""
        if is_downbeat:
            strength *= 1.3  # Emphasize downbeats
        self.current_pulse = min(1.0, self.current_pulse + strength)

    def update(self) -> Tuple[float, float]:
        """
        Update and return current pulse effects.

        Returns:
            (scale_multiplier, brightness_boost)
        """
        if not self.config.enable_rhythm_pulse:
            return 1.0, 0.0

        scale = 1.0 + self.current_pulse * self.config.pulse_scale_amount
        brightness = self.current_pulse * self.config.pulse_brightness_amount

        # Decay
        self.current_pulse *= self.config.pulse_decay_rate

        return scale, brightness


class HarmonicAura:
    """Manages background color based on harmonic content."""

    def __init__(self, config: TemporalRenderConfig):
        self.config = config
        base = config.base_background_color
        self.current_color = np.array(base, dtype=float)
        self.target_color = np.array(base, dtype=float)
        self.current_chord = "N"

    def set_chord(self, chord_label: str):
        """Set target background color based on detected chord."""
        if not self.config.enable_harmonic_aura:
            return

        self.current_chord = chord_label

        # Extract root note
        root = chord_label.rstrip('m').rstrip('7').rstrip('maj').rstrip('dim').rstrip('aug')
        root = root.replace('#', '#').replace('b', 'b')  # Normalize

        # Get base color for root
        if root in HARMONY_COLORS:
            base_color = np.array(HARMONY_COLORS[root], dtype=float)
        else:
            base_color = np.array(HARMONY_COLORS['N'], dtype=float)

        # Minor chords: shift toward cooler colors
        if 'm' in chord_label and 'maj' not in chord_label:
            base_color = base_color * 0.7 + np.array([0, 30, 60])

        # Diminished: darker
        if 'dim' in chord_label:
            base_color = base_color * 0.5

        # Apply saturation and brightness settings
        base_color = base_color * self.config.aura_brightness

        self.target_color = np.clip(base_color, 0, 255)

    def update(self) -> Tuple[int, int, int]:
        """Update and return current background color."""
        if not self.config.enable_harmonic_aura:
            return self.config.base_background_color

        # Smooth transition
        self.current_color += (self.target_color - self.current_color) * self.config.aura_transition_speed

        return tuple(np.clip(self.current_color, 0, 255).astype(int))


class AtmosphereField:
    """Manages global atmosphere effects based on long-term musical features."""

    def __init__(self, config: TemporalRenderConfig):
        self.config = config
        self.energy = 0.5
        self.tension = 0.3
        self.brightness_history = deque(maxlen=90)  # ~3 seconds at 30fps

    def update_atmosphere(self, energy: float, tension: float, brightness: float):
        """Update atmosphere parameters."""
        if not self.config.enable_atmosphere:
            return

        # Smooth updates
        self.energy = self.energy * 0.95 + energy * 0.05
        self.tension = self.tension * 0.95 + tension * 0.05
        self.brightness_history.append(brightness)

    def get_effects(self) -> Dict[str, float]:
        """Get current atmosphere effects."""
        if not self.config.enable_atmosphere:
            return {'rotation_speed': 1.0, 'particle_scale': 1.0, 'color_warmth': 0.0}

        return {
            'rotation_speed': 0.5 + self.energy * 1.5,  # 0.5x to 2x
            'particle_scale': 0.8 + self.energy * 0.4,  # 0.8x to 1.2x
            'color_warmth': self.tension * 0.3,  # Shift toward warm on tension
        }


class TemporalSpiralRenderer:
    """
    Enhanced spiral renderer with temporal visualization features.

    Combines the base spiral visualization with:
    - Melodic Trail: Pitch history as glowing particles
    - Rhythm Pulse: Beat-synchronized scaling and brightness
    - Harmonic Aura: Chord-driven background colors
    - Atmosphere Field: Long-term mood modulation
    """

    def __init__(self, config: Optional[TemporalRenderConfig] = None,
                 frame_rate: int = 30):
        self.config = config or TemporalRenderConfig()
        self.frame_rate = frame_rate

        # Initialize temporal components
        self.melody_trail = MelodicTrail(self.config, frame_rate)
        self.rhythm_pulse = RhythmPulse(self.config)
        self.harmonic_aura = HarmonicAura(self.config)
        self.atmosphere = AtmosphereField(self.config)

        # Harmonic connections
        self.harmonic_connections = None
        if self.config.enable_harmonic_connections:
            from harmonic_connections import HarmonicConnectionRenderer
            self.harmonic_connections = HarmonicConnectionRenderer()

        # Animation state
        self.rotation_angle = 0.0
        self.wave_phase = 0.0

        # Pre-compute spiral geometry
        self._init_spiral_geometry()

        # Font for labels
        try:
            self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            self.title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        except:
            self.font = ImageFont.load_default()
            self.title_font = self.font

    def _init_spiral_geometry(self):
        """Pre-compute spiral geometry."""
        self.num_points = self.config.num_frequency_bins
        self.center_x = self.config.frame_width // 2
        self.center_y = self.config.frame_height // 2
        self.max_radius = min(self.center_x, self.center_y) * 0.85

        # Fermat spiral coordinates
        t = np.linspace(0, 1, self.num_points)
        self.base_theta = t * self.config.num_turns * 2 * np.pi
        self.base_r = np.sqrt(t) * self.max_radius

        # Color for each frequency bin (chromesthesia)
        self.colors = []
        for i in range(self.num_points):
            # Map frequency index to chromesthesia color
            octave_pos = (i / self.num_points) * 7  # 7 octaves
            note_in_octave = (octave_pos % 1) * 12
            color_idx = int(note_in_octave) % 12
            self.colors.append(CHROMESTHESIA_COLORS[color_idx])

    def update_temporal_features(self,
                                 pitch_hz: float = 0,
                                 pitch_confidence: float = 0,
                                 is_beat: bool = False,
                                 is_downbeat: bool = False,
                                 beat_strength: float = 0,
                                 chord_label: str = "N",
                                 energy: float = 0.5,
                                 tension: float = 0.3,
                                 brightness: float = 0.5):
        """
        Update all temporal feature trackers.

        Call this once per frame with extracted temporal features.
        """
        # Melody
        if pitch_hz > 0 and pitch_confidence > 0.3:
            self.melody_trail.update(pitch_hz, pitch_confidence)

        # Rhythm
        if is_beat:
            self.rhythm_pulse.on_beat(beat_strength, is_downbeat)

        # Harmony
        if chord_label and chord_label != self.harmonic_aura.current_chord:
            self.harmonic_aura.set_chord(chord_label)

        # Atmosphere
        self.atmosphere.update_atmosphere(energy, tension, brightness)

    def render_frame(self,
                     amplitude_data: np.ndarray,
                     frame_idx: int = 0,
                     frequencies: Optional[np.ndarray] = None,
                     show_labels: bool = True,
                     show_info: bool = True) -> Image.Image:
        """
        Render a single frame with all temporal features.

        Args:
            amplitude_data: Amplitude values for each frequency bin
            frame_idx: Current frame index (for animation)
            frequencies: Optional frequency values for labels
            show_labels: Whether to show frequency labels
            show_info: Whether to show info overlay

        Returns:
            PIL Image of the rendered frame
        """
        # Get temporal effects
        pulse_scale, pulse_brightness = self.rhythm_pulse.update()
        background_color = self.harmonic_aura.update()
        atmos_effects = self.atmosphere.get_effects()

        # Update animation state
        self.rotation_angle = frame_idx * 0.5 * atmos_effects['rotation_speed']
        self.wave_phase = frame_idx * 0.15

        # Create image with harmonic aura background
        img = Image.new('RGB', (self.config.frame_width, self.config.frame_height),
                        background_color)
        draw = ImageDraw.Draw(img)

        # Apply atmosphere effects to rendering
        effective_scale = pulse_scale * atmos_effects['particle_scale']

        # Render base spiral
        self._render_spiral(draw, amplitude_data, effective_scale, pulse_brightness,
                            frequencies, show_labels)

        # Render melodic trail on top
        self.melody_trail.render(draw, self.center_x, self.center_y,
                                 self.max_radius, self.rotation_angle)

        # Add info overlay
        if show_info:
            self._render_info_overlay(draw, frame_idx, pulse_scale)

        return img

    def _render_spiral(self, draw: ImageDraw.Draw, amplitude_data: np.ndarray,
                       scale: float, brightness_boost: float,
                       frequencies: Optional[np.ndarray], show_labels: bool):
        """Render the main spiral visualization."""
        # Normalize amplitude
        amp_normalized = amplitude_data / (np.max(amplitude_data) + 1e-8)

        # Apply rotation
        theta = self.base_theta + np.radians(self.rotation_angle)

        # Apply wave animation
        wave = np.sin(self.base_theta * 3 + self.wave_phase) * 0.05
        r_animated = self.base_r * (1 + wave) * scale

        # Calculate positions
        x_coords = self.center_x + r_animated * np.cos(theta)
        y_coords = self.center_y + r_animated * np.sin(theta)

        # Harmonic connections (draw lines before circles; apply displacement)
        if self.harmonic_connections is not None and frequencies is not None:
            x_coords, y_coords = self.harmonic_connections.render(
                draw, amp_normalized, frequencies, x_coords, y_coords, self.colors)

        # Frequency labels tracking
        label_frequencies = [73, 110, 147, 220, 294, 440, 587, 880, 1175, 1760, 2349, 3136, 4186]
        labeled_indices = set()

        if frequencies is not None and show_labels:
            for label_freq in label_frequencies:
                idx = np.argmin(np.abs(frequencies - label_freq))
                if amp_normalized[idx] > 0.15:
                    labeled_indices.add(idx)

        # Render points
        for i in range(self.num_points):
            amp = amp_normalized[i]

            # Size based on amplitude and scale
            base_size = self.config.base_point_size
            size = int(base_size + amp * base_size * 3 * scale)

            if size < 1:
                continue

            x, y = int(x_coords[i]), int(y_coords[i])

            # Color with brightness modulation
            base_color = self.colors[i]
            brightness = 0.3 + amp * 0.7 + brightness_boost
            color = tuple(int(min(255, c * brightness)) for c in base_color)

            # Draw point
            draw.ellipse([x - size, y - size, x + size, y + size], fill=color)

            # Draw label if applicable
            if i in labeled_indices and frequencies is not None:
                freq = frequencies[i]
                label = f"{int(freq)}Hz"
                draw.text((x + size + 5, y - 7), label, fill=color, font=self.font)

    def _render_info_overlay(self, draw: ImageDraw.Draw, frame_idx: int, pulse_scale: float):
        """Render information overlay."""
        # Title
        draw.text((20, 15), "SYNESTHESIA 3.0", fill=(200, 200, 200), font=self.title_font)

        # Temporal indicators
        y_pos = 45
        info_color = (150, 150, 150)

        # Chord
        chord = self.harmonic_aura.current_chord
        if chord != "N":
            draw.text((20, y_pos), f"Chord: {chord}", fill=info_color, font=self.font)
            y_pos += 20

        # Rhythm indicator
        if pulse_scale > 1.02:
            beat_indicator = "●" * int((pulse_scale - 1) * 50)
            draw.text((20, y_pos), f"Beat: {beat_indicator}", fill=(100, 255, 100), font=self.font)
            y_pos += 20

        # Energy
        energy_bar_width = int(self.atmosphere.energy * 100)
        draw.rectangle([(20, y_pos), (20 + energy_bar_width, y_pos + 8)],
                       fill=(100, 150, 255))
        draw.text((130, y_pos - 2), "Energy", fill=info_color, font=self.font)

    def save_frame(self, amplitude_data: np.ndarray, output_path: str,
                   frame_idx: int = 0, frequencies: Optional[np.ndarray] = None):
        """Render and save a single frame."""
        img = self.render_frame(amplitude_data, frame_idx, frequencies)
        img.save(output_path)


def demo_temporal_renderer():
    """Demonstrate the temporal renderer."""
    print("=" * 60)
    print("SYNESTHESIA 3.0 - Temporal Renderer Demo")
    print("=" * 60)

    config = TemporalRenderConfig(
        frame_width=1280,
        frame_height=720,
        enable_melody_trail=True,
        enable_rhythm_pulse=True,
        enable_harmonic_aura=True,
        enable_atmosphere=True
    )

    renderer = TemporalSpiralRenderer(config, frame_rate=30)

    # Simulate a musical phrase
    num_frames = 90  # 3 seconds
    frequencies = np.logspace(np.log10(20), np.log10(8000), 381)

    # Melody: C4 -> E4 -> G4 -> C5 (arpeggio)
    melody_pitches = [261.63, 329.63, 392.00, 523.25]
    chord_progression = ['C', 'C', 'Em', 'G']

    print("\nGenerating frames...")

    frames = []
    for frame_idx in range(num_frames):
        # Generate amplitude data (simulate)
        amplitude = np.zeros(381)
        note_idx = (frame_idx // 22) % len(melody_pitches)
        fundamental = melody_pitches[note_idx]

        # Add fundamental and harmonics
        fund_idx = np.argmin(np.abs(frequencies - fundamental))
        amplitude[fund_idx] = 1.0
        for h in range(2, 6):
            h_freq = fundamental * h
            if h_freq < 8000:
                h_idx = np.argmin(np.abs(frequencies - h_freq))
                amplitude[h_idx] = 0.5 ** (h - 1)

        # Add noise
        amplitude += np.random.rand(381) * 0.05

        # Update temporal features
        is_beat = frame_idx % 15 == 0  # Beat every 0.5s
        is_downbeat = frame_idx % 60 == 0  # Downbeat every 2s

        renderer.update_temporal_features(
            pitch_hz=fundamental,
            pitch_confidence=0.9,
            is_beat=is_beat,
            is_downbeat=is_downbeat,
            beat_strength=0.8 if is_beat else 0,
            chord_label=chord_progression[note_idx],
            energy=0.6 + 0.2 * np.sin(frame_idx * 0.1),
            tension=0.3,
            brightness=0.7
        )

        # Render frame
        frame = renderer.render_frame(amplitude, frame_idx, frequencies)
        frames.append(frame)

        if frame_idx % 30 == 0:
            print(f"  Frame {frame_idx + 1}/{num_frames}")

    # Save a sample frame
    output_path = "temporal_demo_frame.png"
    frames[45].save(output_path)
    print(f"\n✅ Sample frame saved to: {output_path}")

    # Create animated GIF
    gif_path = "temporal_demo.gif"
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=33,  # ~30fps
        loop=0
    )
    print(f"✅ Animation saved to: {gif_path}")

    print("\n✅ Temporal renderer demo complete!")


if __name__ == "__main__":
    demo_temporal_renderer()
