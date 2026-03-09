#!/usr/bin/env python3
"""
SYNESTHESIA - Complete 3D Merkabah Renderer
=============================================
TRUE 3D visualization with perspective projection where the Star Tetrahedron
emerges from curving Heaven and Earth planes reaching toward each other.

3D Features:
- True perspective projection with view/projection matrices
- Camera orbiting in 3D space around the Merkabah
- Depth-sorted rendering (painter's algorithm)
- 3D curved mesh surfaces for heaven and earth planes
- 3D tetrahedra that merge with the curved planes at edges

All Symbolic Elements in 3D:
- Ophanim (wheels within wheels) positioned in 3D space
- Chayot (four living creatures) at cardinal 3D positions
- Eyes distributed on 3D structure surfaces
- Fire particles moving in 3D space
- Lightning bolts in 3D
- Divine Throne at the 3D center

The Concept:
- Heaven (above) and Earth (below) are 3D mesh surfaces
- At the center, these surfaces curve/warp toward each other
- The tetrahedra emerge from this curvature - their vertices touching the planes
- Camera orbits to reveal the 3D depth and interpenetration
"""

import numpy as np
import cairo
import math
from PIL import Image, ImageFilter, ImageChops
from dataclasses import dataclass, field
from typing import Tuple, List, Optional
import colorsys


@dataclass
class Camera3D:
    """3D Camera with orbital movement."""
    position: np.ndarray = field(default_factory=lambda: np.array([0.0, 1.0, -5.0]))
    target: np.ndarray = field(default_factory=lambda: np.array([0.0, 0.0, 0.0]))
    up: np.ndarray = field(default_factory=lambda: np.array([0.0, 1.0, 0.0]))
    fov: float = 55.0
    near: float = 0.1
    far: float = 100.0

    def get_view_matrix(self) -> np.ndarray:
        """Calculate view matrix (look-at)."""
        forward = self.target - self.position
        forward = forward / (np.linalg.norm(forward) + 1e-8)
        right = np.cross(forward, self.up)
        right = right / (np.linalg.norm(right) + 1e-8)
        up = np.cross(right, forward)

        view = np.eye(4)
        view[0, :3] = right
        view[1, :3] = up
        view[2, :3] = -forward
        view[:3, 3] = -np.array([
            np.dot(right, self.position),
            np.dot(up, self.position),
            np.dot(-forward, self.position)
        ])
        return view

    def get_projection_matrix(self, aspect: float) -> np.ndarray:
        """Calculate perspective projection matrix."""
        fov_rad = math.radians(self.fov)
        f = 1.0 / math.tan(fov_rad / 2.0)

        proj = np.zeros((4, 4))
        proj[0, 0] = f / aspect
        proj[1, 1] = f
        proj[2, 2] = (self.far + self.near) / (self.near - self.far)
        proj[2, 3] = (2 * self.far * self.near) / (self.near - self.far)
        proj[3, 2] = -1.0
        return proj


@dataclass
class Complete3DConfig:
    """Configuration for complete 3D Merkabah."""
    frame_width: int = 1280
    frame_height: int = 720

    # 3D Geometry
    tetrahedron_size: float = 1.2
    plane_extent: float = 4.0  # How far the planes extend
    plane_resolution: int = 16  # Grid resolution for curved planes
    plane_curvature: float = 0.7  # How much planes curve toward center

    # Colors
    sky_color_top: Tuple[float, float, float] = (0.05, 0.08, 0.25)
    sky_color_mid: Tuple[float, float, float] = (0.3, 0.4, 0.7)
    earth_color_mid: Tuple[float, float, float] = (0.5, 0.35, 0.2)
    earth_color_deep: Tuple[float, float, float] = (0.12, 0.06, 0.02)
    upper_tetra_color: Tuple[float, float, float] = (0.3, 0.5, 1.0)
    lower_tetra_color: Tuple[float, float, float] = (1.0, 0.6, 0.3)

    # Camera
    camera_distance: float = 5.5
    camera_height: float = 1.2
    camera_orbit_speed: float = 0.2

    # Symbolic elements
    num_ophanim: int = 4
    ophan_rings: int = 3
    eyes_per_ring: int = 10
    num_chayot: int = 4
    enable_fire: bool = True
    fire_particles: int = 30
    enable_stars: bool = True
    num_stars: int = 120

    # Animation
    rotation_speed: float = 0.4
    pulse_speed: float = 0.025

    # Rendering
    glow_radius: int = 6


class Complete3DMerkabah:
    """
    Complete 3D Merkabah renderer with all elements.

    True 3D perspective with:
    - Curved heaven/earth planes as 3D mesh
    - Tetrahedra emerging from plane curvature
    - All symbolic elements positioned in 3D
    - Orbiting camera
    """

    def __init__(self, config: Complete3DConfig):
        self.config = config
        self.width = config.frame_width
        self.height = config.frame_height
        self.aspect = self.width / self.height

        # Camera
        self.camera = Camera3D(
            position=np.array([0.0, config.camera_height, -config.camera_distance]),
            fov=55.0
        )

        # Animation state
        self.rotation = 0.0
        self.camera_orbit = 0.0
        self.pulse_phase = 0.0
        self.frame_count = 0

        # Energy state
        self.bass_energy = 0.0
        self.treble_energy = 0.0
        self.throne_energy = 0.0
        self.lightning_active = False

        # Pre-generate geometry
        self._generate_plane_mesh()
        self._generate_tetrahedra()
        self._generate_stars()

        # Chayot types
        self.chayot_types = ['lion', 'man', 'ox', 'eagle']
        self.chayot_colors = {
            'lion': (1.0, 0.75, 0.25),
            'man': (0.9, 0.75, 0.65),
            'ox': (0.6, 0.4, 0.25),
            'eagle': (0.5, 0.55, 0.75)
        }

    def _generate_plane_mesh(self):
        """Generate 3D mesh vertices for curved heaven/earth planes."""
        res = self.config.plane_resolution
        extent = self.config.plane_extent
        curvature = self.config.plane_curvature

        # Heaven plane (curves down toward center)
        self.heaven_verts = []
        self.heaven_faces = []

        # Earth plane (curves up toward center)
        self.earth_verts = []
        self.earth_faces = []

        base_height = self.config.tetrahedron_size * 0.9

        for i in range(res):
            for j in range(res):
                # Normalized coordinates (-1 to 1)
                u = (i / (res - 1)) * 2 - 1
                v = (j / (res - 1)) * 2 - 1

                # World position
                x = u * extent
                z = v * extent

                # Distance from center affects curvature
                dist = math.sqrt(x*x + z*z)
                dist_factor = max(0, 1 - dist / extent)  # 1 at center, 0 at edges

                # Heaven: starts high, curves down toward center
                heaven_y = base_height + 0.5 - curvature * dist_factor * 1.5
                self.heaven_verts.append(np.array([x, heaven_y, z]))

                # Earth: starts low, curves up toward center
                earth_y = -base_height - 0.5 + curvature * dist_factor * 1.5
                self.earth_verts.append(np.array([x, earth_y, z]))

        # Generate face indices (quads as two triangles)
        for i in range(res - 1):
            for j in range(res - 1):
                idx = i * res + j
                # Two triangles per quad
                self.heaven_faces.append((idx, idx + 1, idx + res))
                self.heaven_faces.append((idx + 1, idx + res + 1, idx + res))
                self.earth_faces.append((idx, idx + res, idx + 1))
                self.earth_faces.append((idx + 1, idx + res, idx + res + 1))

    def _generate_tetrahedra(self):
        """Generate 3D tetrahedra vertices.

        FLIPPED ORIENTATION for proper merging with heaven/earth planes:
        - Upper tetrahedron: apex points DOWN, base is UP (merges with sky/heaven)
        - Lower tetrahedron: apex points UP, base is DOWN (merges with earth/ground)

        This creates the visual effect of the tetrahedra emerging FROM the
        curving heaven and earth planes reaching toward each other.
        """
        size = self.config.tetrahedron_size
        h = size * math.sqrt(2/3)
        r = size * math.sqrt(2/3)

        # Upper tetrahedron - BASE at top (merging with heaven), APEX pointing down
        # The base vertices are UP in the sky, apex points toward earth
        apex_down_upper = np.array([0, -h * 0.3, 0])  # Apex points DOWN
        base_y_upper = h * 0.9  # Base is UP (in heaven/sky region)

        self.upper_tetra_verts = [apex_down_upper]  # Index 0 is apex
        for i in range(3):
            angle = math.radians(i * 120 - 90)
            self.upper_tetra_verts.append(np.array([
                r * math.cos(angle),
                base_y_upper,  # Base vertices are HIGH (in sky)
                r * math.sin(angle)
            ]))

        # Face winding adjusted for flipped orientation
        self.upper_tetra_faces = [
            (0, 2, 1), (0, 3, 2), (0, 1, 3), (1, 2, 3)  # Base face at top
        ]

        # Lower tetrahedron - BASE at bottom (merging with earth), APEX pointing up
        # The base vertices are DOWN in the earth, apex points toward heaven
        apex_up_lower = np.array([0, h * 0.3, 0])  # Apex points UP
        base_y_lower = -h * 0.9  # Base is DOWN (in earth/ground region)

        self.lower_tetra_verts = [apex_up_lower]  # Index 0 is apex
        for i in range(3):
            angle = math.radians(i * 120 + 30)
            self.lower_tetra_verts.append(np.array([
                r * math.cos(angle),
                base_y_lower,  # Base vertices are LOW (in earth)
                r * math.sin(angle)
            ]))

        # Face winding adjusted for flipped orientation
        self.lower_tetra_faces = [
            (0, 1, 2), (0, 2, 3), (0, 3, 1), (1, 3, 2)  # Base face at bottom
        ]

    def _generate_stars(self):
        """Generate 3D star positions in the heavenly dome."""
        self.stars = []
        if not self.config.enable_stars:
            return

        np.random.seed(42)
        for _ in range(self.config.num_stars):
            # Random position in upper hemisphere
            theta = np.random.uniform(0, 2 * math.pi)
            phi = np.random.uniform(0, math.pi / 3)
            r = 15 + np.random.uniform(0, 5)

            x = r * math.sin(phi) * math.cos(theta)
            y = r * math.cos(phi) + 3
            z = r * math.sin(phi) * math.sin(theta)

            brightness = np.random.uniform(0.4, 1.0)
            size = np.random.uniform(1.5, 3.0)
            phase = np.random.uniform(0, 2 * math.pi)

            self.stars.append((np.array([x, y, z]), brightness, size, phase))

    def update_state(self, beat_strength: float = 0, is_beat: bool = False,
                     pitch: float = 0, chroma: np.ndarray = None,
                     rms: float = 0.5, bass: float = 0.33, treble: float = 0.33):
        """Update animation state."""
        energy = 0.5 + rms * 1.5

        self.rotation += math.radians(self.config.rotation_speed * energy)
        self.camera_orbit += math.radians(self.config.camera_orbit_speed * energy)
        self.pulse_phase += self.config.pulse_speed * energy
        self.frame_count += 1

        # Update camera position (orbiting)
        dist = self.config.camera_distance
        self.camera.position[0] = dist * math.sin(self.camera_orbit)
        self.camera.position[2] = -dist * math.cos(self.camera_orbit)

        self.bass_energy = bass
        self.treble_energy = treble

        if pitch > 0:
            self.throne_energy = min(1.0, self.throne_energy + 0.25)
        self.throne_energy *= 0.93

        self.lightning_active = is_beat and beat_strength > 0.5

    def render_frame(self, spectrum: np.ndarray, frequencies: np.ndarray,
                     temporal_features: dict = None) -> Image.Image:
        """Render a complete 3D frame."""

        # Normalize spectrum
        if spectrum.max() > 0:
            spectrum = spectrum / spectrum.max()
        spectrum = np.clip(spectrum, 0, 1)

        # Band energies
        bass_mask = frequencies < 250
        treble_mask = frequencies >= 2000
        bass = np.mean(spectrum[bass_mask]) if np.any(bass_mask) else 0.33
        treble = np.mean(spectrum[treble_mask]) if np.any(treble_mask) else 0.33

        # Create Cairo surface
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.width, self.height)
        ctx = cairo.Context(surface)
        ctx.set_antialias(cairo.ANTIALIAS_BEST)

        # Get transformation matrices
        view = self.camera.get_view_matrix()
        proj = self.camera.get_projection_matrix(self.aspect)
        vp = proj @ view

        # Rotation matrix for animated elements
        rot_y = self._rotation_matrix_y(self.rotation)

        # Render layers (back to front with depth sorting)
        self._render_background(ctx)
        self._render_stars_3d(ctx, vp)
        self._render_heaven_plane(ctx, vp, rot_y, treble)
        self._render_earth_plane(ctx, vp, rot_y, bass)
        self._render_tetrahedra_3d(ctx, vp, rot_y, bass, treble)
        self._render_ophanim_3d(ctx, vp, rot_y, spectrum, frequencies)
        self._render_chayot_3d(ctx, vp, rot_y, spectrum)

        if self.config.enable_fire:
            self._render_fire_3d(ctx, vp, rot_y)

        self._render_throne_3d(ctx, vp)

        if self.lightning_active:
            self._render_lightning_3d(ctx, vp)

        # Convert and post-process
        image = self._surface_to_pil(surface)
        if self.config.glow_radius > 0:
            image = self._apply_glow(image)

        return image

    def _rotation_matrix_y(self, angle: float) -> np.ndarray:
        """Y-axis rotation matrix."""
        c, s = math.cos(angle), math.sin(angle)
        return np.array([
            [c, 0, s, 0],
            [0, 1, 0, 0],
            [-s, 0, c, 0],
            [0, 0, 0, 1]
        ])

    def _project_point(self, point: np.ndarray, vp: np.ndarray) -> Optional[Tuple[float, float, float]]:
        """Project 3D point to screen coordinates. Returns (x, y, depth) or None."""
        p4 = np.array([point[0], point[1], point[2], 1.0])
        clip = vp @ p4

        if clip[3] <= 0.01:
            return None

        ndc_x = clip[0] / clip[3]
        ndc_y = clip[1] / clip[3]
        depth = clip[2] / clip[3]

        screen_x = (ndc_x + 1) * 0.5 * self.width
        screen_y = (1 - ndc_y) * 0.5 * self.height

        return (screen_x, screen_y, depth)

    def _transform_point(self, point: np.ndarray, matrix: np.ndarray) -> np.ndarray:
        """Transform point by 4x4 matrix."""
        p4 = np.array([point[0], point[1], point[2], 1.0])
        result = matrix @ p4
        return result[:3]

    def _render_background(self, ctx: cairo.Context):
        """Render 3D atmospheric background with depth and smooth transitions.

        Creates a sense of infinite depth by:
        - Using radial gradients from center for 3D focal point effect
        - Multiple overlapping gradient layers for atmospheric haze
        - Smooth color transitions with many interpolation stops
        - Subtle vignette effect for depth perception
        """
        pulse = 0.85 + 0.15 * math.sin(self.pulse_phase)
        energy_pulse = 0.9 + 0.1 * self.bass_energy

        # Colors
        deep_space = (0.02, 0.03, 0.08)  # Nearly black cosmic depth
        top = self.config.sky_color_top
        mid_sky = self.config.sky_color_mid
        horizon = (0.45, 0.42, 0.48)  # Neutral misty horizon
        mid_earth = self.config.earth_color_mid
        deep = self.config.earth_color_deep
        deep_earth = (0.05, 0.02, 0.01)  # Nearly black earth depth

        # Layer 1: Base gradient with many smooth color stops
        base_gradient = cairo.LinearGradient(0, 0, 0, self.height)

        # Sky region - smooth transition through many stops
        base_gradient.add_color_stop_rgb(0.00, deep_space[0], deep_space[1], deep_space[2])
        base_gradient.add_color_stop_rgb(0.08, deep_space[0] * 1.5, deep_space[1] * 1.5, deep_space[2] * 2)
        base_gradient.add_color_stop_rgb(0.15, top[0] * 0.5 * pulse, top[1] * 0.5 * pulse, top[2] * 0.7 * pulse)
        base_gradient.add_color_stop_rgb(0.25, top[0] * 0.7 * pulse, top[1] * 0.7 * pulse, top[2] * 0.9 * pulse)
        base_gradient.add_color_stop_rgb(0.35, mid_sky[0] * 0.8, mid_sky[1] * 0.8, mid_sky[2] * 0.9)

        # Horizon region - very gradual blend
        base_gradient.add_color_stop_rgb(0.42, mid_sky[0] * 0.7 + horizon[0] * 0.3,
                                          mid_sky[1] * 0.7 + horizon[1] * 0.3,
                                          mid_sky[2] * 0.7 + horizon[2] * 0.3)
        base_gradient.add_color_stop_rgb(0.48, horizon[0], horizon[1], horizon[2])
        base_gradient.add_color_stop_rgb(0.52, horizon[0], horizon[1], horizon[2])
        base_gradient.add_color_stop_rgb(0.58, mid_earth[0] * 0.7 + horizon[0] * 0.3,
                                          mid_earth[1] * 0.7 + horizon[1] * 0.3,
                                          mid_earth[2] * 0.7 + horizon[2] * 0.3)

        # Earth region - smooth transition to depths
        base_gradient.add_color_stop_rgb(0.65, mid_earth[0] * 0.8, mid_earth[1] * 0.8, mid_earth[2] * 0.8)
        base_gradient.add_color_stop_rgb(0.75, mid_earth[0] * 0.5 + deep[0] * 0.5,
                                          mid_earth[1] * 0.5 + deep[1] * 0.5,
                                          mid_earth[2] * 0.5 + deep[2] * 0.5)
        base_gradient.add_color_stop_rgb(0.85, deep[0] * 0.7, deep[1] * 0.7, deep[2] * 0.7)
        base_gradient.add_color_stop_rgb(0.92, deep_earth[0] * 2, deep_earth[1] * 2, deep_earth[2] * 2)
        base_gradient.add_color_stop_rgb(1.00, deep_earth[0], deep_earth[1], deep_earth[2])

        ctx.rectangle(0, 0, self.width, self.height)
        ctx.set_source(base_gradient)
        ctx.fill()

        # Layer 2: Radial depth gradient from center (3D focal point effect)
        center_x = self.width / 2
        center_y = self.height / 2
        max_radius = math.sqrt(center_x ** 2 + center_y ** 2)

        radial = cairo.RadialGradient(center_x, center_y, 0, center_x, center_y, max_radius)
        # Bright haze at center (atmospheric depth)
        radial.add_color_stop_rgba(0.0, 0.5, 0.5, 0.55, 0.15 * energy_pulse)
        radial.add_color_stop_rgba(0.15, 0.4, 0.4, 0.5, 0.12 * energy_pulse)
        radial.add_color_stop_rgba(0.3, 0.3, 0.3, 0.4, 0.08)
        radial.add_color_stop_rgba(0.5, 0.2, 0.2, 0.3, 0.04)
        radial.add_color_stop_rgba(1.0, 0, 0, 0, 0)

        ctx.rectangle(0, 0, self.width, self.height)
        ctx.set_source(radial)
        ctx.fill()

        # Layer 3: Vignette for depth (darker at corners)
        vignette = cairo.RadialGradient(center_x, center_y, max_radius * 0.4,
                                         center_x, center_y, max_radius * 1.2)
        vignette.add_color_stop_rgba(0, 0, 0, 0, 0)
        vignette.add_color_stop_rgba(0.6, 0, 0, 0, 0.1)
        vignette.add_color_stop_rgba(0.85, 0, 0, 0, 0.25)
        vignette.add_color_stop_rgba(1.0, 0, 0, 0, 0.4)

        ctx.rectangle(0, 0, self.width, self.height)
        ctx.set_source(vignette)
        ctx.fill()

        # Layer 4: Subtle atmospheric haze bands (volumetric fog effect)
        for i in range(5):
            y_pos = self.height * (0.35 + i * 0.06)
            band_height = self.height * 0.15
            haze_alpha = 0.03 * (1 - abs(i - 2) / 3)  # Strongest at horizon

            haze = cairo.LinearGradient(0, y_pos - band_height/2, 0, y_pos + band_height/2)
            haze.add_color_stop_rgba(0, 0.5, 0.5, 0.55, 0)
            haze.add_color_stop_rgba(0.5, 0.6, 0.55, 0.6, haze_alpha * pulse)
            haze.add_color_stop_rgba(1, 0.5, 0.5, 0.55, 0)

            ctx.rectangle(0, y_pos - band_height/2, self.width, band_height)
            ctx.set_source(haze)
            ctx.fill()

    def _render_stars_3d(self, ctx: cairo.Context, vp: np.ndarray):
        """Render stars in 3D space."""
        for pos, brightness, size, phase in self.stars:
            proj = self._project_point(pos, vp)
            if proj is None:
                continue

            x, y, depth = proj
            if depth < 0 or x < 0 or x > self.width or y < 0 or y > self.height:
                continue

            twinkle = 0.6 + 0.4 * math.sin(self.pulse_phase * 3 + phase)
            alpha = brightness * twinkle * 0.8

            ctx.set_source_rgba(1, 1, 0.95, alpha)
            ctx.arc(x, y, size, 0, 2 * math.pi)
            ctx.fill()

    def _render_heaven_plane(self, ctx: cairo.Context, vp: np.ndarray,
                              rot: np.ndarray, treble: float):
        """Render the curved heaven plane in 3D.

        The heaven plane curves down from the edges toward the center.
        Its color smoothly blends from sky blue at the edges to the
        upper tetrahedron's blue color at the center, where the
        tetrahedron's BASE emerges from the plane.
        """
        # Collect and sort faces by depth
        faces_to_draw = []

        for face in self.heaven_faces:
            verts_3d = [self._transform_point(self.heaven_verts[i], rot) for i in face]
            center = np.mean(verts_3d, axis=0)

            proj_center = self._project_point(center, vp)
            if proj_center is None:
                continue

            # Project all vertices
            proj_verts = []
            valid = True
            for v in verts_3d:
                pv = self._project_point(v, vp)
                if pv is None:
                    valid = False
                    break
                proj_verts.append(pv)

            if valid:
                # Calculate distance from center for color blending
                dist_from_center = math.sqrt(center[0]**2 + center[2]**2)
                faces_to_draw.append(('heaven', proj_verts, proj_center[2], center[1], dist_from_center))

        # Sort by depth and render
        faces_to_draw.sort(key=lambda x: -x[2])

        pulse = 0.7 + 0.3 * math.sin(self.pulse_phase * 2)
        max_dist = self.config.plane_extent

        for face_type, proj_verts, depth, y_pos, dist in faces_to_draw:
            # Color based on distance from center (smooth radial blend)
            # t=0 at edges (sky color), t=1 at center (tetrahedron color)
            t = max(0, min(1, 1 - dist / max_dist))
            t = t ** 0.7  # Ease the transition for smoother gradient

            sky = self.config.sky_color_mid
            tetra = self.config.upper_tetra_color

            r = sky[0] * (1-t) + tetra[0] * t
            g = sky[1] * (1-t) + tetra[1] * t
            b = sky[2] * (1-t) + tetra[2] * t

            # Brightness increases toward center where tetrahedron emerges
            brightness = (0.25 + 0.45 * t + treble * 0.3) * pulse
            # Alpha increases toward center for solid tetrahedron connection
            alpha = 0.12 + 0.45 * t

            ctx.move_to(proj_verts[0][0], proj_verts[0][1])
            for pv in proj_verts[1:]:
                ctx.line_to(pv[0], pv[1])
            ctx.close_path()

            ctx.set_source_rgba(r * brightness, g * brightness, b * brightness, alpha)
            ctx.fill()

    def _render_earth_plane(self, ctx: cairo.Context, vp: np.ndarray,
                             rot: np.ndarray, bass: float):
        """Render the curved earth plane in 3D.

        The earth plane curves up from the edges toward the center.
        Its color smoothly blends from earth brown at the edges to the
        lower tetrahedron's amber/orange color at the center, where the
        tetrahedron's BASE emerges from the plane.
        """
        faces_to_draw = []

        for face in self.earth_faces:
            verts_3d = [self._transform_point(self.earth_verts[i], rot) for i in face]
            center = np.mean(verts_3d, axis=0)

            proj_center = self._project_point(center, vp)
            if proj_center is None:
                continue

            proj_verts = []
            valid = True
            for v in verts_3d:
                pv = self._project_point(v, vp)
                if pv is None:
                    valid = False
                    break
                proj_verts.append(pv)

            if valid:
                # Calculate distance from center for color blending
                dist_from_center = math.sqrt(center[0]**2 + center[2]**2)
                faces_to_draw.append(('earth', proj_verts, proj_center[2], center[1], dist_from_center))

        faces_to_draw.sort(key=lambda x: -x[2])

        pulse = 0.7 + 0.3 * math.sin(self.pulse_phase * 1.5)
        max_dist = self.config.plane_extent

        for face_type, proj_verts, depth, y_pos, dist in faces_to_draw:
            # Color based on distance from center (smooth radial blend)
            # t=0 at edges (earth color), t=1 at center (tetrahedron color)
            t = max(0, min(1, 1 - dist / max_dist))
            t = t ** 0.7  # Ease the transition for smoother gradient

            earth = self.config.earth_color_mid
            tetra = self.config.lower_tetra_color

            r = earth[0] * (1-t) + tetra[0] * t
            g = earth[1] * (1-t) + tetra[1] * t
            b = earth[2] * (1-t) + tetra[2] * t

            # Brightness increases toward center where tetrahedron emerges
            brightness = (0.25 + 0.45 * t + bass * 0.3) * pulse
            # Alpha increases toward center for solid tetrahedron connection
            alpha = 0.12 + 0.45 * t

            ctx.move_to(proj_verts[0][0], proj_verts[0][1])
            for pv in proj_verts[1:]:
                ctx.line_to(pv[0], pv[1])
            ctx.close_path()

            ctx.set_source_rgba(r * brightness, g * brightness, b * brightness, alpha)
            ctx.fill()

    def _render_tetrahedra_3d(self, ctx: cairo.Context, vp: np.ndarray,
                               rot: np.ndarray, bass: float, treble: float):
        """Render the Star Tetrahedron in true 3D."""
        all_faces = []

        # Upper tetrahedron
        for face in self.upper_tetra_faces:
            verts_3d = [self._transform_point(self.upper_tetra_verts[i], rot) for i in face]
            center = np.mean(verts_3d, axis=0)

            proj_center = self._project_point(center, vp)
            if proj_center is None:
                continue

            proj_verts = []
            valid = True
            for v in verts_3d:
                pv = self._project_point(v, vp)
                if pv is None:
                    valid = False
                    break
                proj_verts.append(pv)

            if valid:
                # Calculate normal for shading
                v0, v1, v2 = verts_3d
                edge1 = v1 - v0
                edge2 = v2 - v0
                normal = np.cross(edge1, edge2)
                normal = normal / (np.linalg.norm(normal) + 1e-8)

                all_faces.append(('upper', proj_verts, proj_center[2], normal, verts_3d, treble))

        # Lower tetrahedron
        for face in self.lower_tetra_faces:
            verts_3d = [self._transform_point(self.lower_tetra_verts[i], rot) for i in face]
            center = np.mean(verts_3d, axis=0)

            proj_center = self._project_point(center, vp)
            if proj_center is None:
                continue

            proj_verts = []
            valid = True
            for v in verts_3d:
                pv = self._project_point(v, vp)
                if pv is None:
                    valid = False
                    break
                proj_verts.append(pv)

            if valid:
                v0, v1, v2 = verts_3d
                edge1 = v1 - v0
                edge2 = v2 - v0
                normal = np.cross(edge1, edge2)
                normal = normal / (np.linalg.norm(normal) + 1e-8)

                all_faces.append(('lower', proj_verts, proj_center[2], normal, verts_3d, bass))

        # Sort by depth
        all_faces.sort(key=lambda x: -x[2])

        pulse = 0.75 + 0.25 * math.sin(self.pulse_phase)

        # Light direction
        light_dir = np.array([0.3, 0.8, -0.5])
        light_dir = light_dir / np.linalg.norm(light_dir)

        for face_type, proj_verts, depth, normal, verts_3d, energy in all_faces:
            if face_type == 'upper':
                base_color = self.config.upper_tetra_color
            else:
                base_color = self.config.lower_tetra_color

            # Diffuse shading
            diffuse = max(0.25, abs(np.dot(normal, light_dir)))
            intensity = diffuse * (0.5 + energy * 0.5) * pulse

            r = min(1, base_color[0] * intensity)
            g = min(1, base_color[1] * intensity)
            b = min(1, base_color[2] * intensity)

            # Draw filled face
            ctx.move_to(proj_verts[0][0], proj_verts[0][1])
            for pv in proj_verts[1:]:
                ctx.line_to(pv[0], pv[1])
            ctx.close_path()

            ctx.set_source_rgba(r, g, b, 0.7)
            ctx.fill_preserve()

            # Glow edge
            ctx.set_source_rgba(min(1, r * 1.4), min(1, g * 1.4), min(1, b * 1.4), 0.4 * pulse)
            ctx.set_line_width(4)
            ctx.stroke_preserve()

            # Sharp edge
            ctx.set_source_rgba(min(1, r * 1.6), min(1, g * 1.6), min(1, b * 1.6), 0.8)
            ctx.set_line_width(2)
            ctx.stroke()

    def _render_ophanim_3d(self, ctx: cairo.Context, vp: np.ndarray,
                            rot: np.ndarray, spectrum: np.ndarray, frequencies: np.ndarray):
        """Render Ophanim (wheels) in 3D space."""
        wheel_distance = self.config.tetrahedron_size * 1.3
        wheel_radius = 0.5

        for i in range(self.config.num_ophanim):
            # Position wheel at cardinal direction
            angle = self.rotation + math.radians(i * 90 + 45)
            wheel_center = np.array([
                wheel_distance * math.cos(angle),
                0,
                wheel_distance * math.sin(angle)
            ])

            proj_center = self._project_point(wheel_center, vp)
            if proj_center is None:
                continue

            cx, cy, depth = proj_center

            # Scale based on depth
            scale = 150 / (depth + 3)
            ring_scale = max(20, min(80, scale))

            # Get spectrum for this wheel
            spec_start = int(len(spectrum) * i / 4)
            spec_end = int(len(spectrum) * (i + 1) / 4)
            wheel_spec = spectrum[spec_start:spec_end]

            # Draw rings
            for ring in range(self.config.ophan_rings):
                ring_r = ring_scale * (0.5 + 0.3 * ring / self.config.ophan_rings)
                ring_rotation = self.rotation * 2 + ring * 0.5

                # Ring circle
                ctx.set_source_rgba(0.8, 0.7, 0.4, 0.4)
                ctx.set_line_width(1.5)
                ctx.arc(cx, cy, ring_r, 0, 2 * math.pi)
                ctx.stroke()

                # Eyes on ring
                for j in range(self.config.eyes_per_ring):
                    eye_angle = ring_rotation + (j / self.config.eyes_per_ring) * 2 * math.pi
                    ex = cx + ring_r * math.cos(eye_angle)
                    ey = cy + ring_r * math.sin(eye_angle)

                    spec_idx = min(j % len(wheel_spec), len(wheel_spec) - 1) if len(wheel_spec) > 0 else 0
                    amp = wheel_spec[spec_idx] if len(wheel_spec) > 0 else 0.2

                    if amp > 0.05:
                        eye_size = 2 + amp * 6
                        freq = frequencies[spec_start + spec_idx] if spec_start + spec_idx < len(frequencies) else 440
                        color = self._freq_to_color(freq, amp)

                        ctx.set_source_rgba(color[0], color[1], color[2], amp * 0.7)
                        ctx.arc(ex, ey, eye_size, 0, 2 * math.pi)
                        ctx.fill()

    def _render_chayot_3d(self, ctx: cairo.Context, vp: np.ndarray,
                           rot: np.ndarray, spectrum: np.ndarray):
        """Render the Four Living Creatures in 3D."""
        distance = self.config.tetrahedron_size * 1.8

        for i, creature in enumerate(self.chayot_types):
            angle = self.rotation * 0.3 + math.radians(i * 90)
            pos = np.array([
                distance * math.cos(angle),
                0.3,
                distance * math.sin(angle)
            ])

            proj = self._project_point(pos, vp)
            if proj is None:
                continue

            x, y, depth = proj

            spec_start = int(len(spectrum) * i / 4)
            spec_end = int(len(spectrum) * (i + 1) / 4)
            energy = np.mean(spectrum[spec_start:spec_end])

            color = self.chayot_colors[creature]
            radius = 25 * (0.7 + energy * 0.3)
            pulse = 0.7 + 0.3 * math.sin(self.pulse_phase + i)

            # Glow
            gradient = cairo.RadialGradient(x, y, 0, x, y, radius)
            gradient.add_color_stop_rgba(0, color[0], color[1], color[2], 0.7 * pulse)
            gradient.add_color_stop_rgba(0.5, color[0] * 0.7, color[1] * 0.7, color[2] * 0.7, 0.3 * pulse)
            gradient.add_color_stop_rgba(1, 0, 0, 0, 0)

            ctx.arc(x, y, radius, 0, 2 * math.pi)
            ctx.set_source(gradient)
            ctx.fill()

    def _render_fire_3d(self, ctx: cairo.Context, vp: np.ndarray, rot: np.ndarray):
        """Render fire particles in 3D space."""
        for i in range(self.config.fire_particles):
            angle = self.rotation * 3 + math.radians(i * 360 / self.config.fire_particles)
            phase = self.pulse_phase + i * 0.2

            r = 0.5 + 0.8 * (0.5 + 0.5 * math.sin(phase))
            y = 0.3 * math.sin(phase * 2)

            pos = np.array([
                r * math.cos(angle),
                y,
                r * math.sin(angle)
            ])

            proj = self._project_point(pos, vp)
            if proj is None:
                continue

            x, py, depth = proj

            t = (i % 4) / 3
            fr, fg, fb = 1.0, 0.4 + 0.4 * t, 0.1 * t

            size = 3 + 4 * (0.5 + 0.5 * math.sin(phase))
            alpha = 0.5 + 0.3 * self.bass_energy

            ctx.set_source_rgba(fr, fg, fb, alpha)
            ctx.arc(x, py, size, 0, 2 * math.pi)
            ctx.fill()

    def _render_throne_3d(self, ctx: cairo.Context, vp: np.ndarray):
        """Render the divine throne at the 3D center."""
        center = np.array([0, 0, 0])
        proj = self._project_point(center, vp)

        if proj is None:
            return

        x, y, depth = proj

        energy = self.throne_energy
        pulse = 0.6 + 0.4 * math.sin(self.pulse_phase * 2)

        glow_radius = 40 * (0.5 + energy * 0.5)

        # Divine glow
        gradient = cairo.RadialGradient(x, y, 0, x, y, glow_radius)
        gradient.add_color_stop_rgba(0, 1, 1, 1, energy * 0.9 * pulse)
        gradient.add_color_stop_rgba(0.3, 1, 0.95, 0.8, energy * 0.5 * pulse)
        gradient.add_color_stop_rgba(0.6, 1, 0.85, 0.5, energy * 0.2 * pulse)
        gradient.add_color_stop_rgba(1, 0, 0, 0, 0)

        ctx.arc(x, y, glow_radius, 0, 2 * math.pi)
        ctx.set_source(gradient)
        ctx.fill()

        # Bright core
        ctx.set_source_rgba(1, 1, 1, energy * pulse)
        ctx.arc(x, y, 8, 0, 2 * math.pi)
        ctx.fill()

    def _render_lightning_3d(self, ctx: cairo.Context, vp: np.ndarray):
        """Render 3D lightning bolts."""
        center_proj = self._project_point(np.array([0, 0, 0]), vp)
        if center_proj is None:
            return

        cx, cy, _ = center_proj

        for _ in range(np.random.randint(2, 4)):
            angle = np.random.uniform(0, 360)
            length = 100 + np.random.uniform(0, 80)

            points = [(cx, cy)]
            segments = np.random.randint(3, 6)

            for i in range(segments):
                t = (i + 1) / segments
                base_x = cx + length * t * math.cos(math.radians(angle))
                base_y = cy - length * t * math.sin(math.radians(angle))

                jitter = length * 0.12 * (1 - t)
                points.append((
                    base_x + np.random.uniform(-jitter, jitter),
                    base_y + np.random.uniform(-jitter, jitter)
                ))

            ctx.set_source_rgba(1, 1, 1, 0.9)
            ctx.set_line_width(2.5)
            ctx.move_to(points[0][0], points[0][1])
            for p in points[1:]:
                ctx.line_to(p[0], p[1])
            ctx.stroke()

    def _freq_to_color(self, freq: float, amp: float) -> Tuple[float, float, float]:
        """Map frequency to color."""
        f_min, f_max = 50, 8000
        if freq <= f_min:
            t = 0
        elif freq >= f_max:
            t = 1
        else:
            t = (np.log(freq) - np.log(f_min)) / (np.log(f_max) - np.log(f_min))

        if t < 0.33:
            hue = 0.08 + t * 0.1
        elif t < 0.66:
            hue = 0.55 + (t - 0.33) * 0.15
        else:
            hue = 0.5 + (t - 0.66) * 0.2

        r, g, b = colorsys.hsv_to_rgb(hue % 1, 0.85, 0.4 + amp * 0.6)
        return (r, g, b)

    def _surface_to_pil(self, surface: cairo.ImageSurface) -> Image.Image:
        """Convert Cairo surface to PIL."""
        data = surface.get_data()
        image = Image.frombuffer('RGBA', (self.width, self.height), data, 'raw', 'BGRA', 0, 1)
        return image.convert('RGB')

    def _apply_glow(self, image: Image.Image) -> Image.Image:
        """Apply bloom effect."""
        bright = image.point(lambda x: min(255, int(x * 1.5)) if x > 80 else 0)
        glow = bright.filter(ImageFilter.GaussianBlur(radius=self.config.glow_radius))
        return ImageChops.add(image, glow)


def create_complete_3d_renderer(width: int = 1280, height: int = 720) -> Complete3DMerkabah:
    """Create a complete 3D Merkabah renderer."""
    config = Complete3DConfig(frame_width=width, frame_height=height)
    return Complete3DMerkabah(config)


if __name__ == '__main__':
    import time

    print("Testing Complete 3D Merkabah Renderer...")

    renderer = create_complete_3d_renderer()

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
            frame.save(f'/tmp/merkabah_complete_3d_{i:03d}.png')

    print("\nTest frames saved to /tmp/merkabah_complete_3d_*.png")
