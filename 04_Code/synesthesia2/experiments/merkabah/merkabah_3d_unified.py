#!/usr/bin/env python3
"""
SYNESTHESIA - Unified 3D Merkabah Renderer
============================================
True 3D visualization where the Star Tetrahedron emerges organically from
the curvature of Heaven and Earth planes stretching toward each other.

The Concept:
- Heaven (sky) and Earth (ground) are two parallel infinite planes
- At the center, these planes bend and curve toward each other
- Where they reach toward each other, the curvature forms triangular shapes
- The tetrahedra ARE the manifestation of this reaching - heaven toward earth,
  earth toward heaven
- The edges of the triangles merge seamlessly with the sky/ground colors
  at their far ends

All symbolic elements from the 2D visualization are preserved:
- Ophanim (wheels within wheels) at the four cardinal directions
- Chayot (four living creatures) - Lion, Ox, Eagle, Man
- Eyes full of seeing distributed across the structure
- Fire moving between elements
- Lightning on beats
- The Throne at the center where heaven and earth meet

References:
- Ezekiel 1:4-28 - The Vision of the Merkabah
- "As above, so below" - The planes mirror and reach for each other
"""

import numpy as np
import cairo
import math
from PIL import Image, ImageFilter, ImageDraw, ImageChops
from dataclasses import dataclass, field
from typing import Tuple, List, Optional
from collections import deque
import colorsys


@dataclass
class UnifiedMerkabah3DConfig:
    """Configuration for unified 3D Merkabah visualization."""
    frame_width: int = 1280
    frame_height: int = 720

    # Plane curvature parameters
    plane_curvature: float = 0.8  # How much the planes bend (0=flat, 1=extreme)
    curvature_points: int = 32  # Resolution of curved surfaces

    # Colors - planes merge with tetrahedra
    sky_color_zenith: Tuple[float, float, float] = (0.08, 0.12, 0.35)  # Deep blue sky
    sky_color_horizon: Tuple[float, float, float] = (0.4, 0.5, 0.8)   # Light blue horizon
    earth_color_horizon: Tuple[float, float, float] = (0.45, 0.35, 0.25)  # Earthy brown horizon
    earth_color_deep: Tuple[float, float, float] = (0.15, 0.08, 0.03)  # Deep earth

    # Tetrahedra colors (merge with planes at edges)
    upper_tetra_color: Tuple[float, float, float] = (0.3, 0.5, 1.0)  # Heavenly sapphire
    lower_tetra_color: Tuple[float, float, float] = (1.0, 0.6, 0.3)  # Earthly amber

    # Ophanim (Wheels) settings
    num_wheels: int = 4
    wheel_rings: int = 3
    wheel_radius: float = 0.18  # Relative to frame
    eyes_per_ring: int = 12

    # Chayot (Four Creatures)
    enable_chayot: bool = True
    chayot_glow_radius: float = 25

    # Throne/Center
    throne_radius: float = 0.06
    throne_glow_intensity: float = 0.8

    # Fire and lightning
    enable_fire: bool = True
    fire_particles: int = 40
    lightning_on_beat: bool = True

    # Stars in the heavens
    enable_stars: bool = True
    num_stars: int = 150

    # Animation
    rotation_speed: float = 0.5
    wheel_rotation_speed: float = 1.2
    pulse_speed: float = 0.03

    # Camera
    camera_distance: float = 4.0
    camera_height: float = 0.5
    camera_orbit_speed: float = 0.15

    # Post-processing
    glow_radius: int = 8


class UnifiedMerkabah3DRenderer:
    """
    3D Merkabah renderer where geometry emerges from curving planes.

    The Star Tetrahedron is not separate from sky/earth - it IS the
    curvature of these planes reaching toward each other.
    """

    def __init__(self, config: UnifiedMerkabah3DConfig):
        self.config = config
        self.width = config.frame_width
        self.height = config.frame_height
        self.aspect = self.width / self.height
        self.center = (self.width // 2, self.height // 2)

        # Animation state
        self.main_rotation = 0.0
        self.wheel_rotation = 0.0
        self.camera_orbit = 0.0
        self.pulse_phase = 0.0
        self.frame_count = 0

        # Energy state
        self.bass_energy = 0.0
        self.mid_energy = 0.0
        self.treble_energy = 0.0
        self.throne_energy = 0.0
        self.fire_energy = 0.0
        self.lightning_active = False

        # Color harmony
        self.current_hue = 0.5
        self.target_hue = 0.5

        # Generate stars
        if config.enable_stars:
            self.stars = self._generate_stars()
        else:
            self.stars = []

        # Chayot positions (Lion, Man, Ox, Eagle)
        self.chayot_types = ['lion', 'man', 'ox', 'eagle']

    def _generate_stars(self) -> List[Tuple]:
        """Generate star positions in the heavenly dome."""
        np.random.seed(42)
        stars = []
        for _ in range(self.config.num_stars):
            # Position in upper portion of screen
            x = np.random.uniform(0, self.width)
            y = np.random.uniform(0, self.height * 0.45)
            brightness = np.random.uniform(0.4, 1.0)
            size = np.random.uniform(1, 2.5)
            twinkle_phase = np.random.uniform(0, 2 * math.pi)
            stars.append((x, y, brightness, size, twinkle_phase))
        return stars

    def update_state(self, beat_strength: float = 0, is_beat: bool = False,
                     pitch: float = 0, chroma: np.ndarray = None,
                     rms: float = 0.5, bass: float = 0.33, treble: float = 0.33):
        """Update animation state based on audio features."""

        energy_factor = 0.5 + rms * 1.5

        self.main_rotation += math.radians(self.config.rotation_speed * energy_factor)
        self.wheel_rotation += math.radians(self.config.wheel_rotation_speed * energy_factor)
        self.camera_orbit += math.radians(self.config.camera_orbit_speed * energy_factor)
        self.pulse_phase += self.config.pulse_speed * energy_factor
        self.frame_count += 1

        # Energy states
        self.bass_energy = bass
        self.mid_energy = 1.0 - bass - treble
        self.treble_energy = treble
        self.fire_energy = rms

        # Throne from pitch
        if pitch > 0:
            self.throne_energy = min(1.0, self.throne_energy + 0.3)
        self.throne_energy *= 0.92

        # Lightning on beats
        self.lightning_active = is_beat and beat_strength > 0.5

        # Harmony color
        if chroma is not None and len(chroma) >= 12:
            dominant_pc = np.argmax(chroma[:12])
            self.target_hue = dominant_pc / 12.0
        self.current_hue += (self.target_hue - self.current_hue) * 0.05

    def render_frame(self, spectrum: np.ndarray, frequencies: np.ndarray,
                     temporal_features: dict = None) -> Image.Image:
        """Render a frame with unified heaven-earth visualization."""

        # Normalize spectrum
        if spectrum.max() > 0:
            spectrum = spectrum / spectrum.max()
        spectrum = np.clip(spectrum, 0, 1)

        # Calculate band energies
        bass_mask = frequencies < 250
        mid_mask = (frequencies >= 250) & (frequencies < 2000)
        treble_mask = frequencies >= 2000

        bass = np.mean(spectrum[bass_mask]) if np.any(bass_mask) else 0.33
        mid = np.mean(spectrum[mid_mask]) if np.any(mid_mask) else 0.33
        treble = np.mean(spectrum[treble_mask]) if np.any(treble_mask) else 0.33

        # Create Cairo surface
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.width, self.height)
        ctx = cairo.Context(surface)
        ctx.set_antialias(cairo.ANTIALIAS_BEST)

        # Render layers
        self._render_sky_plane(ctx, treble)
        self._render_stars(ctx)
        self._render_earth_plane(ctx, bass)
        self._render_curved_tetrahedra(ctx, bass, treble)
        self._render_ophanim(ctx, spectrum, frequencies, mid)
        self._render_eyes_on_structure(ctx, spectrum, frequencies)

        if self.config.enable_fire:
            self._render_fire(ctx, bass + treble)

        self._render_throne(ctx)

        if self.config.enable_chayot:
            self._render_chayot(ctx, spectrum, frequencies)

        if self.lightning_active and self.config.lightning_on_beat:
            self._render_lightning(ctx)

        # Convert to PIL and apply glow
        image = self._surface_to_pil(surface)
        if self.config.glow_radius > 0:
            image = self._apply_glow(image)

        return image

    def _render_sky_plane(self, ctx: cairo.Context, treble: float):
        """Render the heavenly sky plane with curvature toward earth."""

        # Sky gradient from zenith to horizon
        gradient = cairo.LinearGradient(0, 0, 0, self.height * 0.55)

        zenith = self.config.sky_color_zenith
        horizon = self.config.sky_color_horizon

        # Pulse with treble energy
        pulse = 0.8 + 0.2 * math.sin(self.pulse_phase * 2)
        energy_boost = treble * 0.15 * pulse

        gradient.add_color_stop_rgb(0,
            min(1, zenith[0] + energy_boost * 0.3),
            min(1, zenith[1] + energy_boost * 0.2),
            min(1, zenith[2] + energy_boost * 0.5))
        gradient.add_color_stop_rgb(0.7,
            min(1, horizon[0] + energy_boost),
            min(1, horizon[1] + energy_boost),
            min(1, horizon[2] + energy_boost))
        gradient.add_color_stop_rgba(1, horizon[0], horizon[1], horizon[2], 0.3)

        ctx.rectangle(0, 0, self.width, self.height * 0.55)
        ctx.set_source(gradient)
        ctx.fill()

        # Curved section where sky bends down toward center
        self._render_sky_curvature(ctx, treble)

    def _render_sky_curvature(self, ctx: cairo.Context, treble: float):
        """Render the curved portion of sky reaching down."""
        cx, cy = self.center

        curvature = self.config.plane_curvature * (0.7 + treble * 0.3)
        horizon_y = self.height * 0.5

        # The sky curves downward toward the center
        # This curvature will form the upper tetrahedron shape
        num_points = self.config.curvature_points

        pulse = 0.85 + 0.15 * math.sin(self.pulse_phase * 2)

        for ring in range(8, 0, -1):
            ring_factor = ring / 8

            points = []
            for i in range(num_points + 1):
                angle = self.main_rotation + (i / num_points) * 2 * math.pi

                # Distance from center affects curve depth
                dist_factor = 0.3 + 0.7 * abs(math.cos(angle * 1.5 + self.main_rotation))

                # Radius decreases as we go deeper
                radius = self.width * 0.4 * ring_factor

                x = cx + radius * math.cos(angle)

                # Y position curves down toward center
                curve_depth = curvature * 80 * (1 - ring_factor) * dist_factor * pulse
                y = horizon_y - 30 * ring_factor + curve_depth

                points.append((x, y))

            # Draw curved band with gradient color
            if len(points) > 2:
                ctx.move_to(points[0][0], points[0][1])
                for p in points[1:]:
                    ctx.line_to(p[0], p[1])

                # Color fades from sky to tetrahedron blue
                t = 1 - ring_factor
                sky_h = self.config.sky_color_horizon
                tetra = self.config.upper_tetra_color

                r = sky_h[0] * (1-t) + tetra[0] * t
                g = sky_h[1] * (1-t) + tetra[1] * t
                b = sky_h[2] * (1-t) + tetra[2] * t

                alpha = 0.15 + 0.25 * t * (0.5 + treble * 0.5)

                ctx.set_source_rgba(r, g, b, alpha * pulse)
                ctx.set_line_width(3 + 5 * t)
                ctx.stroke()

    def _render_earth_plane(self, ctx: cairo.Context, bass: float):
        """Render the earthly ground plane with curvature toward heaven."""

        # Earth gradient from deep to horizon
        gradient = cairo.LinearGradient(0, self.height * 0.45, 0, self.height)

        horizon = self.config.earth_color_horizon
        deep = self.config.earth_color_deep

        pulse = 0.8 + 0.2 * math.sin(self.pulse_phase * 1.5)
        energy_boost = bass * 0.15 * pulse

        gradient.add_color_stop_rgba(0, horizon[0], horizon[1], horizon[2], 0.3)
        gradient.add_color_stop_rgb(0.3,
            min(1, horizon[0] + energy_boost),
            min(1, horizon[1] + energy_boost * 0.7),
            min(1, horizon[2] + energy_boost * 0.3))
        gradient.add_color_stop_rgb(1,
            deep[0], deep[1], deep[2])

        ctx.rectangle(0, self.height * 0.45, self.width, self.height * 0.55)
        ctx.set_source(gradient)
        ctx.fill()

        # Curved section where earth reaches up toward center
        self._render_earth_curvature(ctx, bass)

    def _render_earth_curvature(self, ctx: cairo.Context, bass: float):
        """Render the curved portion of earth reaching up."""
        cx, cy = self.center

        curvature = self.config.plane_curvature * (0.7 + bass * 0.3)
        horizon_y = self.height * 0.5

        num_points = self.config.curvature_points
        pulse = 0.85 + 0.15 * math.sin(self.pulse_phase * 1.5 + 1)

        for ring in range(8, 0, -1):
            ring_factor = ring / 8

            points = []
            for i in range(num_points + 1):
                angle = -self.main_rotation + (i / num_points) * 2 * math.pi

                dist_factor = 0.3 + 0.7 * abs(math.cos(angle * 1.5 - self.main_rotation))
                radius = self.width * 0.4 * ring_factor

                x = cx + radius * math.cos(angle)

                # Y position curves up toward center
                curve_depth = curvature * 80 * (1 - ring_factor) * dist_factor * pulse
                y = horizon_y + 30 * ring_factor - curve_depth

                points.append((x, y))

            if len(points) > 2:
                ctx.move_to(points[0][0], points[0][1])
                for p in points[1:]:
                    ctx.line_to(p[0], p[1])

                # Color fades from earth to tetrahedron amber
                t = 1 - ring_factor
                earth_h = self.config.earth_color_horizon
                tetra = self.config.lower_tetra_color

                r = earth_h[0] * (1-t) + tetra[0] * t
                g = earth_h[1] * (1-t) + tetra[1] * t
                b = earth_h[2] * (1-t) + tetra[2] * t

                alpha = 0.15 + 0.25 * t * (0.5 + bass * 0.5)

                ctx.set_source_rgba(r, g, b, alpha * pulse)
                ctx.set_line_width(3 + 5 * t)
                ctx.stroke()

    def _render_curved_tetrahedra(self, ctx: cairo.Context, bass: float, treble: float):
        """
        Render the Star Tetrahedron as the meeting point of curved planes.
        The triangles emerge from where heaven and earth reach toward each other.
        """
        cx, cy = self.center

        # Base size affected by energy
        pulse = 0.8 + 0.2 * math.sin(self.pulse_phase)
        base_size = min(self.width, self.height) * 0.28 * pulse

        # Upper tetrahedron (Heaven reaching down)
        self._render_reaching_triangle(
            ctx, cx, cy, base_size,
            pointing_up=True,
            rotation=self.main_rotation,
            base_color=self.config.upper_tetra_color,
            edge_color=self.config.sky_color_horizon,
            energy=treble
        )

        # Lower tetrahedron (Earth reaching up)
        self._render_reaching_triangle(
            ctx, cx, cy, base_size,
            pointing_up=False,
            rotation=-self.main_rotation + math.pi,
            base_color=self.config.lower_tetra_color,
            edge_color=self.config.earth_color_horizon,
            energy=bass
        )

        # Hexagram intersection points where they meet
        self._render_intersection_points(ctx, cx, cy, base_size, bass, treble)

    def _render_reaching_triangle(self, ctx: cairo.Context, cx: float, cy: float,
                                   size: float, pointing_up: bool, rotation: float,
                                   base_color: Tuple, edge_color: Tuple, energy: float):
        """Render a triangle that emerges from its plane and reaches toward the other."""

        # Triangle vertices
        vertices = []
        for i in range(3):
            if pointing_up:
                angle = rotation + math.radians(90 + i * 120)
            else:
                angle = rotation + math.radians(270 + i * 120)

            x = cx + size * math.cos(angle)
            y = cy - size * math.sin(angle)
            vertices.append((x, y))

        # Gradient fill from center (full color) to edges (merging with plane)
        num_layers = 12
        pulse = 0.7 + 0.3 * math.sin(self.pulse_phase * (2 if pointing_up else 1.5))

        for layer in range(num_layers, 0, -1):
            t = layer / num_layers

            # Interpolate vertices toward center
            layer_verts = []
            for vx, vy in vertices:
                lx = cx + (vx - cx) * t
                ly = cy + (vy - cy) * t
                layer_verts.append((lx, ly))

            # Color gradient: edges match plane, center is tetrahedron color
            color_t = 1 - t  # Inverted: outer = edge color, inner = base color
            r = edge_color[0] * (1 - color_t) + base_color[0] * color_t
            g = edge_color[1] * (1 - color_t) + base_color[1] * color_t
            b = edge_color[2] * (1 - color_t) + base_color[2] * color_t

            # Brightness varies with layer and energy
            brightness = (0.3 + 0.7 * color_t) * (0.5 + energy * 0.5) * pulse

            ctx.move_to(layer_verts[0][0], layer_verts[0][1])
            ctx.line_to(layer_verts[1][0], layer_verts[1][1])
            ctx.line_to(layer_verts[2][0], layer_verts[2][1])
            ctx.close_path()

            ctx.set_source_rgba(
                min(1, r * brightness),
                min(1, g * brightness),
                min(1, b * brightness),
                0.4 + 0.4 * color_t
            )
            ctx.fill()

        # Edge outlines with glow
        for glow in range(4, 0, -1):
            ctx.move_to(vertices[0][0], vertices[0][1])
            for vx, vy in vertices[1:]:
                ctx.line_to(vx, vy)
            ctx.close_path()

            alpha = (0.1 + energy * 0.15) / glow * pulse
            ctx.set_source_rgba(
                min(1, base_color[0] * 1.3),
                min(1, base_color[1] * 1.3),
                min(1, base_color[2] * 1.3),
                alpha
            )
            ctx.set_line_width(glow * 2)
            ctx.stroke()

    def _render_intersection_points(self, ctx: cairo.Context, cx: float, cy: float,
                                     size: float, bass: float, treble: float):
        """Render the hexagram intersection points where triangles cross."""
        inner_radius = size * 0.5
        combined_energy = (bass + treble) / 2
        pulse = 0.7 + 0.3 * math.sin(self.pulse_phase * 2)

        for i in range(6):
            angle = self.main_rotation + math.radians(30 + i * 60)
            x = cx + inner_radius * math.cos(angle)
            y = cy - inner_radius * math.sin(angle)

            point_pulse = 0.7 + 0.3 * math.sin(self.pulse_phase + i * 0.5)
            glow_size = 8 + 15 * combined_energy * point_pulse

            # Alternate colors between heaven and earth
            if i % 2 == 0:
                color = self.config.upper_tetra_color
            else:
                color = self.config.lower_tetra_color

            # Radial gradient glow
            gradient = cairo.RadialGradient(x, y, 0, x, y, glow_size)
            gradient.add_color_stop_rgba(0, 1, 1, 0.95, point_pulse * 0.9)
            gradient.add_color_stop_rgba(0.3, color[0], color[1], color[2], point_pulse * 0.6)
            gradient.add_color_stop_rgba(1, color[0] * 0.5, color[1] * 0.5, color[2] * 0.5, 0)

            ctx.arc(x, y, glow_size, 0, 2 * math.pi)
            ctx.set_source(gradient)
            ctx.fill()

    def _render_stars(self, ctx: cairo.Context):
        """Render twinkling stars in the heavens."""
        for x, y, brightness, size, phase in self.stars:
            twinkle = 0.6 + 0.4 * math.sin(self.pulse_phase * 3 + phase)
            alpha = brightness * twinkle

            ctx.set_source_rgba(1, 1, 0.95, alpha)
            ctx.arc(x, y, size, 0, 2 * math.pi)
            ctx.fill()

    def _render_ophanim(self, ctx: cairo.Context, spectrum: np.ndarray,
                        frequencies: np.ndarray, mid_energy: float):
        """Render the Ophanim - wheels within wheels at four directions."""
        cx, cy = self.center
        wheel_distance = min(self.width, self.height) * 0.32

        for i in range(self.config.num_wheels):
            angle = self.main_rotation + math.radians(i * 90 + 45)
            wheel_cx = cx + wheel_distance * math.cos(angle)
            wheel_cy = cy - wheel_distance * math.sin(angle) * 0.6  # Flatten for perspective

            wheel_radius = self.width * self.config.wheel_radius

            # Get spectrum slice for this wheel
            spec_start = int(len(spectrum) * i / 4)
            spec_end = int(len(spectrum) * (i + 1) / 4)
            wheel_spec = spectrum[spec_start:spec_end]
            wheel_freqs = frequencies[spec_start:spec_end]

            # Render concentric rings
            for ring in range(self.config.wheel_rings):
                ring_radius = wheel_radius * (0.5 + 0.3 * ring / self.config.wheel_rings)
                ring_rotation = self.wheel_rotation + math.radians(ring * 20)

                # Ring circle
                ring_alpha = 0.3 + mid_energy * 0.4
                ctx.set_source_rgba(0.8, 0.7, 0.4, ring_alpha)
                ctx.set_line_width(1.5)
                ctx.arc(wheel_cx, wheel_cy, ring_radius, 0, 2 * math.pi)
                ctx.stroke()

                # Eyes on the ring
                for j in range(self.config.eyes_per_ring):
                    eye_angle = ring_rotation + (j / self.config.eyes_per_ring) * 2 * math.pi
                    eye_x = wheel_cx + ring_radius * math.cos(eye_angle)
                    eye_y = wheel_cy + ring_radius * math.sin(eye_angle) * 0.6

                    # Map to spectrum
                    spec_idx = min(j % len(wheel_spec), len(wheel_spec) - 1) if len(wheel_spec) > 0 else 0
                    amp = wheel_spec[spec_idx] if len(wheel_spec) > 0 else 0.2
                    freq = wheel_freqs[spec_idx] if len(wheel_freqs) > spec_idx else 440

                    if amp > 0.05:
                        eye_size = 2 + amp * 8
                        color = self._freq_to_color(freq, amp)

                        # Eye glow
                        ctx.set_source_rgba(color[0], color[1], color[2], amp * 0.8)
                        ctx.arc(eye_x, eye_y, eye_size + 2, 0, 2 * math.pi)
                        ctx.fill()

                        # Eye center
                        ctx.set_source_rgba(
                            min(1, color[0] * 1.5),
                            min(1, color[1] * 1.5),
                            min(1, color[2] * 1.5),
                            0.9
                        )
                        ctx.arc(eye_x, eye_y, eye_size * 0.5, 0, 2 * math.pi)
                        ctx.fill()

    def _render_eyes_on_structure(self, ctx: cairo.Context, spectrum: np.ndarray,
                                   frequencies: np.ndarray):
        """Render eyes distributed along the tetrahedra edges."""
        cx, cy = self.center
        size = min(self.width, self.height) * 0.28

        # Get triangle vertices
        for pointing_up in [True, False]:
            vertices = []
            for i in range(3):
                if pointing_up:
                    angle = self.main_rotation + math.radians(90 + i * 120)
                else:
                    angle = -self.main_rotation + math.pi + math.radians(270 + i * 120)

                x = cx + size * math.cos(angle)
                y = cy - size * math.sin(angle)
                vertices.append((x, y))

            # Eyes along each edge
            for edge_idx in range(3):
                p1 = vertices[edge_idx]
                p2 = vertices[(edge_idx + 1) % 3]

                for j in range(6):
                    t = (j + 1) / 7
                    eye_x = p1[0] + t * (p2[0] - p1[0])
                    eye_y = p1[1] + t * (p2[1] - p1[1])

                    spec_idx = min(int((edge_idx * 6 + j) * len(spectrum) / 36), len(spectrum) - 1)
                    amp = spectrum[spec_idx]
                    freq = frequencies[spec_idx]

                    if amp > 0.08:
                        color = self._freq_to_color(freq, amp)
                        eye_size = 3 + amp * 10

                        # Glow
                        ctx.set_source_rgba(color[0], color[1], color[2], amp * 0.5)
                        ctx.arc(eye_x, eye_y, eye_size + 3, 0, 2 * math.pi)
                        ctx.fill()

                        # Core
                        ctx.set_source_rgba(
                            min(1, color[0] * 1.3),
                            min(1, color[1] * 1.3),
                            min(1, color[2] * 1.3),
                            0.9
                        )
                        ctx.arc(eye_x, eye_y, eye_size * 0.6, 0, 2 * math.pi)
                        ctx.fill()

    def _render_fire(self, ctx: cairo.Context, energy: float):
        """Render fire moving between elements."""
        cx, cy = self.center
        num_particles = int(self.config.fire_particles * (0.3 + energy * 0.7))

        for i in range(num_particles):
            # Particle position orbiting structure
            angle = self.main_rotation * 2 + math.radians(i * 360 / num_particles)
            phase = self.pulse_phase + i * 0.3

            # Spiral motion
            dist = 50 + 100 * (0.5 + 0.5 * math.sin(phase))
            x = cx + dist * math.cos(angle)
            y = cy - dist * math.sin(angle) * 0.7

            # Fire color gradient
            t = (i % 5) / 4
            r = 1.0
            g = 0.3 + 0.5 * t
            b = 0.0 + 0.3 * t

            size = 2 + energy * 4 * (0.5 + 0.5 * math.sin(phase))
            alpha = 0.4 + energy * 0.4

            ctx.set_source_rgba(r, g, b, alpha)
            ctx.arc(x, y, size, 0, 2 * math.pi)
            ctx.fill()

    def _render_throne(self, ctx: cairo.Context):
        """Render the divine throne at the center where heaven and earth meet."""
        cx, cy = self.center

        energy = self.throne_energy
        pulse = 0.6 + 0.4 * math.sin(self.pulse_phase * 2)

        throne_radius = min(self.width, self.height) * self.config.throne_radius
        glow_radius = throne_radius * 3

        # Outer divine glow
        gradient = cairo.RadialGradient(cx, cy, 0, cx, cy, glow_radius * (0.5 + energy * 0.5))
        gradient.add_color_stop_rgba(0, 1, 1, 1, energy * 0.9 * pulse)
        gradient.add_color_stop_rgba(0.3, 1, 0.95, 0.8, energy * 0.5 * pulse)
        gradient.add_color_stop_rgba(0.6, 1, 0.85, 0.5, energy * 0.2 * pulse)
        gradient.add_color_stop_rgba(1, 0, 0, 0, 0)

        ctx.arc(cx, cy, glow_radius, 0, 2 * math.pi)
        ctx.set_source(gradient)
        ctx.fill()

        # Inner throne
        ctx.set_source_rgba(1, 1, 0.9, 0.6 + energy * 0.4)
        ctx.arc(cx, cy, throne_radius, 0, 2 * math.pi)
        ctx.fill()

        # Bright core
        ctx.set_source_rgba(1, 1, 1, energy * pulse)
        ctx.arc(cx, cy, throne_radius * 0.4, 0, 2 * math.pi)
        ctx.fill()

    def _render_chayot(self, ctx: cairo.Context, spectrum: np.ndarray, frequencies: np.ndarray):
        """Render symbols for the Four Living Creatures at cardinal directions."""
        cx, cy = self.center
        distance = min(self.width, self.height) * 0.38

        creature_colors = {
            'lion': (1.0, 0.7, 0.2),    # Golden
            'man': (0.9, 0.75, 0.65),   # Flesh tone
            'ox': (0.6, 0.4, 0.25),     # Brown
            'eagle': (0.5, 0.55, 0.7)   # Grey-blue
        }

        for i, creature in enumerate(self.chayot_types):
            angle = self.main_rotation * 0.3 + math.radians(i * 90)
            x = cx + distance * math.cos(angle)
            y = cy - distance * math.sin(angle) * 0.5

            # Get energy for this quadrant
            spec_start = int(len(spectrum) * i / 4)
            spec_end = int(len(spectrum) * (i + 1) / 4)
            quad_energy = np.mean(spectrum[spec_start:spec_end])

            color = creature_colors[creature]
            radius = self.config.chayot_glow_radius * (0.7 + quad_energy * 0.3)
            pulse = 0.7 + 0.3 * math.sin(self.pulse_phase + i)

            # Glow for creature presence
            gradient = cairo.RadialGradient(x, y, 0, x, y, radius)
            gradient.add_color_stop_rgba(0, color[0], color[1], color[2], 0.7 * pulse)
            gradient.add_color_stop_rgba(0.5, color[0] * 0.8, color[1] * 0.8, color[2] * 0.8, 0.3 * pulse)
            gradient.add_color_stop_rgba(1, 0, 0, 0, 0)

            ctx.arc(x, y, radius, 0, 2 * math.pi)
            ctx.set_source(gradient)
            ctx.fill()

            # Creature symbol (simplified geometric representation)
            ctx.set_source_rgba(color[0], color[1], color[2], 0.9 * pulse)
            ctx.arc(x, y, radius * 0.3, 0, 2 * math.pi)
            ctx.fill()

    def _render_lightning(self, ctx: cairo.Context):
        """Render lightning on beats."""
        cx, cy = self.center

        num_bolts = np.random.randint(2, 5)

        for _ in range(num_bolts):
            angle = np.random.uniform(0, 360)
            length = min(self.width, self.height) * np.random.uniform(0.2, 0.4)

            # Jagged path
            points = [(cx, cy)]
            segments = np.random.randint(3, 6)

            for i in range(segments):
                t = (i + 1) / segments
                base_x = cx + length * t * math.cos(math.radians(angle))
                base_y = cy - length * t * math.sin(math.radians(angle))

                jitter = length * 0.15 * (1 - t)
                x = base_x + np.random.uniform(-jitter, jitter)
                y = base_y + np.random.uniform(-jitter, jitter)
                points.append((x, y))

            # Draw lightning
            ctx.set_source_rgba(1, 1, 1, 0.9)
            ctx.set_line_width(3)
            ctx.move_to(points[0][0], points[0][1])
            for p in points[1:]:
                ctx.line_to(p[0], p[1])
            ctx.stroke()

            ctx.set_source_rgba(0.8, 0.85, 1, 0.6)
            ctx.set_line_width(5)
            ctx.move_to(points[0][0], points[0][1])
            for p in points[1:]:
                ctx.line_to(p[0], p[1])
            ctx.stroke()

    def _freq_to_color(self, freq: float, amplitude: float = 1.0) -> Tuple[float, float, float]:
        """Map frequency to color with Merkabah-inspired palette."""
        f_min, f_max = 50, 8000

        if freq <= f_min:
            freq_norm = 0
        elif freq >= f_max:
            freq_norm = 1
        else:
            freq_norm = (np.log(freq) - np.log(f_min)) / (np.log(f_max) - np.log(f_min))

        # Amber (bass) → Sapphire (mid) → Crystal (treble)
        if freq_norm < 0.33:
            hue = 0.08 + freq_norm * 0.12
        elif freq_norm < 0.66:
            hue = 0.55 + (freq_norm - 0.33) * 0.15
        else:
            hue = 0.5 + (freq_norm - 0.66) * 0.2

        # Blend with harmony
        hue = hue * 0.7 + self.current_hue * 0.3
        hue = hue % 1.0

        sat = 0.85
        val = 0.4 + amplitude * 0.6

        r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
        return (r, g, b)

    def _surface_to_pil(self, surface: cairo.ImageSurface) -> Image.Image:
        """Convert Cairo surface to PIL Image."""
        data = surface.get_data()
        image = Image.frombuffer('RGBA', (self.width, self.height),
                                data, 'raw', 'BGRA', 0, 1)
        return image.convert('RGB')

    def _apply_glow(self, image: Image.Image) -> Image.Image:
        """Apply bloom/glow post-processing."""
        bright = image.point(lambda x: min(255, int(x * 1.5)) if x > 80 else 0)
        glow = bright.filter(ImageFilter.GaussianBlur(radius=self.config.glow_radius))
        return ImageChops.add(image, glow)


def create_unified_merkabah_renderer(width: int = 1280, height: int = 720) -> UnifiedMerkabah3DRenderer:
    """Create a unified 3D Merkabah renderer."""
    config = UnifiedMerkabah3DConfig(frame_width=width, frame_height=height)
    return UnifiedMerkabah3DRenderer(config)


if __name__ == '__main__':
    import time

    print("Testing Unified 3D Merkabah Renderer...")

    renderer = create_unified_merkabah_renderer()

    frequencies = np.linspace(50, 8000, 381)
    spectrum = np.random.rand(381) * 0.5
    spectrum[50:100] = 0.8
    spectrum[200:250] = 0.6

    print("Rendering test frames...")
    for i in range(30):
        t0 = time.time()

        renderer.update_state(
            beat_strength=0.8 if i % 5 == 0 else 0.2,
            is_beat=(i % 5 == 0),
            pitch=440 if i % 3 == 0 else 0,
            rms=0.5 + 0.3 * math.sin(i / 3),
            bass=0.3 + 0.3 * math.sin(i / 4),
            treble=0.3 + 0.3 * math.cos(i / 5)
        )

        frame = renderer.render_frame(spectrum, frequencies)
        elapsed = time.time() - t0

        if i % 5 == 0:
            print(f"  Frame {i}: {elapsed*1000:.0f}ms")
            frame.save(f'/tmp/merkabah_unified_test_{i:03d}.png')

    print("\nTest frames saved to /tmp/merkabah_unified_test_*.png")
