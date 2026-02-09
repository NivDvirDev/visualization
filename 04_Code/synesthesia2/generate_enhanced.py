#!/usr/bin/env python3
"""
SYNESTHESIA 3.0 ENHANCED - Brighter, more vivid spiral visualization.
Uses the existing pipeline but with enhanced rendering parameters.
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from video_generator_temporal import TemporalVideoGenerator, TemporalVideoConfig
from temporal_renderer import TemporalRenderConfig

def main():
    audio_path = "/Users/guydvir/Project/04_Code/synesthesia2/papaoutai_audio.wav"
    output_path = "/Users/guydvir/Project/04_Code/synesthesia2/synth3_enhanced_papaoutai.mp4"
    
    print("=" * 60)
    print("SYNESTHESIA 3.0 ENHANCED - Generating video...")
    print("=" * 60)
    
    # Enhanced config - 1080p with brighter visuals
    config = TemporalVideoConfig(
        output_width=1920,
        output_height=1080,
        frame_rate=30,
        video_codec="libx264",
        video_preset="medium",
        video_crf=18,  # Higher quality
        audio_codec="aac",
        audio_bitrate="320k",
        enable_melody_trail=True,
        enable_rhythm_pulse=True,
        enable_harmonic_aura=True,
        enable_atmosphere=True,
    )
    
    generator = TemporalVideoGenerator(config)
    
    # Override renderer config for enhanced visuals
    renderer = generator.renderer
    renderer.config.base_point_size = 6  # Bigger points (was 4)
    renderer.config.pulse_scale_amount = 0.20  # More beat impact (was 0.12)
    renderer.config.pulse_brightness_amount = 0.40  # Brighter beats (was 0.25)
    renderer.config.pulse_decay_rate = 0.80  # Faster pulse decay for snappier feel
    renderer.config.trail_glow_radius = 12  # Bigger glow (was 8)
    renderer.config.trail_color = (255, 240, 120)  # Brighter golden
    renderer.config.aura_brightness = 0.25  # Richer background (was 0.15)
    renderer.config.aura_transition_speed = 0.12  # Faster chord color changes
    renderer.config.base_background_color = (10, 12, 25)  # Deeper dark blue
    
    # Re-init geometry for new resolution
    renderer._init_spiral_geometry()
    
    # Monkey-patch the _render_spiral for enhanced glow
    original_render_spiral = renderer._render_spiral
    
    def enhanced_render_spiral(draw, amplitude_data, scale, brightness_boost, frequencies, show_labels):
        """Enhanced spiral with glow layers and brighter colors."""
        import numpy as np
        
        # Normalize amplitude
        amp_normalized = amplitude_data / (np.max(amplitude_data) + 1e-8)
        
        # Apply rotation
        theta = renderer.base_theta + np.radians(renderer.rotation_angle)
        
        # Apply wave animation
        wave = np.sin(renderer.base_theta * 3 + renderer.wave_phase) * 0.06
        r_animated = renderer.base_r * (1 + wave) * scale
        
        # Calculate positions
        x_coords = renderer.center_x + r_animated * np.cos(theta)
        y_coords = renderer.center_y + r_animated * np.sin(theta)
        
        # First pass: draw glow halos for bright points
        for i in range(renderer.num_points):
            amp = amp_normalized[i]
            if amp < 0.15:
                continue
                
            x, y = int(x_coords[i]), int(y_coords[i])
            base_color = renderer.colors[i]
            
            # Glow radius scales with amplitude
            glow_radius = int(8 + amp * 16 * scale)
            glow_alpha = amp * 0.25 + brightness_boost * 0.15
            glow_color = tuple(int(min(255, c * glow_alpha)) for c in base_color)
            
            draw.ellipse(
                [x - glow_radius, y - glow_radius, x + glow_radius, y + glow_radius],
                fill=glow_color
            )
        
        # Second pass: draw core points (brighter)
        for i in range(renderer.num_points):
            amp = amp_normalized[i]
            
            base_size = renderer.config.base_point_size
            size = int(base_size + amp * base_size * 3.5 * scale)
            
            if size < 1:
                continue
            
            x, y = int(x_coords[i]), int(y_coords[i])
            
            # Enhanced brightness - minimum brightness higher
            base_color = renderer.colors[i]
            brightness = 0.35 + amp * 0.85 + brightness_boost
            color = tuple(int(min(255, c * brightness)) for c in base_color)
            
            draw.ellipse([x - size, y - size, x + size, y + size], fill=color)
            
            # White core for very bright points
            if amp > 0.6:
                core_size = max(1, size // 3)
                core_alpha = (amp - 0.6) * 2.0
                core_color = tuple(int(min(255, 200 + 55 * core_alpha)) for _ in range(3))
                draw.ellipse(
                    [x - core_size, y - core_size, x + core_size, y + core_size],
                    fill=core_color
                )
    
    renderer._render_spiral = enhanced_render_spiral
    
    # Monkey-patch render_frame for radial gradient background
    original_render_frame = renderer.render_frame
    
    def enhanced_render_frame(amplitude_data, frame_idx=0, frequencies=None, show_labels=True, show_info=True):
        """Enhanced frame with radial gradient background."""
        from PIL import Image, ImageDraw
        import numpy as np
        
        # Get temporal effects
        pulse_scale, pulse_brightness = renderer.rhythm_pulse.update()
        background_color = renderer.harmonic_aura.update()
        atmos_effects = renderer.atmosphere.get_effects()
        
        # Update animation state
        renderer.rotation_angle = frame_idx * 0.5 * atmos_effects['rotation_speed']
        renderer.wave_phase = frame_idx * 0.15
        
        w, h = renderer.config.frame_width, renderer.config.frame_height
        
        # Create radial gradient background
        img = Image.new('RGB', (w, h), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        cx, cy = w // 2, h // 2
        max_r = int((cx**2 + cy**2)**0.5)
        
        # Draw gradient rings from outside in
        bg = background_color
        num_rings = 20
        for ring in range(num_rings, 0, -1):
            r = int(max_r * ring / num_rings)
            t = ring / num_rings  # 1.0 at edge, close to 0 at center
            
            # Edge is darker, center picks up the harmonic aura color
            ring_color = tuple(int(bg[c] * (1.2 - t * 0.9) + 5 * (1 - t)) for c in range(3))
            ring_color = tuple(min(255, max(0, c)) for c in ring_color)
            
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ring_color)
        
        # Apply atmosphere effects
        effective_scale = pulse_scale * atmos_effects['particle_scale']
        
        # Render enhanced spiral
        renderer._render_spiral(draw, amplitude_data, effective_scale, pulse_brightness, frequencies, show_labels)
        
        # Render melodic trail
        renderer.melody_trail.render(draw, renderer.center_x, renderer.center_y,
                                     renderer.max_radius, renderer.rotation_angle)
        
        # Info overlay (smaller, less intrusive)
        if show_info:
            renderer._render_info_overlay(draw, frame_idx, pulse_scale)
        
        return img
    
    renderer.render_frame = enhanced_render_frame
    
    # Override save_frame to use enhanced render
    def enhanced_save_frame(amplitude_data, output_path, frame_idx=0, frequencies=None):
        img = enhanced_render_frame(amplitude_data, frame_idx, frequencies)
        img.save(output_path)
    
    renderer.save_frame = enhanced_save_frame
    
    # Also patch the ffmpeg command to use the correct binary
    original_encode = generator._encode_video
    def patched_encode(frames_dir, audio_path, output_path, start_time, duration):
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
        print(f"Running FFmpeg: {' '.join(cmd[:5])}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"FFmpeg error: {result.stderr[-500:]}")
            raise RuntimeError("FFmpeg encoding failed")
    
    generator._encode_video = patched_encode
    
    # Generate!
    generator.generate(
        audio_path=audio_path,
        output_path=output_path,
    )
    
    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"\n✅ Enhanced video saved: {output_path}")
    print(f"   Size: {size_mb:.1f} MB")

if __name__ == "__main__":
    main()
