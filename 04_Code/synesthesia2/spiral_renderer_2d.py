"""
SYNESTHESIA 2.0 - Fast 2D Spiral Renderer
Optimized for video generation with consistent output.

This renderer creates the cochlear spiral visualization in 2D,
which is faster and more reliable for batch video rendering.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
from dataclasses import dataclass
from typing import Optional, Tuple, List
import colorsys
import os


@dataclass
class Render2DConfig:
    """Configuration for 2D spiral rendering."""
    frame_width: int = 1920
    frame_height: int = 1080

    # Spiral parameters
    num_frequency_bins: int = 381
    spiral_turns: float = 3.5  # Research-validated (VISUALIZATION_LAWS.md)
    center_x: Optional[int] = None  # Auto-center if None
    center_y: Optional[int] = None
    max_radius: Optional[int] = None  # Auto-scale if None

    # Visual parameters
    base_circle_size: int = 3
    max_circle_size: int = 15
    background_color: Tuple[int, int, int] = (10, 10, 20)

    # Glow effect
    enable_glow: bool = True
    glow_radius: int = 8

    # Gradient background
    enable_gradient_bg: bool = True

    # Labels
    show_labels: bool = True
    label_font_size: int = 14

    # Harmonic connections
    enable_harmonic_connections: bool = True


# Solfège definitions
SOLFEGE = [
    ("Do", [32.703, 65.406, 130.813, 261.626, 523.251, 1046.502, 2093.005, 4186.009], (0, 100, 255)),
    ("Re", [36.708, 73.416, 146.832, 293.665, 587.33, 1174.659, 2349.318, 4698.636], (255, 100, 180)),
    ("Mi", [41.203, 82.407, 164.814, 329.628, 659.255, 1318.51, 2637.02, 5274.041], (255, 50, 50)),
    ("Fa", [43.654, 87.307, 174.614, 349.228, 698.456, 1396.913, 2793.826, 5587.652], (255, 150, 0)),
    ("Sol", [48.999, 97.999, 195.998, 391.995, 783.991, 1567.982, 3135.963, 6271.927], (255, 255, 0)),
    ("La", [55, 110, 220, 440, 880, 1760, 3520, 7040], (0, 255, 100)),
    ("Si", [61.735, 123.471, 246.942, 493.883, 987.767, 1975.533, 3951.066, 7902.133], (0, 255, 255)),
]


def create_chromesthesia_colors(num_bins: int) -> np.ndarray:
    """Create HSV-based color mapping for frequencies."""
    colors = np.zeros((num_bins, 3), dtype=np.uint8)

    for i in range(num_bins):
        t = i / (num_bins - 1)
        # Hue: red (0) -> cyan (0.5) based on frequency
        hue = t * 0.7
        saturation = 0.9
        value = 0.9

        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        colors[i] = [int(r * 255), int(g * 255), int(b * 255)]

    return colors


class FastSpiralRenderer:
    """
    Fast 2D spiral renderer optimized for video generation.
    """

    def __init__(self, config: Optional[Render2DConfig] = None):
        self.config = config or Render2DConfig()

        # Auto-calculate center and radius
        if self.config.center_x is None:
            self.config.center_x = self.config.frame_width // 2
        if self.config.center_y is None:
            self.config.center_y = self.config.frame_height // 2
        if self.config.max_radius is None:
            self.config.max_radius = min(self.config.frame_width, self.config.frame_height) // 2 - 50

        # Precompute spiral coordinates
        self._compute_spiral_coordinates()

        # Precompute colors
        self.colors = create_chromesthesia_colors(self.config.num_frequency_bins)

        # Precompute gradient background pattern
        if self.config.enable_gradient_bg:
            self._precompute_gradient()

        # Harmonic connections
        self.harmonic_connections = None
        if self.config.enable_harmonic_connections:
            from harmonic_connections import HarmonicConnectionRenderer
            self.harmonic_connections = HarmonicConnectionRenderer()

        # Animation state
        self.rotation_angle = 0.0
        self.wave_phase = 0.0

    def _compute_spiral_coordinates(self):
        """Precompute the base spiral coordinates."""
        n = self.config.num_frequency_bins

        # Fermat spiral: r = a * sqrt(theta)
        # Modified for cochlear shape
        theta = np.linspace(0, self.config.spiral_turns * 2 * np.pi, n)

        # Radius increases with sqrt for natural spiral
        t = np.linspace(0, 1, n)
        radius = self.config.max_radius * np.sqrt(t)

        self.base_theta = theta
        self.base_radius = radius

        # Store base x, y (will be rotated during rendering)
        self.base_x = radius * np.cos(theta)
        self.base_y = radius * np.sin(theta)

    def _precompute_gradient(self):
        """Precompute radial gradient mask (0 at center, 1 at corners)."""
        w, h = self.config.frame_width, self.config.frame_height
        cx, cy = w // 2, h // 2
        max_dist = np.sqrt(cx ** 2 + cy ** 2)
        Y, X = np.ogrid[:h, :w]
        self._gradient_mask = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2).astype(np.float32) / max_dist
        self._gradient_mask = np.clip(self._gradient_mask, 0, 1)

    def _make_gradient_bg(self, bg_color: Tuple[int, int, int]) -> Image.Image:
        """Create a radial gradient background: brighter at center, darker at edges."""
        center_factor = 1.8
        edge_factor = 0.35
        factor = center_factor + (edge_factor - center_factor) * self._gradient_mask

        img_array = np.zeros((self.config.frame_height, self.config.frame_width, 3), dtype=np.uint8)
        for c in range(3):
            img_array[:, :, c] = np.clip(bg_color[c] * factor, 0, 255).astype(np.uint8)

        return Image.fromarray(img_array, 'RGB')

    def render_frame(self,
                     amplitude_data: np.ndarray,
                     frame_idx: int = 0,
                     frequencies: Optional[np.ndarray] = None,
                     wave_enabled: bool = True,
                     background_color: Optional[Tuple[int, int, int]] = None,
                     scale_factor: float = 1.0,
                     brightness_boost: float = 0.0) -> Image.Image:
        """
        Render a single frame.

        Args:
            amplitude_data: [num_frequency_bins] amplitude values
            frame_idx: Frame index for animation
            frequencies: Optional frequency array for labels
            wave_enabled: Enable radial wave animation
            background_color: Override background color (e.g. from harmonic aura)
            scale_factor: Spiral scale multiplier (e.g. from rhythm pulse)
            brightness_boost: Extra brightness (e.g. from rhythm pulse)

        Returns:
            PIL Image
        """
        bg_color = background_color or self.config.background_color

        # Create background (gradient or flat)
        if self.config.enable_gradient_bg and hasattr(self, '_gradient_mask'):
            img = self._make_gradient_bg(bg_color)
        else:
            img = Image.new('RGB', (self.config.frame_width, self.config.frame_height), bg_color)

        # Update animation state
        self.rotation_angle = frame_idx * 0.5  # Slow rotation
        self.wave_phase = frame_idx * 0.15  # Wave animation

        # Rotate coordinates with optional scale factor (rhythm pulse)
        angle_rad = np.radians(self.rotation_angle)
        cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)

        scaled_x = self.base_x * scale_factor
        scaled_y = self.base_y * scale_factor

        x_rot = scaled_x * cos_a - scaled_y * sin_a + self.config.center_x
        y_rot = scaled_x * sin_a + scaled_y * cos_a + self.config.center_y

        # Normalize amplitude for sizing
        amp_normalized = amplitude_data / (np.max(amplitude_data) + 1e-6)

        # Harmonic connections (draw lines before circles; apply displacement)
        if self.harmonic_connections is not None and frequencies is not None:
            x_rot, y_rot = self.harmonic_connections.render(
                draw, amp_normalized, frequencies, x_rot, y_rot, self.colors)

        # Radial wave modulation
        if wave_enabled:
            wave = 0.5 + 0.5 * np.sin(self.base_theta * 2 + self.wave_phase)
        else:
            wave = np.ones_like(self.base_theta)

        if self.config.enable_glow:
            # Draw circles on a black layer, then blur for glow
            circle_layer = Image.new('RGB',
                                     (self.config.frame_width, self.config.frame_height), (0, 0, 0))
            circle_draw = ImageDraw.Draw(circle_layer)
            self._draw_circles(circle_draw, x_rot, y_rot, amp_normalized, wave, brightness_boost)

            # Gaussian blur creates the glow halo
            glow = circle_layer.filter(ImageFilter.GaussianBlur(radius=self.config.glow_radius))

            # Composite: background + glow halo + sharp circles
            img = ImageChops.add(img, glow)
            img = ImageChops.add(img, circle_layer)
        else:
            draw = ImageDraw.Draw(img)
            self._draw_circles(draw, x_rot, y_rot, amp_normalized, wave, brightness_boost)

        # Draw solfège labels on top
        if self.config.show_labels and frequencies is not None:
            draw = ImageDraw.Draw(img)
            self._draw_labels(draw, x_rot, y_rot, frequencies, amp_normalized)

        return img

    def _draw_circles(self, draw: ImageDraw.Draw, x_rot: np.ndarray,
                      y_rot: np.ndarray, amp_normalized: np.ndarray,
                      wave: np.ndarray, brightness_boost: float = 0.0):
        """Draw the spiral frequency circles."""
        for i in range(self.config.num_frequency_bins - 1, -1, -1):
            x = int(x_rot[i])
            y = int(y_rot[i])

            amp = amp_normalized[i]
            size = int(self.config.base_circle_size +
                       amp * wave[i] * (self.config.max_circle_size - self.config.base_circle_size))
            size = max(1, size)

            base_color = self.colors[i]
            brightness = min(1.0, 0.3 + 0.7 * amp * wave[i] + brightness_boost)
            color = tuple(int(c * brightness) for c in base_color)

            draw.ellipse([x - size, y - size, x + size, y + size], fill=color)

    def _draw_labels(self, draw: ImageDraw, x_coords: np.ndarray,
                     y_coords: np.ndarray, frequencies: np.ndarray,
                     amplitudes: np.ndarray):
        """Draw solfège note labels."""
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                                      self.config.label_font_size)
        except:
            font = ImageFont.load_default()

        for name, freqs, color in SOLFEGE:
            for freq in freqs:
                # Find closest frequency bin
                idx = int(np.argmin(np.abs(frequencies - freq)))

                if idx < len(x_coords):
                    x = int(x_coords[idx])
                    y = int(y_coords[idx])

                    # Only show label if amplitude is significant
                    if amplitudes[idx] > 0.1:
                        label = f"{freq:.0f}Hz"
                        draw.text((x + 10, y - 5), label, fill=color, font=font)

    def render_frame_to_array(self,
                              amplitude_data: np.ndarray,
                              frame_idx: int = 0,
                              frequencies: Optional[np.ndarray] = None) -> np.ndarray:
        """Render frame and return as numpy array."""
        img = self.render_frame(amplitude_data, frame_idx, frequencies)
        return np.array(img)

    def save_frame(self,
                   amplitude_data: np.ndarray,
                   output_path: str,
                   frame_idx: int = 0,
                   frequencies: Optional[np.ndarray] = None):
        """Render and save frame to file."""
        img = self.render_frame(amplitude_data, frame_idx, frequencies)
        img.save(output_path)


def render_test_frame_2d(output_path: str = "test_spiral_2d.png"):
    """Generate a test frame with synthetic data."""
    config = Render2DConfig(
        frame_width=1920,
        frame_height=1080
    )
    renderer = FastSpiralRenderer(config)

    # Create synthetic amplitude data
    n = config.num_frequency_bins
    t = np.linspace(0, 1, n)

    # Simulate harmonics
    amplitude = np.zeros(n)
    for peak in [0.1, 0.2, 0.35, 0.5, 0.65, 0.8]:
        amplitude += 20 * np.exp(-((t - peak) ** 2) / 0.005)
    amplitude += np.random.random(n) * 3

    # Create frequency array
    frequencies = np.logspace(np.log10(20), np.log10(8000), n)

    # Render
    renderer.save_frame(amplitude, output_path, frame_idx=50, frequencies=frequencies)
    print(f"Test frame saved to {output_path}")


if __name__ == "__main__":
    render_test_frame_2d()
