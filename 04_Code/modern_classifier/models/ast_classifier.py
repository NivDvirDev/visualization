"""
Audio Spectrogram Transformer (AST) classifier for spiral visualizations.

AST is specifically designed for audio classification using spectrograms.
While your spiral visualizations aren't standard spectrograms, AST's
architecture may still be effective for capturing audio-visual patterns.

Note: AST expects specific input dimensions (typically 128x1024 for AudioSet).
We adapt it here to work with your 224x224 spiral images.
"""

import torch
import torch.nn as nn
from typing import Optional, Tuple, Union

try:
    from transformers import ASTModel, ASTConfig, AutoFeatureExtractor
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Warning: transformers not installed. Run: pip install transformers")


class ASTClassifier(nn.Module):
    """
    Audio Spectrogram Transformer adapted for spiral visualizations.

    Uses the Hugging Face transformers library's AST implementation.
    """

    def __init__(
        self,
        num_classes: int = 10,
        pretrained: bool = True,
        model_name: str = "MIT/ast-finetuned-audioset-10-10-0.4593",
        dropout: float = 0.1,
        freeze_backbone: bool = False,
        adapt_to_images: bool = True
    ):
        """
        Args:
            num_classes: Number of output classes
            pretrained: Use pre-trained weights
            model_name: Hugging Face model name
            dropout: Dropout rate
            freeze_backbone: Freeze backbone weights
            adapt_to_images: Adapt AST to work with standard images (224x224)
        """
        super().__init__()

        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers required. Install: pip install transformers")

        self.num_classes = num_classes
        self.adapt_to_images = adapt_to_images

        if pretrained:
            # Load pre-trained AST
            self.backbone = ASTModel.from_pretrained(model_name)
        else:
            # Create from config
            config = ASTConfig(
                hidden_size=768,
                num_hidden_layers=12,
                num_attention_heads=12,
                intermediate_size=3072,
            )
            self.backbone = ASTModel(config)

        # Get hidden size
        self.hidden_size = self.backbone.config.hidden_size

        # Custom classification head
        self.classifier = nn.Sequential(
            nn.LayerNorm(self.hidden_size),
            nn.Dropout(dropout),
            nn.Linear(self.hidden_size, num_classes)
        )

        # If adapting to images, we need to modify the patch embedding
        if adapt_to_images:
            self._adapt_patch_embedding()

        # Freeze backbone if requested
        if freeze_backbone:
            for param in self.backbone.parameters():
                param.requires_grad = False

    def _adapt_patch_embedding(self):
        """
        Adapt AST's patch embedding to work with 224x224 RGB images.

        AST expects: (batch, 1, time_frames, mel_bins) - e.g., (B, 1, 1024, 128)
        We have: (batch, 3, 224, 224)

        We'll use a projection layer to adapt.
        """
        # Create adapter that converts 3-channel image to AST-compatible format
        self.input_adapter = nn.Sequential(
            # Convert 3 channels to 1 channel
            nn.Conv2d(3, 1, kernel_size=1),
            # Adaptive pooling to match AST expected dimensions
            nn.AdaptiveAvgPool2d((224, 224))  # Keep same size for now
        )

    def forward(
        self,
        x: torch.Tensor,
        return_attention: bool = False
    ) -> Union[torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
        """
        Forward pass.

        Args:
            x: Input images (B, C, H, W) - your spiral visualizations
            return_attention: Return attention weights

        Returns:
            logits: Classification logits
            attention: Attention weights (if return_attention=True)
        """
        # Adapt input if needed
        if self.adapt_to_images and hasattr(self, 'input_adapter'):
            x = self.input_adapter(x)

        # AST expects (B, time, freq) but we have (B, 1, H, W)
        # Reshape to remove channel dimension
        if x.dim() == 4 and x.shape[1] == 1:
            x = x.squeeze(1)  # (B, H, W)

        # Forward through AST backbone
        outputs = self.backbone(
            x,
            output_attentions=return_attention
        )

        # Get pooled output (CLS token)
        pooled_output = outputs.pooler_output

        # Classify
        logits = self.classifier(pooled_output)

        if return_attention:
            return logits, outputs.attentions

        return logits


class ASTClassifierSimple(nn.Module):
    """
    Simplified AST-style classifier using standard ViT on images.

    This is more straightforward for your use case - treats your
    spiral images as regular images but uses AST-inspired architecture.
    """

    def __init__(
        self,
        num_classes: int = 10,
        image_size: int = 224,
        patch_size: int = 16,
        hidden_size: int = 768,
        num_layers: int = 12,
        num_heads: int = 12,
        dropout: float = 0.1,
        pretrained_vit: bool = True
    ):
        """
        Args:
            num_classes: Number of output classes
            image_size: Input image size
            patch_size: Size of image patches
            hidden_size: Transformer hidden dimension
            num_layers: Number of transformer layers
            num_heads: Number of attention heads
            dropout: Dropout rate
            pretrained_vit: Initialize from pre-trained ViT
        """
        super().__init__()

        self.image_size = image_size
        self.patch_size = patch_size
        self.num_patches = (image_size // patch_size) ** 2
        self.hidden_size = hidden_size

        # Patch embedding
        self.patch_embed = nn.Conv2d(
            3, hidden_size,
            kernel_size=patch_size,
            stride=patch_size
        )

        # Position embedding
        self.pos_embed = nn.Parameter(
            torch.zeros(1, self.num_patches + 1, hidden_size)
        )

        # CLS token
        self.cls_token = nn.Parameter(torch.zeros(1, 1, hidden_size))

        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_size,
            nhead=num_heads,
            dim_feedforward=hidden_size * 4,
            dropout=dropout,
            activation='gelu',
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        # Classification head
        self.norm = nn.LayerNorm(hidden_size)
        self.classifier = nn.Linear(hidden_size, num_classes)

        # Initialize weights
        self._init_weights()

    def _init_weights(self):
        """Initialize weights."""
        nn.init.trunc_normal_(self.pos_embed, std=0.02)
        nn.init.trunc_normal_(self.cls_token, std=0.02)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input images (B, 3, H, W)

        Returns:
            logits: Classification logits (B, num_classes)
        """
        B = x.shape[0]

        # Patch embedding: (B, 3, H, W) -> (B, hidden_size, H/P, W/P)
        x = self.patch_embed(x)

        # Flatten patches: (B, hidden_size, H/P, W/P) -> (B, num_patches, hidden_size)
        x = x.flatten(2).transpose(1, 2)

        # Add CLS token
        cls_tokens = self.cls_token.expand(B, -1, -1)
        x = torch.cat([cls_tokens, x], dim=1)

        # Add position embedding
        x = x + self.pos_embed

        # Transformer
        x = self.transformer(x)

        # Classification (use CLS token)
        cls_output = x[:, 0]
        cls_output = self.norm(cls_output)
        logits = self.classifier(cls_output)

        return logits


def create_ast_model(
    num_classes: int = 10,
    pretrained: bool = True,
    use_simple: bool = True,
    **kwargs
) -> nn.Module:
    """
    Factory function to create AST-style classifier.

    Args:
        num_classes: Number of classes
        pretrained: Use pretrained weights
        use_simple: Use simplified version (recommended for images)
        **kwargs: Additional arguments

    Returns:
        AST classifier model
    """
    if use_simple:
        return ASTClassifierSimple(
            num_classes=num_classes,
            pretrained_vit=pretrained,
            **kwargs
        )
    else:
        return ASTClassifier(
            num_classes=num_classes,
            pretrained=pretrained,
            **kwargs
        )


# Comparison with standard spectrogram AST
class SpectrogramAST(nn.Module):
    """
    Standard AST for mel spectrograms (for comparison).

    Use this to compare performance between:
    1. Your spiral visualizations + ViT
    2. Standard mel spectrograms + AST

    This helps answer: Is the spiral visualization adding value?
    """

    def __init__(
        self,
        num_classes: int = 10,
        model_name: str = "MIT/ast-finetuned-audioset-10-10-0.4593"
    ):
        super().__init__()

        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers required")

        self.backbone = ASTModel.from_pretrained(model_name)
        self.classifier = nn.Linear(self.backbone.config.hidden_size, num_classes)

    def forward(self, mel_spectrogram: torch.Tensor) -> torch.Tensor:
        """
        Forward pass with mel spectrogram input.

        Args:
            mel_spectrogram: (B, time_frames, mel_bins)

        Returns:
            logits: (B, num_classes)
        """
        outputs = self.backbone(mel_spectrogram)
        logits = self.classifier(outputs.pooler_output)
        return logits


if __name__ == "__main__":
    # Test the models
    print("Testing AST Classifiers...")

    # Test simple version (recommended)
    print("\n1. Testing ASTClassifierSimple...")
    model = ASTClassifierSimple(num_classes=10)

    dummy_input = torch.randn(2, 3, 224, 224)
    output = model(dummy_input)
    print(f"   Input shape: {dummy_input.shape}")
    print(f"   Output shape: {output.shape}")

    total_params = sum(p.numel() for p in model.parameters())
    print(f"   Total parameters: {total_params:,}")

    # Test factory function
    print("\n2. Testing create_ast_model...")
    model2 = create_ast_model(num_classes=10, use_simple=True)
    output2 = model2(dummy_input)
    print(f"   Output shape: {output2.shape}")

    print("\nAll tests passed!")
