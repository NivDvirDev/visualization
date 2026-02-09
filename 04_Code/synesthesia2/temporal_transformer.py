"""
SYNESTHESIA 3.0 - Temporal Transformer
=======================================
Phase III: Multi-scale temporal pattern learning using Transformer architecture.

This module implements:
1. TemporalSpiralEncoder: Encodes sequences of spiral frames
2. MultiScaleTemporalBlock: Processes features at different time scales
3. CrossScaleAttention: Learns relationships between short and long-term patterns
4. TemporalSpiralTransformer: Complete model for temporal pattern classification

The goal: Learn to recognize songs by their melodic/rhythmic/harmonic patterns,
not just their instantaneous timbre.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
import math


@dataclass
class TransformerConfig:
    """Configuration for Temporal Transformer."""
    # Input
    input_channels: int = 3  # RGB
    image_size: int = 224
    patch_size: int = 16

    # Transformer
    d_model: int = 512
    n_heads: int = 8
    n_layers: int = 6
    d_ff: int = 2048
    dropout: float = 0.1

    # Multi-scale temporal
    note_window: int = 15      # ~0.5s at 30fps
    motif_window: int = 60     # ~2s
    phrase_window: int = 180   # ~6s
    atmosphere_window: int = 300  # ~10s

    # Output
    num_instrument_classes: int = 10
    num_genre_classes: int = 10
    num_emotion_classes: int = 8


class PatchEmbedding(nn.Module):
    """Convert image to patch embeddings (like ViT)."""

    def __init__(self, config: TransformerConfig):
        super().__init__()
        self.patch_size = config.patch_size
        self.n_patches = (config.image_size // config.patch_size) ** 2

        self.projection = nn.Conv2d(
            config.input_channels,
            config.d_model,
            kernel_size=config.patch_size,
            stride=config.patch_size
        )

        # Learnable position embeddings
        self.position_embeddings = nn.Parameter(
            torch.randn(1, self.n_patches + 1, config.d_model) * 0.02
        )

        # CLS token for classification
        self.cls_token = nn.Parameter(torch.randn(1, 1, config.d_model) * 0.02)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [batch, channels, height, width]
        Returns:
            [batch, n_patches + 1, d_model]
        """
        batch_size = x.shape[0]

        # Project patches
        x = self.projection(x)  # [batch, d_model, h/patch, w/patch]
        x = x.flatten(2).transpose(1, 2)  # [batch, n_patches, d_model]

        # Add CLS token
        cls_tokens = self.cls_token.expand(batch_size, -1, -1)
        x = torch.cat([cls_tokens, x], dim=1)

        # Add position embeddings
        x = x + self.position_embeddings

        return x


class MultiHeadSelfAttention(nn.Module):
    """Multi-head self-attention mechanism."""

    def __init__(self, d_model: int, n_heads: int, dropout: float = 0.1):
        super().__init__()
        assert d_model % n_heads == 0

        self.d_model = d_model
        self.n_heads = n_heads
        self.head_dim = d_model // n_heads

        self.q_proj = nn.Linear(d_model, d_model)
        self.k_proj = nn.Linear(d_model, d_model)
        self.v_proj = nn.Linear(d_model, d_model)
        self.out_proj = nn.Linear(d_model, d_model)

        self.dropout = nn.Dropout(dropout)
        self.scale = math.sqrt(self.head_dim)

        # Store attention weights for visualization
        self.attention_weights = None

    def forward(self, x: torch.Tensor,
                mask: Optional[torch.Tensor] = None,
                return_attention: bool = False) -> torch.Tensor:
        batch_size, seq_len, _ = x.shape

        # Project to Q, K, V
        q = self.q_proj(x).view(batch_size, seq_len, self.n_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(x).view(batch_size, seq_len, self.n_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(x).view(batch_size, seq_len, self.n_heads, self.head_dim).transpose(1, 2)

        # Attention scores
        attn = torch.matmul(q, k.transpose(-2, -1)) / self.scale

        if mask is not None:
            attn = attn.masked_fill(mask == 0, float('-inf'))

        attn = F.softmax(attn, dim=-1)
        self.attention_weights = attn.detach()
        attn = self.dropout(attn)

        # Apply attention to values
        out = torch.matmul(attn, v)
        out = out.transpose(1, 2).contiguous().view(batch_size, seq_len, self.d_model)
        out = self.out_proj(out)

        if return_attention:
            return out, self.attention_weights
        return out


class TransformerBlock(nn.Module):
    """Standard transformer encoder block."""

    def __init__(self, d_model: int, n_heads: int, d_ff: int, dropout: float = 0.1):
        super().__init__()

        self.attention = MultiHeadSelfAttention(d_model, n_heads, dropout)
        self.norm1 = nn.LayerNorm(d_model)

        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model),
            nn.Dropout(dropout)
        )
        self.norm2 = nn.LayerNorm(d_model)

    def forward(self, x: torch.Tensor,
                mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        # Self-attention with residual
        attn_out = self.attention(self.norm1(x), mask)
        x = x + attn_out

        # FFN with residual
        ffn_out = self.ffn(self.norm2(x))
        x = x + ffn_out

        return x


class FrameEncoder(nn.Module):
    """
    Encodes individual spiral visualization frames.
    Similar to ViT but optimized for spiral images.
    """

    def __init__(self, config: TransformerConfig):
        super().__init__()
        self.config = config

        self.patch_embed = PatchEmbedding(config)

        self.transformer_blocks = nn.ModuleList([
            TransformerBlock(
                config.d_model,
                config.n_heads,
                config.d_ff,
                config.dropout
            )
            for _ in range(config.n_layers // 2)  # Half the layers for frame encoding
        ])

        self.norm = nn.LayerNorm(config.d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [batch, channels, height, width]
        Returns:
            [batch, d_model] - CLS token representation
        """
        x = self.patch_embed(x)

        for block in self.transformer_blocks:
            x = block(x)

        x = self.norm(x)

        # Return CLS token
        return x[:, 0]


class TemporalBlock(nn.Module):
    """
    Processes sequences of frame embeddings at a specific time scale.
    Uses temporal attention to capture patterns within the window.
    """

    def __init__(self, d_model: int, n_heads: int, window_size: int,
                 dropout: float = 0.1):
        super().__init__()
        self.window_size = window_size

        self.temporal_attention = MultiHeadSelfAttention(d_model, n_heads, dropout)
        self.norm = nn.LayerNorm(d_model)

        # Temporal position encoding
        self.temporal_pos = nn.Parameter(
            torch.randn(1, window_size, d_model) * 0.02
        )

        # Aggregation layer
        self.aggregate = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.GELU(),
            nn.Linear(d_model, d_model)
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            x: [batch, seq_len, d_model] - sequence of frame embeddings
        Returns:
            aggregated: [batch, d_model] - aggregated representation
            temporal_features: [batch, seq_len, d_model] - processed sequence
        """
        batch_size, seq_len, d_model = x.shape

        # Pad or truncate to window size
        if seq_len < self.window_size:
            padding = torch.zeros(batch_size, self.window_size - seq_len, d_model,
                                  device=x.device, dtype=x.dtype)
            x = torch.cat([x, padding], dim=1)
        elif seq_len > self.window_size:
            # Use sliding window and average
            x = x[:, -self.window_size:]

        # Add temporal position encoding
        x = x + self.temporal_pos[:, :x.shape[1]]

        # Temporal attention
        x = self.norm(x)
        x_attn = self.temporal_attention(x)
        x = x + x_attn

        # Aggregate (mean pooling + projection)
        aggregated = self.aggregate(x.mean(dim=1))

        return aggregated, x


class CrossScaleAttention(nn.Module):
    """
    Learns relationships between features at different time scales.
    Allows short-term features to be informed by long-term context and vice versa.
    """

    def __init__(self, d_model: int, n_heads: int, dropout: float = 0.1):
        super().__init__()

        self.cross_attention = nn.MultiheadAttention(
            d_model, n_heads, dropout=dropout, batch_first=True
        )
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)

        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_model * 4),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model * 4, d_model),
            nn.Dropout(dropout)
        )

    def forward(self, query: torch.Tensor, context: torch.Tensor) -> torch.Tensor:
        """
        Args:
            query: [batch, d_model] - features to be enhanced
            context: [batch, n_scales, d_model] - multi-scale context
        Returns:
            [batch, d_model] - enhanced features
        """
        # Add sequence dimension to query
        query = query.unsqueeze(1)  # [batch, 1, d_model]

        # Cross-attention
        attended, _ = self.cross_attention(
            self.norm1(query),
            self.norm2(context),
            context
        )
        query = query + attended

        # FFN
        query = query + self.ffn(query)

        return query.squeeze(1)


class TemporalSpiralTransformer(nn.Module):
    """
    Complete Temporal Transformer for spiral visualization classification.

    Architecture:
    1. Frame Encoder: Encodes individual spiral frames
    2. Multi-scale Temporal Blocks: Process at note/motif/phrase/atmosphere scales
    3. Cross-scale Attention: Learn relationships between scales
    4. Classification Heads: Instrument, genre, emotion
    """

    def __init__(self, config: Optional[TransformerConfig] = None):
        super().__init__()
        self.config = config or TransformerConfig()

        # Frame encoder (shared across all frames)
        self.frame_encoder = FrameEncoder(self.config)

        # Multi-scale temporal blocks
        self.note_block = TemporalBlock(
            self.config.d_model, self.config.n_heads,
            self.config.note_window, self.config.dropout
        )
        self.motif_block = TemporalBlock(
            self.config.d_model, self.config.n_heads,
            self.config.motif_window, self.config.dropout
        )
        self.phrase_block = TemporalBlock(
            self.config.d_model, self.config.n_heads,
            self.config.phrase_window, self.config.dropout
        )
        self.atmosphere_block = TemporalBlock(
            self.config.d_model, self.config.n_heads,
            self.config.atmosphere_window, self.config.dropout
        )

        # Cross-scale attention
        self.cross_scale_attention = CrossScaleAttention(
            self.config.d_model, self.config.n_heads, self.config.dropout
        )

        # Fusion layer
        self.fusion = nn.Sequential(
            nn.Linear(self.config.d_model * 4, self.config.d_model),
            nn.GELU(),
            nn.Dropout(self.config.dropout),
            nn.Linear(self.config.d_model, self.config.d_model)
        )

        # Classification heads
        self.instrument_head = nn.Linear(self.config.d_model, self.config.num_instrument_classes)
        self.genre_head = nn.Linear(self.config.d_model, self.config.num_genre_classes)
        self.emotion_head = nn.Linear(self.config.d_model, self.config.num_emotion_classes)

        # Initialize weights
        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            torch.nn.init.xavier_uniform_(module.weight)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.LayerNorm):
            torch.nn.init.ones_(module.weight)
            torch.nn.init.zeros_(module.bias)

    def encode_frames(self, frames: torch.Tensor) -> torch.Tensor:
        """
        Encode a batch of frames.

        Args:
            frames: [batch, seq_len, channels, height, width]
        Returns:
            [batch, seq_len, d_model]
        """
        batch_size, seq_len, c, h, w = frames.shape

        # Flatten batch and sequence for efficient processing
        frames_flat = frames.view(batch_size * seq_len, c, h, w)

        # Encode all frames
        embeddings = self.frame_encoder(frames_flat)

        # Reshape back
        embeddings = embeddings.view(batch_size, seq_len, -1)

        return embeddings

    def forward(self, frames: torch.Tensor,
                return_features: bool = False) -> Dict[str, torch.Tensor]:
        """
        Forward pass through the complete model.

        Args:
            frames: [batch, seq_len, channels, height, width] - sequence of spiral frames
            return_features: Whether to return intermediate features

        Returns:
            Dictionary with predictions and optionally features
        """
        # Encode all frames
        frame_embeddings = self.encode_frames(frames)

        # Multi-scale temporal processing
        note_features, note_seq = self.note_block(frame_embeddings)
        motif_features, motif_seq = self.motif_block(frame_embeddings)
        phrase_features, phrase_seq = self.phrase_block(frame_embeddings)
        atmos_features, atmos_seq = self.atmosphere_block(frame_embeddings)

        # Stack multi-scale features for cross-attention
        multi_scale = torch.stack([
            note_features, motif_features, phrase_features, atmos_features
        ], dim=1)  # [batch, 4, d_model]

        # Cross-scale attention: enhance each scale with context from others
        note_enhanced = self.cross_scale_attention(note_features, multi_scale)
        motif_enhanced = self.cross_scale_attention(motif_features, multi_scale)
        phrase_enhanced = self.cross_scale_attention(phrase_features, multi_scale)
        atmos_enhanced = self.cross_scale_attention(atmos_features, multi_scale)

        # Concatenate and fuse
        fused = torch.cat([
            note_enhanced, motif_enhanced, phrase_enhanced, atmos_enhanced
        ], dim=-1)
        fused = self.fusion(fused)

        # Classification
        instrument_logits = self.instrument_head(fused)
        genre_logits = self.genre_head(fused)
        emotion_logits = self.emotion_head(fused)

        output = {
            'instrument_logits': instrument_logits,
            'genre_logits': genre_logits,
            'emotion_logits': emotion_logits,
        }

        if return_features:
            output['features'] = {
                'note': note_features,
                'motif': motif_features,
                'phrase': phrase_features,
                'atmosphere': atmos_features,
                'fused': fused
            }

        return output

    def get_attention_maps(self) -> Dict[str, torch.Tensor]:
        """Extract attention maps from all temporal blocks."""
        return {
            'note': self.note_block.temporal_attention.attention_weights,
            'motif': self.motif_block.temporal_attention.attention_weights,
            'phrase': self.phrase_block.temporal_attention.attention_weights,
            'atmosphere': self.atmosphere_block.temporal_attention.attention_weights,
        }


class TemporalClassificationLoss(nn.Module):
    """
    Multi-task loss for temporal classification.
    Combines instrument, genre, and emotion classification losses.
    """

    def __init__(self, instrument_weight: float = 1.0,
                 genre_weight: float = 0.5,
                 emotion_weight: float = 0.3):
        super().__init__()
        self.instrument_weight = instrument_weight
        self.genre_weight = genre_weight
        self.emotion_weight = emotion_weight

        self.ce_loss = nn.CrossEntropyLoss()

    def forward(self, outputs: Dict[str, torch.Tensor],
                targets: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """
        Compute multi-task loss.

        Args:
            outputs: Model outputs with logits
            targets: Dictionary with target labels

        Returns:
            Dictionary with individual losses and total loss
        """
        losses = {}

        if 'instrument' in targets:
            losses['instrument'] = self.ce_loss(
                outputs['instrument_logits'], targets['instrument']
            )

        if 'genre' in targets:
            losses['genre'] = self.ce_loss(
                outputs['genre_logits'], targets['genre']
            )

        if 'emotion' in targets:
            losses['emotion'] = self.ce_loss(
                outputs['emotion_logits'], targets['emotion']
            )

        # Total loss
        total = 0
        if 'instrument' in losses:
            total += self.instrument_weight * losses['instrument']
        if 'genre' in losses:
            total += self.genre_weight * losses['genre']
        if 'emotion' in losses:
            total += self.emotion_weight * losses['emotion']

        losses['total'] = total

        return losses


def demo_temporal_transformer():
    """Demonstrate the Temporal Transformer."""
    print("=" * 60)
    print("SYNESTHESIA 3.0 - Temporal Transformer Demo")
    print("=" * 60)

    # Create model
    config = TransformerConfig(
        d_model=256,  # Smaller for demo
        n_heads=4,
        n_layers=4,
        note_window=15,
        motif_window=30,
        phrase_window=60,
        atmosphere_window=90
    )

    model = TemporalSpiralTransformer(config)
    print(f"\nModel created with {sum(p.numel() for p in model.parameters()):,} parameters")

    # Create dummy input (batch of frame sequences)
    batch_size = 2
    seq_len = 90  # 3 seconds at 30fps
    frames = torch.randn(batch_size, seq_len, 3, 224, 224)

    print(f"\nInput shape: {frames.shape}")
    print(f"  Batch size: {batch_size}")
    print(f"  Sequence length: {seq_len} frames (~{seq_len/30:.1f}s)")
    print(f"  Frame size: 224x224x3")

    # Forward pass
    print("\nRunning forward pass...")
    model.eval()
    with torch.no_grad():
        outputs = model(frames, return_features=True)

    print("\nOutputs:")
    print(f"  Instrument logits: {outputs['instrument_logits'].shape}")
    print(f"  Genre logits: {outputs['genre_logits'].shape}")
    print(f"  Emotion logits: {outputs['emotion_logits'].shape}")

    print("\nFeatures:")
    for name, feat in outputs['features'].items():
        print(f"  {name}: {feat.shape}")

    # Compute loss
    print("\nComputing multi-task loss...")
    loss_fn = TemporalClassificationLoss()
    targets = {
        'instrument': torch.randint(0, 10, (batch_size,)),
        'genre': torch.randint(0, 10, (batch_size,)),
        'emotion': torch.randint(0, 8, (batch_size,))
    }

    losses = loss_fn(outputs, targets)
    print(f"  Instrument loss: {losses['instrument']:.4f}")
    print(f"  Genre loss: {losses['genre']:.4f}")
    print(f"  Emotion loss: {losses['emotion']:.4f}")
    print(f"  Total loss: {losses['total']:.4f}")

    # Get predictions
    print("\nPredictions:")
    instrument_pred = outputs['instrument_logits'].argmax(dim=-1)
    genre_pred = outputs['genre_logits'].argmax(dim=-1)
    emotion_pred = outputs['emotion_logits'].argmax(dim=-1)

    instrument_names = ['piano', 'guitar', 'violin', 'drums', 'flute',
                        'trumpet', 'saxophone', 'cello', 'clarinet', 'bass']
    genre_names = ['classical', 'jazz', 'rock', 'electronic', 'folk',
                   'world', 'ambient', 'pop', 'metal', 'blues']
    emotion_names = ['happy', 'sad', 'energetic', 'calm', 'tense',
                     'relaxed', 'aggressive', 'melancholic']

    for i in range(batch_size):
        print(f"\n  Sample {i+1}:")
        print(f"    Instrument: {instrument_names[instrument_pred[i]]}")
        print(f"    Genre: {genre_names[genre_pred[i]]}")
        print(f"    Emotion: {emotion_names[emotion_pred[i]]}")

    print("\n✅ Temporal Transformer demo complete!")


if __name__ == "__main__":
    demo_temporal_transformer()
