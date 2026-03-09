#!/usr/bin/env python3
"""
SYNESTHESIA 3.1 - Pitch-Driven Shape Visualization
===================================================
Instead of circles, the current pitch determines the SHAPE:
- Low frequencies → triangular/square shapes (3-4 sides)
- Mid frequencies → pentagonal/hexagonal (5-6 sides)
- High frequencies → star-like with many points (8-12 spikes)
- Amplitude controls "spikiness" — how pointy the shape is
- Shapes are oriented along the spiral tangent for organic flow
"""

import numpy as np
import os
import sys
import math
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from video_generator_temporal import TemporalVideoGenerator, TemporalVideoConfig
from temporal_renderer import TemporalSpiralRenderer, TemporalRenderConfig


class PitchShapeRenderer(TemporalSpiralRenderer):
    """
    Renderer where pitch characteristics determine the shape geometry.
    """

    def __init__(self, config, frame_rate=30):
        super().__init__(config, frame_rate)
        # Precompute frequency bins for shape mapping
        # We'll map log-frequency to number of shape points
        self.min_freq = 20  # Hz
        self.max_freq = 8000  # Hz

    def _freq_to_num_points(self, freq):
        """Map frequency to number of polygon/star points."""
        if freq < self.min_freq:
            freq = self.min_freq
        if freq > self.max_freq:
            freq = self.max_freq

        # Log scale mapping
        log_min = np.log10(self.min_freq)
        log_max = np.log10(self.max_freq)
        log_freq = np.log10(freq)

        # Normalize to 0-1
        t = (log_freq - log_min) / (log_max - log_min)

        # Map to 3-12 points
        # Low freq (t=0) → 3 points (triangle)
        # High freq (t=1) → 12 points (dodecagon/star)
        num_points = int(3 + t * 9)
        return max(3, min(12, num_points))

    def _draw_star_shape(self, draw, cx, cy, outer_radius, inner_radius, 
                         num_points, rotation_angle, color):
        """
        Draw a star/polygon shape.
        - num_points: number of outer points
        - outer_radius: radius to the points
        - inner_radius: radius to the valleys (for star effect)
        - rotation_angle: orientation in radians
        """
        points = []
        for i in range(num_points * 2):
            angle = rotation_angle + (i * math.pi / num_points)
            if i % 2 == 0:
                # Outer point
                r = outer_radius
            else:
                # Inner valley
                r = inner_radius
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append((x, y))

        if len(points) >= 3:
            draw.polygon(points, fill=color)

    def _get_spiral_tangent_angle(self, theta, r):
        """
        Get the tangent angle of the spiral at position (theta, r).
        For a logarithmic spiral r = a * e^(b*theta), the tangent angle is:
        tan(alpha) = 1/b, which is constant. But we use Archimedean-ish.
        Simplified: tangent roughly follows theta + pi/2 with some adjustment.
        """
        # For visual appeal, orient shapes to point outward along spiral
        return theta + math.pi / 2

    def _render_spiral(self, draw, amplitude_data, scale, brightness_boost,
                       frequencies, show_labels):
        """Override to render pitch-driven shapes instead of circles."""
        # Normalize amplitude
        amp_max = np.max(amplitude_data)
        if amp_max < 1e-8:
            amp_normalized = np.zeros_like(amplitude_data)
        else:
            amp_normalized = amplitude_data / amp_max

        # Apply rotation
        theta = self.base_theta + np.radians(self.rotation_angle)

        # Apply wave animation
        wave = np.sin(self.base_theta * 3 + self.wave_phase) * 0.05
        r_animated = self.base_r * (1 + wave) * scale

        # Calculate positions
        x_coords = self.center_x + r_animated * np.cos(theta)
        y_coords = self.center_y + r_animated * np.sin(theta)

        # Frequency labels tracking
        label_frequencies = [73, 110, 147, 220, 294, 440, 587, 880, 1175, 1760, 2349, 3136, 4186]
        labeled_indices = set()

        if frequencies is not None and show_labels:
            for label_freq in label_frequencies:
                idx = np.argmin(np.abs(frequencies - label_freq))
                if amp_normalized[idx] > 0.15:
                    labeled_indices.add(idx)

        # === PASS 1: Outer glow halos (only for louder sounds) ===
        for i in range(self.num_points):
            amp = amp_normalized[i]
            # Only draw glow for sounds above threshold
            if amp < 0.25:
                continue

            base_size = self.config.base_point_size
            size = int(base_size + amp * base_size * 3 * scale)

            x, y = int(x_coords[i]), int(y_coords[i])

            base_color = self.colors[i]
            brightness = 0.3 + amp * 0.5 + brightness_boost

            # Glow halo - use circle for glow (softer)
            glow_radius = int(size * 2.0)
            glow_alpha = amp * 0.15
            glow_color = tuple(int(min(255, c * brightness * glow_alpha)) for c in base_color)

            draw.ellipse(
                [x - glow_radius, y - glow_radius, x + glow_radius, y + glow_radius],
                fill=glow_color
            )

        # === PASS 2: Pitch-driven shapes (ALL points rendered for spiral continuity) ===
        for i in range(self.num_points):
            amp = amp_normalized[i]
            # NO filtering - render ALL points to maintain spiral continuity
            # Amplitude only affects SIZE and SPIKINESS, not visibility

            base_size = self.config.base_point_size
            # Minimum size of 2 ensures all points are visible
            # Size scales with amplitude: quiet = small, loud = large
            min_size = 2
            outer_size = int(min_size + amp * base_size * 3.5 * scale)
            outer_size = max(min_size, outer_size)

            x, y = float(x_coords[i]), float(y_coords[i])

            base_color = self.colors[i]
            # Brightness: quiet points are dimmer but still visible
            brightness = 0.25 + amp * 0.75 + brightness_boost
            color = tuple(int(min(255, c * brightness)) for c in base_color)

            # Get frequency for this bin
            if frequencies is not None and i < len(frequencies):
                freq = frequencies[i]
            else:
                # Estimate from position along spiral
                freq = 20 * (2 ** (i / self.num_points * 8))  # ~20Hz to ~5kHz

            # Determine number of shape points from frequency
            num_points_shape = self._freq_to_num_points(freq)

            # Calculate spikiness from amplitude
            # Low amplitude → nearly circular polygon (inner ≈ outer)
            # High amplitude → spiky star (inner << outer)
            # For very quiet sounds, use simple polygon (no spikiness)
            if amp < 0.15:
                # Quiet: simple polygon, inner = outer (no star effect)
                inner_size = outer_size * 0.85
            else:
                # Louder: star effect increases with amplitude
                spikiness = 0.2 + amp * 0.5  # 0.2 to 0.7
                inner_size = outer_size * (1 - spikiness * 0.5)

            # Get orientation from spiral tangent
            tangent_angle = self._get_spiral_tangent_angle(theta[i], r_animated[i])

            # Draw the pitch-driven shape
            self._draw_star_shape(
                draw, x, y,
                outer_radius=outer_size,
                inner_radius=inner_size,
                num_points=num_points_shape,
                rotation_angle=tangent_angle,
                color=color
            )

            # === White-hot core for peaks above 0.5 amplitude ===
            if amp > 0.5:
                white_blend = (amp - 0.5) / 0.5
                white_blend = min(1.0, white_blend)

                core_r = int(color[0] + (255 - color[0]) * white_blend)
                core_g = int(color[1] + (255 - color[1]) * white_blend)
                core_b = int(color[2] + (255 - color[2]) * white_blend)
                core_color = (core_r, core_g, core_b)

                # Core shape: same num_points but smaller, less spiky
                core_size = max(2, int(outer_size * 0.4))
                core_inner = core_size * 0.75

                self._draw_star_shape(
                    draw, x, y,
                    outer_radius=core_size,
                    inner_radius=core_inner,
                    num_points=num_points_shape,
                    rotation_angle=tangent_angle,
                    color=core_color
                )

            # Draw label if applicable
            if i in labeled_indices and frequencies is not None:
                freq_val = frequencies[i]
                label = f"{int(freq_val)}Hz"
                draw.text((int(x) + outer_size + 5, int(y) - 7), label, fill=color, font=self.font)

    def render_frame(self, amplitude_data, frame_idx=0, frequencies=None,
                     show_labels=True, show_info=True):
        """Override to use radial gradient background."""
        # Get temporal effects
        pulse_scale, pulse_brightness = self.rhythm_pulse.update()
        background_color = self.harmonic_aura.update()
        atmos_effects = self.atmosphere.get_effects()

        # Update animation state
        self.rotation_angle = frame_idx * 0.5 * atmos_effects['rotation_speed']
        self.wave_phase = frame_idx * 0.15

        # Create image with radial gradient background
        img = self._create_radial_gradient_background(background_color)
        draw = ImageDraw.Draw(img)

        # Apply atmosphere effects to rendering
        effective_scale = pulse_scale * atmos_effects['particle_scale']

        # Render spiral with pitch-driven shapes
        self._render_spiral(draw, amplitude_data, effective_scale, pulse_brightness,
                            frequencies, show_labels)

        # Render melodic trail on top
        self.melody_trail.render(draw, self.center_x, self.center_y,
                                 self.max_radius, self.rotation_angle)

        # Add info overlay
        if show_info:
            self._render_info_overlay(draw, frame_idx, pulse_scale)

        return img

    def _create_radial_gradient_background(self, aura_color):
        """Create a radial gradient background from center to edges."""
        w = self.config.frame_width
        h = self.config.frame_height

        base = self.config.base_background_color
        center_r = min(255, int(base[0] * 1.8 + aura_color[0] * 0.3))
        center_g = min(255, int(base[1] * 1.8 + aura_color[1] * 0.3))
        center_b = min(255, int(base[2] * 1.8 + aura_color[2] * 0.3))

        edge_r = max(0, base[0] // 2)
        edge_g = max(0, base[1] // 2)
        edge_b = max(0, base[2] // 2)

        cx, cy = w // 2, h // 2
        max_dist = math.sqrt(cx * cx + cy * cy)

        y_coords, x_coords = np.mgrid[0:h, 0:w]
        dist = np.sqrt((x_coords - cx) ** 2 + (y_coords - cy) ** 2) / max_dist
        dist = np.clip(dist, 0, 1) ** 0.7

        r_channel = (center_r * (1 - dist) + edge_r * dist).astype(np.uint8)
        g_channel = (center_g * (1 - dist) + edge_g * dist).astype(np.uint8)
        b_channel = (center_b * (1 - dist) + edge_b * dist).astype(np.uint8)

        img_array = np.stack([r_channel, g_channel, b_channel], axis=-1)
        return Image.fromarray(img_array, 'RGB')


def main():
    audio_path = "/Users/guydvir/Project/07_Media/Papaoutai_Stromae.mp3"
    output_path = "/Users/guydvir/Project/04_Code/synesthesia2/synth31_pitch_shapes.mp4"

    print("=" * 70)
    print("SYNESTHESIA 3.1 - Pitch-Driven Shape Visualization")
    print("=" * 70)
    print("Shape mapping:")
    print("  • Low pitch (bass) → Triangles/Squares (3-4 sides)")
    print("  • Mid pitch → Pentagons/Hexagons (5-6 sides)")
    print("  • High pitch → Stars with many points (8-12 spikes)")
    print("  • Amplitude → Spikiness of the shape")
    print("  • Orientation → Follows spiral tangent")
    print()
    print(f"Audio:  {audio_path}")
    print(f"Output: {output_path}")
    print()

    if not os.path.exists(audio_path):
        print(f"ERROR: Audio file not found: {audio_path}")
        sys.exit(1)

    # Configure - using 720p for faster preview, can bump to 1080p
    config = TemporalVideoConfig(
        output_width=1280,
        output_height=720,
        frame_rate=30,
        video_codec="libx264",
        video_preset="medium",
        video_crf=20,
        audio_codec="aac",
        audio_bitrate="256k",
        enable_melody_trail=True,
        enable_rhythm_pulse=True,
        enable_harmonic_aura=True,
        enable_atmosphere=True,
    )

    generator = TemporalVideoGenerator(config)

    # Use our pitch-shape renderer
    render_config = TemporalRenderConfig(
        frame_width=1280,
        frame_height=720,
        base_point_size=5,
        pulse_scale_amount=0.18,
        pulse_brightness_amount=0.35,
        pulse_decay_rate=0.82,
        trail_glow_radius=10,
        trail_color=(255, 240, 120),
        aura_brightness=0.22,
        aura_transition_speed=0.12,
        base_background_color=(8, 10, 22),
        enable_melody_trail=True,
        enable_rhythm_pulse=True,
        enable_harmonic_aura=True,
        enable_atmosphere=True,
    )

    generator.renderer = PitchShapeRenderer(render_config, config.frame_rate)
    generator.render_config = render_config

    # Override FFmpeg path
    def encode_with_homebrew_ffmpeg(frames_dir, audio_path, output_path, start_time, duration):
        import subprocess
        cmd = [
            "/opt/homebrew/bin/ffmpeg", "-y",
            "-framerate", str(config.frame_rate),
            "-i", os.path.join(frames_dir, "frame_%06d.png"),
            "-ss", str(start_time),
            "-t", str(duration),
            "-i", audio_path,
            "-c:v", config.video_codec,
            "-preset", config.video_preset,
            "-crf", str(config.video_crf),
            "-c:a", config.audio_codec,
            "-b:a", config.audio_bitrate,
            "-pix_fmt", "yuv420p",
            "-shortest",
            output_path
        ]
        print(f"Running FFmpeg...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"FFmpeg error: {result.stderr}")
            raise RuntimeError("FFmpeg encoding failed")

    generator._encode_video = encode_with_homebrew_ffmpeg

    # Generate 30-second preview first (for quick iteration)
    print("Generating 30-second preview...")
    generator.generate(
        audio_path=audio_path,
        output_path=output_path,
        start_time=30.0,  # Start at 30s (into the main melody)
        duration=30.0,
    )

    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\nDone!")
    print(f"Output: {output_path}")
    print(f"Size:   {file_size_mb:.1f} MB")


if __name__ == "__main__":
    main()
