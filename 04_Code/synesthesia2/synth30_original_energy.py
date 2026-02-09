#!/usr/bin/env python3
"""
SYNESTHESIA 3.0 - Original Style with Energy Background
========================================================
Using the ORIGINAL temporal_renderer.py rendering style
but adding energy-reactive background like the reference video.
"""

import numpy as np
import os
import sys
import math
import colorsys
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from video_generator_temporal import TemporalVideoGenerator, TemporalVideoConfig
from temporal_renderer import TemporalSpiralRenderer, TemporalRenderConfig, CHROMESTHESIA_COLORS


class OriginalEnergyRenderer(TemporalSpiralRenderer):
    """
    Original 3.0 spiral style with energy-reactive background.
    This is the closest match to the reference video.
    """

    def __init__(self, config, frame_rate=30):
        super().__init__(config, frame_rate)
        self._dominant_energy = 0.0
        self._energy_smoothed = 0.0

    def render_frame(self, amplitude_data, frame_idx=0, frequencies=None,
                     show_labels=True, show_info=True):
        """Render frame with energy-reactive background."""
        
        # Get temporal effects
        pulse_scale, pulse_brightness = self.rhythm_pulse.update()
        atmos_effects = self.atmosphere.get_effects()
        
        # Calculate dominant energy
        beat = self.rhythm_pulse.current_pulse
        mid_bands = amplitude_data[len(amplitude_data)//4:len(amplitude_data)//2]
        amp_max = np.max(amplitude_data) if np.max(amplitude_data) > 0 else 1.0
        vocal_energy = np.mean(mid_bands) / amp_max
        dominant_energy = min(1.0, vocal_energy * 2.0 + beat * 0.5)
        
        # Smooth energy transitions
        self._energy_smoothed = self._energy_smoothed * 0.7 + dominant_energy * 0.3
        self._dominant_energy = self._energy_smoothed
        
        # Update animation state
        self.rotation_angle = frame_idx * 0.5 * atmos_effects['rotation_speed']
        self.wave_phase = frame_idx * 0.15
        
        w = self.config.frame_width
        h = self.config.frame_height
        
        # Create energy-reactive background
        bg_color = self._get_energy_background()
        img = Image.new('RGB', (w, h), bg_color)
        draw = ImageDraw.Draw(img)
        
        # Apply atmosphere effects to rendering
        effective_scale = pulse_scale * atmos_effects['particle_scale']
        
        # Render base spiral with ENHANCED pulsing (override)
        self._render_dramatic_spiral(draw, amplitude_data, effective_scale, pulse_brightness,
                                     frequencies, show_labels)
        
        # Add info overlay
        if show_info:
            self._render_info_overlay(draw, frame_idx, pulse_scale)
        
        return img

    def _render_dramatic_spiral(self, draw, amplitude_data, scale, brightness_boost,
                                 frequencies, show_labels):
        """Render spiral with MORE DRAMATIC pulsing - 6x size multiplier for high amp."""
        from temporal_renderer import CHROMESTHESIA_COLORS
        
        # Normalize amplitude
        amp_normalized = amplitude_data / (np.max(amplitude_data) + 1e-8)
        
        # Apply rotation
        theta = self.base_theta + np.radians(self.rotation_angle)
        
        # Apply wave animation
        wave = np.sin(self.base_theta * 3 + self.wave_phase) * 0.05
        r_animated = self.base_r * (1 + wave) * scale
        
        # Calculate positions
        x_coords = self.center_x + r_animated * np.cos(theta)
        y_coords = self.center_y + r_animated * np.sin(theta)
        
        # Render points with DRAMATIC sizing
        for i in range(self.num_points):
            amp = amp_normalized[i]
            
            # DRAMATIC SIZE: 6x multiplier instead of 3x
            base_size = self.config.base_point_size
            size = int(base_size + amp * base_size * 6 * scale)
            
            if size < 1:
                continue
            
            x, y = int(x_coords[i]), int(y_coords[i])
            
            # Color with brightness modulation
            base_color = self.colors[i]
            brightness = 0.3 + amp * 0.7 + brightness_boost
            color = tuple(int(min(255, c * brightness)) for c in base_color)
            
            # EXTRA GLOW for high amplitude dots
            if amp > 0.3:
                glow_size = int(size * 1.8)
                glow_brightness = 0.5 + amp * 0.3
                glow_color = tuple(int(min(255, c * glow_brightness)) for c in base_color)
                draw.ellipse([x - glow_size, y - glow_size, x + glow_size, y + glow_size], 
                            fill=glow_color)
            
            # Draw main point
            draw.ellipse([x - size, y - size, x + size, y + size], fill=color)

    def _get_energy_background(self):
        """Get background color based on energy - matching reference video."""
        energy = self._dominant_energy
        
        # Dark blue-gray (silence) → Bright olive-green (high energy)
        base_r = 15 + int(energy * 115)   # 15 → 130
        base_g = 20 + int(energy * 125)   # 20 → 145
        base_b = 30 - int(energy * 15)    # 30 → 15
        
        return (base_r, base_g, base_b)

    def _render_spiral(self, draw, amplitude_data, scale, brightness_boost,
                       frequencies, show_labels):
        """
        Override: Render spiral with MORE DRAMATIC pulsing.
        - Increased size multiplier (3 → 6)
        - Extra glow effect for high amplitude dots
        - Original chromesthesia colors preserved
        """
        # Normalize amplitude
        amp_normalized = amplitude_data / (np.max(amplitude_data) + 1e-8)

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

        # Render points with DRAMATIC pulsing
        for i in range(self.num_points):
            amp = amp_normalized[i]

            # Size based on amplitude - INCREASED MULTIPLIER (3 → 6)
            base_size = self.config.base_point_size
            size = int(base_size + amp * base_size * 6 * scale)

            if size < 1:
                continue

            x, y = int(x_coords[i]), int(y_coords[i])

            # Color with brightness modulation (using CHROMESTHESIA_COLORS)
            base_color = self.colors[i]
            brightness = 0.3 + amp * 0.7 + brightness_boost
            color = tuple(int(min(255, c * brightness)) for c in base_color)

            # EXTRA GLOW EFFECT for high amplitude dots (amp > 0.5)
            if amp > 0.5:
                glow_intensity = (amp - 0.5) * 2  # 0 to 1 for amp 0.5 to 1.0
                
                # Outer glow layer (larger, more transparent)
                glow_size_outer = int(size * 2.5)
                glow_alpha_outer = 0.15 * glow_intensity
                glow_color_outer = tuple(int(min(255, c * glow_alpha_outer)) for c in base_color)
                draw.ellipse([x - glow_size_outer, y - glow_size_outer, 
                              x + glow_size_outer, y + glow_size_outer], 
                             fill=glow_color_outer)
                
                # Middle glow layer
                glow_size_mid = int(size * 1.8)
                glow_alpha_mid = 0.3 * glow_intensity
                glow_color_mid = tuple(int(min(255, c * glow_alpha_mid)) for c in base_color)
                draw.ellipse([x - glow_size_mid, y - glow_size_mid, 
                              x + glow_size_mid, y + glow_size_mid], 
                             fill=glow_color_mid)
                
                # Inner glow layer (brightest)
                glow_size_inner = int(size * 1.3)
                glow_alpha_inner = 0.5 * glow_intensity
                glow_color_inner = tuple(int(min(255, c * (brightness + glow_alpha_inner))) for c in base_color)
                draw.ellipse([x - glow_size_inner, y - glow_size_inner, 
                              x + glow_size_inner, y + glow_size_inner], 
                             fill=glow_color_inner)

            # Draw main point
            draw.ellipse([x - size, y - size, x + size, y + size], fill=color)

            # Draw label if applicable
            if i in labeled_indices and frequencies is not None:
                freq = frequencies[i]
                label = f"{int(freq)}Hz"
                draw.text((x + size + 5, y - 7), label, fill=color, font=self.font)


def main():
    audio_path = "/Users/guydvir/Project/07_Media/Papaoutai_Stromae.mp3"
    output_path = "/Users/guydvir/Project/04_Code/synesthesia2/synth30_dramatic_v1.mp4"

    print("=" * 70)
    print("SYNESTHESIA 3.0 - Original + Energy Background")
    print("=" * 70)
    print("Using ORIGINAL temporal_renderer style")
    print("Adding energy-reactive background like reference")
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
        enable_harmonic_aura=False,  # We handle background ourselves
        enable_atmosphere=True,
    )

    generator = TemporalVideoGenerator(config)

    render_config = TemporalRenderConfig(
        frame_width=1280,
        frame_height=720,
        base_point_size=4,
        num_frequency_bins=381,
        num_turns=7.0,
        pulse_scale_amount=0.15,
        pulse_brightness_amount=0.3,
        pulse_decay_rate=0.85,
        enable_melody_trail=False,
        enable_rhythm_pulse=True,
        enable_harmonic_aura=False,
        enable_atmosphere=True,
    )

    generator.renderer = OriginalEnergyRenderer(render_config, config.frame_rate)
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
        subprocess.run(cmd, capture_output=True, text=True)

    generator._encode_video = encode_with_homebrew_ffmpeg

    print("Generating 30-second preview...")
    generator.generate(
        audio_path=audio_path,
        output_path=output_path,
        start_time=30.0,
        duration=30.0,
    )

    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\nDone! Output: {output_path} ({file_size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
