"""
SYNESTHESIA 2.0 - AI Classification Overlay (Phase 2)

Adds intelligent overlays to visualization frames:
- Instrument classification with confidence
- Genre detection
- Attention map visualization showing which spiral regions drive classification
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict
import os
from PIL import Image, ImageDraw, ImageFont
import colorsys

# Deep learning imports
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torchvision import transforms
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    import timm
    HAS_TIMM = True
except ImportError:
    HAS_TIMM = False


@dataclass
class OverlayConfig:
    """Configuration for AI overlay rendering."""
    # Classification display
    show_instrument: bool = True
    show_confidence: bool = True
    show_genre: bool = True

    # Attention visualization
    show_attention: bool = True
    attention_opacity: float = 0.4
    attention_colormap: str = "jet"  # jet, viridis, plasma

    # Label styling
    label_font_size: int = 32
    label_color: Tuple[int, int, int] = (255, 255, 255)
    label_bg_color: Tuple[int, int, int, int] = (0, 0, 0, 180)
    label_position: str = "top-left"  # top-left, top-right, bottom-left, bottom-right

    # Confidence bar
    confidence_bar_width: int = 200
    confidence_bar_height: int = 20


# Instrument classes (matching training data)
INSTRUMENT_CLASSES = [
    "piano", "guitar", "violin", "drums", "flute",
    "trumpet", "saxophone", "cello", "clarinet", "bass"
]

# Genre classes
GENRE_CLASSES = [
    "classical", "jazz", "rock", "electronic", "folk",
    "world", "ambient", "pop", "metal", "blues"
]


class ViTAttentionExtractor(nn.Module):
    """
    Vision Transformer with attention extraction capability.
    Wraps a ViT model to expose attention maps.
    """

    def __init__(self, num_classes: int = 10, model_name: str = "vit_base_patch16_224"):
        super().__init__()

        if not HAS_TIMM:
            raise ImportError("timm required for ViT. Install: pip install timm")

        self.backbone = timm.create_model(model_name, pretrained=True, num_classes=0)
        self.feature_dim = self.backbone.num_features
        self.classifier = nn.Linear(self.feature_dim, num_classes)

        # Store attention weights
        self.attention_weights = []
        self._register_hooks()

    def _register_hooks(self):
        """Register forward hooks to capture attention weights."""

        def hook_fn(module, input, output):
            # ViT attention returns (attn_output, attn_weights)
            if hasattr(module, 'attn_drop'):
                # Get attention weights before dropout
                self.attention_weights.append(output)

        # Register hooks on all attention layers
        for name, module in self.backbone.named_modules():
            if 'attn' in name and isinstance(module, nn.Module):
                if hasattr(module, 'softmax'):
                    module.register_forward_hook(hook_fn)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, List[torch.Tensor]]:
        """
        Forward pass with attention extraction.

        Returns:
            logits: Classification logits
            attention_maps: List of attention maps from each layer
        """
        self.attention_weights = []
        features = self.backbone(x)
        logits = self.classifier(features)
        return logits, self.attention_weights

    def get_attention_map(self, attention_weights: List[torch.Tensor],
                          method: str = "rollout") -> np.ndarray:
        """
        Compute attention map from layer-wise attention weights.

        Args:
            attention_weights: List of attention tensors from each layer
            method: "rollout" (multiply through layers) or "last" (use last layer only)

        Returns:
            attention_map: [H, W] normalized attention map
        """
        if not attention_weights:
            return None

        if method == "last":
            # Use only the last layer's attention
            attn = attention_weights[-1]
            # Average over heads, exclude CLS token
            attn_map = attn.mean(dim=1)[0, 0, 1:]  # [num_patches]

        elif method == "rollout":
            # Attention rollout: multiply attention matrices
            result = torch.eye(attention_weights[0].shape[-1]).to(attention_weights[0].device)

            for attn in attention_weights:
                # Average over heads
                attn_heads_fused = attn.mean(dim=1)
                # Add identity (residual connection)
                attn_heads_fused = attn_heads_fused + torch.eye(attn_heads_fused.shape[-1]).to(attn.device)
                # Normalize
                attn_heads_fused = attn_heads_fused / attn_heads_fused.sum(dim=-1, keepdim=True)
                # Multiply
                result = torch.matmul(result, attn_heads_fused)

            # Get attention to CLS token, excluding CLS itself
            attn_map = result[0, 0, 1:]

        # Reshape to 2D (assuming 14x14 patches for 224x224 input)
        num_patches = int(np.sqrt(attn_map.shape[0]))
        attn_map = attn_map.reshape(num_patches, num_patches)

        # Normalize to [0, 1]
        attn_map = attn_map.cpu().numpy()
        attn_map = (attn_map - attn_map.min()) / (attn_map.max() - attn_map.min() + 1e-8)

        return attn_map


class AIOverlayClassifier:
    """
    AI classifier for adding intelligent overlays to SYNESTHESIA frames.
    """

    def __init__(self,
                 instrument_model_path: Optional[str] = None,
                 genre_model_path: Optional[str] = None,
                 config: Optional[OverlayConfig] = None):

        self.config = config or OverlayConfig()

        if not HAS_TORCH:
            raise ImportError("PyTorch required. Install: pip install torch torchvision")

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"AI Overlay using device: {self.device}")

        # Image preprocessing
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])

        # Load models
        self.instrument_model = self._load_model(
            instrument_model_path, len(INSTRUMENT_CLASSES)
        ) if instrument_model_path else None

        self.genre_model = self._load_model(
            genre_model_path, len(GENRE_CLASSES)
        ) if genre_model_path else None

        # Smoothing for temporal consistency
        self.prediction_history = []
        self.history_length = 10

    def _load_model(self, model_path: str, num_classes: int) -> ViTAttentionExtractor:
        """Load a trained model."""
        model = ViTAttentionExtractor(num_classes=num_classes)

        if os.path.exists(model_path):
            checkpoint = torch.load(model_path, map_location=self.device)
            if 'model_state_dict' in checkpoint:
                model.load_state_dict(checkpoint['model_state_dict'])
            else:
                model.load_state_dict(checkpoint)
            print(f"Loaded model from {model_path}")
        else:
            print(f"Warning: Model not found at {model_path}, using pretrained weights")

        model.to(self.device)
        model.eval()
        return model

    def classify_frame(self, frame: np.ndarray) -> Dict:
        """
        Classify a visualization frame.

        Args:
            frame: [H, W, 3] RGB image array

        Returns:
            Dictionary with classification results and attention map
        """
        # Convert to PIL and preprocess
        pil_image = Image.fromarray(frame)
        input_tensor = self.transform(pil_image).unsqueeze(0).to(self.device)

        results = {
            "instrument": None,
            "instrument_confidence": 0.0,
            "instrument_probs": None,
            "genre": None,
            "genre_confidence": 0.0,
            "attention_map": None
        }

        with torch.no_grad():
            # Instrument classification
            if self.instrument_model is not None:
                logits, attn_weights = self.instrument_model(input_tensor)
                probs = F.softmax(logits, dim=1)[0]

                pred_idx = probs.argmax().item()
                results["instrument"] = INSTRUMENT_CLASSES[pred_idx]
                results["instrument_confidence"] = probs[pred_idx].item()
                results["instrument_probs"] = {
                    cls: probs[i].item()
                    for i, cls in enumerate(INSTRUMENT_CLASSES)
                }

                # Get attention map
                if attn_weights:
                    results["attention_map"] = self.instrument_model.get_attention_map(
                        attn_weights, method="rollout"
                    )

            # Genre classification
            if self.genre_model is not None:
                logits, _ = self.genre_model(input_tensor)
                probs = F.softmax(logits, dim=1)[0]

                pred_idx = probs.argmax().item()
                results["genre"] = GENRE_CLASSES[pred_idx]
                results["genre_confidence"] = probs[pred_idx].item()

        # Temporal smoothing
        results = self._smooth_predictions(results)

        return results

    def _smooth_predictions(self, results: Dict) -> Dict:
        """Apply temporal smoothing for more stable predictions."""
        self.prediction_history.append(results)
        if len(self.prediction_history) > self.history_length:
            self.prediction_history.pop(0)

        # Only smooth if we have enough history
        if len(self.prediction_history) < 3:
            return results

        # Average confidence over history
        if results["instrument_probs"] is not None:
            smoothed_probs = {}
            for cls in INSTRUMENT_CLASSES:
                probs = [h["instrument_probs"][cls]
                         for h in self.prediction_history
                         if h["instrument_probs"] is not None]
                smoothed_probs[cls] = np.mean(probs) if probs else 0

            best_cls = max(smoothed_probs, key=smoothed_probs.get)
            results["instrument"] = best_cls
            results["instrument_confidence"] = smoothed_probs[best_cls]

        return results

    def render_overlay(self,
                       frame: np.ndarray,
                       classification: Dict) -> np.ndarray:
        """
        Render classification overlay on frame.

        Args:
            frame: Original frame [H, W, 3]
            classification: Results from classify_frame()

        Returns:
            Frame with overlay [H, W, 3]
        """
        # Convert to PIL for drawing
        pil_image = Image.fromarray(frame)
        draw = ImageDraw.Draw(pil_image, 'RGBA')

        # Load font
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                                      self.config.label_font_size)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                                            self.config.label_font_size - 8)
        except:
            font = ImageFont.load_default()
            small_font = font

        h, w = frame.shape[:2]

        # Calculate position
        if "top" in self.config.label_position:
            y_start = 20
        else:
            y_start = h - 150

        if "left" in self.config.label_position:
            x_start = 20
        else:
            x_start = w - 300

        y_offset = 0

        # Draw instrument label
        if self.config.show_instrument and classification["instrument"]:
            label = classification["instrument"].upper()
            conf = classification["instrument_confidence"]

            # Background box
            bbox = draw.textbbox((x_start, y_start + y_offset), label, font=font)
            padding = 10
            draw.rectangle([
                bbox[0] - padding, bbox[1] - padding,
                bbox[2] + padding + 100, bbox[3] + padding
            ], fill=self.config.label_bg_color)

            # Label text
            draw.text((x_start, y_start + y_offset), label,
                      fill=self.config.label_color, font=font)

            y_offset += 50

            # Confidence bar
            if self.config.show_confidence:
                bar_x = x_start
                bar_y = y_start + y_offset

                # Background
                draw.rectangle([bar_x, bar_y,
                                bar_x + self.config.confidence_bar_width,
                                bar_y + self.config.confidence_bar_height],
                               fill=(50, 50, 50, 200))

                # Filled portion
                fill_width = int(self.config.confidence_bar_width * conf)
                color = self._confidence_to_color(conf)
                draw.rectangle([bar_x, bar_y,
                                bar_x + fill_width,
                                bar_y + self.config.confidence_bar_height],
                               fill=color)

                # Percentage text
                conf_text = f"{conf * 100:.1f}%"
                draw.text((bar_x + self.config.confidence_bar_width + 10, bar_y),
                          conf_text, fill=self.config.label_color, font=small_font)

                y_offset += 40

        # Draw genre label
        if self.config.show_genre and classification["genre"]:
            genre_label = f"Genre: {classification['genre']}"
            draw.text((x_start, y_start + y_offset), genre_label,
                      fill=(200, 200, 200), font=small_font)

        # Draw attention map overlay
        if self.config.show_attention and classification["attention_map"] is not None:
            frame_with_attention = self._overlay_attention(
                np.array(pil_image),
                classification["attention_map"]
            )
            return frame_with_attention

        return np.array(pil_image)

    def _confidence_to_color(self, confidence: float) -> Tuple[int, int, int, int]:
        """Convert confidence to color (red -> yellow -> green)."""
        if confidence < 0.5:
            # Red to yellow
            r = 255
            g = int(255 * (confidence * 2))
        else:
            # Yellow to green
            r = int(255 * (1 - (confidence - 0.5) * 2))
            g = 255

        return (r, g, 50, 255)

    def _overlay_attention(self,
                           frame: np.ndarray,
                           attention_map: np.ndarray) -> np.ndarray:
        """
        Overlay attention heatmap on frame.
        """
        h, w = frame.shape[:2]

        # Resize attention map to frame size
        from scipy.ndimage import zoom
        scale_h = h / attention_map.shape[0]
        scale_w = w / attention_map.shape[1]
        attention_resized = zoom(attention_map, (scale_h, scale_w), order=1)

        # Apply colormap
        if self.config.attention_colormap == "jet":
            cmap = plt.cm.jet
        elif self.config.attention_colormap == "viridis":
            cmap = plt.cm.viridis
        else:
            cmap = plt.cm.plasma

        import matplotlib.pyplot as plt
        attention_colored = (cmap(attention_resized)[:, :, :3] * 255).astype(np.uint8)

        # Blend with original frame
        alpha = self.config.attention_opacity
        blended = (1 - alpha) * frame + alpha * attention_colored
        blended = np.clip(blended, 0, 255).astype(np.uint8)

        return blended


def demo_overlay():
    """Demo the AI overlay with a test image."""
    # Create synthetic test frame
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)

    # Add some spiral-like patterns
    for i in range(100):
        angle = i * 0.3
        r = 50 + i * 3
        x = int(640 + r * np.cos(angle))
        y = int(360 + r * np.sin(angle))

        if 0 <= x < 1280 and 0 <= y < 720:
            color = colorsys.hsv_to_rgb(i / 100, 0.8, 0.9)
            frame[max(0, y - 5):min(720, y + 5),
            max(0, x - 5):min(1280, x + 5)] = [int(c * 255) for c in color]

    # Simulate classification results
    fake_results = {
        "instrument": "piano",
        "instrument_confidence": 0.87,
        "instrument_probs": {cls: 0.1 for cls in INSTRUMENT_CLASSES},
        "genre": "classical",
        "genre_confidence": 0.72,
        "attention_map": np.random.random((14, 14))  # Fake attention
    }
    fake_results["instrument_probs"]["piano"] = 0.87

    # Create overlay (without model)
    config = OverlayConfig()
    overlay = AIOverlayClassifier.__new__(AIOverlayClassifier)
    overlay.config = config

    result = overlay.render_overlay(frame, fake_results)

    # Save
    Image.fromarray(result).save("demo_ai_overlay.png")
    print("Demo overlay saved to demo_ai_overlay.png")

    return result


if __name__ == "__main__":
    demo_overlay()
