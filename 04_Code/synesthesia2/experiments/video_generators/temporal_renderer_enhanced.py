"""
SYNESTHESIA 3.0 ENHANCED - Temporal Renderer
============================================
Enhanced spiral renderer with brighter visuals, smoother animations,
better effects, and more dynamic responses:

ENHANCEMENTS OVER 3.0:
- Brighter, more vivid colors (gamma correction, HDR-style lighting)
- Smoother animations with momentum-based interpolation
- Better glow/bloom effects with multi-layer rendering
- More dynamic beat response (bigger visual impact)
- Richer background with gradients and particle fields  
- Higher contrast between active and quiet frequencies
- Enhanced spiral point rendering with halos

This version maintains the core 2D spiral identity while adding
visual impact for showcase presentations.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict
from collections import deque
import colorsys
import math


@dataclass
class EnhancedTemporalRenderConfig:
    """Enhanced configuration for spectacular temporal rendering."""
    # Frame dimensions
    frame_width: int = 1920  # Full HD
    frame_height: int = 1080
    
    # Visual enhancements
    gamma_correction: float = 0.7  # Brighten midtones
    color_saturation: float = 1.4  # More vivid colors
    color_brightness: float = 1.3  # Brighter overall
    contrast_boost: float = 1.5  # Higher contrast
    hdr_tone_mapping: bool = True  # HDR-style lighting

    # Spiral parameters (enhanced)
    num_turns: float = 8.0  # More turns for elegance
    num_frequency_bins: int = 381
    base_point_size: int = 5  # Larger base size
    max_point_size: int = 24  # Bigger max size
    
    # Enhanced glow system
    enable_multi_layer_glow: bool = True
    glow_layers: int = 5  # Multi-layer glow
    glow_intensity: float = 1.8  # Stronger glow
    glow_radius_multiplier: float = 1.5
    
    # Enhanced melodic trail
    enable_melody_trail: bool = True
    trail_duration_seconds: float = 4.0  # Longer trail
    trail_decay_rate: float = 0.88  # Slower decay
    trail_particles: int = 150  # More trail particles
    trail_glow_radius: int = 12  # Bigger trail glow
    trail_colors: List[Tuple[int, int, int]] = field(default_factory=lambda: [
        (255, 255, 100),  # Bright yellow
        (255, 180, 60),   # Orange
        (255, 120, 180),  # Pink
        (180, 120, 255),  # Purple
        (120, 255, 200),  # Cyan
    ])
    
    # Enhanced rhythm pulse
    enable_rhythm_pulse: bool = True
    pulse_scale_amount: float = 0.25  # Bigger pulse (25%)
    pulse_brightness_amount: float = 0.8  # Much brighter on beat
    pulse_decay_rate: float = 0.75  # Slower decay for more impact
    pulse_wave_effect: bool = True  # Wave propagation on beat
    
    # Enhanced background system
    enable_rich_background: bool = True
    background_type: str = "gradient_particle"  # "gradient", "particle", "gradient_particle"
    gradient_colors: List[Tuple[int, int, int]] = field(default_factory=lambda: [
        (5, 8, 20),    # Deep blue
        (15, 25, 45),  # Medium blue
        (25, 15, 35),  # Purple tint
    ])
    particle_count: int = 200
    particle_brightness: float = 0.3
    
    # Enhanced harmonic aura
    enable_harmonic_aura: bool = True
    aura_transition_speed: float = 0.12  # Faster transitions
    aura_saturation: float = 0.6  # More saturated
    aura_brightness: float = 0.25  # Brighter
    aura_gradient_radius: float = 0.8  # Gradient effect
    
    # Enhanced atmosphere
    enable_atmosphere: bool = True
    atmosphere_particle_density: float = 0.5
    atmosphere_energy_response: float = 2.0  # More responsive
    
    # Animation smoothing
    enable_momentum_interpolation: bool = True
    momentum_factor: float = 0.15  # Smoother transitions


# Enhanced chromesthesia with brighter, more vivid colors
ENHANCED_CHROMESTHESIA_COLORS = [
    (80, 100, 255),     # Do - Bright Blue (C)
    (120, 60, 220),     # C# - Bright Indigo  
    (255, 140, 220),    # Re - Bright Pink (D)
    (255, 160, 255),    # D# - Bright Violet
    (255, 80, 80),      # Mi - Bright Red (E)
    (255, 180, 60),     # Fa - Bright Orange (F)
    (255, 200, 40),     # F# - Golden Orange
    (255, 255, 80),     # Sol - Bright Yellow (G)
    (180, 255, 100),    # G# - Bright Lime
    (80, 255, 120),     # La - Bright Green (A)
    (60, 220, 220),     # A# - Bright Turquoise
    (100, 255, 255),    # Si - Bright Cyan (B)
]

# Enhanced harmony colors - brighter and more saturated
ENHANCED_HARMONY_COLORS = {
    'C': (255, 120, 120),    # Bright Red
    'G': (255, 180, 100),    # Bright Orange
    'D': (255, 220, 100),    # Bright Yellow-Orange
    'A': (255, 255, 120),    # Bright Yellow
    'E': (200, 255, 120),    # Bright Yellow-Green
    'B': (120, 255, 120),    # Bright Green
    'F#': (120, 255, 200),   # Bright Cyan-Green
    'Db': (120, 255, 255),   # Bright Cyan
    'Ab': (120, 200, 255),   # Bright Sky Blue
    'Eb': (120, 120, 255),   # Bright Blue
    'Bb': (200, 120, 255),   # Bright Purple
    'F': (255, 120, 220),    # Bright Magenta
    'N': (80, 90, 120),      # Neutral (darker for contrast)
}


class EnhancedMelodicTrail:
    """Enhanced melodic trail with momentum, multiple colors, and better effects."""
    
    def __init__(self, config: EnhancedTemporalRenderConfig, frame_rate: int = 30):
        self.config = config
        self.frame_rate = frame_rate
        self.trail_length = int(config.trail_duration_seconds * frame_rate)
        self.pitch_history: deque = deque(maxlen=self.trail_length)
        
        # Momentum system for smoother trails
        self.position_history: deque = deque(maxlen=self.trail_length)
        
        # Spiral mapping parameters
        self.freq_min = 50.0
        self.freq_max = 2000.0
    
    def update(self, pitch_hz: float, confidence: float = 1.0):
        """Add current pitch with momentum smoothing."""
        self.pitch_history.append((pitch_hz, confidence))
    
    def render(self, draw: ImageDraw.Draw, center_x: int, center_y: int,
               max_radius: float, rotation: float):
        """Render enhanced melodic trail with multi-layer effects."""
        if not self.config.enable_melody_trail or len(self.pitch_history) == 0:
            return
            
        points = []
        
        for i, (pitch, confidence) in enumerate(self.pitch_history):
            if pitch <= 0 or confidence < 0.2:
                continue
                
            # Enhanced coordinate mapping with momentum
            x, y = self._pitch_to_coords_enhanced(pitch, center_x, center_y, 
                                                max_radius, rotation, i)
            
            # Enhanced alpha with slower decay
            age = len(self.pitch_history) - i - 1
            alpha = (self.config.trail_decay_rate ** age) * confidence
            
            if alpha < 0.03:
                continue
                
            # Color cycling based on pitch
            color_idx = int((np.log(pitch) - np.log(self.freq_min)) / 
                          (np.log(self.freq_max) - np.log(self.freq_min)) * 
                          len(self.config.trail_colors)) % len(self.config.trail_colors)
            
            points.append((x, y, alpha, confidence, color_idx))
        
        # Render enhanced trail points
        for x, y, alpha, confidence, color_idx in points:
            trail_color = self.config.trail_colors[color_idx]
            
            # Enhanced multi-layer glow
            if self.config.enable_multi_layer_glow:
                self._render_enhanced_glow(draw, x, y, alpha, confidence, trail_color)
            else:
                # Fallback simple glow
                glow_r = int(self.config.trail_glow_radius * confidence)
                self._render_simple_glow(draw, x, y, glow_r, alpha, trail_color)
    
    def _render_enhanced_glow(self, draw: ImageDraw.Draw, x: int, y: int, 
                            alpha: float, confidence: float, color: Tuple[int, int, int]):
        """Render multi-layer glow effect."""
        base_radius = int(self.config.trail_glow_radius * confidence)
        
        for layer in range(self.config.glow_layers, 0, -1):
            layer_alpha = alpha * (0.4 / layer) * self.config.glow_intensity
            layer_radius = int(base_radius * (layer * 0.6))
            
            # Apply gamma correction for brighter glow
            gamma_alpha = layer_alpha ** self.config.gamma_correction
            enhanced_color = tuple(int(min(255, c * gamma_alpha * 
                                         self.config.color_brightness)) for c in color)
            
            if enhanced_color[0] > 5 or enhanced_color[1] > 5 or enhanced_color[2] > 5:
                draw.ellipse([x - layer_radius, y - layer_radius,
                            x + layer_radius, y + layer_radius],
                           fill=enhanced_color)
        
        # Bright core
        core_alpha = alpha * self.config.glow_intensity
        core_color = tuple(int(min(255, c * core_alpha * 
                                 self.config.color_brightness)) for c in color)
        core_radius = max(2, int(base_radius * 0.3))
        draw.ellipse([x - core_radius, y - core_radius,
                    x + core_radius, y + core_radius],
                   fill=core_color)
    
    def _render_simple_glow(self, draw: ImageDraw.Draw, x: int, y: int,
                          radius: int, alpha: float, color: Tuple[int, int, int]):
        """Simple glow fallback."""
        for layer in range(3, 0, -1):
            layer_alpha = alpha * (0.4 / layer)
            layer_radius = radius * layer
            layer_color = tuple(int(c * layer_alpha) for c in color)
            
            draw.ellipse([x - layer_radius, y - layer_radius,
                        x + layer_radius, y + layer_radius],
                       fill=layer_color)
    
    def _pitch_to_coords_enhanced(self, pitch_hz: float, center_x: int, center_y: int,
                                max_radius: float, rotation: float, age: int) -> Tuple[int, int]:
        """Enhanced coordinate mapping with subtle momentum."""
        # Logarithmic frequency mapping
        if pitch_hz <= self.freq_min:
            rel_freq = 0.05
        elif pitch_hz >= self.freq_max:
            rel_freq = 0.95
        else:
            rel_freq = (np.log(pitch_hz) - np.log(self.freq_min)) / \
                      (np.log(self.freq_max) - np.log(self.freq_min))
        
        # Enhanced Fermat spiral with momentum
        theta = rel_freq * self.config.num_turns * 2 * np.pi + np.radians(rotation)
        r = np.sqrt(rel_freq) * max_radius * 0.92
        
        # Add subtle breathing effect
        breath_factor = 1.0 + 0.03 * np.sin(age * 0.3)
        r *= breath_factor
        
        x = int(center_x + r * np.cos(theta))
        y = int(center_y + r * np.sin(theta))
        
        return x, y


class EnhancedRhythmPulse:
    """Enhanced rhythm pulse with wave effects and bigger impact."""
    
    def __init__(self, config: EnhancedTemporalRenderConfig):
        self.config = config
        self.current_pulse = 0.0
        self.pulse_wave = 0.0  # For wave propagation effect
        self.momentum = 0.0  # For smoother pulse transitions
        
    def on_beat(self, strength: float = 1.0, is_downbeat: bool = False):
        """Enhanced beat response with bigger impact."""
        if is_downbeat:
            strength *= 1.5  # Even bigger emphasis on downbeats
        
        # Add to current pulse (can accumulate for stronger effect)
        pulse_boost = strength * 1.2  # Stronger base response
        self.current_pulse = min(1.5, self.current_pulse + pulse_boost)  # Allow over 1.0
        
        # Trigger wave effect
        if self.config.pulse_wave_effect:
            self.pulse_wave = 1.0
    
    def update(self) -> Tuple[float, float, float]:
        """
        Update and return enhanced pulse effects.
        
        Returns:
            (scale_multiplier, brightness_boost, wave_intensity)
        """
        if not self.config.enable_rhythm_pulse:
            return 1.0, 0.0, 0.0
        
        # Enhanced scale with momentum
        target_scale = 1.0 + self.current_pulse * self.config.pulse_scale_amount
        if self.config.enable_momentum_interpolation:
            self.momentum += (target_scale - 1.0 - self.momentum) * self.config.momentum_factor
            scale = 1.0 + self.momentum
        else:
            scale = target_scale
        
        # Enhanced brightness boost
        brightness = self.current_pulse * self.config.pulse_brightness_amount
        
        # Wave effect
        wave_intensity = self.pulse_wave
        
        # Enhanced decay
        self.current_pulse *= self.config.pulse_decay_rate
        if self.pulse_wave > 0:
            self.pulse_wave *= 0.8  # Wave fades faster
        
        return scale, brightness, wave_intensity


class EnhancedHarmonicAura:
    """Enhanced harmonic background with gradients and smoother transitions."""
    
    def __init__(self, config: EnhancedTemporalRenderConfig):
        self.config = config
        base_colors = config.gradient_colors[0] if config.gradient_colors else (15, 20, 30)
        self.current_color = np.array(base_colors, dtype=float)
        self.target_color = np.array(base_colors, dtype=float)
        self.current_chord = "N"
        
        # Momentum for smoother transitions
        self.color_momentum = np.array([0.0, 0.0, 0.0])
    
    def set_chord(self, chord_label: str):
        """Enhanced chord color mapping."""
        if not self.config.enable_harmonic_aura:
            return
            
        self.current_chord = chord_label
        
        # Enhanced root note extraction
        root = chord_label.replace('maj', '').replace('min', 'm').replace('dim', '°').replace('aug', '+')
        root = root.rstrip('7').rstrip('9').rstrip('11').rstrip('13')
        root = root.replace('m', '')  # Remove minor marker for root lookup
        
        # Get enhanced base color
        if root in ENHANCED_HARMONY_COLORS:
            base_color = np.array(ENHANCED_HARMONY_COLORS[root], dtype=float)
        else:
            base_color = np.array(ENHANCED_HARMONY_COLORS['N'], dtype=float)
        
        # Enhanced chord type modifications
        if 'm' in chord_label and 'maj' not in chord_label:
            # Minor: cooler, slightly darker
            base_color = base_color * 0.8 + np.array([0, 20, 40])
        elif 'dim' in chord_label or '°' in chord_label:
            # Diminished: much darker, more purple
            base_color = base_color * 0.4 + np.array([20, 0, 30])
        elif 'aug' in chord_label or '+' in chord_label:
            # Augmented: brighter, more intense
            base_color = base_color * 1.3
        
        # Apply enhanced saturation and brightness
        base_color = base_color * self.config.aura_brightness * 2.0  # Brighter
        
        self.target_color = np.clip(base_color, 0, 255)
    
    def update(self) -> Tuple[int, int, int]:
        """Update with enhanced smooth transitions."""
        if not self.config.enable_harmonic_aura:
            return self.config.gradient_colors[0] if self.config.gradient_colors else (15, 20, 30)
        
        # Enhanced momentum-based transition
        if self.config.enable_momentum_interpolation:
            color_diff = self.target_color - self.current_color
            self.color_momentum += color_diff * self.config.aura_transition_speed
            self.current_color += self.color_momentum * 0.6
            self.color_momentum *= 0.85  # Momentum decay
        else:
            # Direct transition
            self.current_color += (self.target_color - self.current_color) * self.config.aura_transition_speed
        
        return tuple(np.clip(self.current_color, 0, 255).astype(int))


class EnhancedBackgroundRenderer:
    """Renders rich backgrounds with gradients and particles."""
    
    def __init__(self, config: EnhancedTemporalRenderConfig):
        self.config = config
        self.particles = self._generate_particles()
        
    def _generate_particles(self) -> List[Dict]:
        """Generate background particles."""
        particles = []
        for _ in range(self.config.particle_count):
            particles.append({
                'x': np.random.randint(0, self.config.frame_width),
                'y': np.random.randint(0, self.config.frame_height),
                'size': np.random.uniform(1, 3),
                'brightness': np.random.uniform(0.1, 0.5),
                'phase': np.random.uniform(0, 2 * np.pi),
                'speed': np.random.uniform(0.01, 0.05),
            })
        return particles
        
    def render_background(self, background_color: Tuple[int, int, int], 
                         frame_idx: int, energy: float = 0.5) -> Image.Image:
        """Render enhanced background."""
        img = Image.new('RGB', (self.config.frame_width, self.config.frame_height), 
                        background_color)
        
        if self.config.background_type in ["gradient", "gradient_particle"]:
            img = self._add_gradient(img, background_color)
            
        if self.config.background_type in ["particle", "gradient_particle"]:
            img = self._add_particles(img, frame_idx, energy)
            
        return img
    
    def _add_gradient(self, img: Image.Image, 
                     center_color: Tuple[int, int, int]) -> Image.Image:
        """Add radial gradient."""
        gradient = Image.new('RGB', (self.config.frame_width, self.config.frame_height))
        draw = ImageDraw.Draw(gradient)
        
        center_x, center_y = self.config.frame_width // 2, self.config.frame_height // 2
        max_dist = max(center_x, center_y)
        
        # Multiple gradient rings
        for r in range(max_dist, 0, -max_dist // 20):
            # Interpolate between gradient colors
            t = 1.0 - (r / max_dist)
            if len(self.config.gradient_colors) >= 2:
                color1 = np.array(self.config.gradient_colors[0])
                color2 = np.array(center_color)
                interpolated = color1 * (1 - t) + color2 * t
                ring_color = tuple(int(c) for c in interpolated)
            else:
                ring_color = center_color
                
            draw.ellipse([center_x - r, center_y - r, 
                         center_x + r, center_y + r], 
                        fill=ring_color)
        
        # Blend with base image
        return Image.blend(img, gradient, 0.6)
    
    def _add_particles(self, img: Image.Image, 
                      frame_idx: int, energy: float) -> Image.Image:
        """Add animated particles."""
        draw = ImageDraw.Draw(img)
        
        for particle in self.particles:
            # Animate particle
            animated_brightness = (particle['brightness'] * 
                                 (1 + 0.3 * np.sin(particle['phase'] + frame_idx * particle['speed'])))
            animated_brightness *= (0.5 + energy * 0.5)  # React to energy
            
            if animated_brightness < 0.05:
                continue
                
            # Particle color (subtle white/blue)
            color_intensity = int(255 * animated_brightness * self.config.particle_brightness)
            particle_color = (color_intensity, color_intensity, 
                            min(255, int(color_intensity * 1.1)))
            
            # Draw particle
            size = particle['size']
            x, y = particle['x'], particle['y']
            draw.ellipse([x - size, y - size, x + size, y + size], 
                        fill=particle_color)
        
        return img


class EnhancedTemporalSpiralRenderer:
    """
    SYNESTHESIA 3.0 ENHANCED - Spectacular temporal visualization.
    
    All the features of 3.0 plus:
    - Brighter, more vivid colors with gamma correction
    - Smoother momentum-based animations  
    - Multi-layer glow and bloom effects
    - Bigger, more dynamic beat responses
    - Rich gradient/particle backgrounds
    - Enhanced contrast and HDR-style lighting
    """
    
    def __init__(self, config: Optional[EnhancedTemporalRenderConfig] = None,
                 frame_rate: int = 30):
        self.config = config or EnhancedTemporalRenderConfig()
        self.frame_rate = frame_rate
        
        # Initialize enhanced components
        self.melody_trail = EnhancedMelodicTrail(self.config, frame_rate)
        self.rhythm_pulse = EnhancedRhythmPulse(self.config)
        self.harmonic_aura = EnhancedHarmonicAura(self.config)
        self.background_renderer = EnhancedBackgroundRenderer(self.config)
        
        # Enhanced animation state with momentum
        self.rotation_angle = 0.0
        self.rotation_momentum = 0.0
        self.wave_phase = 0.0
        self.scale_momentum = 1.0
        
        # Pre-compute enhanced spiral geometry
        self._init_enhanced_spiral_geometry()
        
        # Fonts
        try:
            self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            self.title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        except:
            try:
                # macOS fonts
                self.font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
                self.title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
            except:
                self.font = ImageFont.load_default()
                self.title_font = self.font
    
    def _init_enhanced_spiral_geometry(self):
        """Pre-compute enhanced spiral with more elegance."""
        self.num_points = self.config.num_frequency_bins
        self.center_x = self.config.frame_width // 2
        self.center_y = self.config.frame_height // 2
        self.max_radius = min(self.center_x, self.center_y) * 0.88  # Slightly larger
        
        # Enhanced Fermat spiral coordinates
        t = np.linspace(0, 1, self.num_points)
        self.base_theta = t * self.config.num_turns * 2 * np.pi
        self.base_r = np.sqrt(t) * self.max_radius
        
        # Enhanced colors with gamma correction and saturation boost
        self.colors = []
        for i in range(self.num_points):
            octave_pos = (i / self.num_points) * 8  # 8 octaves for more range
            note_in_octave = (octave_pos % 1) * 12
            color_idx = int(note_in_octave) % 12
            base_color = ENHANCED_CHROMESTHESIA_COLORS[color_idx]
            
            # Apply gamma correction and saturation boost
            enhanced_color = tuple(int(min(255, c * self.config.color_brightness)) 
                                 for c in base_color)
            self.colors.append(enhanced_color)
    
    def update_temporal_features(self, **kwargs):
        """Update all enhanced temporal feature trackers."""
        # Same interface as original for compatibility
        pitch_hz = kwargs.get('pitch_hz', 0)
        pitch_confidence = kwargs.get('pitch_confidence', 0)
        is_beat = kwargs.get('is_beat', False)
        is_downbeat = kwargs.get('is_downbeat', False)
        beat_strength = kwargs.get('beat_strength', 0)
        chord_label = kwargs.get('chord_label', 'N')
        energy = kwargs.get('energy', 0.5)
        tension = kwargs.get('tension', 0.3)
        brightness = kwargs.get('brightness', 0.5)
        
        # Update components
        if pitch_hz > 0 and pitch_confidence > 0.2:
            self.melody_trail.update(pitch_hz, pitch_confidence)
            
        if is_beat:
            self.rhythm_pulse.on_beat(beat_strength, is_downbeat)
            
        if chord_label and chord_label != self.harmonic_aura.current_chord:
            self.harmonic_aura.set_chord(chord_label)
    
    def render_frame(self, amplitude_data: np.ndarray, frame_idx: int = 0,
                    frequencies: Optional[np.ndarray] = None,
                    show_labels: bool = True, show_info: bool = True) -> Image.Image:
        """Render enhanced frame with all improvements."""
        
        # Get enhanced temporal effects
        pulse_scale, pulse_brightness, wave_intensity = self.rhythm_pulse.update()
        background_color = self.harmonic_aura.update()
        
        # Enhanced momentum-based animation updates
        target_rotation_speed = 0.3 + wave_intensity * 0.7
        if self.config.enable_momentum_interpolation:
            self.rotation_momentum += (target_rotation_speed - self.rotation_momentum) * 0.1
            self.rotation_angle += self.rotation_momentum
        else:
            self.rotation_angle += target_rotation_speed
            
        self.wave_phase += 0.12 + wave_intensity * 0.08
        
        # Enhanced scale with momentum
        if self.config.enable_momentum_interpolation:
            self.scale_momentum += (pulse_scale - self.scale_momentum) * self.config.momentum_factor
            effective_scale = self.scale_momentum
        else:
            effective_scale = pulse_scale
        
        # Create enhanced background
        img = self.background_renderer.render_background(
            background_color, frame_idx, 
            energy=np.mean(amplitude_data) if len(amplitude_data) > 0 else 0.5
        )
        
        draw = ImageDraw.Draw(img)
        
        # Render enhanced spiral
        self._render_enhanced_spiral(draw, amplitude_data, effective_scale, 
                                   pulse_brightness, wave_intensity,
                                   frequencies, show_labels)
        
        # Render enhanced melodic trail
        self.melody_trail.render(draw, self.center_x, self.center_y,
                               self.max_radius, self.rotation_angle)
        
        # Apply HDR tone mapping if enabled
        if self.config.hdr_tone_mapping:
            img = self._apply_hdr_tone_mapping(img)
        
        # Enhanced info overlay
        if show_info:
            self._render_enhanced_info_overlay(draw, frame_idx, pulse_scale, wave_intensity)
        
        return img
    
    def _render_enhanced_spiral(self, draw: ImageDraw.Draw, amplitude_data: np.ndarray,
                              scale: float, brightness_boost: float, wave_intensity: float,
                              frequencies: Optional[np.ndarray], show_labels: bool):
        """Render the enhanced spiral with all improvements."""
        
        # Enhanced amplitude processing with contrast boost
        amp_max = np.max(amplitude_data)
        if amp_max > 0:
            amp_normalized = amplitude_data / amp_max
            # Apply contrast boost
            amp_normalized = np.power(amp_normalized, 1.0 / self.config.contrast_boost)
        else:
            amp_normalized = amplitude_data * 0
            
        # Enhanced spiral coordinates with wave effects
        theta = self.base_theta + np.radians(self.rotation_angle)
        
        # Multi-layer wave animation
        wave1 = np.sin(self.base_theta * 2 + self.wave_phase) * 0.04
        wave2 = np.sin(self.base_theta * 5 + self.wave_phase * 1.5) * 0.02
        wave_effect = wave1 + wave2 + wave_intensity * 0.08
        
        r_animated = self.base_r * (1 + wave_effect) * scale
        
        # Calculate positions
        x_coords = self.center_x + r_animated * np.cos(theta)
        y_coords = self.center_y + r_animated * np.sin(theta)
        
        # Enhanced frequency labeling
        label_frequencies = [55, 73, 98, 131, 175, 220, 294, 392, 523, 698, 880, 1175, 1568, 2093]
        labeled_indices = set()
        
        if frequencies is not None and show_labels:
            for label_freq in label_frequencies:
                idx = np.argmin(np.abs(frequencies - label_freq))
                if amp_normalized[idx] > 0.12:  # Lower threshold for more labels
                    labeled_indices.add(idx)
        
        # Render enhanced points with multi-layer glow
        for i in range(self.num_points):
            amp = amp_normalized[i]
            
            if amp < 0.02:  # Skip very quiet points
                continue
                
            # Enhanced size calculation
            base_size = self.config.base_point_size
            max_size = self.config.max_point_size
            size = int(base_size + amp * (max_size - base_size) * scale)
            
            x, y = int(x_coords[i]), int(y_coords[i])
            
            # Enhanced color with gamma correction and brightness boost
            base_color = self.colors[i]
            brightness = (0.2 + amp * 0.8 + brightness_boost) ** self.config.gamma_correction
            brightness *= self.config.color_brightness
            
            enhanced_color = tuple(int(min(255, c * brightness)) for c in base_color)
            
            # Multi-layer glow rendering
            if self.config.enable_multi_layer_glow and size > 3:
                self._render_point_with_enhanced_glow(draw, x, y, size, enhanced_color, amp)
            else:
                # Simple point
                draw.ellipse([x - size, y - size, x + size, y + size], 
                           fill=enhanced_color)
            
            # Enhanced labels
            if i in labeled_indices and frequencies is not None:
                freq = frequencies[i]
                label = f"{int(freq)}Hz"
                label_color = tuple(min(255, int(c * 1.2)) for c in enhanced_color)
                draw.text((x + size + 6, y - 8), label, fill=label_color, font=self.font)
    
    def _render_point_with_enhanced_glow(self, draw: ImageDraw.Draw, x: int, y: int,
                                       size: int, color: Tuple[int, int, int], amplitude: float):
        """Render a single point with enhanced multi-layer glow."""
        glow_radius = int(size * self.config.glow_radius_multiplier)
        
        # Multiple glow layers for bloom effect
        for layer in range(self.config.glow_layers, 0, -1):
            layer_alpha = (0.6 / layer) * self.config.glow_intensity * amplitude
            layer_radius = int(glow_radius * (layer * 0.5))
            layer_color = tuple(int(min(255, c * layer_alpha)) for c in color)
            
            if any(c > 8 for c in layer_color):  # Skip very dark layers
                draw.ellipse([x - layer_radius, y - layer_radius,
                            x + layer_radius, y + layer_radius],
                           fill=layer_color)
        
        # Bright center core
        core_brightness = amplitude * self.config.glow_intensity
        core_color = tuple(int(min(255, c * core_brightness)) for c in color)
        core_size = max(2, size // 2)
        
        draw.ellipse([x - core_size, y - core_size, x + core_size, y + core_size],
                   fill=core_color)
    
    def _apply_hdr_tone_mapping(self, img: Image.Image) -> Image.Image:
        """Apply HDR-style tone mapping for enhanced visuals."""
        # Increase contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(self.config.contrast_boost * 0.8)
        
        # Slight saturation boost
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(self.config.color_saturation)
        
        return img
    
    def _render_enhanced_info_overlay(self, draw: ImageDraw.Draw, frame_idx: int, 
                                    pulse_scale: float, wave_intensity: float):
        """Render enhanced information overlay."""
        # Enhanced title with glow effect
        title_color = (220, 220, 255)
        shadow_color = (100, 100, 150)
        
        # Title shadow
        draw.text((22, 17), "SYNESTHESIA 3.0 ENHANCED", fill=shadow_color, font=self.title_font)
        # Title main
        draw.text((20, 15), "SYNESTHESIA 3.0 ENHANCED", fill=title_color, font=self.title_font)
        
        # Enhanced temporal indicators
        y_pos = 50
        info_color = (180, 180, 200)
        
        # Chord with enhanced styling
        chord = self.harmonic_aura.current_chord
        if chord != "N":
            chord_color = ENHANCED_HARMONY_COLORS.get(chord.rstrip('m'), (180, 180, 200))
            draw.text((20, y_pos), f"♪ {chord}", fill=chord_color, font=self.font)
            y_pos += 22
        
        # Enhanced beat indicator
        if pulse_scale > 1.05:
            beat_intensity = int((pulse_scale - 1) * 100)
            beat_bar = "█" * min(20, beat_intensity)
            beat_color = (120, 255, 120) if wave_intensity > 0.3 else (100, 200, 100)
            draw.text((20, y_pos), f"♩ {beat_bar}", fill=beat_color, font=self.font)
            y_pos += 22
        
        # Enhanced energy visualization
        energy = np.random.random() * 0.3 + 0.4  # Placeholder
        energy_width = int(energy * 150)
        
        # Energy bar background
        draw.rectangle([(20, y_pos), (170, y_pos + 10)], fill=(40, 40, 60))
        # Energy bar fill with gradient effect
        for i in range(energy_width):
            bar_color = (80 + i // 2, 120 + i // 3, 255 - i // 4)
            draw.rectangle([(20 + i, y_pos), (21 + i, y_pos + 10)], fill=bar_color)
        
        draw.text((180, y_pos - 2), "Energy", fill=info_color, font=self.font)
    
    def save_frame(self, amplitude_data: np.ndarray, output_path: str,
                   frame_idx: int = 0, frequencies: Optional[np.ndarray] = None):
        """Render and save enhanced frame."""
        img = self.render_frame(amplitude_data, frame_idx, frequencies)
        img.save(output_path, quality=95, optimize=True)


def demo_enhanced_renderer():
    """Demonstrate the enhanced renderer."""
    print("=" * 70)
    print("SYNESTHESIA 3.0 ENHANCED - Temporal Renderer Demo")
    print("=" * 70)
    
    config = EnhancedTemporalRenderConfig(
        frame_width=1920,
        frame_height=1080,
        enable_melody_trail=True,
        enable_rhythm_pulse=True,
        enable_harmonic_aura=True,
        enable_rich_background=True,
        background_type="gradient_particle"
    )
    
    renderer = EnhancedTemporalSpiralRenderer(config, frame_rate=30)
    
    print("✅ Enhanced renderer demo initialized!")
    print("Features enabled:")
    print("  - Brighter, more vivid colors")
    print("  - Multi-layer glow effects")
    print("  - Rich gradient/particle background")
    print("  - Enhanced beat response")
    print("  - Smoother animations")
    
    return renderer


if __name__ == "__main__":
    demo_enhanced_renderer()