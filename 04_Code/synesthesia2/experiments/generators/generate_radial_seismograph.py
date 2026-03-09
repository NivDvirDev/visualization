#!/usr/bin/env python3
"""
SYNESTHESIA 3.5 - Radial Seismograph
====================================
The "paper" rolls from center outward:
- Center = current audio (newest)
- Edge = history (oldest)
- Creates cumulative radial traces like a seismograph

Each frame:
1. Expand existing canvas outward (scale up from center)
2. Draw new audio data at the center
3. Old data naturally pushes outward creating radial trails
"""

import numpy as np
import os
import sys
import math
from PIL import Image, ImageDraw
from collections import deque
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from video_generator_temporal import TemporalVideoGenerator, TemporalVideoConfig
from temporal_renderer import TemporalSpiralRenderer, TemporalRenderConfig


class RadialSeismographRenderer(TemporalSpiralRenderer):
    """
    Radial seismograph renderer where:
    - New audio appears at center
    - Over time, content expands outward
    - Creates cumulative radial traces
    """

    def __init__(self, config, frame_rate=30):
        super().__init__(config, frame_rate)
        
        # Accumulated canvas
        self.accumulated_canvas = None
        
        # Expansion rate per frame (how fast content moves outward)
        # 1.01 = 1% expansion per frame = content reaches edge in ~230 frames (~7.7 sec at 30fps)
        self.expansion_rate = 1.008
        
        # Fade rate for old content (prevents infinite buildup)
        self.fade_rate = 0.992
        
        # How much of the new frame to add to accumulator
        self.accumulation_strength = 0.7
        
        # Center region radius (where new content is drawn strongest)
        self.center_radius_ratio = 0.15  # 15% of max radius

    def _expand_canvas_outward(self, canvas):
        """
        Expand canvas content radially outward from center.
        Uses affine transformation to scale up from center point.
        """
        if canvas is None:
            return None
            
        canvas_arr = np.array(canvas, dtype=np.float32)
        h, w = canvas_arr.shape[:2]
        cx, cy = w // 2, h // 2
        
        # Create output array
        expanded = np.zeros_like(canvas_arr)
        
        # For each pixel, find where it came from (inverse mapping)
        y_coords, x_coords = np.mgrid[0:h, 0:w]
        
        # Convert to centered coordinates
        x_centered = x_coords - cx
        y_centered = y_coords - cy
        
        # Scale down coordinates to find source (inverse of expansion)
        scale = 1.0 / self.expansion_rate
        x_source = (x_centered * scale + cx).astype(np.float32)
        y_source = (y_centered * scale + cy).astype(np.float32)
        
        # Bilinear interpolation for each channel
        for c in range(3):
            expanded[:, :, c] = ndimage.map_coordinates(
                canvas_arr[:, :, c],
                [y_source, x_source],
                order=1,
                mode='constant',
                cval=0
            )
        
        # Apply fade
        expanded *= self.fade_rate
        
        return expanded

    def _create_center_mask(self, width, height):
        """Create a mask that's strongest at center, fading outward."""
        cx, cy = width // 2, height // 2
        max_radius = min(cx, cy)
        center_radius = max_radius * self.center_radius_ratio
        
        y_coords, x_coords = np.mgrid[0:height, 0:width]
        dist = np.sqrt((x_coords - cx) ** 2 + (y_coords - cy) ** 2)
        
        # Mask: 1.0 at center, fading to 0.2 at edge
        # Strong in center region, weaker outside
        mask = np.clip(1.0 - (dist / max_radius) * 0.8, 0.2, 1.0)
        
        # Extra boost for center region
        center_boost = np.clip(1.0 - dist / center_radius, 0, 1)
        mask = mask + center_boost * 0.5
        mask = np.clip(mask, 0, 1)
        
        return mask

    def render_frame(self, amplitude_data, frame_idx=0, frequencies=None,
                     show_labels=True, show_info=True):
        """Render frame with radial seismograph accumulation."""
        pulse_scale, pulse_brightness = self.rhythm_pulse.update()
        background_color = self.harmonic_aura.update()
        atmos_effects = self.atmosphere.get_effects()

        self.rotation_angle = frame_idx * 0.5 * atmos_effects['rotation_speed']
        self.wave_phase = frame_idx * 0.15

        w = self.config.frame_width
        h = self.config.frame_height

        # Create current frame (just the spiral, no background)
        current_frame = Image.new('RGB', (w, h), (0, 0, 0))
        draw = ImageDraw.Draw(current_frame)

        effective_scale = pulse_scale * atmos_effects['particle_scale']

        # Render spiral elements onto current frame
        self._render_spiral_elements(draw, amplitude_data, effective_scale, 
                                      pulse_brightness, frequencies)

        # === RADIAL SEISMOGRAPH ACCUMULATION ===
        
        # Initialize accumulated canvas if needed
        if self.accumulated_canvas is None:
            self.accumulated_canvas = np.zeros((h, w, 3), dtype=np.float32)
        
        # Step 1: Expand existing canvas outward
        self.accumulated_canvas = self._expand_canvas_outward(
            Image.fromarray(self.accumulated_canvas.astype(np.uint8), 'RGB')
        )
        
        # Step 2: Add current frame to accumulator (weighted by center mask)
        current_arr = np.array(current_frame, dtype=np.float32)
        center_mask = self._create_center_mask(w, h)
        
        # Apply mask to current frame contribution
        for c in range(3):
            self.accumulated_canvas[:, :, c] += (
                current_arr[:, :, c] * center_mask * self.accumulation_strength
            )
        
        # Clip to valid range
        self.accumulated_canvas = np.clip(self.accumulated_canvas, 0, 255)
        
        # Step 3: Create final frame with background + accumulated content
        final_frame = self._create_radial_gradient_background(background_color)
        
        # Blend accumulated canvas onto background
        final_arr = np.array(final_frame, dtype=np.float32)
        
        # Use screen blending for nice glow effect
        acc_normalized = self.accumulated_canvas / 255.0
        final_normalized = final_arr / 255.0
        
        # Screen blend: 1 - (1-a)(1-b)
        blended = 1.0 - (1.0 - final_normalized) * (1.0 - acc_normalized)
        blended = (blended * 255).astype(np.uint8)
        
        final_frame = Image.fromarray(blended, 'RGB')
        
        # Add info overlay
        if show_info:
            draw_final = ImageDraw.Draw(final_frame)
            self._render_info_overlay(draw_final, frame_idx, pulse_scale)

        return final_frame

    def _create_radial_gradient_background(self, aura_color):
        """Create radial gradient background."""
        w = self.config.frame_width
        h = self.config.frame_height

        base = self.config.base_background_color
        center_r = min(255, int(base[0] * 1.5 + aura_color[0] * 0.2))
        center_g = min(255, int(base[1] * 1.5 + aura_color[1] * 0.2))
        center_b = min(255, int(base[2] * 1.5 + aura_color[2] * 0.2))

        edge_r = max(0, base[0] // 3)
        edge_g = max(0, base[1] // 3)
        edge_b = max(0, base[2] // 3)

        cx, cy = w // 2, h // 2
        max_dist = math.sqrt(cx * cx + cy * cy)

        y_coords, x_coords = np.mgrid[0:h, 0:w]
        dist = np.sqrt((x_coords - cx) ** 2 + (y_coords - cy) ** 2) / max_dist
        dist = np.clip(dist, 0, 1) ** 0.6

        r_channel = (center_r * (1 - dist) + edge_r * dist).astype(np.uint8)
        g_channel = (center_g * (1 - dist) + edge_g * dist).astype(np.uint8)
        b_channel = (center_b * (1 - dist) + edge_b * dist).astype(np.uint8)

        img_array = np.stack([r_channel, g_channel, b_channel], axis=-1)
        return Image.fromarray(img_array, 'RGB')

    def _render_spiral_elements(self, draw, amplitude_data, scale, brightness_boost,
                                 frequencies):
        """Render spiral elements (shapes based on pitch)."""
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

        # Draw all points with pitch-driven shapes
        for i in range(self.num_points):
            amp = amp_normalized[i]
            
            # Skip very quiet
            if amp < 0.05:
                continue

            base_size = self.config.base_point_size
            outer_size = int(2 + amp * base_size * 3.5 * scale)
            outer_size = max(2, outer_size)

            x, y = float(x_coords[i]), float(y_coords[i])
            base_color = self.colors[i]
            brightness = 0.3 + amp * 0.7 + brightness_boost
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

            tangent_angle = theta[i] + math.pi / 2

            # Draw shape
            self._draw_star_shape(
                draw, x, y,
                outer_radius=outer_size,
                inner_radius=inner_size,
                num_points=num_points_shape,
                rotation_angle=tangent_angle,
                color=color
            )

            # White-hot core for peaks
            if amp > 0.6:
                white_blend = (amp - 0.6) / 0.4
                white_blend = min(1.0, white_blend)

                core_r = int(color[0] + (255 - color[0]) * white_blend)
                core_g = int(color[1] + (255 - color[1]) * white_blend)
                core_b = int(color[2] + (255 - color[2]) * white_blend)
                core_color = (core_r, core_g, core_b)

                core_size = max(2, int(outer_size * 0.4))
                self._draw_star_shape(
                    draw, x, y,
                    outer_radius=core_size,
                    inner_radius=core_size * 0.75,
                    num_points=num_points_shape,
                    rotation_angle=tangent_angle,
                    color=core_color
                )

    def _freq_to_num_points(self, freq):
        """Map frequency to number of polygon/star points."""
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
        """Draw a star/polygon shape."""
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
    output_path = "/Users/guydvir/Project/04_Code/synesthesia2/synth35_radial_seismo.mp4"

    print("=" * 70)
    print("SYNESTHESIA 3.5 - Radial Seismograph")
    print("=" * 70)
    print("Concept:")
    print("  • Center = current audio (newest)")
    print("  • Edge = history (oldest)")
    print("  • Content expands outward over time")
    print("  • Creates cumulative radial traces")
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
        enable_melody_trail=False,  # Disabled - we have radial trails now
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
        base_background_color=(5, 7, 18),  # Darker for better trails
        enable_melody_trail=False,
        enable_rhythm_pulse=True,
        enable_harmonic_aura=True,
        enable_atmosphere=True,
    )

    generator.renderer = RadialSeismographRenderer(render_config, config.frame_rate)
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
        start_time=25.0,  # Start a bit earlier to see buildup
        duration=25.0,
    )

    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\nDone!")
    print(f"Output: {output_path}")
    print(f"Size:   {file_size_mb:.1f} MB")


if __name__ == "__main__":
    main()
