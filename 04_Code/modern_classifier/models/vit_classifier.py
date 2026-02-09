"""
Vision Transformer (ViT) classifier for spiral visualizations.

ViT treats images as sequences of patches and applies transformer
attention to capture global patterns - ideal for your spiral visualizations
where frequency information is distributed across the entire image.
"""

import torch
import torch.nn as nn
from typing import Optional, Tuple

try:
    import timm
    TIMM_AVAILABLE = True
except ImportError:
    TIMM_AVAILABLE = False
    print("Warning: timm not installed. Run: pip install timm")


class ViTClassifier(nn.Module):
    """
    Vision Transformer classifier with optional attention visualization.

    Uses pre-trained ViT from timm library and adds custom classification head.
    """

    def __init__(
        self,
        num_classes: int = 10,
        model_name: str = "vit_base_patch16_224",
        pretrained: bool = True,
        dropout: float = 0.1,
        freeze_backbone: bool = False
    ):
        """
        Args:
            num_classes: Number of output classes (instruments)
            model_name: timm model name for ViT variant
            pretrained: Use ImageNet pre-trained weights
            dropout: Dropout rate for classification head
            freeze_backbone: Freeze backbone weights (only train head)
        """
        super().__init__()

        if not TIMM_AVAILABLE:
            raise ImportError("timm is required for ViT. Install with: pip install timm")

        # Load pre-trained ViT
        self.backbone = timm.create_model(
            model_name,
            pretrained=pretrained,
            num_classes=0  # Remove classification head
        )

        # Get feature dimension
        self.feature_dim = self.backbone.num_features

        # Custom classification head
        self.classifier = nn.Sequential(
            nn.LayerNorm(self.feature_dim),
            nn.Dropout(dropout),
            nn.Linear(self.feature_dim, num_classes)
        )

        # Optionally freeze backbone
        if freeze_backbone:
            for param in self.backbone.parameters():
                param.requires_grad = False

        # Store config for later
        self.num_classes = num_classes
        self.model_name = model_name

    def forward(
        self,
        x: torch.Tensor,
        return_attention: bool = False
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        Forward pass.

        Args:
            x: Input images (B, C, H, W)
            return_attention: If True, also return attention weights

        Returns:
            logits: Classification logits (B, num_classes)
            attention: Attention weights if return_attention=True
        """
        # Extract features
        features = self.backbone(x)

        # Classify
        logits = self.classifier(features)

        if return_attention:
            # Get attention from last block
            attention = self._get_attention(x)
            return logits, attention

        return logits

    def _get_attention(self, x: torch.Tensor) -> torch.Tensor:
        """
        Extract attention weights for visualization.

        Returns attention map from the last transformer block.
        """
        # This requires hook-based extraction
        # Simplified version - full implementation would use forward hooks
        attention_weights = None

        # Register hook to capture attention
        def attention_hook(module, input, output):
            nonlocal attention_weights
            # For ViT, attention is in the Attention module
            if hasattr(module, 'attn_drop'):
                attention_weights = output

        # Get last attention block
        if hasattr(self.backbone, 'blocks'):
            last_block = self.backbone.blocks[-1]
            if hasattr(last_block, 'attn'):
                hook = last_block.attn.register_forward_hook(attention_hook)
                _ = self.backbone(x)
                hook.remove()

        return attention_weights

    def get_attention_maps(self, x: torch.Tensor) -> torch.Tensor:
        """
        Get attention maps for visualization.

        Returns:
            attention_maps: (B, num_heads, num_patches, num_patches)
        """
        B = x.shape[0]
        attention_maps = []

        def hook_fn(module, input, output):
            # output is (B, num_heads, N, N) for attention
            attention_maps.append(output)

        hooks = []
        for block in self.backbone.blocks:
            if hasattr(block, 'attn'):
                hook = block.attn.attn_drop.register_forward_hook(hook_fn)
                hooks.append(hook)

        # Forward pass to collect attention
        with torch.no_grad():
            _ = self.backbone(x)

        # Remove hooks
        for hook in hooks:
            hook.remove()

        if attention_maps:
            # Return last layer's attention
            return attention_maps[-1]

        return None


class ViTClassifierSmall(ViTClassifier):
    """Smaller ViT variant for limited GPU memory."""

    def __init__(self, num_classes: int = 10, pretrained: bool = True, **kwargs):
        super().__init__(
            num_classes=num_classes,
            model_name="vit_small_patch16_224",
            pretrained=pretrained,
            **kwargs
        )


class ViTClassifierTiny(ViTClassifier):
    """Tiny ViT variant for very limited resources."""

    def __init__(self, num_classes: int = 10, pretrained: bool = True, **kwargs):
        super().__init__(
            num_classes=num_classes,
            model_name="vit_tiny_patch16_224",
            pretrained=pretrained,
            **kwargs
        )


def create_vit_model(
    num_classes: int = 10,
    model_size: str = "base",
    pretrained: bool = True,
    dropout: float = 0.1,
    freeze_backbone: bool = False
) -> ViTClassifier:
    """
    Factory function to create ViT classifier.

    Args:
        num_classes: Number of output classes
        model_size: "tiny", "small", or "base"
        pretrained: Use pre-trained weights
        dropout: Dropout rate
        freeze_backbone: Freeze backbone weights

    Returns:
        ViT classifier model
    """
    model_names = {
        "tiny": "vit_tiny_patch16_224",
        "small": "vit_small_patch16_224",
        "base": "vit_base_patch16_224"
    }

    if model_size not in model_names:
        raise ValueError(f"model_size must be one of {list(model_names.keys())}")

    return ViTClassifier(
        num_classes=num_classes,
        model_name=model_names[model_size],
        pretrained=pretrained,
        dropout=dropout,
        freeze_backbone=freeze_backbone
    )


def visualize_attention(
    model: ViTClassifier,
    image: torch.Tensor,
    save_path: Optional[str] = None
) -> torch.Tensor:
    """
    Visualize attention maps for a given image.

    Args:
        model: ViT classifier
        image: Input image (1, C, H, W) or (C, H, W)
        save_path: Optional path to save visualization

    Returns:
        Attention heatmap
    """
    import matplotlib.pyplot as plt
    import numpy as np

    model.eval()

    # Ensure batch dimension
    if image.dim() == 3:
        image = image.unsqueeze(0)

    # Get attention maps
    attention = model.get_attention_maps(image)

    if attention is None:
        print("Could not extract attention maps")
        return None

    # Average over heads and get CLS token attention
    # attention shape: (B, num_heads, num_patches+1, num_patches+1)
    # CLS token is at position 0
    attn_weights = attention[0].mean(dim=0)  # Average over heads
    cls_attention = attn_weights[0, 1:]  # CLS token attention to patches

    # Reshape to 2D grid
    num_patches = int(np.sqrt(cls_attention.shape[0]))
    attention_map = cls_attention.reshape(num_patches, num_patches)
    attention_map = attention_map.cpu().numpy()

    # Resize to original image size
    from scipy.ndimage import zoom
    scale = 224 // num_patches
    attention_map = zoom(attention_map, scale, order=1)

    if save_path:
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        # Original image
        img_np = image[0].permute(1, 2, 0).cpu().numpy()
        # Denormalize
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        img_np = img_np * std + mean
        img_np = np.clip(img_np, 0, 1)

        axes[0].imshow(img_np)
        axes[0].set_title("Original Image")
        axes[0].axis('off')

        # Attention map
        axes[1].imshow(attention_map, cmap='hot')
        axes[1].set_title("Attention Map")
        axes[1].axis('off')

        # Overlay
        axes[2].imshow(img_np)
        axes[2].imshow(attention_map, cmap='hot', alpha=0.5)
        axes[2].set_title("Overlay")
        axes[2].axis('off')

        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

    return torch.from_numpy(attention_map)


if __name__ == "__main__":
    # Test the model
    print("Testing ViT Classifier...")

    # Create model
    model = create_vit_model(num_classes=10, model_size="small")
    print(f"Model created: {model.model_name}")
    print(f"Feature dimension: {model.feature_dim}")

    # Test forward pass
    dummy_input = torch.randn(2, 3, 224, 224)
    output = model(dummy_input)
    print(f"Output shape: {output.shape}")  # Should be (2, 10)

    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Total parameters: {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")
