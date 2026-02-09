#!/usr/bin/env python3
"""
SYNESTHESIA 3.7 - Hybrid Trails (Blueprint Effect)
===================================================
Middle ground between 3.5 and 3.6:

- Needle: Exactly like 3.3 (on top, sharp, beautiful)
- Trail: Accumulating canvas expansion BUT:
  - NO blur (stays sharp)
  - Very low opacity (subtle ghosting)
  - Desaturated (grayish blueprint feel)
  - Rendered BEHIND the needle

This creates the cumulative "blueprint" effect without destroying the needle.
"""

import numpy as np
import os
import sys
import math
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from video_generator_temporal import TemporalVideoGenerator, TemporalVideoConfig
from temporal_renderer import TemporalSpiralRenderer, TemporalRenderConfig


class HybridTrailRenderer(TemporalSpiralRenderer):
    """
    Hybrid approach: sharp accumulating trails + pristine needle on top.
    """

    def __init__(self, config, frame_rate=30):
        super().__init__(config, frame_rate)
        
        # Accumulated trail canvas
        self.trail_canvas = None
        
        # === HYBRID PARAMETERS ===
        # Expansion (how fast trails move outward)
        self.expansion_rate = 1.005  # Slower expansion
        
        # Fade rate (how fast old trails disappear)
        self.fade_rate = 0.988
        
        # How much of current frame adds to trails (VERY subtle)
        self.accumulation_strength = 0.12  # Much lower than before
        
        # Trail visual treatment
        self.trail_opacity = 0.4           # Overall trail layer opacity
        self.trail_desaturation = 0.7      # Strong desaturation for blueprint feel
        
        # NO BLUR - keep trails sharp

    def _expand_canvas_outward(self, canvas_arr):
        """Expand canvas radially outward from center."""
        if canvas_arr is None:
            return None
            
        h, w = canvas_arr.shape[:2]
        cx, cy = w // 2, h // 2
        
        expanded = np.zeros_like(canvas_arr)
        
        y_coords, x_coords = np.mgrid[0:h, 0:w]
        x_centered = x_coords - cx
        y_centered = y_coords - cy
        
        scale = 1.0 / self.expansion_rate
        x_source = (x_centered * scale + cx).astype(np.float32)
        y_source = (y_centered * scale + cy).astype(np.float32)
        
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

    def _desaturate_array(self, arr, amount):
        """Desaturate RGB array."""
        luminance = 0.299 * arr[:,:,0] + 0.587 * arr[:,:,1] + 0.114 * arr[:,:,2]
        luminance = luminance[:,:,np.newaxis]
        desaturated = arr * (1 - amount) + luminance * amount
        return desaturated

    def _create_center_mask(self, width, height):
        """Mask strongest at center, fading outward."""
        cx, cy = width // 2, height // 2
        max_radius = min(cx, cy)
        
        y_coords, x_coords = np.mgrid[0:height, 0:width]
        dist = np.sqrt((x_coords - cx) ** 2 + (y_coords - cy) ** 2)
        
        # Smooth falloff from center
        mask = np.clip(1.0 - (dist / (max_radius * 0.6)), 0, 1)
        mask = mask ** 1.5  # Gentle falloff
        
        return mask

    def render_frame(self, amplitude_data, frame_idx=0, frequencies=None,
                     show_labels=True, show_info=True):
        """Render with hybrid trail approach."""
        pulse_scale, pulse_brightness = self.rhythm_pulse.update()
        background_color = self.harmonic_aura.update()
        atmos_effects = self.atmosphere.get_effects()

        self.rotation_angle = frame_idx * 0.5 * atmos_effects['rotation_speed']
        self.wave_phase = frame_idx * 0.15

        w = self.config.frame_width
        h = self.config.frame_height
        effective_scale = pulse_scale * atmos_effects['particle_scale']

        # === STEP 1: Render current needle frame (black background) ===
        needle_frame = Image.new('RGB', (w, h), (0, 0, 0))
        needle_draw = ImageDraw.Draw(needle_frame)
        self._render_spiral_needle(needle_draw, amplitude_data, effective_scale, 
                                    pulse_brightness, frequencies, show_labels)

        # === STEP 2: Update trail canvas ===
        if self.trail_canvas is None:
            self.trail_canvas = np.zeros((h, w, 3), dtype=np.float32)
        
        # Expand existing trails outward
        self.trail_canvas = self._expand_canvas_outward(self.trail_canvas)
        
        # Add current needle to trails (subtle, center-weighted)
        needle_arr = np.array(needle_frame, dtype=np.float32)
        center_mask = self._create_center_mask(w, h)
        
        for c in range(3):
            self.trail_canvas[:, :, c] += (
                needle_arr[:, :, c] * center_mask * self.accumulation_strength
            )
        
        self.trail_canvas = np.clip(self.trail_canvas, 0, 255)

        # === STEP 3: Process trail for display (desaturate, NO blur) ===
        trail_display = self._desaturate_array(self.trail_canvas.copy(), self.trail_desaturation)
        trail_display *= self.trail_opacity
        trail_display = np.clip(trail_display, 0, 255)

        # === STEP 4: Composite final frame ===
        # Background
        final_frame = self._create_radial_gradient_background(background_color)
        final_arr = np.array(final_frame, dtype=np.float32)
        
        # Add trail layer (screen blend)
        trail_normalized = trail_display / 255.0
        final_normalized = final_arr / 255.0
        with_trail = 1.0 - (1.0 - final_normalized) * (1.0 - trail_normalized)
        
        # Add needle ON TOP (additive)
        needle_normalized = needle_arr / 255.0
        final_composite = with_trail + needle_normalized * 1.1  # Slight boost
        final_composite = np.clip(final_composite * 255, 0, 255).astype(np.uint8)
        
        final_frame = Image.fromarray(final_composite, 'RGB')
        
        if show_info:
            draw_final = ImageDraw.Draw(final_frame)
            self._render_info_overlay(draw_final, frame_idx, pulse_scale)

        return final_frame

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

    def _render_spiral_needle(self, draw, amplitude_data, scale, brightness_boost,
                               frequencies, show_labels):
        """Render the main spiral - exactly like 3.3."""
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

        # PASS 2: Pitch-driven shapes
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

            # White-hot core
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
    output_path = "/Users/guydvir/Project/04_Code/synesthesia2/synth37_hybrid.mp4"

    print("=" * 70)
    print("SYNESTHESIA 3.7 - Hybrid Trails (Blueprint Effect)")
    print("=" * 70)
    print("Hybrid approach:")
    print("  • Needle: Exactly like 3.3 (pristine, on top)")
    print("  • Trails: Sharp accumulation (no blur!)")
    print("  • Very subtle opacity (0.12 accumulation, 0.4 display)")
    print("  • Desaturated for blueprint feel")
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

    generator.renderer = HybridTrailRenderer(render_config, config.frame_rate)
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
