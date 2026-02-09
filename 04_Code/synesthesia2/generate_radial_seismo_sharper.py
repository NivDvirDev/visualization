#!/usr/bin/env python3
"""
SYNESTHESIA 3.6.6 - Energy Glow
================================
Blueprint seismograph with energy-reactive background:
- Background GLOWS with dominant energy (vocals + drums)
- Dark blue in silence → warm olive-green on loud moments
- The whole screen "breathes" with the music
- Perceptual color gradient: warm (bass) → cool (treble)
- Amplitude as radial displacement (true seismograph behavior)
- Band-dependent fade rates (bass lingers, treble crisp)
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


class BlueprintSeismographRenderer(TemporalSpiralRenderer):
    """
    Blueprint-style radial seismograph — designed so any viewer
    can intuitively read the music structure.

    Key ideas:
    - Color = frequency band (warm→cool gradient, no repeating)
    - Radial displacement = amplitude (like a real seismograph needle)
    - Trail persistence = musical memory (bass slow, treble fast)
    - Octave rings = visual grid for orientation
    """

    # Frequency band definitions (Hz boundaries)
    BANDS = [
        ('sub',      20,   80,  (180, 50, 50)),    # Deep red
        ('bass',     80,  250,  (220, 100, 40)),    # Orange-red
        ('low_mid', 250,  600,  (220, 180, 50)),    # Warm yellow
        ('mid',     600, 1500,  (80, 200, 80)),     # Green
        ('hi_mid', 1500, 3500,  (60, 150, 220)),    # Sky blue
        ('treble', 3500, 8000,  (140, 90, 220)),    # Violet
    ]

    def __init__(self, config, frame_rate=30):
        super().__init__(config, frame_rate)

        self.accumulated_canvas = None

        # === BLUEPRINT PARAMETERS ===
        # Expansion is now BEAT-REACTIVE (set dynamically in render_frame)
        self.expansion_rate = 1.005  # base (between beats)
        self.expansion_rate_base = 1.002  # calm
        self.expansion_rate_beat = 1.06   # on strong beat

        # Moderate fade — enough history to read, not so much it smears
        self.fade_rate = 0.988

        # Stronger accumulation = visible trail record
        self.accumulation_strength = 0.65

        self.center_radius_ratio = 0.14

        self.brightness_multiplier = 1.2

        # Radial displacement: amplitude pushes dots outward from base spiral
        self.displacement_strength_base = 8.0    # calm
        self.displacement_strength_beat = 50.0    # on beat hit

        # Wave phase accumulator (beat-reactive speed)
        self._wave_phase_accum = 0.0
        self._wave_speed_base = 0.06    # calm wave crawl
        self._wave_speed_beat = 1.0     # fast wave burst on beat

        # Build per-point color gradient and band-specific fade multipliers
        self._build_band_colors()
        self._build_fade_map()

    def _build_band_colors(self):
        """Build a smooth perceptual color gradient for every frequency point."""
        self.band_colors = []
        for i in range(self.num_points):
            freq = 20 * (2 ** (i / self.num_points * 8))  # ~20-5120 Hz
            # Find which band this belongs to
            color = self.BANDS[-1][3]  # default treble
            for _, lo, hi, band_color in self.BANDS:
                if lo <= freq < hi:
                    color = band_color
                    break
            # Smooth interpolation within band for gradient feel
            t = i / max(1, self.num_points - 1)
            # Slight hue shift based on position for within-band variation
            h_base, s_base, v_base = colorsys.rgb_to_hsv(
                color[0] / 255, color[1] / 255, color[2] / 255)
            h_shifted = (h_base + t * 0.02) % 1.0  # tiny hue drift
            r, g, b = colorsys.hsv_to_rgb(h_shifted, s_base, v_base)
            self.band_colors.append((int(r * 255), int(g * 255), int(b * 255)))
        # Override parent's chromesthesia colors
        self.colors = self.band_colors

    def _build_fade_map(self):
        """Band-dependent fade: bass lingers longer, treble fades faster."""
        # Per-pixel fade would be expensive, so we store per-point fade rates
        # and apply a radial approximation in the canvas fade
        self.band_fade_rates = []
        for i in range(self.num_points):
            t = i / max(1, self.num_points - 1)  # 0=lowest freq, 1=highest
            # Bass: 0.992 (slow fade), Treble: 0.980 (fast fade)
            fade = 0.992 - t * 0.012
            self.band_fade_rates.append(fade)

    def _expand_canvas_outward(self, canvas):
        """Expand outward with linear interpolation for smooth trails."""
        if canvas is None:
            return None

        canvas_arr = np.array(canvas, dtype=np.float32)
        h, w = canvas_arr.shape[:2]
        cx, cy = w // 2, h // 2

        expanded = np.zeros_like(canvas_arr)

        y_coords, x_coords = np.mgrid[0:h, 0:w]
        x_centered = x_coords - cx
        y_centered = y_coords - cy

        scale = 1.0 / self.expansion_rate
        x_source = (x_centered * scale + cx).astype(np.float32)
        y_source = (y_centered * scale + cy).astype(np.float32)

        # Order=1 (bilinear) for smoother trail expansion
        for c in range(3):
            expanded[:, :, c] = ndimage.map_coordinates(
                canvas_arr[:, :, c],
                [y_source, x_source],
                order=1,
                mode='constant',
                cval=0
            )

        # Radial-dependent fade: inner pixels (bass) fade slower than outer (treble)
        dist = np.sqrt(x_centered ** 2 + y_centered ** 2)
        max_r = min(cx, cy)
        t = np.clip(dist / max_r, 0, 1)
        fade_map = 0.992 - t * 0.012  # matches band_fade_rates range
        for c in range(3):
            expanded[:, :, c] *= fade_map

        return expanded

    def _create_center_mask(self, width, height):
        """Tighter center mask."""
        cx, cy = width // 2, height // 2
        max_radius = min(cx, cy)
        center_radius = max_radius * self.center_radius_ratio
        
        y_coords, x_coords = np.mgrid[0:height, 0:width]
        dist = np.sqrt((x_coords - cx) ** 2 + (y_coords - cy) ** 2)
        
        # Steeper falloff for tighter mask
        mask = np.clip(1.0 - (dist / max_radius) * 0.9, 0.1, 1.0)
        center_boost = np.clip(1.0 - dist / center_radius, 0, 1) ** 1.5  # Steeper
        mask = mask + center_boost * 0.6
        mask = np.clip(mask, 0, 1)
        
        return mask

    def render_frame(self, amplitude_data, frame_idx=0, frequencies=None,
                     show_labels=True, show_info=True):
        """Render blueprint-style frame."""
        # Capture beat intensity BEFORE update() decays it
        beat = self.rhythm_pulse.current_pulse  # 0.0 = silence, 1.0 = hard beat

        pulse_scale, pulse_brightness = self.rhythm_pulse.update()
        background_color = self.harmonic_aura.update()
        atmos_effects = self.atmosphere.get_effects()

        # --- DOMINANT ENERGY: voice + beat ---
        # Vocal energy from mid-frequency bands (low_mid, mid, hi_mid = voice range)
        mid_bands = amplitude_data[2:5]
        amp_max = np.max(amplitude_data)
        vocal_energy = np.mean(mid_bands) / amp_max if amp_max > 0 else 0.0
        # Voice is the main driver, drums ADD to voice instead of replacing
        dominant_energy = min(1.0, vocal_energy * 2.5 + beat * 0.5)
        
        # Store for background glow effect
        self._dominant_energy = dominant_energy

        # --- DOMINANT-ENERGY-REACTIVE MODULATION ---
        # Expansion: slow drift in silence, burst outward with voice/beat
        self.expansion_rate = self.expansion_rate_base + (
            (self.expansion_rate_beat - self.expansion_rate_base) * dominant_energy
        )

        # Wave phase: accumulate with energy-reactive speed
        wave_speed = self._wave_speed_base + (
            (self._wave_speed_beat - self._wave_speed_base) * dominant_energy
        )
        self._wave_phase_accum += wave_speed
        self.wave_phase = self._wave_phase_accum

        # Displacement strength: pulses with voice and beat
        self.displacement_strength = self.displacement_strength_base + (
            (self.displacement_strength_beat - self.displacement_strength_base) * dominant_energy
        )

        self.rotation_angle = frame_idx * 0.5 * atmos_effects['rotation_speed']

        w = self.config.frame_width
        h = self.config.frame_height

        current_frame = Image.new('RGB', (w, h), (0, 0, 0))
        draw = ImageDraw.Draw(current_frame)

        # Amplify pulse impact: exaggerate beat-driven scale changes
        effective_scale = (1.0 + (pulse_scale - 1.0) * 2.5) * atmos_effects['particle_scale']
        self._render_spiral_elements(draw, amplitude_data, effective_scale, 
                                      pulse_brightness, frequencies)

        # === ACCUMULATION ===
        if self.accumulated_canvas is None:
            self.accumulated_canvas = np.zeros((h, w, 3), dtype=np.float32)
        
        self.accumulated_canvas = self._expand_canvas_outward(
            Image.fromarray(self.accumulated_canvas.astype(np.uint8), 'RGB')
        )
        
        current_arr = np.array(current_frame, dtype=np.float32)
        center_mask = self._create_center_mask(w, h)
        
        for c in range(3):
            self.accumulated_canvas[:, :, c] += (
                current_arr[:, :, c] * center_mask * self.accumulation_strength
            )
        
        self.accumulated_canvas = np.clip(self.accumulated_canvas, 0, 255)
        
        # Background
        final_frame = self._create_dark_gradient_background(background_color)
        final_arr = np.array(final_frame, dtype=np.float32)
        
        # Screen blend: brighter without blowing out whites
        acc = self.accumulated_canvas * self.brightness_multiplier / 255.0
        blended = final_arr + (255.0 - final_arr) * acc
        blended = np.clip(blended, 0, 255).astype(np.uint8)
        
        final_frame = Image.fromarray(blended, 'RGB')
        
        # Draw octave guide rings on top (subtle)
        self._draw_octave_rings(final_frame)
        
        if show_info:
            draw_final = ImageDraw.Draw(final_frame)
            self._render_info_overlay(draw_final, frame_idx, pulse_scale)

        return final_frame

    def _draw_octave_rings(self, frame):
        """Draw frequency circles grid: dense concentric rings showing frequency structure."""
        draw = ImageDraw.Draw(frame)
        cx, cy = self.center_x, self.center_y

        # --- Dense subdivision rings (the "frequency grid" from 3.0) ---
        # 4 subdivisions per octave across 8 octaves = 32 rings
        num_subdivisions = 4
        for octave_idx in range(0, 8):
            for sub in range(1, num_subdivisions + 1):
                t = (octave_idx + sub / num_subdivisions) / 8.0
                if t > 1.0:
                    break
                r = math.sqrt(t) * self.max_radius
                # Subdivision rings: faint but visible grid
                grid_color = (20, 24, 38)
                draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                             outline=grid_color, width=1)

        # --- Octave boundary rings (brighter, labeled) ---
        octave_labels = ['40', '80', '160', '320', '640', '1.3k', '2.5k', '5k']
        for octave_idx in range(1, 8):
            t = octave_idx / 8.0
            r = math.sqrt(t) * self.max_radius
            ring_color = (40, 48, 68)
            draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                         outline=ring_color, width=1)
            # Label at 2 o'clock position
            label_angle = -math.pi / 6
            lx = cx + r * math.cos(label_angle)
            ly = cy + r * math.sin(label_angle)
            label = f"{octave_labels[octave_idx - 1]}Hz"
            draw.text((lx + 3, ly - 6), label, fill=(55, 62, 80), font=self.font)

    def _create_dark_gradient_background(self, aura_color):
        """Energy-reactive background that glows DRAMATICALLY with the music."""
        w = self.config.frame_width
        h = self.config.frame_height

        # Get current energy level (0 = silence, 1 = max energy)
        energy = getattr(self, '_dominant_energy', 0.0)
        
        # DRAMATIC glow - like reference video
        base = (5, 6, 15)  # Very dark blue (silence)
        energy_glow = (90, 110, 45)  # BRIGHT olive-green (reference video peak)
        
        # Full interpolation - no dampening!
        glow_r = int(base[0] + (energy_glow[0] - base[0]) * energy)
        glow_g = int(base[1] + (energy_glow[1] - base[1]) * energy)
        glow_b = int(base[2] + (energy_glow[2] - base[2]) * energy)
        
        center_r = min(255, int(glow_r * 1.5 + aura_color[0] * 0.15))
        center_g = min(255, int(glow_g * 1.5 + aura_color[1] * 0.15))
        center_b = min(255, int(glow_b * 1.5 + aura_color[2] * 0.15))

        edge_r = max(0, int(glow_r * 0.7))
        edge_g = max(0, int(glow_g * 0.7))
        edge_b = max(0, int(glow_b * 0.7))

        cx, cy = w // 2, h // 2
        max_dist = math.sqrt(cx * cx + cy * cy)

        y_coords, x_coords = np.mgrid[0:h, 0:w]
        dist = np.sqrt((x_coords - cx) ** 2 + (y_coords - cy) ** 2) / max_dist
        dist = np.clip(dist, 0, 1) ** 0.5

        r_channel = (center_r * (1 - dist) + edge_r * dist).astype(np.uint8)
        g_channel = (center_g * (1 - dist) + edge_g * dist).astype(np.uint8)
        b_channel = (center_b * (1 - dist) + edge_b * dist).astype(np.uint8)

        img_array = np.stack([r_channel, g_channel, b_channel], axis=-1)
        return Image.fromarray(img_array, 'RGB')

    def _render_spiral_elements(self, draw, amplitude_data, scale, brightness_boost,
                                 frequencies):
        """Render sharper, smaller shapes."""
        amp_max = np.max(amplitude_data)
        if amp_max < 1e-8:
            amp_normalized = np.zeros_like(amplitude_data)
        else:
            amp_normalized = amplitude_data / amp_max

        theta = self.base_theta + np.radians(self.rotation_angle)
        wave = np.sin(self.base_theta * 3 + self.wave_phase) * 0.09  # More wave amplitude
        r_animated = self.base_r * (1 + wave) * scale

        x_coords = self.center_x + r_animated * np.cos(theta)
        y_coords = self.center_y + r_animated * np.sin(theta)

        for i in range(self.num_points):
            amp = amp_normalized[i]
            x, y = float(x_coords[i]), float(y_coords[i])
            base_color = self.colors[i]

            # Always draw base "needle" marker (dimmed, 2-3px)
            dimmed = tuple(int(c * 0.35) for c in base_color)
            draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill=dimmed)

            # Animated shape only when amplitude is present
            if amp < 0.08:
                continue

            base_size = self.config.base_point_size
            # Smaller shapes
            outer_size = int(1.5 + amp * base_size * 2.5 * scale)
            outer_size = max(2, min(outer_size, 20))  # Cap max size

            # Higher contrast brightness
            brightness = 0.4 + amp * 0.8 + brightness_boost
            color = tuple(int(min(255, c * brightness * 1.2)) for c in base_color)

            if frequencies is not None and i < len(frequencies):
                freq = frequencies[i]
            else:
                freq = 20 * (2 ** (i / self.num_points * 8))

            num_points_shape = self._freq_to_num_points(freq)

            # More distinct star points
            if amp < 0.2:
                inner_size = outer_size * 0.8
            else:
                spikiness = 0.3 + amp * 0.4
                inner_size = outer_size * (1 - spikiness * 0.6)

            tangent_angle = theta[i] + math.pi / 2

            self._draw_star_shape(
                draw, x, y,
                outer_radius=outer_size,
                inner_radius=inner_size,
                num_points=num_points_shape,
                rotation_angle=tangent_angle,
                color=color
            )

            # Brighter core for peaks
            if amp > 0.5:
                white_blend = (amp - 0.5) / 0.5
                white_blend = min(1.0, white_blend)

                core_r = int(color[0] + (255 - color[0]) * white_blend * 0.8)
                core_g = int(color[1] + (255 - color[1]) * white_blend * 0.8)
                core_b = int(color[2] + (255 - color[2]) * white_blend * 0.8)
                core_color = (core_r, core_g, core_b)

                core_size = max(1, int(outer_size * 0.35))
                self._draw_star_shape(
                    draw, x, y,
                    outer_radius=core_size,
                    inner_radius=core_size * 0.7,
                    num_points=num_points_shape,
                    rotation_angle=tangent_angle,
                    color=core_color
                )

    def _freq_to_num_points(self, freq):
        """Map frequency to shape points."""
        min_freq, max_freq = 20, 8000
        freq = max(min_freq, min(max_freq, freq))

        log_min = np.log10(min_freq)
        log_max = np.log10(max_freq)
        log_freq = np.log10(freq)
        t = (log_freq - log_min) / (log_max - log_min)
        num_points = int(3 + t * 9)
        return max(3, min(12, num_points))

    def _draw_star_shape(self, draw, cx, cy, outer_radius, inner_radius, 
                         num_points, rotation_angle, color):
        """Draw star/polygon."""
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
    output_path = "/Users/guydvir/Project/04_Code/synesthesia2/synth36_glow_v2.mp4"

    print("=" * 70)
    print("SYNESTHESIA 3.6.6 - Energy Glow")
    print("=" * 70)
    print("New in 3.6.6:")
    print("  • Background GLOWS with dominant energy")
    print("  • Dark blue silence → warm olive-green on loud moments")
    print("  • The whole screen 'breathes' with the music")
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
        base_point_size=4,  # Smaller base
        pulse_scale_amount=0.15,
        pulse_brightness_amount=0.3,
        pulse_decay_rate=0.85,
        aura_brightness=0.18,
        aura_transition_speed=0.1,
        base_background_color=(5, 6, 15),  # Darker
        enable_melody_trail=False,
        enable_rhythm_pulse=True,
        enable_harmonic_aura=True,
        enable_atmosphere=True,
    )

    generator.renderer = BlueprintSeismographRenderer(render_config, config.frame_rate)
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
