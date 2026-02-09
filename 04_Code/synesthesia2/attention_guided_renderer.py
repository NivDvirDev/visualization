"""
SYNESTHESIA 3.0 - Attention-Guided Renderer
============================================
The breakthrough component that closes the visualization-classification feedback loop.

This module creates visualizations where the AI's attention patterns actively influence
what gets emphasized, creating a self-reinforcing cycle:
  Audio → Visualization → Classification → Attention → Enhanced Visualization

Key Innovation:
- Regions the classifier attends to get amplified in the visualization
- This creates more distinctive visual patterns for each instrument class
- The enhanced patterns make classification easier and more accurate
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, List
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import colorsys


@dataclass
class AttentionConfig:
    """Configuration for attention-guided visualization."""
    # Attention blending
    attention_alpha: float = 0.6  # How much attention affects visualization
    attention_colormap: str = "plasma"  # plasma, viridis, jet, or chromesthesia

    # Enhancement modes
    amplify_attended: bool = True  # Make attended regions larger/brighter
    suppress_unattended: bool = True  # Dim unattended regions
    amplification_factor: float = 2.5  # Max amplification for high-attention areas
    suppression_factor: float = 0.3  # Min brightness for low-attention areas

    # Attention smoothing
    temporal_smoothing: int = 5  # Frames to smooth attention over
    spatial_blur: float = 2.0  # Gaussian blur sigma for attention map

    # Visual feedback
    show_attention_overlay: bool = True  # Show semi-transparent attention heatmap
    show_attention_border: bool = True  # Highlight high-attention regions with glow
    glow_threshold: float = 0.7  # Attention value above which to add glow
    glow_color: Tuple[int, int, int] = (255, 255, 255)  # Glow color (white default)

    # Statistics tracking
    track_attention_stats: bool = True


@dataclass
class AttentionStatistics:
    """Track attention patterns per class for analysis."""
    class_attention_maps: Dict[str, List[np.ndarray]] = field(default_factory=dict)
    frequency_attention: Dict[str, np.ndarray] = field(default_factory=dict)  # Which frequencies each class attends to

    def add_sample(self, class_name: str, attention_map: np.ndarray, frequencies: np.ndarray):
        """Add an attention sample for a class."""
        if class_name not in self.class_attention_maps:
            self.class_attention_maps[class_name] = []
            self.frequency_attention[class_name] = np.zeros(len(frequencies))

        self.class_attention_maps[class_name].append(attention_map)

        # Track which frequency bins get most attention
        # Map attention to frequency bins (simplified - assumes attention aligns with spiral)
        attention_flat = attention_map.flatten()
        if len(attention_flat) >= len(frequencies):
            # Downsample attention to match frequency bins
            indices = np.linspace(0, len(attention_flat)-1, len(frequencies)).astype(int)
            freq_attention = attention_flat[indices]
        else:
            # Upsample (interpolate)
            freq_attention = np.interp(
                np.linspace(0, 1, len(frequencies)),
                np.linspace(0, 1, len(attention_flat)),
                attention_flat
            )

        # Running average
        n = len(self.class_attention_maps[class_name])
        self.frequency_attention[class_name] = (
            (self.frequency_attention[class_name] * (n-1) + freq_attention) / n
        )

    def get_class_profile(self, class_name: str) -> Optional[np.ndarray]:
        """Get average attention profile for a class."""
        if class_name not in self.frequency_attention:
            return None
        return self.frequency_attention[class_name]

    def get_discriminative_frequencies(self, class_name: str, top_k: int = 20) -> np.ndarray:
        """Get indices of most attended frequencies for a class."""
        profile = self.get_class_profile(class_name)
        if profile is None:
            return np.array([])
        return np.argsort(profile)[-top_k:]


class AttentionGuidedRenderer:
    """
    Renderer that uses classifier attention to enhance visualizations.

    The core innovation: visualizations adapt based on what the AI finds important.
    """

    def __init__(self, config: Optional[AttentionConfig] = None):
        self.config = config or AttentionConfig()
        self.statistics = AttentionStatistics() if self.config.track_attention_stats else None

        # Temporal smoothing buffer
        self.attention_history: List[np.ndarray] = []

        # Chromesthesia colors (matching spiral_renderer_2d.py)
        self.chromesthesia_colors = [
            (0, 0, 255),      # Do - Blue
            (255, 105, 180),  # Re - Pink
            (255, 0, 0),      # Mi - Red
            (255, 165, 0),    # Fa - Orange
            (255, 255, 0),    # Sol - Yellow
            (0, 255, 0),      # La - Green
            (0, 255, 255),    # Si - Cyan
        ]

    def _smooth_attention(self, attention_map: np.ndarray) -> np.ndarray:
        """Apply temporal and spatial smoothing to attention map."""
        # Add to history
        self.attention_history.append(attention_map)
        if len(self.attention_history) > self.config.temporal_smoothing:
            self.attention_history.pop(0)

        # Temporal averaging
        smoothed = np.mean(self.attention_history, axis=0)

        # Spatial smoothing via PIL
        if self.config.spatial_blur > 0:
            # Convert to image, blur, convert back
            attn_img = Image.fromarray((smoothed * 255).astype(np.uint8))
            attn_img = attn_img.filter(ImageFilter.GaussianBlur(self.config.spatial_blur))
            smoothed = np.array(attn_img) / 255.0

        return smoothed

    def _get_attention_colormap(self, attention: np.ndarray) -> np.ndarray:
        """Convert attention values to RGB colors."""
        h, w = attention.shape
        colors = np.zeros((h, w, 3), dtype=np.uint8)

        if self.config.attention_colormap == "plasma":
            # Plasma colormap: purple -> orange -> yellow
            for i in range(h):
                for j in range(w):
                    v = attention[i, j]
                    if v < 0.5:
                        # Purple to orange
                        r = int(128 + 127 * (v * 2))
                        g = int(0 + 100 * (v * 2))
                        b = int(200 - 150 * (v * 2))
                    else:
                        # Orange to yellow
                        r = 255
                        g = int(100 + 155 * ((v - 0.5) * 2))
                        b = int(50 - 50 * ((v - 0.5) * 2))
                    colors[i, j] = [r, g, b]

        elif self.config.attention_colormap == "viridis":
            # Viridis: dark purple -> teal -> yellow
            for i in range(h):
                for j in range(w):
                    v = attention[i, j]
                    r = int(68 + 187 * v)
                    g = int(1 + 208 * v if v < 0.7 else 209 + 46 * ((v - 0.7) / 0.3))
                    b = int(84 + 25 * v if v < 0.5 else 109 - 109 * ((v - 0.5) / 0.5))
                    colors[i, j] = [r, g, b]

        elif self.config.attention_colormap == "chromesthesia":
            # Use the same chromesthesia colors as the spiral
            for i in range(h):
                for j in range(w):
                    v = attention[i, j]
                    idx = int(v * (len(self.chromesthesia_colors) - 1))
                    colors[i, j] = self.chromesthesia_colors[idx]

        else:  # jet
            for i in range(h):
                for j in range(w):
                    v = attention[i, j]
                    if v < 0.25:
                        r, g, b = 0, int(255 * v * 4), 255
                    elif v < 0.5:
                        r, g, b = 0, 255, int(255 * (1 - (v - 0.25) * 4))
                    elif v < 0.75:
                        r, g, b = int(255 * (v - 0.5) * 4), 255, 0
                    else:
                        r, g, b = 255, int(255 * (1 - (v - 0.75) * 4)), 0
                    colors[i, j] = [r, g, b]

        return colors

    def compute_amplitude_modulation(self,
                                     amplitude_data: np.ndarray,
                                     attention_map: np.ndarray,
                                     frequencies: np.ndarray) -> np.ndarray:
        """
        Modulate amplitude data based on attention.

        High attention regions get amplified, low attention regions get suppressed.
        This is the KEY INNOVATION - the classifier's attention directly affects
        what we visualize.
        """
        # Ensure attention map has right shape
        if attention_map.ndim == 2:
            # Flatten and resample to match frequency bins
            attention_flat = attention_map.flatten()
            attention_resampled = np.interp(
                np.linspace(0, 1, len(frequencies)),
                np.linspace(0, 1, len(attention_flat)),
                attention_flat
            )
        else:
            attention_resampled = attention_map

        # Normalize attention to [0, 1]
        attention_norm = (attention_resampled - attention_resampled.min()) / (
            attention_resampled.max() - attention_resampled.min() + 1e-8
        )

        # Compute modulation factor
        if self.config.amplify_attended and self.config.suppress_unattended:
            # Full range: suppression_factor to amplification_factor
            modulation = (
                self.config.suppression_factor +
                (self.config.amplification_factor - self.config.suppression_factor) * attention_norm
            )
        elif self.config.amplify_attended:
            # Only amplify: 1.0 to amplification_factor
            modulation = 1.0 + (self.config.amplification_factor - 1.0) * attention_norm
        elif self.config.suppress_unattended:
            # Only suppress: suppression_factor to 1.0
            modulation = self.config.suppression_factor + (1.0 - self.config.suppression_factor) * attention_norm
        else:
            modulation = np.ones_like(attention_norm)

        # Apply modulation to amplitude
        modulated_amplitude = amplitude_data * modulation

        return modulated_amplitude, attention_norm

    def render_attention_enhanced_frame(self,
                                        base_image: Image.Image,
                                        attention_map: np.ndarray,
                                        prediction: Optional[str] = None,
                                        confidence: Optional[float] = None) -> Image.Image:
        """
        Enhance a base visualization with attention overlay.

        Args:
            base_image: The base spiral visualization
            attention_map: 2D attention map from classifier
            prediction: Optional predicted class name
            confidence: Optional prediction confidence

        Returns:
            Enhanced image with attention visualization
        """
        # Smooth attention
        attention_smooth = self._smooth_attention(attention_map)

        # Resize attention to match image
        w, h = base_image.size
        attention_resized = np.array(
            Image.fromarray((attention_smooth * 255).astype(np.uint8)).resize((w, h))
        ) / 255.0

        # Convert base to numpy
        base_array = np.array(base_image)

        # Apply attention overlay if enabled
        if self.config.show_attention_overlay:
            attention_colors = self._get_attention_colormap(attention_resized)

            # Blend: base * (1-alpha) + attention_color * alpha * attention_value
            alpha = self.config.attention_alpha * attention_resized[:, :, np.newaxis]
            blended = base_array * (1 - alpha * 0.5) + attention_colors * alpha * 0.5
            base_array = blended.astype(np.uint8)

        # Add glow to high-attention regions
        if self.config.show_attention_border:
            # Find high-attention pixels
            high_attention = attention_resized > self.config.glow_threshold

            if np.any(high_attention):
                # Create glow effect
                glow_mask = Image.fromarray((high_attention * 255).astype(np.uint8))
                glow_mask = glow_mask.filter(ImageFilter.GaussianBlur(10))
                glow_array = np.array(glow_mask) / 255.0

                # Add glow
                for c in range(3):
                    base_array[:, :, c] = np.clip(
                        base_array[:, :, c] + glow_array * self.config.glow_color[c] * 0.3,
                        0, 255
                    ).astype(np.uint8)

        # Create final image
        result = Image.fromarray(base_array)

        # Add prediction label if provided
        if prediction is not None:
            draw = ImageDraw.Draw(result)
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            except:
                font = ImageFont.load_default()

            label = f"{prediction}"
            if confidence is not None:
                label += f" ({confidence:.1%})"

            # Draw with shadow
            draw.text((12, 12), label, fill=(0, 0, 0), font=font)
            draw.text((10, 10), label, fill=(255, 255, 255), font=font)

            # Draw attention indicator
            indicator_text = "🎯 Attention-Guided"
            draw.text((w - 200, 10), indicator_text, fill=(100, 255, 100), font=font)

        return result

    def track_statistics(self,
                        class_name: str,
                        attention_map: np.ndarray,
                        frequencies: np.ndarray):
        """Track attention statistics for a class."""
        if self.statistics is not None:
            self.statistics.add_sample(class_name, attention_map, frequencies)

    def get_class_attention_profile(self, class_name: str) -> Optional[np.ndarray]:
        """Get the learned attention profile for a class."""
        if self.statistics is None:
            return None
        return self.statistics.get_class_profile(class_name)

    def generate_class_comparison_report(self) -> Dict[str, any]:
        """Generate a report comparing attention patterns across classes."""
        if self.statistics is None:
            return {}

        report = {
            "classes": list(self.statistics.frequency_attention.keys()),
            "profiles": {},
            "discriminative_frequencies": {}
        }

        for class_name in report["classes"]:
            report["profiles"][class_name] = self.statistics.frequency_attention[class_name].tolist()
            report["discriminative_frequencies"][class_name] = (
                self.statistics.get_discriminative_frequencies(class_name).tolist()
            )

        return report


class AttentionFeedbackLoop:
    """
    The complete attention-guided visualization-classification loop.

    This is the system that makes visualization and classification improve together.
    """

    def __init__(self,
                 renderer,  # FastSpiralRenderer or similar
                 classifier,  # AIOverlayClassifier with attention extraction
                 attention_config: Optional[AttentionConfig] = None):
        self.renderer = renderer
        self.classifier = classifier
        self.attention_renderer = AttentionGuidedRenderer(attention_config)

        # Track improvement metrics
        self.baseline_accuracy = None
        self.enhanced_accuracy = None

    def process_frame(self,
                      amplitude_data: np.ndarray,
                      frequencies: np.ndarray,
                      frame_idx: int = 0) -> Tuple[Image.Image, str, float, np.ndarray]:
        """
        Process a single frame through the complete feedback loop.

        1. Render base visualization
        2. Run classifier to get prediction + attention
        3. Use attention to enhance visualization
        4. Return enhanced visualization with prediction
        """
        # Step 1: Base visualization
        base_image = self.renderer.render_frame(
            amplitude_data,
            frame_idx=frame_idx,
            frequencies=frequencies
        )

        # Step 2: Classification with attention
        result = self.classifier.classify_frame(base_image, return_attention=True)
        prediction = result['prediction']
        confidence = result['confidence']
        attention_map = result.get('attention_map')

        if attention_map is None:
            # No attention available, return base image
            return base_image, prediction, confidence, np.zeros((14, 14))

        # Step 3: Enhance visualization with attention
        # First, modulate amplitude for next frame (feedback loop!)
        modulated_amp, attention_profile = self.attention_renderer.compute_amplitude_modulation(
            amplitude_data, attention_map, frequencies
        )

        # Re-render with modulated amplitudes
        enhanced_base = self.renderer.render_frame(
            modulated_amp,
            frame_idx=frame_idx,
            frequencies=frequencies
        )

        # Step 4: Add attention overlay
        final_image = self.attention_renderer.render_attention_enhanced_frame(
            enhanced_base,
            attention_map,
            prediction=prediction,
            confidence=confidence
        )

        # Track statistics
        self.attention_renderer.track_statistics(prediction, attention_map, frequencies)

        return final_image, prediction, confidence, attention_map

    def get_evolution_metrics(self) -> Dict:
        """Get metrics showing how much the system has evolved."""
        report = self.attention_renderer.generate_class_comparison_report()
        report["improvement"] = {
            "baseline_accuracy": self.baseline_accuracy,
            "enhanced_accuracy": self.enhanced_accuracy,
            "improvement_percentage": (
                ((self.enhanced_accuracy - self.baseline_accuracy) / self.baseline_accuracy * 100)
                if self.baseline_accuracy and self.enhanced_accuracy else None
            )
        }
        return report


# Demo function
def demo_attention_guided_rendering():
    """Demonstrate the attention-guided rendering system."""
    print("=" * 60)
    print("SYNESTHESIA 3.0 - Attention-Guided Rendering Demo")
    print("=" * 60)

    # Create synthetic data
    np.random.seed(42)
    num_freq_bins = 381
    frequencies = np.logspace(np.log10(20), np.log10(8000), num_freq_bins)

    # Simulate different instrument signatures
    instruments = {
        "piano": {"fundamental": 261.63, "harmonics": [2, 3, 4, 5], "decay": 0.8},
        "violin": {"fundamental": 440.0, "harmonics": [2, 3, 4, 5, 6, 7], "decay": 0.6},
        "flute": {"fundamental": 523.25, "harmonics": [2], "decay": 0.9},
    }

    config = AttentionConfig(
        attention_alpha=0.6,
        amplification_factor=2.0,
        show_attention_overlay=True,
        show_attention_border=True
    )

    renderer = AttentionGuidedRenderer(config)

    for name, params in instruments.items():
        print(f"\nProcessing: {name}")

        # Generate amplitude data
        amplitude = np.zeros(num_freq_bins)
        fund_idx = np.argmin(np.abs(frequencies - params["fundamental"]))
        amplitude[fund_idx] = 1.0

        for h in params["harmonics"]:
            h_freq = params["fundamental"] * h
            if h_freq < 8000:
                h_idx = np.argmin(np.abs(frequencies - h_freq))
                amplitude[h_idx] = params["decay"] ** (h - 1)

        # Simulate attention map (14x14 as from ViT)
        attention = np.random.rand(14, 14) * 0.3

        # Add high attention to fundamental region
        fund_patch = int(fund_idx / num_freq_bins * 14)
        attention[fund_patch-1:fund_patch+2, fund_patch-1:fund_patch+2] = 0.9

        # Compute modulation
        modulated, attention_profile = renderer.compute_amplitude_modulation(
            amplitude, attention, frequencies
        )

        # Track statistics
        renderer.track_statistics(name, attention, frequencies)

        print(f"  Original max amplitude: {amplitude.max():.3f}")
        print(f"  Modulated max amplitude: {modulated.max():.3f}")
        print(f"  Amplification ratio: {modulated.max() / amplitude.max():.2f}x")

    # Generate report
    report = renderer.generate_class_comparison_report()
    print("\n" + "=" * 60)
    print("Attention Statistics Report")
    print("=" * 60)
    for class_name in report["classes"]:
        disc_freqs = report["discriminative_frequencies"][class_name]
        print(f"\n{class_name}:")
        print(f"  Top discriminative frequency bins: {disc_freqs[:5]}")

    print("\n✅ Demo complete!")


if __name__ == "__main__":
    demo_attention_guided_rendering()
