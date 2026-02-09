#!/usr/bin/env python3
"""
SYNESTHESIA 3.3 - Combined: Pitch Shapes + Line Trail
======================================================
Combines:
- Pitch-driven shapes from 3.1 (triangles/stars based on frequency)
- Continuous line trail from 3.2 (instead of glowing circles)
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
    """Melody trail as continuous line instead of circles."""

    def render(self, draw: ImageDraw.Draw, center_x: int, center_y: int,
               max_radius: float, rotation: float):
        if not self.config.enable_melody_trail or len(self.pitch_history) < 2:
            return

        points = []
        for i, (pitch, confidence) in enumerate(self.pitch_history):
            if pitch <= 0 or confidence < 0.2:
                continue

            x, y = self._pitch_to_coords(pitch, center_x, center_y, max_radius, rotation)
            age = len(self.pitch_history) - i - 1
            alpha = (self.config.trail_decay_rate ** age) * confidence
            
            if alpha < 0.03:
                continue
                
            points.append((x, y, alpha, confidence))

        if len(points) < 2:
            return

        for i in range(len(points) - 1):
            x1, y1, alpha1, conf1 = points[i]
            x2, y2, alpha2, conf2 = points[i + 1]
            
            avg_alpha = (alpha1 + alpha2) / 2
            avg_conf = (conf1 + conf2) / 2
            width = max(1, int(2 + avg_conf * 6))
            
            base_color = self.config.trail_color
            color = tuple(int(c * avg_alpha) for c in base_color)
            draw.line([(x1, y1), (x2, y2)], fill=color, width=width)
        
        if points:
            hx, hy, halpha, hconf = points[-1]
            head_color = tuple(int(c * min(1.0, halpha * 1.5)) for c in self.config.trail_color)
            head_radius = max(3, int(4 + hconf * 4))
            draw.ellipse(
                [hx - head_radius, hy - head_radius, hx + head_radius, hy + head_radius],
                fill=head_color
            )


class CombinedRenderer(TemporalSpiralRenderer):
    """
    Combined renderer with:
    - Pitch-driven shapes (from 3.1)
    - Continuous line trail (from 3.2)
    """

    def __init__(self, config, frame_rate=30):
        super().__init__(config, frame_rate)
        # Replace melody trail with line version
        self.melody_trail = ContinuousLineTrail(config, frame_rate)
        # Frequency mapping for shapes
        self.min_freq = 20
        self.max_freq = 8000

    def _freq_to_num_points(self, freq):
        """Map frequency to number of polygon/star points."""
        if freq < self.min_freq:
            freq = self.min_freq
        if freq > self.max_freq:
            freq = self.max_freq

        log_min = np.log10(self.min_freq)
        log_max = np.log10(self.max_freq)
        log_freq = np.log10(freq)
        t = (log_freq - log_min) / (log_max - log_min)
        num_points = int(3 + t * 9)
        return max(3, min(12, num_points))

    def _draw_star_shape(self, draw, cx, cy, outer_radius, inner_radius, 
                         num_points, rotation_angle, color):
        """Draw a star/polygon shape."""
        points = []
        for i in range(num_points * 2):
            angle = rotation_angle + (i * math.pi / num_points)
            if i % 2 == 0:
                r = outer_radius
            else:
                r = inner_radius
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append((x, y))

        if len(points) >= 3:
            draw.polygon(points, fill=color)

    def _get_spiral_tangent_angle(self, theta, r):
        """Get tangent angle for shape orientation."""
        return theta + math.pi / 2

    def render_frame(self, amplitude_data, frame_idx=0, frequencies=None,
                     show_labels=True, show_info=True):
        pulse_scale, pulse_brightness = self.rhythm_pulse.update()
        background_color = self.harmonic_aura.update()
        atmos_effects = self.atmosphere.get_effects()

        self.rotation_angle = frame_idx * 0.5 * atmos_effects['rotation_speed']
        self.wave_phase = frame_idx * 0.15

        img = self._create_radial_gradient_background(background_color)
        draw = ImageDraw.Draw(img)

        effective_scale = pulse_scale * atmos_effects['particle_scale']

        # Render spiral with PITCH-DRIVEN SHAPES
        self._render_pitch_spiral(draw, amplitude_data, effective_scale, pulse_brightness,
                                   frequencies, show_labels)

        # Render LINE TRAIL on top
        self.melody_trail.render(draw, self.center_x, self.center_y,
                                 self.max_radius, self.rotation_angle)

        if show_info:
            self._render_info_overlay(draw, frame_idx, pulse_scale)

        return img

    def _create_radial_gradient_background(self, aura_color):
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

    def _render_pitch_spiral(self, draw, amplitude_data, scale, brightness_boost,
                              frequencies, show_labels):
        """Render spiral with pitch-driven shapes (from 3.1)."""
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

        # PASS 1: Glow halos (only for louder sounds)
        for i in range(self.num_points):
            amp = amp_normalized[i]
            if amp < 0.25:
                continue

            base_size = self.config.base_point_size
            size = int(base_size + amp * base_size * 3 * scale)

            x, y = int(x_coords[i]), int(y_coords[i])
            base_color = self.colors[i]
            brightness = 0.3 + amp * 0.5 + brightness_boost

            glow_radius = int(size * 2.0)
            glow_alpha = amp * 0.15
            glow_color = tuple(int(min(255, c * brightness * glow_alpha)) for c in base_color)

            draw.ellipse(
                [x - glow_radius, y - glow_radius, x + glow_radius, y + glow_radius],
                fill=glow_color
            )

        # PASS 2: Pitch-driven shapes (ALL points)
        for i in range(self.num_points):
            amp = amp_normalized[i]

            base_size = self.config.base_point_size
            min_size = 2
            outer_size = int(min_size + amp * base_size * 3.5 * scale)
            outer_size = max(min_size, outer_size)

            x, y = float(x_coords[i]), float(y_coords[i])
            base_color = self.colors[i]
            brightness = 0.25 + amp * 0.75 + brightness_boost
            color = tuple(int(min(255, c * brightness)) for c in base_color)

            # Get frequency for shape
            if frequencies is not None and i < len(frequencies):
                freq = frequencies[i]
            else:
                freq = 20 * (2 ** (i / self.num_points * 8))

            num_points_shape = self._freq_to_num_points(freq)

            # Spikiness from amplitude
            if amp < 0.15:
                inner_size = outer_size * 0.85
            else:
                spikiness = 0.2 + amp * 0.5
                inner_size = outer_size * (1 - spikiness * 0.5)

            tangent_angle = self._get_spiral_tangent_angle(theta[i], r_animated[i])

            # Draw pitch-driven shape
            self._draw_star_shape(
                draw, x, y,
                outer_radius=outer_size,
                inner_radius=inner_size,
                num_points=num_points_shape,
                rotation_angle=tangent_angle,
                color=color
            )

            # White-hot core for peaks
            if amp > 0.5:
                white_blend = (amp - 0.5) / 0.5
                white_blend = min(1.0, white_blend)

                core_r = int(color[0] + (255 - color[0]) * white_blend)
                core_g = int(color[1] + (255 - color[1]) * white_blend)
                core_b = int(color[2] + (255 - color[2]) * white_blend)
                core_color = (core_r, core_g, core_b)

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

            if i in labeled_indices and frequencies is not None:
                freq_val = frequencies[i]
                label = f"{int(freq_val)}Hz"
                draw.text((int(x) + outer_size + 5, int(y) - 7), label, fill=color, font=self.font)


def main():
    audio_path = "/Users/guydvir/Project/07_Media/Papaoutai_Stromae.mp3"
    output_path = "/Users/guydvir/Project/04_Code/synesthesia2/synth33_combined.mp4"

    print("=" * 70)
    print("SYNESTHESIA 3.3 - Combined: Pitch Shapes + Line Trail")
    print("=" * 70)
    print("Features:")
    print("  ✓ Pitch-driven shapes (triangles→stars based on frequency)")
    print("  ✓ Continuous line melody trail (no more circle glows)")
    print()
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
        trail_duration_seconds=2.5,
        trail_decay_rate=0.90,
        trail_glow_radius=6,
        trail_color=(255, 200, 80),
        aura_brightness=0.22,
        aura_transition_speed=0.12,
        base_background_color=(8, 10, 22),
        enable_melody_trail=True,
        enable_rhythm_pulse=True,
        enable_harmonic_aura=True,
        enable_atmosphere=True,
    )

    generator.renderer = CombinedRenderer(render_config, config.frame_rate)
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
