#!/usr/bin/env python3
"""
SYNESTHESIA - High-Quality Merkabah Renderer
=============================================
Enhanced renderer using Cairo for smooth anti-aliased graphics,
proper gradients, and professional visual quality.

Features:
- Anti-aliased vector graphics via Cairo
- Smooth radial and linear gradients
- Alpha blending and compositing
- Gaussian blur glow effects
- High-quality color interpolation
"""

import numpy as np
import cairo
import math
from PIL import Image, ImageFilter
from dataclasses import dataclass
from typing import Tuple, List, Optional
from collections import deque
import colorsys


@dataclass
class MerkabahHQConfig:
    """Configuration for high-quality Merkabah visualization."""
    # Frame dimensions
    frame_width: int = 1280
    frame_height: int = 720

    # Anti-aliasing quality (1 = normal, 2 = 2x supersampling)
    supersample: int = 1

    # Merkabah geometry
    merkabah_scale: float = 0.38
    rotation_speed: float = 0.5

    # Star Tetrahedron colors (RGB 0-1 for Cairo)
    tetra_upper_color: Tuple[float, float, float] = (0.39, 0.59, 1.0)   # Heavenly blue
    tetra_lower_color: Tuple[float, float, float] = (1.0, 0.59, 0.39)   # Earthly amber

    # Ophanim (Wheels)
    num_wheels: int = 4
    wheel_rings: int = 3
    wheel_rotation_speed: float = 1.2
    wheel_color: Tuple[float, float, float] = (0.78, 0.71, 0.39)  # Golden

    # Eyes
    num_eyes_per_ring: int = 12
    eye_base_size: float = 3
    eye_max_size: float = 15

    # Throne
    throne_radius: float = 0.08
    throne_glow_radius: float = 0.18
    throne_color: Tuple[float, float, float] = (1.0, 1.0, 0.85)

    # Effects
    enable_fire: bool = True
    fire_intensity: float = 0.5
    lightning_on_beat: bool = True
    glow_blur_radius: int = 8

    # Trail
    trail_length: int = 10
    trail_decay: float = 0.7

    # Background
    background_color: Tuple[float, float, float] = (0.02, 0.02, 0.06)

    # Color settings
    color_saturation: float = 0.95
    brightness_min: float = 0.35
    brightness_max: float = 1.0


class MerkabahGeometryHQ:
    """Sacred geometry calculations optimized for Cairo rendering."""

    @staticmethod
    def star_tetrahedron_2d(center: Tuple[float, float], radius: float,
                            rotation: float = 0) -> Tuple[List[Tuple], List[Tuple]]:
        """Calculate 2D projection of star tetrahedron."""
        cx, cy = center

        upper_points = []
        for i in range(3):
            angle = math.radians(rotation + 90 + i * 120)
            x = cx + radius * math.cos(angle)
            y = cy - radius * math.sin(angle)
            upper_points.append((x, y))

        lower_points = []
        for i in range(3):
            angle = math.radians(rotation + 270 + i * 120)
            x = cx + radius * math.cos(angle)
            y = cy - radius * math.sin(angle)
            lower_points.append((x, y))

        return upper_points, lower_points

    @staticmethod
    def hexagram_points(center: Tuple[float, float], radius: float,
                        rotation: float = 0) -> List[Tuple]:
        """Calculate the 6 intersection points of the hexagram."""
        cx, cy = center
        inner_radius = radius * 0.5

        points = []
        for i in range(6):
            angle = math.radians(rotation + 30 + i * 60)
            x = cx + inner_radius * math.cos(angle)
            y = cy - inner_radius * math.sin(angle)
            points.append((x, y))

        return points

    @staticmethod
    def ophan_wheel_points(center: Tuple[float, float], radius: float,
                           rotation: float, num_rings: int = 3,
                           points_per_ring: int = 12) -> List[List[Tuple]]:
        """Calculate wheel within wheel structure."""
        cx, cy = center
        rings = []

        for ring_idx in range(num_rings):
            ring_radius = radius * (0.4 + 0.3 * ring_idx / num_rings)
            ring_rotation = rotation + ring_idx * 15

            ring_points = []
            for i in range(points_per_ring):
                angle = math.radians(ring_rotation + i * (360 / points_per_ring))
                x = cx + ring_radius * math.cos(angle)
                y = cy - ring_radius * math.sin(angle)
                ring_points.append((x, y))

            rings.append((ring_radius, ring_points))

        return rings


class MerkabahRendererHQ:
    """
    High-quality Merkabah renderer using Cairo graphics library.

    Improvements over PIL version:
    - True anti-aliased vector graphics
    - Smooth radial gradients
    - Proper alpha compositing
    - Better color interpolation
    - Post-processing glow effects
    """

    def __init__(self, config: MerkabahHQConfig):
        self.config = config
        self.geometry = MerkabahGeometryHQ()

        # Rendering dimensions (with optional supersampling)
        self.render_width = config.frame_width * config.supersample
        self.render_height = config.frame_height * config.supersample
        self.output_width = config.frame_width
        self.output_height = config.frame_height

        self.center = (self.render_width / 2, self.render_height / 2)
        self.base_radius = min(self.render_width, self.render_height) * config.merkabah_scale

        # Animation state
        self.main_rotation = 0.0
        self.wheel_rotation = 0.0
        self.frame_count = 0

        # Energy state
        self.throne_energy = 0.0
        self.fire_energy = 0.0
        self.lightning_active = False

        # Trail history
        self.eye_history: deque = deque(maxlen=config.trail_length)

        # Harmony color
        self.current_hue = 0.55
        self.target_hue = 0.55

    def update_state(self, beat_strength: float = 0, is_beat: bool = False,
                     pitch: float = 0, chroma: np.ndarray = None,
                     rms: float = 0.5):
        """Update animation state based on audio features."""
        energy_factor = 0.5 + rms * 1.5
        self.main_rotation += self.config.rotation_speed * energy_factor
        self.wheel_rotation += self.config.wheel_rotation_speed * energy_factor
        self.frame_count += 1

        if pitch > 0:
            self.throne_energy = min(1.0, self.throne_energy + 0.3)
        self.throne_energy *= 0.92

        self.fire_energy = rms
        self.lightning_active = is_beat and beat_strength > 0.5

        if chroma is not None and len(chroma) >= 12:
            dominant_pc = np.argmax(chroma[:12])
            self.target_hue = dominant_pc / 12.0

        self.current_hue += (self.target_hue - self.current_hue) * 0.05

    def render_frame(self, spectrum: np.ndarray, frequencies: np.ndarray,
                     temporal_features: dict = None) -> Image.Image:
        """Render a high-quality frame with Cairo."""

        # Normalize spectrum
        if spectrum.max() > 0:
            spectrum = spectrum / spectrum.max()
        spectrum = np.clip(spectrum, 0, 1)

        # Create Cairo surface
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32,
                                     self.render_width, self.render_height)
        ctx = cairo.Context(surface)

        # Enable anti-aliasing
        ctx.set_antialias(cairo.ANTIALIAS_BEST)

        # Calculate energies
        bass_energy, mid_energy, treble_energy = self._calculate_band_energies(spectrum, frequencies)

        # Store spectrum for trails
        self.eye_history.append((spectrum.copy(), frequencies.copy()))

        # Render layers
        self._render_background(ctx, bass_energy, mid_energy, treble_energy)
        self._render_aura(ctx, bass_energy, mid_energy, treble_energy)
        self._render_ophanim(ctx, spectrum, frequencies, mid_energy)
        self._render_star_tetrahedron(ctx, bass_energy, treble_energy)
        self._render_eyes(ctx, spectrum, frequencies)

        if self.config.enable_fire:
            self._render_fire(ctx, bass_energy + treble_energy)

        self._render_throne(ctx)

        if self.lightning_active and self.config.lightning_on_beat:
            self._render_lightning(ctx)

        # Convert to PIL Image
        image = self._surface_to_pil(surface)

        # Apply post-processing glow
        if self.config.glow_blur_radius > 0:
            image = self._apply_glow(image)

        # Downsample if supersampled
        if self.config.supersample > 1:
            image = image.resize((self.output_width, self.output_height),
                                Image.Resampling.LANCZOS)

        return image

    def _calculate_band_energies(self, spectrum: np.ndarray,
                                  frequencies: np.ndarray) -> Tuple[float, float, float]:
        """Calculate energy in frequency bands."""
        bass_mask = frequencies < 250
        mid_mask = (frequencies >= 250) & (frequencies < 2000)
        treble_mask = frequencies >= 2000

        bass = np.mean(spectrum[bass_mask]) if np.any(bass_mask) else 0
        mid = np.mean(spectrum[mid_mask]) if np.any(mid_mask) else 0
        treble = np.mean(spectrum[treble_mask]) if np.any(treble_mask) else 0

        total = bass + mid + treble + 0.001
        return bass/total, mid/total, treble/total

    def _render_background(self, ctx: cairo.Context, bass: float, mid: float, treble: float):
        """Render background with subtle gradient."""
        bg = self.config.background_color

        # Create radial gradient for subtle vignette
        cx, cy = self.center
        gradient = cairo.RadialGradient(cx, cy, 0, cx, cy, self.base_radius * 2)

        # Center slightly lighter
        energy = (bass + mid + treble) / 3
        center_boost = 0.02 + energy * 0.03

        gradient.add_color_stop_rgb(0, bg[0] + center_boost, bg[1] + center_boost, bg[2] + center_boost * 1.5)
        gradient.add_color_stop_rgb(0.7, bg[0], bg[1], bg[2])
        gradient.add_color_stop_rgb(1, bg[0] * 0.5, bg[1] * 0.5, bg[2] * 0.5)

        ctx.set_source(gradient)
        ctx.paint()

    def _render_aura(self, ctx: cairo.Context, bass: float, mid: float, treble: float):
        """Render background aura with smooth gradients."""
        cx, cy = self.center

        # Outer aura
        for i in range(3):
            radius = self.base_radius * (1.8 - i * 0.3)
            alpha = 0.08 * (3 - i) / 3 * (bass * 0.5 + mid * 0.3 + treble * 0.2)

            gradient = cairo.RadialGradient(cx, cy, 0, cx, cy, radius)

            # Color based on dominant frequency
            if bass > mid and bass > treble:
                gradient.add_color_stop_rgba(0, 0.8, 0.4, 0.2, alpha)
            elif treble > mid:
                gradient.add_color_stop_rgba(0, 0.4, 0.5, 0.9, alpha)
            else:
                gradient.add_color_stop_rgba(0, 0.3, 0.5, 0.7, alpha)

            gradient.add_color_stop_rgba(1, 0, 0, 0, 0)

            ctx.set_source(gradient)
            ctx.arc(cx, cy, radius, 0, 2 * math.pi)
            ctx.fill()

    def _render_star_tetrahedron(self, ctx: cairo.Context,
                                  bass_energy: float, treble_energy: float):
        """Render star tetrahedron with smooth Cairo gradients."""
        upper, lower = self.geometry.star_tetrahedron_2d(
            self.center, self.base_radius, self.main_rotation
        )

        cx, cy = self.center
        pulse_phase = self.main_rotation * 0.02
        energy_pulse = 0.7 + 0.3 * math.sin(pulse_phase)

        # Lower triangle (Earth/Bass)
        self._render_gradient_triangle(ctx, lower, cx, cy,
                                       self.config.tetra_lower_color,
                                       bass_energy, energy_pulse,
                                       hue_shift_amount=0.05,
                                       warm=True)

        # Upper triangle (Heaven/Treble)
        self._render_gradient_triangle(ctx, upper, cx, cy,
                                       self.config.tetra_upper_color,
                                       treble_energy, energy_pulse,
                                       hue_shift_amount=0.08,
                                       warm=False)

        # Hexagram intersection points
        hex_points = self.geometry.hexagram_points(self.center, self.base_radius, self.main_rotation)
        combined_energy = (bass_energy + treble_energy) / 2

        for idx, point in enumerate(hex_points):
            point_phase = pulse_phase + idx * 0.5
            point_pulse = 0.7 + 0.3 * math.sin(point_phase)
            glow_size = 6 + 12 * combined_energy * point_pulse

            if idx % 2 == 0:
                color = (1.0, 0.86, 0.59)  # Warm gold
            else:
                color = (0.71, 0.78, 1.0)  # Cool blue

            self._draw_glow_point(ctx, point, glow_size, color, point_pulse)

    def _render_gradient_triangle(self, ctx: cairo.Context, points: List[Tuple],
                                   cx: float, cy: float,
                                   base_color: Tuple[float, float, float],
                                   energy: float, energy_pulse: float,
                                   hue_shift_amount: float, warm: bool):
        """Render a triangle with radial gradient fill."""

        # Calculate triangle centroid for gradient center
        tri_cx = sum(p[0] for p in points) / 3
        tri_cy = sum(p[1] for p in points) / 3

        # Calculate approximate radius
        max_dist = max(math.sqrt((p[0] - tri_cx)**2 + (p[1] - tri_cy)**2) for p in points)

        intensity = 0.5 + energy * 0.5
        hue_shift = energy * hue_shift_amount * math.sin(self.main_rotation * 0.04)

        # Create radial gradient
        gradient = cairo.RadialGradient(tri_cx, tri_cy, 0, tri_cx, tri_cy, max_dist)

        # Inner color (bright)
        inner_brightness = 0.7 * intensity * energy_pulse
        if warm:
            r = min(1.0, base_color[0] * inner_brightness * (1 + hue_shift))
            g = min(1.0, base_color[1] * inner_brightness * (1 - hue_shift * 0.3))
            b = min(1.0, base_color[2] * inner_brightness * 0.4)
        else:
            r = min(1.0, base_color[0] * inner_brightness * (1 + hue_shift * 0.3))
            g = min(1.0, base_color[1] * inner_brightness)
            b = min(1.0, base_color[2] * inner_brightness * (1 + hue_shift))

        gradient.add_color_stop_rgba(0, r, g, b, 0.9)

        # Outer color (darker, more transparent)
        outer_brightness = 0.25 * intensity * energy_pulse
        if warm:
            r = base_color[0] * outer_brightness
            g = base_color[1] * outer_brightness * 0.6
            b = base_color[2] * outer_brightness * 0.2
        else:
            r = base_color[0] * outer_brightness * 0.5
            g = base_color[1] * outer_brightness * 0.7
            b = base_color[2] * outer_brightness

        gradient.add_color_stop_rgba(1, r, g, b, 0.4)

        # Draw filled triangle
        ctx.move_to(points[0][0], points[0][1])
        for p in points[1:]:
            ctx.line_to(p[0], p[1])
        ctx.close_path()

        ctx.set_source(gradient)
        ctx.fill_preserve()

        # Draw glowing outline
        glow_intensity = 0.6 + energy * 0.4
        for glow_width in [6, 4, 2, 1]:
            alpha = glow_intensity * (0.15 / (glow_width ** 0.5))

            if warm:
                ctx.set_source_rgba(1.0, 0.7, 0.3, alpha)
            else:
                ctx.set_source_rgba(0.5, 0.7, 1.0, alpha)

            ctx.set_line_width(glow_width * (self.config.supersample or 1))
            ctx.stroke_preserve()

        ctx.new_path()

    def _render_ophanim(self, ctx: cairo.Context, spectrum: np.ndarray,
                        frequencies: np.ndarray, mid_energy: float):
        """Render the Ophanim wheels with smooth graphics."""
        wheel_distance = self.base_radius * 0.7

        for i in range(self.config.num_wheels):
            angle = math.radians(self.main_rotation + i * 90)
            wheel_cx = self.center[0] + wheel_distance * math.cos(angle)
            wheel_cy = self.center[1] - wheel_distance * math.sin(angle)
            wheel_radius = self.base_radius * 0.35

            # Get frequency band for this wheel
            freq_start = int(len(spectrum) * i / 4)
            freq_end = int(len(spectrum) * (i + 1) / 4)
            wheel_spectrum = spectrum[freq_start:freq_end]
            wheel_freqs = frequencies[freq_start:freq_end]

            # Render rings
            rings = self.geometry.ophan_wheel_points(
                (wheel_cx, wheel_cy), wheel_radius,
                self.wheel_rotation + i * 45,
                num_rings=self.config.wheel_rings,
                points_per_ring=self.config.num_eyes_per_ring
            )

            for ring_idx, (ring_radius, ring_points) in enumerate(rings):
                # Ring glow
                ring_alpha = 0.3 + mid_energy * 0.4
                gradient = cairo.RadialGradient(wheel_cx, wheel_cy, ring_radius * 0.95,
                                               wheel_cx, wheel_cy, ring_radius * 1.05)
                gradient.add_color_stop_rgba(0, 0.8, 0.7, 0.4, ring_alpha * 0.5)
                gradient.add_color_stop_rgba(0.5, 0.8, 0.7, 0.4, ring_alpha)
                gradient.add_color_stop_rgba(1, 0.8, 0.7, 0.4, ring_alpha * 0.5)

                ctx.set_source(gradient)
                ctx.set_line_width(2 * (self.config.supersample or 1))
                ctx.arc(wheel_cx, wheel_cy, ring_radius, 0, 2 * math.pi)
                ctx.stroke()

                # Eyes on ring
                for j, point in enumerate(ring_points):
                    if len(wheel_spectrum) > 0:
                        spec_idx = min(j % len(wheel_spectrum), len(wheel_spectrum) - 1)
                        amp = wheel_spectrum[spec_idx]
                        freq = wheel_freqs[spec_idx] if spec_idx < len(wheel_freqs) else 440

                        if amp > 0.05:
                            color = self._freq_to_color(freq, amp)
                            size = self.config.eye_base_size + amp * self.config.eye_max_size
                            self._draw_eye(ctx, point, size, color, amp)

    def _render_eyes(self, ctx: cairo.Context, spectrum: np.ndarray,
                     frequencies: np.ndarray):
        """Render eyes distributed on the structure."""
        upper, lower = self.geometry.star_tetrahedron_2d(
            self.center, self.base_radius, self.main_rotation
        )

        all_edges = []
        for i in range(3):
            all_edges.append((upper[i], upper[(i+1)%3]))
            all_edges.append((lower[i], lower[(i+1)%3]))

        points_per_edge = len(spectrum) // len(all_edges)

        for edge_idx, (p1, p2) in enumerate(all_edges):
            start_freq_idx = edge_idx * points_per_edge

            for i in range(min(points_per_edge, 8)):
                t = (i + 1) / (min(points_per_edge, 8) + 1)
                x = p1[0] + t * (p2[0] - p1[0])
                y = p1[1] + t * (p2[1] - p1[1])

                freq_idx = min(start_freq_idx + i, len(spectrum) - 1)
                amp = spectrum[freq_idx]
                freq = frequencies[freq_idx]

                if amp > 0.08:
                    color = self._freq_to_color(freq, amp)
                    size = self.config.eye_base_size + amp * (self.config.eye_max_size - self.config.eye_base_size)
                    self._draw_eye(ctx, (x, y), size, color, amp)

    def _render_fire(self, ctx: cairo.Context, energy: float):
        """Render fire particles with smooth gradients."""
        num_particles = int(10 + energy * 25)

        for i in range(num_particles):
            angle = (self.main_rotation + i * 37) % 360
            distance = self.base_radius * (0.3 + 0.4 * ((i * 7) % 10) / 10)

            x = self.center[0] + distance * math.cos(math.radians(angle))
            y = self.center[1] - distance * math.sin(math.radians(angle))

            intensity = 0.3 + energy * 0.7
            size = 3 + energy * 6

            # Fire gradient
            gradient = cairo.RadialGradient(x, y, 0, x, y, size * 2)

            fire_phase = (self.frame_count * 0.3 + i * 0.5) % 1.0
            if fire_phase < 0.33:
                gradient.add_color_stop_rgba(0, 1.0, 0.9, 0.5, intensity)
                gradient.add_color_stop_rgba(0.5, 1.0, 0.5, 0.1, intensity * 0.5)
            elif fire_phase < 0.66:
                gradient.add_color_stop_rgba(0, 1.0, 0.6, 0.2, intensity)
                gradient.add_color_stop_rgba(0.5, 1.0, 0.3, 0.0, intensity * 0.5)
            else:
                gradient.add_color_stop_rgba(0, 1.0, 0.4, 0.1, intensity)
                gradient.add_color_stop_rgba(0.5, 0.8, 0.2, 0.0, intensity * 0.5)

            gradient.add_color_stop_rgba(1, 0, 0, 0, 0)

            ctx.set_source(gradient)
            ctx.arc(x, y, size * 2, 0, 2 * math.pi)
            ctx.fill()

    def _render_throne(self, ctx: cairo.Context):
        """Render the center throne with radiant glow."""
        cx, cy = self.center
        throne_radius = self.base_radius * self.config.throne_radius
        glow_radius = self.base_radius * self.config.throne_glow_radius

        energy = self.throne_energy

        # Outer glow
        gradient = cairo.RadialGradient(cx, cy, 0, cx, cy, glow_radius * (1 + energy * 0.5))
        gradient.add_color_stop_rgba(0, 1.0, 1.0, 0.9, 0.8 * energy)
        gradient.add_color_stop_rgba(0.3, 1.0, 0.95, 0.7, 0.4 * energy)
        gradient.add_color_stop_rgba(0.6, 1.0, 0.85, 0.5, 0.15 * energy)
        gradient.add_color_stop_rgba(1, 0, 0, 0, 0)

        ctx.set_source(gradient)
        ctx.arc(cx, cy, glow_radius * (1 + energy * 0.5), 0, 2 * math.pi)
        ctx.fill()

        # Inner throne
        gradient = cairo.RadialGradient(cx, cy, 0, cx, cy, throne_radius)
        brightness = 0.6 + energy * 0.4
        gradient.add_color_stop_rgb(0, 1.0, 1.0, 1.0)
        gradient.add_color_stop_rgb(0.5, 1.0 * brightness, 0.98 * brightness, 0.85 * brightness)
        gradient.add_color_stop_rgb(1, 0.9 * brightness, 0.85 * brightness, 0.6 * brightness)

        ctx.set_source(gradient)
        ctx.arc(cx, cy, throne_radius, 0, 2 * math.pi)
        ctx.fill()

    def _render_lightning(self, ctx: cairo.Context):
        """Render lightning bolts with glow."""
        cx, cy = self.center
        num_bolts = np.random.randint(2, 5)

        for _ in range(num_bolts):
            angle = np.random.uniform(0, 360)
            length = self.base_radius * np.random.uniform(0.8, 1.3)

            points = [(cx, cy)]
            segments = np.random.randint(3, 6)

            for i in range(segments):
                t = (i + 1) / segments
                base_x = cx + length * t * math.cos(math.radians(angle))
                base_y = cy - length * t * math.sin(math.radians(angle))

                jitter = length * 0.1 * (1 - t)
                x = base_x + np.random.uniform(-jitter, jitter)
                y = base_y + np.random.uniform(-jitter, jitter)
                points.append((x, y))

            # Draw glow
            for width, alpha in [(8, 0.2), (4, 0.4), (2, 0.8)]:
                ctx.set_source_rgba(0.8, 0.85, 1.0, alpha)
                ctx.set_line_width(width * (self.config.supersample or 1))
                ctx.set_line_cap(cairo.LINE_CAP_ROUND)
                ctx.set_line_join(cairo.LINE_JOIN_ROUND)

                ctx.move_to(points[0][0], points[0][1])
                for p in points[1:]:
                    ctx.line_to(p[0], p[1])
                ctx.stroke()

            # Core
            ctx.set_source_rgba(1.0, 1.0, 1.0, 1.0)
            ctx.set_line_width(1 * (self.config.supersample or 1))
            ctx.move_to(points[0][0], points[0][1])
            for p in points[1:]:
                ctx.line_to(p[0], p[1])
            ctx.stroke()

    def _draw_eye(self, ctx: cairo.Context, center: Tuple[float, float],
                  size: float, color: Tuple[float, float, float], intensity: float = 1.0):
        """Draw an eye with smooth gradient glow."""
        x, y = center

        # Outer glow
        gradient = cairo.RadialGradient(x, y, 0, x, y, size * 3)
        gradient.add_color_stop_rgba(0, color[0], color[1], color[2], 0.8 * intensity)
        gradient.add_color_stop_rgba(0.3, color[0], color[1], color[2], 0.3 * intensity)
        gradient.add_color_stop_rgba(1, color[0], color[1], color[2], 0)

        ctx.set_source(gradient)
        ctx.arc(x, y, size * 3, 0, 2 * math.pi)
        ctx.fill()

        # Core
        gradient = cairo.RadialGradient(x, y, 0, x, y, size)
        gradient.add_color_stop_rgb(0, min(1, color[0] + 0.3), min(1, color[1] + 0.3), min(1, color[2] + 0.3))
        gradient.add_color_stop_rgb(1, color[0], color[1], color[2])

        ctx.set_source(gradient)
        ctx.arc(x, y, size, 0, 2 * math.pi)
        ctx.fill()

    def _draw_glow_point(self, ctx: cairo.Context, center: Tuple[float, float],
                         size: float, color: Tuple[float, float, float], intensity: float = 1.0):
        """Draw a glowing point."""
        x, y = center

        gradient = cairo.RadialGradient(x, y, 0, x, y, size * 2)
        gradient.add_color_stop_rgba(0, color[0], color[1], color[2], intensity)
        gradient.add_color_stop_rgba(0.4, color[0], color[1], color[2], intensity * 0.5)
        gradient.add_color_stop_rgba(1, color[0], color[1], color[2], 0)

        ctx.set_source(gradient)
        ctx.arc(x, y, size * 2, 0, 2 * math.pi)
        ctx.fill()

    def _freq_to_color(self, freq: float, amplitude: float = 1.0) -> Tuple[float, float, float]:
        """Map frequency to color (RGB 0-1)."""
        f_min, f_max = 50, 8000

        if freq <= f_min:
            freq_norm = 0
        elif freq >= f_max:
            freq_norm = 1
        else:
            freq_norm = (np.log(freq) - np.log(f_min)) / (np.log(f_max) - np.log(f_min))

        # Color mapping
        if freq_norm < 0.33:
            hue = 0.08 + freq_norm * 0.1
        elif freq_norm < 0.66:
            hue = 0.55 + (freq_norm - 0.33) * 0.15
        else:
            hue = 0.5 + (freq_norm - 0.66) * 0.2

        hue = (hue * 0.7 + self.current_hue * 0.3) % 1.0
        sat = self.config.color_saturation
        val = self.config.brightness_min + amplitude * (self.config.brightness_max - self.config.brightness_min)

        r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
        return (r, g, b)

    def _surface_to_pil(self, surface: cairo.ImageSurface) -> Image.Image:
        """Convert Cairo surface to PIL Image."""
        # Get data from surface
        data = surface.get_data()
        width = surface.get_width()
        height = surface.get_height()

        # Cairo uses BGRA, PIL uses RGBA
        image = Image.frombuffer('RGBA', (width, height), data, 'raw', 'BGRA', 0, 1)
        return image.convert('RGB')

    def _apply_glow(self, image: Image.Image) -> Image.Image:
        """Apply bloom/glow post-processing effect."""
        # Create bright mask
        bright = image.point(lambda x: x * 1.5 if x > 128 else 0)

        # Blur the bright areas
        glow = bright.filter(ImageFilter.GaussianBlur(radius=self.config.glow_blur_radius))

        # Composite
        from PIL import ImageChops
        result = ImageChops.add(image, glow)

        return result


def create_merkabah_renderer_hq(width: int = 1280, height: int = 720) -> MerkabahRendererHQ:
    """Create a high-quality Merkabah renderer."""
    config = MerkabahHQConfig(frame_width=width, frame_height=height)
    return MerkabahRendererHQ(config)


if __name__ == '__main__':
    # Test render
    renderer = create_merkabah_renderer_hq()

    frequencies = np.linspace(50, 8000, 381)
    spectrum = np.random.rand(381) * 0.5
    spectrum[50:100] = 0.8
    spectrum[200:250] = 0.6

    for i in range(10):
        renderer.update_state(
            beat_strength=0.8 if i % 5 == 0 else 0.2,
            is_beat=(i % 5 == 0),
            pitch=440 if i % 3 == 0 else 0,
            rms=0.5 + 0.3 * np.sin(i / 3)
        )

        frame = renderer.render_frame(spectrum, frequencies)
        frame.save(f'/tmp/merkabah_hq_test_{i:03d}.png')

    print("HQ test frames saved to /tmp/merkabah_hq_test_*.png")
