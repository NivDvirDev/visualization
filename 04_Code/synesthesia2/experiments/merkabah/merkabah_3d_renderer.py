#!/usr/bin/env python3
"""
SYNESTHESIA - 3D Merkabah Renderer
===================================
True 3D rendering of Merkabah sacred geometry with perspective projection.

The Star Tetrahedron in proper 3D:
- Upper tetrahedron points toward the heavens (sky)
- Lower tetrahedron points toward the earth (ground)
- They interpenetrate, crossing at their edges
- Camera positioned to view the mystical chariot in space

Features:
- True 3D perspective projection
- Depth-sorted rendering with painter's algorithm
- Atmospheric effects (sky gradient, ground plane)
- Smooth shading and glow effects using Cairo
- Dynamic camera movement synced to audio
"""

import numpy as np
import cairo
import math
from PIL import Image, ImageFilter, ImageDraw
from dataclasses import dataclass, field
from typing import Tuple, List, Optional
from collections import deque
import colorsys


@dataclass
class Camera3D:
    """3D Camera with position, rotation, and projection settings."""
    position: np.ndarray = field(default_factory=lambda: np.array([0.0, 0.0, -5.0]))
    target: np.ndarray = field(default_factory=lambda: np.array([0.0, 0.0, 0.0]))
    up: np.ndarray = field(default_factory=lambda: np.array([0.0, 1.0, 0.0]))
    fov: float = 60.0  # Field of view in degrees
    near: float = 0.1
    far: float = 100.0

    def get_view_matrix(self) -> np.ndarray:
        """Calculate view matrix (look-at)."""
        forward = self.target - self.position
        forward = forward / np.linalg.norm(forward)

        right = np.cross(forward, self.up)
        right = right / np.linalg.norm(right)

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
class Merkabah3DConfig:
    """Configuration for 3D Merkabah visualization."""
    frame_width: int = 1280
    frame_height: int = 720

    # Tetrahedron size
    tetrahedron_size: float = 1.5

    # Colors (RGB 0-1)
    upper_tetra_color: Tuple[float, float, float] = (0.3, 0.5, 1.0)  # Heavenly blue
    lower_tetra_color: Tuple[float, float, float] = (1.0, 0.6, 0.3)  # Earthly amber
    edge_glow_color: Tuple[float, float, float] = (1.0, 1.0, 0.9)

    # Sky/Ground atmosphere
    sky_color_top: Tuple[float, float, float] = (0.05, 0.05, 0.15)  # Deep space
    sky_color_horizon: Tuple[float, float, float] = (0.15, 0.1, 0.25)  # Purple horizon
    ground_color: Tuple[float, float, float] = (0.1, 0.05, 0.02)  # Dark earth

    # Camera settings
    camera_distance: float = 5.0
    camera_height: float = 1.0
    camera_orbit_speed: float = 0.3  # Degrees per frame

    # Animation
    rotation_speed: float = 0.5
    pulse_speed: float = 0.03

    # Rendering quality
    edge_thickness: float = 3.0
    glow_intensity: float = 0.8
    glow_radius: int = 12

    # Effects
    enable_atmosphere: bool = True
    enable_stars: bool = True
    num_stars: int = 200


class Geometry3D:
    """3D geometry utilities for Merkabah."""

    @staticmethod
    def create_tetrahedron(size: float = 1.0, pointing_up: bool = True) -> Tuple[np.ndarray, List[Tuple]]:
        """
        Create a tetrahedron (4 vertices, 4 triangular faces).

        Returns:
            vertices: (4, 3) array of vertex positions
            faces: list of (v1, v2, v3) vertex indices for each face
        """
        # Regular tetrahedron vertices
        # Apex at top/bottom, base is equilateral triangle
        h = size * math.sqrt(2/3)  # Height
        r = size * math.sqrt(2/3)  # Circumradius of base

        if pointing_up:
            apex = np.array([0, h, 0])
            base_y = -h/3
        else:
            apex = np.array([0, -h, 0])
            base_y = h/3

        # Base triangle vertices (120 degrees apart)
        base = []
        for i in range(3):
            angle = math.radians(i * 120 - 90)  # Start pointing forward
            x = r * math.cos(angle)
            z = r * math.sin(angle)
            base.append(np.array([x, base_y, z]))

        vertices = np.array([apex, base[0], base[1], base[2]])

        # Faces (vertex indices, counter-clockwise for front-facing)
        if pointing_up:
            faces = [
                (0, 1, 2),  # Front face
                (0, 2, 3),  # Right face
                (0, 3, 1),  # Left face
                (1, 3, 2),  # Base
            ]
        else:
            faces = [
                (0, 2, 1),  # Front face
                (0, 3, 2),  # Right face
                (0, 1, 3),  # Left face
                (1, 2, 3),  # Base
            ]

        return vertices, faces

    @staticmethod
    def get_tetrahedron_edges(vertices: np.ndarray) -> List[Tuple[np.ndarray, np.ndarray]]:
        """Get all edges of a tetrahedron."""
        edges = [
            (0, 1), (0, 2), (0, 3),  # Apex to base
            (1, 2), (2, 3), (3, 1),  # Base triangle
        ]
        return [(vertices[e[0]], vertices[e[1]]) for e in edges]

    @staticmethod
    def rotation_matrix_y(angle: float) -> np.ndarray:
        """Create Y-axis rotation matrix (4x4)."""
        c, s = math.cos(angle), math.sin(angle)
        return np.array([
            [c, 0, s, 0],
            [0, 1, 0, 0],
            [-s, 0, c, 0],
            [0, 0, 0, 1]
        ])

    @staticmethod
    def rotation_matrix_x(angle: float) -> np.ndarray:
        """Create X-axis rotation matrix (4x4)."""
        c, s = math.cos(angle), math.sin(angle)
        return np.array([
            [1, 0, 0, 0],
            [0, c, -s, 0],
            [0, s, c, 0],
            [0, 0, 0, 1]
        ])


class Merkabah3DRenderer:
    """
    3D Merkabah renderer with true perspective projection.

    Renders the Star Tetrahedron as two interpenetrating tetrahedra
    in 3D space with atmospheric effects.
    """

    def __init__(self, config: Merkabah3DConfig):
        self.config = config
        self.geometry = Geometry3D()

        self.width = config.frame_width
        self.height = config.frame_height
        self.aspect = self.width / self.height

        # Create camera
        self.camera = Camera3D(
            position=np.array([0.0, config.camera_height, -config.camera_distance]),
            target=np.array([0.0, 0.0, 0.0]),
            fov=60.0
        )

        # Create tetrahedra
        self.upper_verts, self.upper_faces = self.geometry.create_tetrahedron(
            config.tetrahedron_size, pointing_up=True
        )
        self.lower_verts, self.lower_faces = self.geometry.create_tetrahedron(
            config.tetrahedron_size, pointing_up=False
        )

        # Animation state
        self.rotation_angle = 0.0
        self.camera_orbit_angle = 0.0
        self.pulse_phase = 0.0
        self.frame_count = 0

        # Energy state
        self.bass_energy = 0.0
        self.treble_energy = 0.0
        self.throne_energy = 0.0

        # Generate stars once
        if config.enable_stars:
            self.stars = self._generate_stars(config.num_stars)
        else:
            self.stars = []

    def _generate_stars(self, num: int) -> List[Tuple[float, float, float, float]]:
        """Generate random star positions and brightness."""
        np.random.seed(42)  # Consistent stars
        stars = []
        for _ in range(num):
            # Random position on upper hemisphere
            theta = np.random.uniform(0, 2 * math.pi)
            phi = np.random.uniform(0, math.pi / 2)  # Only upper half

            x = math.cos(theta) * math.sin(phi)
            y = math.cos(phi)  # Always positive (above horizon)
            z = math.sin(theta) * math.sin(phi)

            brightness = np.random.uniform(0.3, 1.0)
            size = np.random.uniform(1, 3)

            stars.append((x, y, z, brightness, size))

        return stars

    def update_state(self, beat_strength: float = 0, is_beat: bool = False,
                     pitch: float = 0, chroma: np.ndarray = None,
                     rms: float = 0.5, bass: float = 0.33, treble: float = 0.33):
        """Update animation state based on audio features."""

        # Rotation speeds affected by energy
        energy_factor = 0.5 + rms * 1.5

        self.rotation_angle += math.radians(self.config.rotation_speed * energy_factor)
        self.camera_orbit_angle += math.radians(self.config.camera_orbit_speed * energy_factor)
        self.pulse_phase += self.config.pulse_speed * energy_factor
        self.frame_count += 1

        # Update camera position (orbiting)
        orbit_radius = self.config.camera_distance
        self.camera.position[0] = orbit_radius * math.sin(self.camera_orbit_angle)
        self.camera.position[2] = -orbit_radius * math.cos(self.camera_orbit_angle)

        # Energy states
        self.bass_energy = bass
        self.treble_energy = treble

        if pitch > 0:
            self.throne_energy = min(1.0, self.throne_energy + 0.3)
        self.throne_energy *= 0.92

    def render_frame(self, spectrum: np.ndarray, frequencies: np.ndarray,
                     temporal_features: dict = None) -> Image.Image:
        """Render a 3D frame of the Merkabah."""

        # Normalize spectrum
        if spectrum.max() > 0:
            spectrum = spectrum / spectrum.max()
        spectrum = np.clip(spectrum, 0, 1)

        # Calculate band energies
        bass_mask = frequencies < 250
        mid_mask = (frequencies >= 250) & (frequencies < 2000)
        treble_mask = frequencies >= 2000

        bass = np.mean(spectrum[bass_mask]) if np.any(bass_mask) else 0.33
        treble = np.mean(spectrum[treble_mask]) if np.any(treble_mask) else 0.33

        # Create Cairo surface
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.width, self.height)
        ctx = cairo.Context(surface)
        ctx.set_antialias(cairo.ANTIALIAS_BEST)

        # Get transformation matrices
        view_matrix = self.camera.get_view_matrix()
        proj_matrix = self.camera.get_projection_matrix(self.aspect)
        model_matrix = self.geometry.rotation_matrix_y(self.rotation_angle)

        mvp = proj_matrix @ view_matrix @ model_matrix

        # Render layers
        self._render_atmosphere(ctx)

        if self.config.enable_stars:
            self._render_stars(ctx, view_matrix, proj_matrix)

        self._render_ground_plane(ctx, mvp)
        self._render_merkabah(ctx, mvp, bass, treble)
        self._render_center_throne(ctx, mvp)

        # Convert to PIL and apply post-processing
        image = self._surface_to_pil(surface)

        if self.config.glow_radius > 0:
            image = self._apply_glow(image)

        return image

    def _render_atmosphere(self, ctx: cairo.Context):
        """Render sky gradient background."""
        # Vertical gradient from deep space to horizon
        gradient = cairo.LinearGradient(0, 0, 0, self.height)

        top = self.config.sky_color_top
        horizon = self.config.sky_color_horizon
        ground = self.config.ground_color

        # Add pulse to atmosphere
        pulse = 0.5 + 0.5 * math.sin(self.pulse_phase)
        energy_boost = (self.bass_energy + self.treble_energy) * 0.1 * pulse

        gradient.add_color_stop_rgb(0, top[0] + energy_boost * 0.2,
                                      top[1] + energy_boost * 0.1,
                                      top[2] + energy_boost * 0.3)
        gradient.add_color_stop_rgb(0.45, horizon[0] + energy_boost * 0.3,
                                       horizon[1] + energy_boost * 0.2,
                                       horizon[2] + energy_boost * 0.4)
        gradient.add_color_stop_rgb(0.55, horizon[0] * 0.7,
                                       horizon[1] * 0.5,
                                       horizon[2] * 0.6)
        gradient.add_color_stop_rgb(1, ground[0], ground[1], ground[2])

        ctx.set_source(gradient)
        ctx.paint()

    def _render_stars(self, ctx: cairo.Context, view: np.ndarray, proj: np.ndarray):
        """Render background stars."""
        vp = proj @ view

        for x, y, z, brightness, size in self.stars:
            # Transform star position (far away)
            star_pos = np.array([x * 50, y * 50, z * 50, 1.0])
            clip = vp @ star_pos

            if clip[3] > 0 and clip[2] > 0:  # In front of camera
                ndc_x = clip[0] / clip[3]
                ndc_y = clip[1] / clip[3]

                screen_x = (ndc_x + 1) * 0.5 * self.width
                screen_y = (1 - ndc_y) * 0.5 * self.height

                # Only draw if on screen and above horizon
                if 0 < screen_x < self.width and 0 < screen_y < self.height * 0.5:
                    # Twinkle effect
                    twinkle = 0.7 + 0.3 * math.sin(self.pulse_phase * 3 + x * 10 + y * 7)
                    alpha = brightness * twinkle

                    ctx.set_source_rgba(1.0, 1.0, 0.95, alpha)
                    ctx.arc(screen_x, screen_y, size, 0, 2 * math.pi)
                    ctx.fill()

    def _render_ground_plane(self, ctx: cairo.Context, mvp: np.ndarray):
        """Render a subtle ground plane grid."""
        # Ground plane at y = -tetrahedron_size
        ground_y = -self.config.tetrahedron_size * 0.8
        grid_size = 5
        grid_step = 0.5

        ctx.set_line_width(0.5)

        for i in np.arange(-grid_size, grid_size + grid_step, grid_step):
            # Lines parallel to X
            p1 = self._project_point(np.array([-grid_size, ground_y, i]), mvp)
            p2 = self._project_point(np.array([grid_size, ground_y, i]), mvp)

            if p1 is not None and p2 is not None:
                # Fade with distance
                alpha = max(0.05, 0.2 - abs(i) * 0.03)
                ctx.set_source_rgba(0.3, 0.2, 0.15, alpha)
                ctx.move_to(p1[0], p1[1])
                ctx.line_to(p2[0], p2[1])
                ctx.stroke()

            # Lines parallel to Z
            p1 = self._project_point(np.array([i, ground_y, -grid_size]), mvp)
            p2 = self._project_point(np.array([i, ground_y, grid_size]), mvp)

            if p1 is not None and p2 is not None:
                alpha = max(0.05, 0.2 - abs(i) * 0.03)
                ctx.set_source_rgba(0.3, 0.2, 0.15, alpha)
                ctx.move_to(p1[0], p1[1])
                ctx.line_to(p2[0], p2[1])
                ctx.stroke()

    def _render_merkabah(self, ctx: cairo.Context, mvp: np.ndarray,
                          bass: float, treble: float):
        """Render the Star Tetrahedron (two interpenetrating tetrahedra)."""

        # Collect all faces with their depths for sorting
        all_faces = []

        # Upper tetrahedron faces
        for face in self.upper_faces:
            verts_3d = [self.upper_verts[i] for i in face]
            center = np.mean(verts_3d, axis=0)

            # Transform center to get depth
            center_4d = np.append(center, 1.0)
            transformed = mvp @ center_4d
            if transformed[3] > 0:
                depth = transformed[2] / transformed[3]
                all_faces.append(('upper', face, verts_3d, depth, treble))

        # Lower tetrahedron faces
        for face in self.lower_faces:
            verts_3d = [self.lower_verts[i] for i in face]
            center = np.mean(verts_3d, axis=0)

            center_4d = np.append(center, 1.0)
            transformed = mvp @ center_4d
            if transformed[3] > 0:
                depth = transformed[2] / transformed[3]
                all_faces.append(('lower', face, verts_3d, depth, bass))

        # Sort by depth (back to front - painter's algorithm)
        all_faces.sort(key=lambda x: -x[3])

        # Render faces
        for face_type, face_indices, verts_3d, depth, energy in all_faces:
            # Project vertices to screen
            screen_verts = []
            for v in verts_3d:
                sv = self._project_point(v, mvp)
                if sv is None:
                    break
                screen_verts.append(sv)

            if len(screen_verts) != 3:
                continue

            # Get face color based on type
            if face_type == 'upper':
                base_color = self.config.upper_tetra_color
            else:
                base_color = self.config.lower_tetra_color

            # Calculate face normal for basic shading
            v0, v1, v2 = [np.array(v) for v in verts_3d]
            edge1 = v1 - v0
            edge2 = v2 - v0
            normal = np.cross(edge1, edge2)
            normal = normal / (np.linalg.norm(normal) + 0.0001)

            # Simple diffuse shading (light from above-front)
            light_dir = np.array([0.3, 0.8, -0.5])
            light_dir = light_dir / np.linalg.norm(light_dir)
            diffuse = max(0.2, abs(np.dot(normal, light_dir)))

            # Pulse effect
            pulse = 0.7 + 0.3 * math.sin(self.pulse_phase + depth)
            intensity = diffuse * (0.4 + energy * 0.6) * pulse

            # Face color with shading
            r = min(1.0, base_color[0] * intensity)
            g = min(1.0, base_color[1] * intensity)
            b = min(1.0, base_color[2] * intensity)

            # Draw filled face with transparency
            ctx.move_to(screen_verts[0][0], screen_verts[0][1])
            ctx.line_to(screen_verts[1][0], screen_verts[1][1])
            ctx.line_to(screen_verts[2][0], screen_verts[2][1])
            ctx.close_path()

            ctx.set_source_rgba(r, g, b, 0.7)
            ctx.fill_preserve()

            # Edge glow
            glow_intensity = 0.5 + energy * 0.5
            ctx.set_source_rgba(1.0, 1.0, 0.9, glow_intensity * 0.3)
            ctx.set_line_width(self.config.edge_thickness + 2)
            ctx.stroke_preserve()

            # Sharp edge
            ctx.set_source_rgba(r * 1.3, g * 1.3, b * 1.3, 0.9)
            ctx.set_line_width(self.config.edge_thickness)
            ctx.stroke()

        # Render all edges with glow
        self._render_edges_with_glow(ctx, mvp, bass, treble)

    def _render_edges_with_glow(self, ctx: cairo.Context, mvp: np.ndarray,
                                 bass: float, treble: float):
        """Render edges with glow effect."""

        # Upper tetrahedron edges
        upper_edges = self.geometry.get_tetrahedron_edges(self.upper_verts)
        for v1, v2 in upper_edges:
            self._draw_edge_3d(ctx, v1, v2, mvp,
                              self.config.upper_tetra_color, treble)

        # Lower tetrahedron edges
        lower_edges = self.geometry.get_tetrahedron_edges(self.lower_verts)
        for v1, v2 in lower_edges:
            self._draw_edge_3d(ctx, v1, v2, mvp,
                              self.config.lower_tetra_color, bass)

    def _draw_edge_3d(self, ctx: cairo.Context, v1: np.ndarray, v2: np.ndarray,
                      mvp: np.ndarray, color: Tuple[float, float, float], energy: float):
        """Draw a 3D edge with glow."""
        p1 = self._project_point(v1, mvp)
        p2 = self._project_point(v2, mvp)

        if p1 is None or p2 is None:
            return

        pulse = 0.7 + 0.3 * math.sin(self.pulse_phase)
        intensity = (0.5 + energy * 0.5) * pulse

        # Outer glow
        for glow_size in [8, 5, 3]:
            alpha = intensity * (0.15 / (glow_size / 3))
            ctx.set_source_rgba(color[0], color[1], color[2], alpha)
            ctx.set_line_width(glow_size)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.move_to(p1[0], p1[1])
            ctx.line_to(p2[0], p2[1])
            ctx.stroke()

        # Core edge
        ctx.set_source_rgba(min(1, color[0] * 1.5),
                           min(1, color[1] * 1.5),
                           min(1, color[2] * 1.5), intensity)
        ctx.set_line_width(2)
        ctx.move_to(p1[0], p1[1])
        ctx.line_to(p2[0], p2[1])
        ctx.stroke()

    def _render_center_throne(self, ctx: cairo.Context, mvp: np.ndarray):
        """Render the divine light at the center."""
        center = self._project_point(np.array([0, 0, 0]), mvp)

        if center is None:
            return

        energy = self.throne_energy
        pulse = 0.6 + 0.4 * math.sin(self.pulse_phase * 2)
        radius = 15 + 25 * energy * pulse

        # Radial glow
        gradient = cairo.RadialGradient(center[0], center[1], 0,
                                        center[0], center[1], radius * 2)
        gradient.add_color_stop_rgba(0, 1.0, 1.0, 1.0, energy * 0.9)
        gradient.add_color_stop_rgba(0.3, 1.0, 0.95, 0.8, energy * 0.5)
        gradient.add_color_stop_rgba(0.6, 1.0, 0.85, 0.5, energy * 0.2)
        gradient.add_color_stop_rgba(1, 0, 0, 0, 0)

        ctx.set_source(gradient)
        ctx.arc(center[0], center[1], radius * 2, 0, 2 * math.pi)
        ctx.fill()

        # Bright core
        ctx.set_source_rgba(1.0, 1.0, 1.0, energy)
        ctx.arc(center[0], center[1], radius * 0.3, 0, 2 * math.pi)
        ctx.fill()

    def _project_point(self, point_3d: np.ndarray, mvp: np.ndarray) -> Optional[Tuple[float, float]]:
        """Project a 3D point to screen coordinates."""
        point_4d = np.append(point_3d, 1.0)
        clip = mvp @ point_4d

        if clip[3] <= 0:  # Behind camera
            return None

        ndc_x = clip[0] / clip[3]
        ndc_y = clip[1] / clip[3]

        screen_x = (ndc_x + 1) * 0.5 * self.width
        screen_y = (1 - ndc_y) * 0.5 * self.height

        return (screen_x, screen_y)

    def _surface_to_pil(self, surface: cairo.ImageSurface) -> Image.Image:
        """Convert Cairo surface to PIL Image."""
        data = surface.get_data()
        image = Image.frombuffer('RGBA', (self.width, self.height),
                                data, 'raw', 'BGRA', 0, 1)
        return image.convert('RGB')

    def _apply_glow(self, image: Image.Image) -> Image.Image:
        """Apply bloom/glow post-processing."""
        # Extract bright areas
        bright = image.point(lambda x: min(255, int(x * 1.5)) if x > 100 else 0)

        # Blur for glow
        glow = bright.filter(ImageFilter.GaussianBlur(radius=self.config.glow_radius))

        # Composite
        from PIL import ImageChops
        result = ImageChops.add(image, glow)

        return result


def create_merkabah_3d_renderer(width: int = 1280, height: int = 720) -> Merkabah3DRenderer:
    """Create a 3D Merkabah renderer with default settings."""
    config = Merkabah3DConfig(frame_width=width, frame_height=height)
    return Merkabah3DRenderer(config)


if __name__ == '__main__':
    import time

    print("Testing 3D Merkabah Renderer...")

    renderer = create_merkabah_3d_renderer()

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
            frame.save(f'/tmp/merkabah_3d_test_{i:03d}.png')

    print("\n3D test frames saved to /tmp/merkabah_3d_test_*.png")
