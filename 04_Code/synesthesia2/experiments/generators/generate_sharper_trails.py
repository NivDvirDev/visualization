#!/usr/bin/env python3
"""
SYNESTHESIA 3.2 - Sharper Radial Trails
========================================
Based on 3.0 Enhanced (circles, glow, white-hot cores) BUT with improved trails:
- Particles move OUTWARD radially after being created (same radial speed)
- Particles stay tight tangentially (less spread along the spiral curve)
- Creates a "shooting outward" effect from the center

Reverts pitch-shape experiment. This is what Malkam actually wanted.
"""

import numpy as np
import os
import sys
import math
from PIL import Image, ImageDraw, ImageFilter
from collections import deque
from dataclasses import dataclass
from typing import Tuple, Optional, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from video_generator_temporal import TemporalVideoGenerator, TemporalVideoConfig
from temporal_renderer import (
    TemporalSpiralRenderer, TemporalRenderConfig,
    MelodicTrail, RhythmPulse, HarmonicAura, AtmosphereField
)


class RadialMelodicTrail(MelodicTrail):
    """
    Enhanced melodic trail where particles move OUTWARD radially.
    
    Key changes from base MelodicTrail:
    - Each particle has a birth_radius and moves outward over time
    - Tangential position (theta) stays fixed (sharp, no spread)
    - Radial position increases at constant speed (moves outward)
    - Opacity decays as particles age
    """
    
    def __init__(self, config: TemporalRenderConfig, frame_rate: int = 30):
        super().__init__(config, frame_rate)
        
        # Trail particles: each is (theta, birth_radius, age, color_hue, confidence)
        self.particles: deque = deque(maxlen=self.trail_length)
        
        # Radial expansion speed (fraction of max_radius per frame)
        # Higher = faster outward movement
        self.radial_speed = 0.012  # ~1.2% of max radius per frame
        
        # How tight the particles stay (1.0 = perfectly tight, lower = more spread)
        self.tangential_tightness = 1.0
    
    def update(self, pitch_hz: float, confidence: float = 1.0):
        """Add a new particle at the current pitch position."""
        if pitch_hz <= 0 or confidence < 0.3:
            return
            
        # Calculate theta (angle on spiral) from pitch
        if pitch_hz <= self.freq_min:
            rel_freq = 0.05
        elif pitch_hz >= self.freq_max:
            rel_freq = 0.95
        else:
            rel_freq = (np.log(pitch_hz) - np.log(self.freq_min)) / \
                       (np.log(self.freq_max) - np.log(self.freq_min))
        
        theta = rel_freq * self.config.num_turns * 2 * np.pi
        birth_radius_fraction = np.sqrt(rel_freq) * 0.9  # Fraction of max_radius
        
        # Color hue based on frequency (for chromesthesia effect)
        octave_pos = rel_freq * 7
        color_hue = (octave_pos % 1)  # 0-1 for hue cycle
        
        self.particles.append({
            'theta': theta,
            'birth_radius': birth_radius_fraction,
            'age': 0,
            'hue': color_hue,
            'confidence': confidence
        })
    
    def render(self, draw: ImageDraw.Draw, center_x: int, center_y: int,
               max_radius: float, rotation: float):
        """Render particles moving outward radially."""
        if not self.config.enable_melody_trail or len(self.particles) == 0:
            return
        
        # Age all particles
        for p in self.particles:
            p['age'] += 1
        
        # Render particles (oldest first, so newest on top)
        for p in list(self.particles):
            age = p['age']
            
            # Calculate current radius (moves outward with age)
            current_radius_fraction = p['birth_radius'] + (age * self.radial_speed)
            
            # Skip if moved beyond visible area
            if current_radius_fraction > 1.1:
                continue
            
            current_radius = current_radius_fraction * max_radius
            
            # Theta stays fixed (no tangential spread) + rotation
            theta = p['theta'] + np.radians(rotation)
            
            # Calculate position
            x = center_x + current_radius * np.cos(theta)
            y = center_y + current_radius * np.sin(theta)
            
            # Alpha decays with age
            alpha = (self.config.trail_decay_rate ** age) * p['confidence']
            
            if alpha < 0.05:
                continue
            
            # Color from hue
            import colorsys
            rgb = colorsys.hsv_to_rgb(p['hue'], 0.8, 1.0)
            base_color = tuple(int(c * 255) for c in rgb)
            
            # Blend with trail_color for golden glow effect
            trail_color = self.config.trail_color
            blend = 0.4
            color = tuple(int(base_color[i] * (1-blend) + trail_color[i] * blend) 
                         for i in range(3))
            
            # Glow radius based on confidence and age (shrinks as it ages)
            size_factor = max(0.3, 1.0 - age * 0.015)
            glow_r = int(self.config.trail_glow_radius * size_factor * 
                        (0.5 + 0.5 * p['confidence']))
            
            # Draw glow layers
            for layer in range(3, 0, -1):
                layer_alpha = alpha * (0.3 / layer)
                layer_radius = glow_r * layer
                glow_color = tuple(int(c * layer_alpha) for c in color)
                draw.ellipse(
                    [x - layer_radius, y - layer_radius,
                     x + layer_radius, y + layer_radius],
                    fill=glow_color
                )
            
            # Draw bright core
            core_alpha = min(1.0, alpha * 1.5)
            core_color = tuple(int(min(255, c * core_alpha * 1.2)) for c in color)
            core_radius = max(2, int(glow_r * 0.4))
            draw.ellipse(
                [x - core_radius, y - core_radius,
                 x + core_radius, y + core_radius],
                fill=core_color
            )


class SharperTrailRenderer(TemporalSpiralRenderer):
    """
    Renderer with sharper radial trails.
    
    Base visualization: Same as 3.0 Enhanced (circles, glow, white-hot cores)
    Trails: Particles move outward radially, stay tight tangentially
    """
    
    def __init__(self, config: TemporalRenderConfig, frame_rate: int = 30):
        super().__init__(config, frame_rate)
        # Replace the melody trail with our radial version
        self.melody_trail = RadialMelodicTrail(config, frame_rate)
    
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

        # Render base spiral with glow (same as 3.0 Enhanced)
        self._render_spiral(draw, amplitude_data, effective_scale, pulse_brightness,
                            frequencies, show_labels)

        # Render radial melodic trail on top
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

    def _render_spiral(self, draw, amplitude_data, scale, brightness_boost,
                       frequencies, show_labels):
        """Same as 3.0 Enhanced - circles with glow halos and white-hot cores."""
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

        # === PASS 1: Outer glow halos ===
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

            draw.ellipse([x - size, y - size, x + size, y + size], fill=color)

            # White-hot core for peaks above 0.6 amplitude
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

            # Labels
            if i in labeled_indices and frequencies is not None:
                freq = frequencies[i]
                label = f"{int(freq)}Hz"
                draw.text((x + size + 5, y - 7), label, fill=color, font=self.font)


def main():
    audio_path = "/Users/guydvir/Project/07_Media/Papaoutai_Stromae.mp3"
    output_path = "/Users/guydvir/Project/04_Code/synesthesia2/synth32_sharper_trails.mp4"

    print("=" * 70)
    print("SYNESTHESIA 3.2 - Sharper Radial Trails")
    print("=" * 70)
    print("Changes from 3.1:")
    print("  • Reverted to circles (no pitch-driven shapes)")
    print("  • Trail particles move OUTWARD radially (constant speed)")
    print("  • Particles stay TIGHT tangentially (no spread along spiral)")
    print("  • Creates 'shooting star' effect from melody positions")
    print()
    print(f"Audio:  {audio_path}")
    print(f"Output: {output_path}")
    print()

    if not os.path.exists(audio_path):
        print(f"ERROR: Audio file not found: {audio_path}")
        sys.exit(1)

    # 720p preview
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
        trail_glow_radius=10,
        trail_color=(255, 240, 120),  # Golden
        trail_decay_rate=0.94,  # Slower decay = longer trails
        trail_duration_seconds=4.0,  # Longer trail history
        aura_brightness=0.22,
        aura_transition_speed=0.12,
        base_background_color=(8, 10, 22),
        enable_melody_trail=True,
        enable_rhythm_pulse=True,
        enable_harmonic_aura=True,
        enable_atmosphere=True,
    )

    generator.renderer = SharperTrailRenderer(render_config, config.frame_rate)
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

    # 30-second preview
    print("Generating 30-second preview...")
    generator.generate(
        audio_path=audio_path,
        output_path=output_path,
        start_time=30.0,
        duration=30.0,
    )

    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\nDone!")
    print(f"Output: {output_path}")
    print(f"Size:   {file_size_mb:.1f} MB")


if __name__ == "__main__":
    main()
