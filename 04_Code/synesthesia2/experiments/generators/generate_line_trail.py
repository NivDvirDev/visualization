#!/usr/bin/env python3
"""
SYNESTHESIA 3.2 - Continuous Line Trail
========================================
Instead of discrete glowing circles for melody trail,
draws a continuous winding line that follows the melodic pitch.
"""

import numpy as np
import os
import sys
import math
from PIL import Image, ImageDraw
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from video_generator_temporal import TemporalVideoGenerator, TemporalVideoConfig
from temporal_renderer import TemporalSpiralRenderer, TemporalRenderConfig, MelodicTrail


class ContinuousLineTrail(MelodicTrail):
    """
    Melody trail rendered as a continuous flowing line instead of circles.
    """

    def render(self, draw: ImageDraw.Draw, center_x: int, center_y: int,
               max_radius: float, rotation: float):
        """Render the melodic trail as a continuous line."""
        if not self.config.enable_melody_trail or len(self.pitch_history) < 2:
            return

        # Collect valid points
        points = []
        for i, (pitch, confidence) in enumerate(self.pitch_history):
            if pitch <= 0 or confidence < 0.2:
                continue

            x, y = self._pitch_to_coords(pitch, center_x, center_y, max_radius, rotation)
            
            # Age-based alpha
            age = len(self.pitch_history) - i - 1
            alpha = (self.config.trail_decay_rate ** age) * confidence
            
            if alpha < 0.03:
                continue
                
            points.append((x, y, alpha, confidence))

        if len(points) < 2:
            return

        # Draw the line in segments with varying width and alpha
        for i in range(len(points) - 1):
            x1, y1, alpha1, conf1 = points[i]
            x2, y2, alpha2, conf2 = points[i + 1]
            
            # Average alpha and confidence for this segment
            avg_alpha = (alpha1 + alpha2) / 2
            avg_conf = (conf1 + conf2) / 2
            
            # Line width based on confidence (thicker = more confident pitch)
            width = max(1, int(2 + avg_conf * 6))
            
            # Color with alpha
            base_color = self.config.trail_color
            color = tuple(int(c * avg_alpha) for c in base_color)
            
            # Draw line segment
            draw.line([(x1, y1), (x2, y2)], fill=color, width=width)
        
        # Draw brighter "head" at the newest point (most recent pitch)
        if points:
            hx, hy, halpha, hconf = points[-1]
            head_color = tuple(int(c * min(1.0, halpha * 1.5)) for c in self.config.trail_color)
            head_radius = max(3, int(4 + hconf * 4))
            draw.ellipse(
                [hx - head_radius, hy - head_radius,
                 hx + head_radius, hy + head_radius],
                fill=head_color
            )


class LineTrailRenderer(TemporalSpiralRenderer):
    """Renderer using continuous line trail instead of circle particles."""

    def __init__(self, config, frame_rate=30):
        super().__init__(config, frame_rate)
        # Replace the melody trail with our line version
        self.melody_trail = ContinuousLineTrail(config, frame_rate)

    def render_frame(self, amplitude_data, frame_idx=0, frequencies=None,
                     show_labels=True, show_info=True):
        """Render with radial gradient background."""
        pulse_scale, pulse_brightness = self.rhythm_pulse.update()
        background_color = self.harmonic_aura.update()
        atmos_effects = self.atmosphere.get_effects()

        self.rotation_angle = frame_idx * 0.5 * atmos_effects['rotation_speed']
        self.wave_phase = frame_idx * 0.15

        img = self._create_radial_gradient_background(background_color)
        draw = ImageDraw.Draw(img)

        effective_scale = pulse_scale * atmos_effects['particle_scale']

        self._render_spiral(draw, amplitude_data, effective_scale, pulse_brightness,
                            frequencies, show_labels)

        # Render the continuous line trail
        self.melody_trail.render(draw, self.center_x, self.center_y,
                                 self.max_radius, self.rotation_angle)

        if show_info:
            self._render_info_overlay(draw, frame_idx, pulse_scale)

        return img

    def _create_radial_gradient_background(self, aura_color):
        """Radial gradient background."""
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

    def _render_spiral(self, draw, amplitude_data, scale, brightness_boost,
                       frequencies, show_labels):
        """Render spiral with glow halos and white-hot cores."""
        amp_max = np.max(amplitude_data)
        if amp_max < 1e-8:
            amp_normalized = np.zeros_like(amplitude_data)
        else:
            amp_normalized = amplitude_data / amp_max

        theta = self.base_theta + np.radians(self.rotation_angle)
        wave = np.sin(self.base_theta * 3 + self.wave_phase) * 0.05
        r_animated = self.base_r * (1 + wave) * scale

        x_coords = self.center_x + r_animated * np.cos(theta)
        y_coords = self.center_y + r_animated * np.sin(theta)

        label_frequencies = [73, 110, 147, 220, 294, 440, 587, 880, 1175, 1760, 2349, 3136, 4186]
        labeled_indices = set()

        if frequencies is not None and show_labels:
            for label_freq in label_frequencies:
                idx = np.argmin(np.abs(frequencies - label_freq))
                if amp_normalized[idx] > 0.15:
                    labeled_indices.add(idx)

        # PASS 1: Glow halos
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

            glow_radius = int(size * 2.5)
            glow_alpha = amp * 0.25
            glow_color = tuple(int(min(255, c * brightness * glow_alpha)) for c in base_color)

            draw.ellipse(
                [x - glow_radius, y - glow_radius, x + glow_radius, y + glow_radius],
                fill=glow_color
            )

        # PASS 2: Core points
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

            draw.ellipse([x - size, y - size, x + size, y + size], fill=color)

            # White-hot core
            if amp > 0.6:
                white_blend = (amp - 0.6) / 0.4
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

            if i in labeled_indices and frequencies is not None:
                freq = frequencies[i]
                label = f"{int(freq)}Hz"
                draw.text((x + size + 5, y - 7), label, fill=color, font=self.font)


def main():
    audio_path = "/Users/guydvir/Project/07_Media/Papaoutai_Stromae.mp3"
    output_path = "/Users/guydvir/Project/04_Code/synesthesia2/synth32_line_trail.mp4"

    print("=" * 70)
    print("SYNESTHESIA 3.2 - Continuous Line Trail")
    print("=" * 70)
    print("Melody trail now rendered as continuous flowing line")
    print(f"Audio:  {audio_path}")
    print(f"Output: {output_path}")
    print()

    if not os.path.exists(audio_path):
        print(f"ERROR: Audio file not found: {audio_path}")
        sys.exit(1)

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

    render_config = TemporalRenderConfig(
        frame_width=1280,
        frame_height=720,
        base_point_size=5,
        pulse_scale_amount=0.18,
        pulse_brightness_amount=0.35,
        pulse_decay_rate=0.82,
        trail_duration_seconds=2.5,  # Shorter trail for cleaner look
        trail_decay_rate=0.90,
        trail_glow_radius=6,
        trail_color=(255, 200, 80),  # Warm orange-gold
        aura_brightness=0.22,
        aura_transition_speed=0.12,
        base_background_color=(8, 10, 22),
        enable_melody_trail=True,
        enable_rhythm_pulse=True,
        enable_harmonic_aura=True,
        enable_atmosphere=True,
    )

    generator.renderer = LineTrailRenderer(render_config, config.frame_rate)
    generator.render_config = render_config

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

    # Generate 20-second preview
    print("Generating 20-second preview...")
    generator.generate(
        audio_path=audio_path,
        output_path=output_path,
        start_time=30.0,
        duration=20.0,
    )

    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\nDone!")
    print(f"Output: {output_path}")
    print(f"Size:   {file_size_mb:.1f} MB")


if __name__ == "__main__":
    main()
