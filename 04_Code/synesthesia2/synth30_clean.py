#!/usr/bin/env python3
"""
SYNESTHESIA 3.0 CLEAN - Exact Reference Recreation
===================================================
Faithful recreation of the reference video style:
- Fixed dots on cochlear spiral (NO movement outward)
- Dots PULSE/GLOW in place based on amplitude
- Background GLOWS with dominant energy (dark → olive-green)
- Clean, organized look
"""

import numpy as np
import os
import sys
import math
import colorsys
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from video_generator_temporal import TemporalVideoGenerator, TemporalVideoConfig
from temporal_renderer import TemporalSpiralRenderer, TemporalRenderConfig


class CleanSpiralRenderer(TemporalSpiralRenderer):
    """
    Clean spiral renderer matching the reference video exactly:
    - Fixed dot positions on cochlear spiral
    - Dots pulse/glow based on their frequency amplitude
    - Background color changes with overall energy
    - No trails, no expansion, just pulsing dots
    """

    def __init__(self, config, frame_rate=30):
        super().__init__(config, frame_rate)
        
        # Build color gradient (warm bass → cool treble)
        self._build_colors()
        
        # Store dominant energy for background
        self._dominant_energy = 0.0
        self._energy_smoothed = 0.0  # Smooth transitions

    def _build_colors(self):
        """Build perceptual color gradient for frequency bands."""
        self.colors = []
        for i in range(self.num_points):
            t = i / max(1, self.num_points - 1)
            # Warm (red/orange) for bass → Cool (blue/cyan) for treble
            if t < 0.2:
                # Deep red → Orange
                r = 180 + int(t * 5 * 40)
                g = 50 + int(t * 5 * 50)
                b = 50
            elif t < 0.4:
                # Orange → Yellow
                tt = (t - 0.2) / 0.2
                r = 220
                g = 100 + int(tt * 80)
                b = 40 + int(tt * 10)
            elif t < 0.6:
                # Yellow → Green
                tt = (t - 0.4) / 0.2
                r = 220 - int(tt * 140)
                g = 180 + int(tt * 20)
                b = 50 + int(tt * 30)
            elif t < 0.8:
                # Green → Cyan
                tt = (t - 0.6) / 0.2
                r = 80 - int(tt * 20)
                g = 200 - int(tt * 50)
                b = 80 + int(tt * 140)
            else:
                # Cyan → Blue/Violet
                tt = (t - 0.8) / 0.2
                r = 60 + int(tt * 80)
                g = 150 - int(tt * 60)
                b = 220
            
            self.colors.append((r, g, b))

    def render_frame(self, amplitude_data, frame_idx=0, frequencies=None,
                     show_labels=True, show_info=True):
        """Render clean spiral with pulsing dots and glowing background."""
        
        # Get rhythm pulse for additional effects
        pulse_scale, pulse_brightness = self.rhythm_pulse.update()
        background_color = self.harmonic_aura.update()
        
        # Calculate dominant energy (vocals + drums)
        beat = self.rhythm_pulse.current_pulse
        mid_bands = amplitude_data[2:5] if len(amplitude_data) > 5 else amplitude_data
        amp_max = np.max(amplitude_data) if np.max(amplitude_data) > 0 else 1.0
        vocal_energy = np.mean(mid_bands) / amp_max
        dominant_energy = min(1.0, vocal_energy * 2.5 + beat * 0.5)
        
        # Smooth energy transitions
        self._energy_smoothed = self._energy_smoothed * 0.7 + dominant_energy * 0.3
        self._dominant_energy = self._energy_smoothed
        
        w = self.config.frame_width
        h = self.config.frame_height
        
        # Create frame with energy-reactive background
        frame = self._create_energy_background(w, h)
        draw = ImageDraw.Draw(frame)
        
        # Normalize amplitude
        if np.max(amplitude_data) > 0:
            amp_normalized = amplitude_data / np.max(amplitude_data)
        else:
            amp_normalized = np.zeros_like(amplitude_data)
        
        # Draw fixed spiral dots that pulse with amplitude
        self._draw_pulsing_spiral(draw, amp_normalized, w, h)
        
        # Optional: draw frequency rings for reference
        self._draw_frequency_rings(draw, w, h)
        
        # Info overlay
        if show_info:
            self._draw_info(draw, frame_idx)
        
        return frame

    def _create_energy_background(self, w, h):
        """Create background that glows BRIGHTLY with energy level - matching reference."""
        energy = self._dominant_energy
        
        # Dark blue (silence) → BRIGHT olive green (high energy) - matching reference!
        base = np.array([8, 12, 20])
        glow = np.array([130, 145, 55])  # MUCH brighter - like reference video
        
        # Interpolate based on energy
        bg_color = base + (glow - base) * energy
        bg_color = bg_color.astype(int)
        
        # Create radial gradient with brighter center
        cx, cy = w // 2, h // 2
        max_dist = math.sqrt(cx * cx + cy * cy)
        
        y_coords, x_coords = np.mgrid[0:h, 0:w]
        dist = np.sqrt((x_coords - cx) ** 2 + (y_coords - cy) ** 2) / max_dist
        dist = np.clip(dist, 0, 1) ** 0.5  # Wider bright area
        
        # Brighter center, still visible edges
        center_mult = 1.3 + energy * 0.4
        edge_mult = 0.6 + energy * 0.2
        
        r_channel = np.clip(bg_color[0] * (center_mult * (1 - dist) + edge_mult * dist), 0, 255).astype(np.uint8)
        g_channel = np.clip(bg_color[1] * (center_mult * (1 - dist) + edge_mult * dist), 0, 255).astype(np.uint8)
        b_channel = np.clip(bg_color[2] * (center_mult * (1 - dist) + edge_mult * dist), 0, 255).astype(np.uint8)
        
        img_array = np.stack([r_channel, g_channel, b_channel], axis=-1)
        return Image.fromarray(img_array, 'RGB')

    def _draw_pulsing_spiral(self, draw, amp_normalized, w, h):
        """Draw single continuous Fermat spiral - exactly like reference."""
        cx, cy = w // 2, h // 2
        max_radius = min(cx, cy) * 0.85
        
        # Single continuous Fermat spiral
        num_dots = 350  # Many dots along the spiral
        num_turns = 2.5  # ~2.5 complete rotations
        
        for i in range(num_dots):
            # Position along spiral (0 = center, 1 = edge)
            t = (i + 1) / num_dots
            
            # Fermat spiral: r = sqrt(t), theta increases with t
            theta = t * num_turns * 2 * math.pi - math.pi / 2  # Start at top
            r = math.sqrt(t) * max_radius
            
            x = cx + r * math.cos(theta)
            y = cy + r * math.sin(theta)
            
            # Map to frequency bin
            freq_idx = int(i * len(amp_normalized) / num_dots)
            freq_idx = min(freq_idx, len(amp_normalized) - 1)
            amp = amp_normalized[freq_idx]
            
            # Color: rainbow following spiral position
            # Center (pink/magenta) → blue → cyan → green → yellow → orange → red (edge)
            hue = 0.85 - t * 0.85  # Start at pink (0.85), end at red (0.0)
            if hue < 0:
                hue += 1.0
            
            sat = 0.9
            val = 0.4 + amp * 0.6  # Brightness from amplitude
            
            rgb = colorsys.hsv_to_rgb(hue, sat, val)
            base_color = (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
            
            # Size: small when quiet, LARGE when active
            base_size = 3
            max_size = 12
            size = base_size + amp * max_size
            
            # Draw glow for active dots
            if amp > 0.2:
                glow_size = size * 2
                glow_color = (
                    min(255, base_color[0] + 50),
                    min(255, base_color[1] + 50),
                    min(255, base_color[2] + 50)
                )
                draw.ellipse([x - glow_size, y - glow_size,
                             x + glow_size, y + glow_size],
                            fill=glow_color)
            
            # Draw main dot
            draw.ellipse([x - size, y - size, x + size, y + size], fill=base_color)

    def _draw_frequency_rings(self, draw, w, h):
        """Draw subtle frequency reference rings."""
        cx, cy = w // 2, h // 2
        max_radius = min(cx, cy) * 0.85
        
        # Draw rings at octave boundaries
        for octave in range(1, 8):
            t = octave / 8.0
            r = math.sqrt(t) * max_radius
            ring_color = (25, 30, 45)
            draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                        outline=ring_color, width=1)

    def _draw_info(self, draw, frame_idx):
        """Draw info overlay."""
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
        except:
            font = ImageFont.load_default()
        
        info_text = "SYNESTHESIA 3.0"
        draw.text((20, 20), info_text, fill=(100, 110, 130), font=font)
        
        # Energy bar
        energy_width = int(self._dominant_energy * 100)
        draw.text((20, 45), "Energy", fill=(80, 90, 110), font=font)
        draw.rectangle([80, 45, 80 + energy_width, 55], 
                      fill=(80, 100, 50))


def main():
    audio_path = "/Users/guydvir/Project/07_Media/Papaoutai_Stromae.mp3"
    output_path = "/Users/guydvir/Project/04_Code/synesthesia2/synth30_clean_v3.mp4"

    print("=" * 70)
    print("SYNESTHESIA 3.0 CLEAN - Reference Recreation")
    print("=" * 70)
    print("Features:")
    print("  • Fixed dots on cochlear spiral (no movement)")
    print("  • Dots PULSE/GLOW in place with amplitude")
    print("  • Background GLOWS with dominant energy")
    print("  • Dark blue (silence) → Olive green (loud)")
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
        enable_atmosphere=False,
    )

    generator = TemporalVideoGenerator(config)

    render_config = TemporalRenderConfig(
        frame_width=1280,
        frame_height=720,
        base_point_size=4,
        pulse_scale_amount=0.15,
        pulse_brightness_amount=0.3,
        pulse_decay_rate=0.85,
        aura_brightness=0.18,
        aura_transition_speed=0.1,
        base_background_color=(5, 6, 15),
        enable_melody_trail=False,
        enable_rhythm_pulse=True,
        enable_harmonic_aura=True,
        enable_atmosphere=False,
    )

    generator.renderer = CleanSpiralRenderer(render_config, config.frame_rate)
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
