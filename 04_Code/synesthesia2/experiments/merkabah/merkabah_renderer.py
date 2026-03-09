#!/usr/bin/env python3
"""
SYNESTHESIA - Merkabah Sacred Geometry Renderer
================================================
Audio visualization based on Merkabah mysticism geometry from Ezekiel's vision.

The Merkabah (Divine Chariot) structure:
- Two interlocking tetrahedra (Star Tetrahedron / Star of David in 3D)
- The Four Living Creatures (Chayot) - Lion, Ox, Eagle, Man
- The Ophanim (Wheels within Wheels)
- The Throne/Center (Kisse HaKavod)

Frequency Mapping:
- Bass frequencies → Lower tetrahedron (Earth/Foundation)
- Mid frequencies → Ophanim wheels (Movement/Rotation)
- High frequencies → Upper tetrahedron (Heaven/Spirit)
- Dominant pitch → Center throne glow

Visual Elements from Ezekiel 1:
- "Wheels within wheels" (Ophanim) - concentric rotating rings
- "Full of eyes" - frequency points distributed around structure
- "Fire moving back and forth" - energy flowing between elements
- "Lightning" - transient flashes on beats
- Four faces/directions - quadrant-based frequency distribution

References:
- Ezekiel 1:4-28 - The Vision of the Merkabah
- Ezekiel 10 - The Cherubim and Wheels
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from dataclasses import dataclass
from typing import Tuple, List, Optional
from collections import deque
import colorsys
import math


@dataclass
class MerkabahConfig:
    """Configuration for Merkabah visualization."""
    # Frame dimensions
    frame_width: int = 1280
    frame_height: int = 720

    # Merkabah geometry
    merkabah_scale: float = 0.38  # Size relative to frame
    rotation_speed: float = 0.5   # Base rotation degrees per frame

    # Star Tetrahedron (two interlocking triangles in 2D projection)
    tetra_upper_color: Tuple[int, int, int] = (100, 150, 255)  # Heavenly blue
    tetra_lower_color: Tuple[int, int, int] = (255, 150, 100)  # Earthly orange
    tetra_line_width: int = 2

    # Ophanim (Wheels within Wheels)
    num_wheels: int = 4           # Four wheels as in Ezekiel's vision
    wheel_rings: int = 3          # Concentric rings per wheel
    wheel_rotation_speed: float = 1.2  # Faster than main structure
    wheel_color: Tuple[int, int, int] = (200, 180, 100)  # Golden/Bronze

    # Eyes (frequency visualization points)
    num_eyes_per_ring: int = 12   # "Full of eyes all around"
    eye_base_size: int = 3
    eye_max_size: int = 12

    # Chayot (Four Living Creatures) - frequency quadrants
    enable_chayot: bool = True
    chayot_positions: List[str] = None  # Lion, Ox, Eagle, Man

    # Center Throne (dominant frequency)
    throne_radius: float = 0.08
    throne_glow_radius: float = 0.15
    throne_color: Tuple[int, int, int] = (255, 255, 200)  # Divine light

    # Fire/Lightning effects
    enable_fire: bool = True
    fire_intensity: float = 0.5
    lightning_on_beat: bool = True

    # Trail/Persistence
    trail_length: int = 10
    trail_decay: float = 0.7

    # Background
    background_color: Tuple[int, int, int] = (5, 5, 15)  # Deep space

    # Color mapping
    color_saturation: float = 0.95
    brightness_min: float = 0.35
    brightness_max: float = 1.0

    def __post_init__(self):
        if self.chayot_positions is None:
            # Four faces: Lion (right/east), Ox (left/west), Eagle (back/north), Man (front/south)
            self.chayot_positions = ['lion', 'man', 'ox', 'eagle']


class MerkabahGeometry:
    """Sacred geometry calculations for Merkabah structure."""

    @staticmethod
    def star_tetrahedron_2d(center: Tuple[float, float], radius: float,
                            rotation: float = 0) -> Tuple[List[Tuple], List[Tuple]]:
        """
        Calculate 2D projection of star tetrahedron (two interlocking triangles).

        Returns:
            (upper_triangle_points, lower_triangle_points)
        """
        cx, cy = center

        # Upper triangle (pointing up) - Heavenly
        upper_points = []
        for i in range(3):
            angle = math.radians(rotation + 90 + i * 120)  # Start pointing up
            x = cx + radius * math.cos(angle)
            y = cy - radius * math.sin(angle)  # Negative for screen coords
            upper_points.append((x, y))

        # Lower triangle (pointing down) - Earthly
        lower_points = []
        for i in range(3):
            angle = math.radians(rotation + 270 + i * 120)  # Start pointing down
            x = cx + radius * math.cos(angle)
            y = cy - radius * math.sin(angle)
            lower_points.append((x, y))

        return upper_points, lower_points

    @staticmethod
    def hexagram_points(center: Tuple[float, float], radius: float,
                        rotation: float = 0) -> List[Tuple]:
        """
        Calculate the 6 points of the hexagram (Star of David).
        These are where the triangles intersect.
        """
        cx, cy = center
        inner_radius = radius * 0.5  # Intersection points

        points = []
        for i in range(6):
            angle = math.radians(rotation + 30 + i * 60)
            x = cx + inner_radius * math.cos(angle)
            y = cy - inner_radius * math.sin(angle)
            points.append((x, y))

        return points

    @staticmethod
    def ophan_wheel(center: Tuple[float, float], radius: float,
                    rotation: float, num_rings: int = 3,
                    points_per_ring: int = 12) -> List[List[Tuple]]:
        """
        Calculate "wheel within wheel" structure (Ophanim).

        Returns list of rings, each containing points around that ring.
        """
        cx, cy = center
        rings = []

        for ring_idx in range(num_rings):
            # Each ring has different radius and rotation offset
            ring_radius = radius * (0.4 + 0.3 * ring_idx / num_rings)
            ring_rotation = rotation + ring_idx * 15  # Offset rotation

            ring_points = []
            for i in range(points_per_ring):
                angle = math.radians(ring_rotation + i * (360 / points_per_ring))
                x = cx + ring_radius * math.cos(angle)
                y = cy - ring_radius * math.sin(angle)
                ring_points.append((x, y))

            rings.append(ring_points)

        return rings

    @staticmethod
    def chayot_positions(center: Tuple[float, float], radius: float,
                         rotation: float = 0) -> dict:
        """
        Calculate positions for the Four Living Creatures.

        Lion (East), Ox (West), Eagle (North), Man (South)
        """
        cx, cy = center
        positions = {}

        # Four cardinal directions
        directions = {
            'lion': 0,      # East/Right
            'man': 90,      # South/Front
            'ox': 180,      # West/Left
            'eagle': 270,   # North/Back
        }

        for creature, base_angle in directions.items():
            angle = math.radians(rotation + base_angle)
            x = cx + radius * math.cos(angle)
            y = cy - radius * math.sin(angle)
            positions[creature] = (x, y)

        return positions


class MerkabahRenderer:
    """
    Renderer using Merkabah sacred geometry for audio visualization.

    Maps audio features to the mystical chariot structure:
    - Spectrum → distributed across wheels and triangles
    - Bass → Lower tetrahedron intensity
    - Treble → Upper tetrahedron intensity
    - Rhythm → Rotation speed and lightning
    - Melody → Throne/center glow
    - Harmony → Overall color temperature
    """

    def __init__(self, config: MerkabahConfig):
        self.config = config
        self.geometry = MerkabahGeometry()

        # Frame dimensions
        self.width = config.frame_width
        self.height = config.frame_height
        self.center = (self.width // 2, self.height // 2)
        self.base_radius = min(self.width, self.height) * config.merkabah_scale

        # Animation state
        self.main_rotation = 0.0
        self.wheel_rotation = 0.0
        self.counter_rotation = 0.0

        # Pulse/energy state
        self.throne_energy = 0.0
        self.fire_energy = 0.0
        self.lightning_active = False

        # Trail history for "eyes"
        self.eye_history: deque = deque(maxlen=config.trail_length)

        # Harmony color state
        self.current_hue = 0.5
        self.target_hue = 0.5

    def update_state(self, beat_strength: float = 0, is_beat: bool = False,
                     pitch: float = 0, chroma: np.ndarray = None,
                     rms: float = 0.5):
        """Update animation state based on audio features."""

        # Rotation speeds affected by energy
        energy_factor = 0.5 + rms * 1.5
        self.main_rotation += self.config.rotation_speed * energy_factor
        self.wheel_rotation += self.config.wheel_rotation_speed * energy_factor
        self.counter_rotation -= self.config.rotation_speed * 0.7 * energy_factor

        # Throne energy from pitch/melody
        if pitch > 0:
            self.throne_energy = min(1.0, self.throne_energy + 0.3)
        self.throne_energy *= 0.92

        # Fire energy from RMS
        self.fire_energy = rms

        # Lightning on beats
        self.lightning_active = is_beat and beat_strength > 0.5

        # Harmony affects color
        if chroma is not None and len(chroma) >= 12:
            dominant_pc = np.argmax(chroma[:12])
            self.target_hue = dominant_pc / 12.0

        self.current_hue += (self.target_hue - self.current_hue) * 0.05

    def freq_to_color(self, freq: float, amplitude: float = 1.0) -> Tuple[int, int, int]:
        """Map frequency to color with Merkabah-inspired palette."""
        f_min, f_max = 50, 8000

        # Normalize frequency
        if freq <= f_min:
            freq_norm = 0
        elif freq >= f_max:
            freq_norm = 1
        else:
            freq_norm = (np.log(freq) - np.log(f_min)) / (np.log(f_max) - np.log(f_min))

        # Color mapping inspired by Ezekiel's vision:
        # Low freq (amber/bronze) → Mid (sapphire blue) → High (crystal/white)
        if freq_norm < 0.33:
            # Amber/Bronze for bass (earthly)
            hue = 0.08 + freq_norm * 0.1  # Orange-yellow
        elif freq_norm < 0.66:
            # Sapphire for mids (the throne appearance)
            hue = 0.55 + (freq_norm - 0.33) * 0.15  # Blue range
        else:
            # Crystal/White-blue for highs (heavenly)
            hue = 0.5 + (freq_norm - 0.66) * 0.2

        # Blend with harmony hue
        hue = hue * 0.7 + self.current_hue * 0.3
        hue = hue % 1.0

        sat = self.config.color_saturation
        val = self.config.brightness_min + amplitude * (self.config.brightness_max - self.config.brightness_min)

        r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
        return (int(r * 255), int(g * 255), int(b * 255))

    def render_frame(self, spectrum: np.ndarray, frequencies: np.ndarray,
                     temporal_features: dict = None) -> Image.Image:
        """Render a single frame with Merkabah geometry."""

        # Normalize spectrum to 0-1 range to handle varying amplitude scales
        if spectrum.max() > 0:
            spectrum = spectrum / spectrum.max()
        spectrum = np.clip(spectrum, 0, 1)

        # Create base image
        image = Image.new('RGB', (self.width, self.height), self.config.background_color)
        draw = ImageDraw.Draw(image)

        # Calculate band energies
        bass_energy, mid_energy, treble_energy = self._calculate_band_energies(spectrum, frequencies)

        # Store current spectrum for eyes
        self.eye_history.append((spectrum.copy(), frequencies.copy()))

        # Layer 1: Background glow/aura
        self._render_aura(draw, bass_energy, mid_energy, treble_energy)

        # Layer 2: Ophanim (Wheels within Wheels) - mid frequencies
        self._render_ophanim(draw, spectrum, frequencies, mid_energy)

        # Layer 3: Star Tetrahedron structure
        self._render_star_tetrahedron(draw, bass_energy, treble_energy)

        # Layer 4: Eyes (frequency points distributed on structure)
        self._render_eyes(draw, spectrum, frequencies)

        # Layer 5: Fire between elements
        if self.config.enable_fire:
            self._render_fire(draw, bass_energy + treble_energy)

        # Layer 6: Center Throne
        self._render_throne(draw)

        # Layer 7: Lightning on beats
        if self.lightning_active and self.config.lightning_on_beat:
            self._render_lightning(draw)

        return image

    def _calculate_band_energies(self, spectrum: np.ndarray,
                                  frequencies: np.ndarray) -> Tuple[float, float, float]:
        """Calculate energy in bass, mid, and treble bands."""
        bass_mask = frequencies < 250
        mid_mask = (frequencies >= 250) & (frequencies < 2000)
        treble_mask = frequencies >= 2000

        bass = np.mean(spectrum[bass_mask]) if np.any(bass_mask) else 0
        mid = np.mean(spectrum[mid_mask]) if np.any(mid_mask) else 0
        treble = np.mean(spectrum[treble_mask]) if np.any(treble_mask) else 0

        # Normalize
        total = bass + mid + treble + 0.001
        return bass/total, mid/total, treble/total

    def _render_aura(self, draw: ImageDraw.Draw, bass: float, mid: float, treble: float):
        """Render background aura/glow."""
        cx, cy = self.center

        # Concentric gradient circles
        for i in range(5, 0, -1):
            radius = self.base_radius * (1.5 + i * 0.15)
            alpha = int(20 * (bass * 0.5 + mid * 0.3 + treble * 0.2) * (6 - i) / 5)

            # Color based on dominant energy
            if bass > mid and bass > treble:
                color = (alpha, int(alpha * 0.6), int(alpha * 0.3))
            elif treble > mid:
                color = (int(alpha * 0.5), int(alpha * 0.7), alpha)
            else:
                color = (int(alpha * 0.4), int(alpha * 0.6), alpha)

            draw.ellipse(
                [cx - radius, cy - radius, cx + radius, cy + radius],
                fill=color
            )

    def _render_star_tetrahedron(self, draw: ImageDraw.Draw,
                                  bass_energy: float, treble_energy: float):
        """Render the Star Tetrahedron with smooth gradients that dance with audio."""
        upper, lower = self.geometry.star_tetrahedron_2d(
            self.center, self.base_radius, self.main_rotation
        )

        cx, cy = self.center

        # Calculate energy-based color shifts for the "dance"
        # Use rotation and energy to create pulsing, shifting gradients
        pulse_phase = self.main_rotation * 0.02  # Slow color cycling
        energy_pulse = 0.7 + 0.3 * math.sin(pulse_phase)

        # Lower triangle (Earth/Bass) - warm gradient from center outward
        lower_intensity = 0.5 + bass_energy * 0.5

        # Create radial gradient effect for lower triangle
        num_gradient_steps = 8
        for step in range(num_gradient_steps, 0, -1):
            t = step / num_gradient_steps

            # Interpolate triangle vertices toward center
            grad_lower = []
            for pt in lower:
                gx = cx + (pt[0] - cx) * t
                gy = cy + (pt[1] - cy) * t
                grad_lower.append((gx, gy))

            # Color shifts from deep amber at edges to bright gold at center
            # Add energy-based hue shift for "dancing"
            hue_shift = bass_energy * 0.05 * math.sin(pulse_phase * 2)

            base_r = self.config.tetra_lower_color[0]
            base_g = self.config.tetra_lower_color[1]
            base_b = self.config.tetra_lower_color[2]

            # Gradient: darker at edges, brighter toward center
            brightness = 0.2 + 0.6 * (1 - t) * lower_intensity * energy_pulse

            # Add subtle color variation based on energy
            r = int(min(255, base_r * brightness * (1 + hue_shift)))
            g = int(min(255, base_g * brightness * (1 - hue_shift * 0.5)))
            b = int(min(255, base_b * brightness * 0.3))

            fill_color = (r, g, b)
            draw.polygon(grad_lower, fill=fill_color)

        # Draw lower triangle outline with glow effect
        lower_glow_intensity = 0.6 + bass_energy * 0.4
        for glow_width in range(4, 0, -1):
            glow_alpha = lower_glow_intensity * (0.3 / glow_width)
            glow_color = (
                int(min(255, self.config.tetra_lower_color[0] * glow_alpha * 1.5)),
                int(min(255, self.config.tetra_lower_color[1] * glow_alpha)),
                int(min(255, self.config.tetra_lower_color[2] * glow_alpha * 0.5))
            )
            draw.polygon(lower, outline=glow_color, width=self.config.tetra_line_width + glow_width)

        # Upper triangle (Heaven/Treble) - cool gradient from center outward
        upper_intensity = 0.5 + treble_energy * 0.5

        # Create radial gradient effect for upper triangle
        for step in range(num_gradient_steps, 0, -1):
            t = step / num_gradient_steps

            # Interpolate triangle vertices toward center
            grad_upper = []
            for pt in upper:
                gx = cx + (pt[0] - cx) * t
                gy = cy + (pt[1] - cy) * t
                grad_upper.append((gx, gy))

            # Color shifts based on treble energy
            hue_shift = treble_energy * 0.08 * math.sin(pulse_phase * 3 + 1.5)

            base_r = self.config.tetra_upper_color[0]
            base_g = self.config.tetra_upper_color[1]
            base_b = self.config.tetra_upper_color[2]

            # Gradient: darker at edges, brighter toward center
            brightness = 0.15 + 0.5 * (1 - t) * upper_intensity * energy_pulse

            # Add subtle color variation - shifts toward purple/white on high energy
            r = int(min(255, base_r * brightness * (1 + hue_shift * 0.5)))
            g = int(min(255, base_g * brightness * (1 - hue_shift * 0.3)))
            b = int(min(255, base_b * brightness * (1 + hue_shift)))

            fill_color = (r, g, b)
            draw.polygon(grad_upper, fill=fill_color)

        # Draw upper triangle outline with glow effect
        upper_glow_intensity = 0.6 + treble_energy * 0.4
        for glow_width in range(4, 0, -1):
            glow_alpha = upper_glow_intensity * (0.3 / glow_width)
            glow_color = (
                int(min(255, self.config.tetra_upper_color[0] * glow_alpha * 0.7)),
                int(min(255, self.config.tetra_upper_color[1] * glow_alpha)),
                int(min(255, self.config.tetra_upper_color[2] * glow_alpha * 1.3))
            )
            draw.polygon(upper, outline=glow_color, width=self.config.tetra_line_width + glow_width)

        # Hexagram intersection points with enhanced pulsing glow
        hex_points = self.geometry.hexagram_points(self.center, self.base_radius, self.main_rotation)
        combined_energy = (bass_energy + treble_energy) / 2

        for idx, point in enumerate(hex_points):
            # Each point pulses slightly differently
            point_phase = pulse_phase + idx * 0.5
            point_pulse = 0.7 + 0.3 * math.sin(point_phase)

            glow_size = 5 + int(10 * combined_energy * point_pulse)

            # Alternate colors between warm and cool at intersection points
            if idx % 2 == 0:
                glow_color = (
                    int(255 * point_pulse),
                    int(220 * point_pulse),
                    int(150 * point_pulse)
                )
            else:
                glow_color = (
                    int(180 * point_pulse),
                    int(200 * point_pulse),
                    int(255 * point_pulse)
                )

            self._draw_glow_point(draw, point, glow_size, glow_color)

    def _render_ophanim(self, draw: ImageDraw.Draw, spectrum: np.ndarray,
                        frequencies: np.ndarray, mid_energy: float):
        """Render the Ophanim - wheels within wheels."""

        # Four wheels at cardinal positions
        wheel_distance = self.base_radius * 0.7

        for i, creature in enumerate(self.config.chayot_positions):
            angle = math.radians(self.main_rotation + i * 90)
            wheel_center = (
                self.center[0] + wheel_distance * math.cos(angle),
                self.center[1] - wheel_distance * math.sin(angle)
            )

            wheel_radius = self.base_radius * 0.35

            # Get frequency band for this wheel
            freq_start = int(len(spectrum) * i / 4)
            freq_end = int(len(spectrum) * (i + 1) / 4)
            wheel_spectrum = spectrum[freq_start:freq_end]
            wheel_freqs = frequencies[freq_start:freq_end]

            # Render rings with "eyes"
            rings = self.geometry.ophan_wheel(
                wheel_center, wheel_radius,
                self.wheel_rotation + i * 45,  # Offset each wheel
                num_rings=self.config.wheel_rings,
                points_per_ring=self.config.num_eyes_per_ring
            )

            # Draw ring circles
            for ring_idx, ring_points in enumerate(rings):
                ring_radius = wheel_radius * (0.4 + 0.3 * ring_idx / len(rings))
                ring_color_intensity = 0.3 + mid_energy * 0.5
                ring_color = tuple(int(c * ring_color_intensity)
                                  for c in self.config.wheel_color)

                draw.ellipse(
                    [wheel_center[0] - ring_radius, wheel_center[1] - ring_radius,
                     wheel_center[0] + ring_radius, wheel_center[1] + ring_radius],
                    outline=ring_color, width=1
                )

                # Draw "eyes" (frequency points) on ring
                for j, point in enumerate(ring_points):
                    if len(wheel_spectrum) > 0:
                        spec_idx = min(j % len(wheel_spectrum), len(wheel_spectrum) - 1)
                        amp = wheel_spectrum[spec_idx]
                        freq = wheel_freqs[spec_idx] if spec_idx < len(wheel_freqs) else 440

                        if amp > 0.05:
                            color = self.freq_to_color(freq, amp)
                            size = self.config.eye_base_size + int(amp * self.config.eye_max_size)
                            self._draw_eye(draw, point, size, color)

    def _render_eyes(self, draw: ImageDraw.Draw, spectrum: np.ndarray,
                     frequencies: np.ndarray):
        """Render the 'eyes' - frequency visualization points on the structure."""

        # Distribute eyes along hexagram edges
        hex_points = self.geometry.hexagram_points(self.center, self.base_radius, self.main_rotation)

        # Also on triangle edges
        upper, lower = self.geometry.star_tetrahedron_2d(
            self.center, self.base_radius, self.main_rotation
        )

        all_edges = []
        for i in range(3):
            all_edges.append((upper[i], upper[(i+1)%3]))
            all_edges.append((lower[i], lower[(i+1)%3]))

        # Distribute spectrum across edges
        points_per_edge = len(spectrum) // len(all_edges)

        for edge_idx, (p1, p2) in enumerate(all_edges):
            start_freq_idx = edge_idx * points_per_edge
            end_freq_idx = start_freq_idx + points_per_edge

            for i in range(min(points_per_edge, 8)):  # Max 8 eyes per edge
                t = (i + 1) / (min(points_per_edge, 8) + 1)
                x = p1[0] + t * (p2[0] - p1[0])
                y = p1[1] + t * (p2[1] - p1[1])

                freq_idx = start_freq_idx + i * (end_freq_idx - start_freq_idx) // max(1, points_per_edge)
                freq_idx = min(freq_idx, len(spectrum) - 1)

                amp = spectrum[freq_idx]
                freq = frequencies[freq_idx]

                if amp > 0.08:
                    color = self.freq_to_color(freq, amp)
                    size = self.config.eye_base_size + int(amp * (self.config.eye_max_size - self.config.eye_base_size))
                    self._draw_eye(draw, (x, y), size, color)

    def _render_fire(self, draw: ImageDraw.Draw, energy: float):
        """Render fire/energy flowing between elements."""

        # Fire particles moving between triangles
        num_particles = int(10 + energy * 20)

        for i in range(num_particles):
            # Random position along structure
            angle = (self.main_rotation + i * 37) % 360
            distance = self.base_radius * (0.3 + 0.4 * ((i * 7) % 10) / 10)

            x = self.center[0] + distance * math.cos(math.radians(angle))
            y = self.center[1] - distance * math.sin(math.radians(angle))

            # Fire color (amber to white)
            intensity = 0.3 + energy * 0.7
            fire_colors = [
                (255, int(100 * intensity), 0),
                (255, int(180 * intensity), int(50 * intensity)),
                (255, int(220 * intensity), int(150 * intensity)),
            ]
            color = fire_colors[i % 3]

            size = 2 + int(energy * 4)
            draw.ellipse([x-size, y-size, x+size, y+size], fill=color)

    def _render_throne(self, draw: ImageDraw.Draw):
        """Render the center throne with divine light."""
        cx, cy = self.center

        throne_radius = self.base_radius * self.config.throne_radius
        glow_radius = self.base_radius * self.config.throne_glow_radius

        energy = self.throne_energy

        # Outer glow layers
        for i in range(5, 0, -1):
            r = glow_radius * (1 + i * 0.2) * (0.5 + energy * 0.5)
            alpha = int(30 * energy * (6 - i) / 5)

            glow_color = (
                min(255, int(self.config.throne_color[0] * 0.4) + alpha),
                min(255, int(self.config.throne_color[1] * 0.4) + alpha),
                min(255, int(self.config.throne_color[2] * 0.3) + alpha)
            )

            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=glow_color)

        # Inner throne
        inner_color = tuple(int(c * (0.6 + energy * 0.4)) for c in self.config.throne_color)
        draw.ellipse(
            [cx - throne_radius, cy - throne_radius,
             cx + throne_radius, cy + throne_radius],
            fill=inner_color
        )

        # Bright core
        core_radius = throne_radius * 0.4
        draw.ellipse(
            [cx - core_radius, cy - core_radius,
             cx + core_radius, cy + core_radius],
            fill=(255, 255, 255)
        )

    def _render_lightning(self, draw: ImageDraw.Draw):
        """Render lightning effect on beats."""
        cx, cy = self.center

        # Random lightning bolts from center
        num_bolts = np.random.randint(2, 5)

        for _ in range(num_bolts):
            angle = np.random.uniform(0, 360)
            length = self.base_radius * np.random.uniform(0.8, 1.3)

            # Jagged path
            points = [(cx, cy)]
            segments = np.random.randint(3, 6)

            for i in range(segments):
                t = (i + 1) / segments
                base_x = cx + length * t * math.cos(math.radians(angle))
                base_y = cy - length * t * math.sin(math.radians(angle))

                # Add jitter
                jitter = length * 0.1 * (1 - t)
                x = base_x + np.random.uniform(-jitter, jitter)
                y = base_y + np.random.uniform(-jitter, jitter)
                points.append((x, y))

            # Draw lightning
            draw.line(points, fill=(255, 255, 255), width=2)
            draw.line(points, fill=(200, 200, 255), width=1)

    def _draw_eye(self, draw: ImageDraw.Draw, center: Tuple[float, float],
                  size: int, color: Tuple[int, int, int]):
        """Draw an 'eye' point with glow effect."""
        x, y = center

        # Outer glow
        for i in range(2, 0, -1):
            glow_size = size + i * 2
            glow_color = tuple(int(c * 0.3 / i) for c in color)
            draw.ellipse(
                [x - glow_size, y - glow_size, x + glow_size, y + glow_size],
                fill=glow_color
            )

        # Core
        draw.ellipse([x - size, y - size, x + size, y + size], fill=color)

        # Bright center
        if size > 3:
            inner = max(1, size // 3)
            bright = tuple(min(255, c + 50) for c in color)
            draw.ellipse([x - inner, y - inner, x + inner, y + inner], fill=bright)

    def _draw_glow_point(self, draw: ImageDraw.Draw, center: Tuple[float, float],
                         size: int, color: Tuple[int, int, int]):
        """Draw a glowing point."""
        x, y = center

        for i in range(3, 0, -1):
            r = size * i / 2
            alpha = 1.0 / i
            c = tuple(int(v * alpha) for v in color)
            draw.ellipse([x - r, y - r, x + r, y + r], fill=c)


# Convenience function for quick testing
def create_merkabah_renderer(width: int = 1280, height: int = 720) -> MerkabahRenderer:
    """Create a Merkabah renderer with default settings."""
    config = MerkabahConfig(frame_width=width, frame_height=height)
    return MerkabahRenderer(config)


if __name__ == '__main__':
    # Test render
    renderer = create_merkabah_renderer()

    # Fake spectrum for testing
    frequencies = np.linspace(50, 8000, 381)
    spectrum = np.random.rand(381) * 0.5
    spectrum[50:100] = 0.8  # Bass boost
    spectrum[200:250] = 0.6  # Mid presence

    for i in range(30):
        renderer.update_state(
            beat_strength=0.8 if i % 15 == 0 else 0.2,
            is_beat=(i % 15 == 0),
            pitch=440 if i % 5 == 0 else 0,
            rms=0.5 + 0.3 * np.sin(i / 5)
        )

        frame = renderer.render_frame(spectrum, frequencies)
        frame.save(f'/tmp/merkabah_test_{i:03d}.png')

    print("Test frames saved to /tmp/merkabah_test_*.png")
