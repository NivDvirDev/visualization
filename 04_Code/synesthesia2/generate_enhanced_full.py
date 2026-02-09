#!/usr/bin/env python3
"""
SYNESTHESIA 3.0 - Enhanced Full Track Generator
================================================
Generates an enhanced visualization of the full Papaoutai track with:
- Glow halos around spiral points (outer glow pass before core)
- White-hot cores for peaks above 0.6 amplitude
- Radial gradient background instead of flat color
- Enhanced renderer settings for richer visuals
"""

import numpy as np
import os
import sys
import math
from PIL import Image, ImageDraw, ImageFilter

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from video_generator_temporal import TemporalVideoGenerator, TemporalVideoConfig
from temporal_renderer import TemporalSpiralRenderer, TemporalRenderConfig


class EnhancedSpiralRenderer(TemporalSpiralRenderer):
    """
    Enhanced renderer with glow halos, white-hot cores, and radial gradient background.
    """

    def render_frame(self, amplitude_data, frame_idx=0, frequencies=None,
                     show_labels=True, show_info=True):
        """Override to use radial gradient background instead of flat color."""
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

        # Render base spiral with glow
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
        img = Image.new('RGB', (w, h))
        pixels = img.load()

        base = self.config.base_background_color
        # Center color is a blend of base and aura, brightened
        center_r = min(255, int(base[0] * 1.8 + aura_color[0] * 0.3))
        center_g = min(255, int(base[1] * 1.8 + aura_color[1] * 0.3))
        center_b = min(255, int(base[2] * 1.8 + aura_color[2] * 0.3))

        # Edge color is darker base
        edge_r = max(0, base[0] // 2)
        edge_g = max(0, base[1] // 2)
        edge_b = max(0, base[2] // 2)

        cx, cy = w // 2, h // 2
        max_dist = math.sqrt(cx * cx + cy * cy)

        # Use numpy for speed
        y_coords, x_coords = np.mgrid[0:h, 0:w]
        dist = np.sqrt((x_coords - cx) ** 2 + (y_coords - cy) ** 2) / max_dist
        dist = np.clip(dist, 0, 1)

        # Ease the gradient (power curve for softer center)
        dist = dist ** 0.7

        r_channel = (center_r * (1 - dist) + edge_r * dist).astype(np.uint8)
        g_channel = (center_g * (1 - dist) + edge_g * dist).astype(np.uint8)
        b_channel = (center_b * (1 - dist) + edge_b * dist).astype(np.uint8)

        img_array = np.stack([r_channel, g_channel, b_channel], axis=-1)
        img = Image.fromarray(img_array, 'RGB')
        return img

    def _render_spiral(self, draw, amplitude_data, scale, brightness_boost,
                       frequencies, show_labels):
        """Override to add glow halos and white-hot cores."""
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

        # === PASS 1: Outer glow halos (drawn first, behind everything) ===
        for i in range(self.num_points):
            amp = amp_normalized[i]
            if amp < 0.15:
                continue

            base_size = self.config.base_point_size
            size = int(base_size + amp * base_size * 3 * scale)
            if size < 2:
                continue

            x, y = int(x_coords[i]), int(y_coords[i])

            base_color = self.colors[i]
            brightness = 0.3 + amp * 0.7 + brightness_boost

            # Glow halo: larger, dimmer version of the point
            glow_radius = int(size * 2.5)
            glow_alpha = amp * 0.25
            glow_color = tuple(int(min(255, c * brightness * glow_alpha)) for c in base_color)

            draw.ellipse(
                [x - glow_radius, y - glow_radius, x + glow_radius, y + glow_radius],
                fill=glow_color
            )

        # === PASS 2: Core points ===
        for i in range(self.num_points):
            amp = amp_normalized[i]

            base_size = self.config.base_point_size
            size = int(base_size + amp * base_size * 3 * scale)
            if size < 1:
                continue

            x, y = int(x_coords[i]), int(y_coords[i])

            base_color = self.colors[i]
            brightness = 0.3 + amp * 0.7 + brightness_boost
            color = tuple(int(min(255, c * brightness)) for c in base_color)

            # Draw main point
            draw.ellipse([x - size, y - size, x + size, y + size], fill=color)

            # === White-hot core for peaks above 0.6 amplitude ===
            if amp > 0.6:
                # Blend toward white based on how far above 0.6
                white_blend = (amp - 0.6) / 0.4  # 0.0 at 0.6, 1.0 at 1.0
                white_blend = min(1.0, white_blend)

                core_r = int(color[0] + (255 - color[0]) * white_blend)
                core_g = int(color[1] + (255 - color[1]) * white_blend)
                core_b = int(color[2] + (255 - color[2]) * white_blend)
                core_color = (core_r, core_g, core_b)

                core_size = max(2, int(size * 0.5))
                draw.ellipse(
                    [x - core_size, y - core_size, x + core_size, y + core_size],
                    fill=core_color
                )

            # Draw label if applicable
            if i in labeled_indices and frequencies is not None:
                freq = frequencies[i]
                label = f"{int(freq)}Hz"
                draw.text((x + size + 5, y - 7), label, fill=color, font=self.font)


def main():
    # Paths
    audio_path = "/Users/guydvir/Project/07_Media/Papaoutai_Stromae.mp3"
    output_path = "/Users/guydvir/Project/04_Code/synesthesia2/synth3_enhanced_full_papaoutai.mp4"

    print("=" * 70)
    print("SYNESTHESIA 3.0 - Enhanced Full Track Generator")
    print("=" * 70)
    print(f"Audio:  {audio_path}")
    print(f"Output: {output_path}")
    print()

    # Verify input exists
    if not os.path.exists(audio_path):
        print(f"ERROR: Audio file not found: {audio_path}")
        sys.exit(1)

    # Configure video generator
    config = TemporalVideoConfig(
        output_width=1920,
        output_height=1080,
        frame_rate=30,
        video_codec="libx264",
        video_preset="medium",
        video_crf=18,
        audio_codec="aac",
        audio_bitrate="320k",
        enable_melody_trail=True,
        enable_rhythm_pulse=True,
        enable_harmonic_aura=True,
        enable_atmosphere=True,
    )

    # Create generator
    generator = TemporalVideoGenerator(config)

    # Replace the renderer with our enhanced version
    enhanced_render_config = TemporalRenderConfig(
        frame_width=1920,
        frame_height=1080,
        base_point_size=6,
        pulse_scale_amount=0.20,
        pulse_brightness_amount=0.40,
        pulse_decay_rate=0.80,
        trail_glow_radius=12,
        trail_color=(255, 240, 120),
        aura_brightness=0.25,
        aura_transition_speed=0.12,
        base_background_color=(10, 12, 25),
        enable_melody_trail=True,
        enable_rhythm_pulse=True,
        enable_harmonic_aura=True,
        enable_atmosphere=True,
    )

    generator.renderer = EnhancedSpiralRenderer(enhanced_render_config, config.frame_rate)
    generator.render_config = enhanced_render_config

    # Override _encode_video to use /opt/homebrew/bin/ffmpeg
    original_encode = generator._encode_video

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
        print(f"Running FFmpeg: /opt/homebrew/bin/ffmpeg")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"FFmpeg error: {result.stderr}")
            raise RuntimeError("FFmpeg encoding failed")

    generator._encode_video = encode_with_homebrew_ffmpeg

    # Generate the full video (no start_time/duration limits)
    print("Starting full track generation...")
    print("This will process the entire audio file.\n")

    generator.generate(
        audio_path=audio_path,
        output_path=output_path,
    )

    # Report
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\nDone!")
    print(f"Output: {output_path}")
    print(f"Size:   {file_size_mb:.1f} MB")


if __name__ == "__main__":
    main()
