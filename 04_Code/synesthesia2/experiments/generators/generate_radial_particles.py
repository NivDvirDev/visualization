#!/usr/bin/env python3
"""
SYNESTHESIA 3.6 - Radial Particle Trails
=========================================
New approach: Don't blur/expand full frames.
Instead, track individual particles that move outward.

- Needle: Rendered exactly like 3.3 (sharp, beautiful, unchanged)
- Trails: Separate thin particles/lines that drift outward from center
- Clear separation: needle = colorful shapes, trails = subtle thin lines

This preserves the original spiral quality while adding radial memory.
"""

import numpy as np
import os
import sys
import math
from PIL import Image, ImageDraw
from collections import deque
from dataclasses import dataclass
from typing import List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from video_generator_temporal import TemporalVideoGenerator, TemporalVideoConfig
from temporal_renderer import TemporalSpiralRenderer, TemporalRenderConfig


@dataclass
class TrailParticle:
    """A single particle in the radial trail."""
    angle: float        # Radial angle (fixed)
    radius: float       # Current radius from center (increases over time)
    birth_radius: float # Where it was born
    amplitude: float    # Amplitude when born (affects brightness)
    color: Tuple[int, int, int]  # Base color
    age: int           # Frames since birth


class RadialParticleRenderer(TemporalSpiralRenderer):
    """
    Renderer with separate particle system for radial trails.
    Needle is rendered normally; trails are thin particles moving outward.
    """

    def __init__(self, config, frame_rate=30):
        super().__init__(config, frame_rate)
        
        # Particle system for trails
        self.particles: List[TrailParticle] = []
        
        # Trail settings
        self.particle_spawn_threshold = 0.2  # Min amplitude to spawn particle
        self.particle_spawn_rate = 0.3       # Probability of spawning per bin per frame
        self.particle_max_age = 180          # Frames before particle dies (~6 sec at 30fps)
        self.particle_speed = 2.5            # Pixels per frame outward
        self.particle_fade_start = 0.5       # Start fading at this % of max age
        
        # Visual settings for trails
        self.trail_color_shift = 0.4         # How much to shift toward blue (0-1)
        self.trail_opacity = 0.5             # Base opacity for trails
        self.trail_line_length = 8           # Length of trail line segments

    def _spawn_particles(self, amplitude_data, frequencies):
        """Spawn new trail particles based on current audio."""
        amp_max = np.max(amplitude_data)
        if amp_max < 1e-8:
            return
            
        amp_normalized = amplitude_data / amp_max
        
        theta = self.base_theta + np.radians(self.rotation_angle)
        
        for i in range(self.num_points):
            amp = amp_normalized[i]
            
            # Only spawn for significant amplitudes
            if amp < self.particle_spawn_threshold:
                continue
            
            # Probabilistic spawning (more likely for louder sounds)
            if np.random.random() > self.particle_spawn_rate * amp:
                continue
            
            # Create particle
            angle = theta[i]
            birth_radius = self.base_r[i]  # Born at spiral position
            base_color = self.colors[i]
            
            particle = TrailParticle(
                angle=angle,
                radius=birth_radius,
                birth_radius=birth_radius,
                amplitude=amp,
                color=base_color,
                age=0
            )
            self.particles.append(particle)

    def _update_particles(self):
        """Update all particles (move outward, age, remove dead)."""
        alive_particles = []
        
        for p in self.particles:
            p.age += 1
            p.radius += self.particle_speed
            
            # Keep if not too old and not too far from center
            max_radius = min(self.config.frame_width, self.config.frame_height) * 0.55
            if p.age < self.particle_max_age and p.radius < max_radius:
                alive_particles.append(p)
        
        self.particles = alive_particles

    def _render_trails(self, draw):
        """Render all trail particles as thin fading lines."""
        cx, cy = self.center_x, self.center_y
        
        for p in self.particles:
            # Calculate opacity based on age
            age_ratio = p.age / self.particle_max_age
            
            if age_ratio > self.particle_fade_start:
                # Fade out in second half of life
                fade = 1.0 - (age_ratio - self.particle_fade_start) / (1.0 - self.particle_fade_start)
            else:
                fade = 1.0
            
            # Also fade based on distance from birth
            distance_traveled = p.radius - p.birth_radius
            distance_fade = max(0, 1.0 - distance_traveled / 200)
            
            opacity = self.trail_opacity * fade * distance_fade * p.amplitude
            
            if opacity < 0.05:
                continue
            
            # Shift color toward blue/gray for trails
            r = int(p.color[0] * (1 - self.trail_color_shift) + 100 * self.trail_color_shift)
            g = int(p.color[1] * (1 - self.trail_color_shift) + 120 * self.trail_color_shift)
            b = int(p.color[2] * (1 - self.trail_color_shift) + 180 * self.trail_color_shift)
            
            # Apply opacity
            r = int(r * opacity)
            g = int(g * opacity)
            b = int(b * opacity)
            color = (r, g, b)
            
            # Calculate position
            x = cx + p.radius * math.cos(p.angle)
            y = cy + p.radius * math.sin(p.angle)
            
            # Draw as a short radial line segment
            inner_x = cx + (p.radius - self.trail_line_length) * math.cos(p.angle)
            inner_y = cy + (p.radius - self.trail_line_length) * math.sin(p.angle)
            
            # Line width based on amplitude (louder = thicker)
            width = max(1, int(1 + p.amplitude * 2))
            
            draw.line([(inner_x, inner_y), (x, y)], fill=color, width=width)

    def render_frame(self, amplitude_data, frame_idx=0, frequencies=None,
                     show_labels=True, show_info=True):
        """Render frame with separate needle and particle trails."""
        pulse_scale, pulse_brightness = self.rhythm_pulse.update()
        background_color = self.harmonic_aura.update()
        atmos_effects = self.atmosphere.get_effects()

        self.rotation_angle = frame_idx * 0.5 * atmos_effects['rotation_speed']
        self.wave_phase = frame_idx * 0.15

        # === PARTICLE SYSTEM UPDATE ===
        self._spawn_particles(amplitude_data, frequencies)
        self._update_particles()

        # === RENDER ===
        # Start with background
        img = self._create_radial_gradient_background(background_color)
        draw = ImageDraw.Draw(img)

        effective_scale = pulse_scale * atmos_effects['particle_scale']

        # Layer 1: Render trail particles FIRST (behind needle)
        self._render_trails(draw)

        # Layer 2: Render needle (spiral) ON TOP - exactly like 3.3
        self._render_spiral_needle(draw, amplitude_data, effective_scale, 
                                    pulse_brightness, frequencies, show_labels)

        # Info overlay
        if show_info:
            self._render_info_overlay(draw, frame_idx, pulse_scale)

        return img

    def _create_radial_gradient_background(self, aura_color):
        """Create radial gradient background."""
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

    def _render_spiral_needle(self, draw, amplitude_data, scale, brightness_boost,
                               frequencies, show_labels):
        """Render the main spiral needle - exactly like version 3.3."""
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

        # PASS 1: Glow halos for louder sounds
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

            if frequencies is not None and i < len(frequencies):
                freq = frequencies[i]
            else:
                freq = 20 * (2 ** (i / self.num_points * 8))

            num_points_shape = self._freq_to_num_points(freq)

            if amp < 0.15:
                inner_size = outer_size * 0.85
            else:
                spikiness = 0.2 + amp * 0.5
                inner_size = outer_size * (1 - spikiness * 0.5)

            tangent_angle = theta[i] + math.pi / 2

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

    def _freq_to_num_points(self, freq):
        min_freq, max_freq = 20, 8000
        if freq < min_freq:
            freq = min_freq
        if freq > max_freq:
            freq = max_freq

        log_min = np.log10(min_freq)
        log_max = np.log10(max_freq)
        log_freq = np.log10(freq)
        t = (log_freq - log_min) / (log_max - log_min)
        num_points = int(3 + t * 9)
        return max(3, min(12, num_points))

    def _draw_star_shape(self, draw, cx, cy, outer_radius, inner_radius, 
                         num_points, rotation_angle, color):
        points = []
        for i in range(num_points * 2):
            angle = rotation_angle + (i * math.pi / num_points)
            r = outer_radius if i % 2 == 0 else inner_radius
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append((x, y))

        if len(points) >= 3:
            draw.polygon(points, fill=color)


def main():
    audio_path = "/Users/guydvir/Project/07_Media/Papaoutai_Stromae.mp3"
    output_path = "/Users/guydvir/Project/04_Code/synesthesia2/synth36_particles.mp4"

    print("=" * 70)
    print("SYNESTHESIA 3.6 - Radial Particle Trails")
    print("=" * 70)
    print("New approach:")
    print("  • Needle: Exactly like 3.3 (sharp, beautiful)")
    print("  • Trails: Separate thin particles drifting outward")
    print("  • Clear separation: shapes vs thin lines")
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
        enable_melody_trail=False,
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
        enable_melody_trail=False,
        enable_rhythm_pulse=True,
        enable_harmonic_aura=True,
        enable_atmosphere=True,
    )

    generator.renderer = RadialParticleRenderer(render_config, config.frame_rate)
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

    print("Generating 25-second preview...")
    generator.generate(
        audio_path=audio_path,
        output_path=output_path,
        start_time=25.0,
        duration=25.0,
    )

    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\nDone!")
    print(f"Output: {output_path}")
    print(f"Size:   {file_size_mb:.1f} MB")


if __name__ == "__main__":
    main()
