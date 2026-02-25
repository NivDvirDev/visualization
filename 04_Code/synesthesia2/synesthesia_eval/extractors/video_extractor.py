"""Video feature extraction for synesthesia evaluation.

Uses PyTorchVideo SlowR50 backbone for temporal video feature extraction
at frame-level and clip-level granularity.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import torch
import torch.nn as nn
from torchvision import transforms


@dataclass
class VideoFeatures:
    """Container for extracted video features."""

    frame_features: torch.Tensor  # (num_frames, feature_dim)
    clip_features: torch.Tensor  # (num_clips, feature_dim)
    temporal_features: torch.Tensor  # (num_clips, T, feature_dim)


def _load_model(pretrained: bool = True) -> nn.Module:
    """Load SlowR50 backbone from pytorchvideo hub.

    Args:
        pretrained: Whether to load pretrained Kinetics-400 weights.

    Returns:
        SlowR50 model.
    """
    from pytorchvideo.models.hub import slow_r50

    model = slow_r50(pretrained=pretrained)
    return model


class VideoFeatureExtractor:
    """Extract temporal video features using a PyTorchVideo SlowR50 backbone.

    The model processes clips of shape (B, C, T, H, W) and produces:
    - Clip-level features via global average pooling over the final conv block
    - Temporal features retaining the time dimension
    - Frame-level features by extracting per-frame spatial features

    Args:
        pretrained: Use Kinetics-400 pretrained weights. Defaults to True.
        clip_length: Number of frames per clip. Defaults to 8.
        frame_size: Spatial resolution (H, W). Defaults to (224, 224).
        device: Torch device. Defaults to auto-detect.
    """

    def __init__(
        self,
        pretrained: bool = True,
        clip_length: int = 8,
        frame_size: Tuple[int, int] = (224, 224),
        device: Optional[str] = None,
    ):
        self.clip_length = clip_length
        self.frame_size = frame_size
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        self.model = _load_model(pretrained=pretrained)
        self.model = self.model.to(self.device)
        self.model.eval()

        # Backbone = all blocks except the classification head
        self._backbone = self.model.blocks[:-1]
        self._head_pool = nn.AdaptiveAvgPool3d((1, 1, 1))

        self.transform = transforms.Compose(
            [
                transforms.Resize(self.frame_size),
                transforms.Normalize(
                    mean=[0.45, 0.45, 0.45], std=[0.225, 0.225, 0.225]
                ),
            ]
        )

    def _preprocess(self, frames: np.ndarray) -> torch.Tensor:
        """Preprocess frames for the model.

        Args:
            frames: Array of shape (T, H, W, C) with values in [0, 255]
                    or (T, C, H, W) with values in [0, 1].

        Returns:
            Tensor of shape (1, C, T, H, W) normalized and resized.
        """
        if isinstance(frames, np.ndarray):
            frames = torch.from_numpy(frames).float()

        # Handle (T, H, W, C) -> (T, C, H, W)
        if frames.ndim == 4 and frames.shape[-1] in (1, 3):
            frames = frames.permute(0, 3, 1, 2)

        # Normalize to [0, 1] if values are in [0, 255]
        if frames.max() > 1.0:
            frames = frames / 255.0

        # Apply spatial transforms per-frame
        processed = []
        for t in range(frames.shape[0]):
            frame = self.transform(frames[t])
            processed.append(frame)
        clip = torch.stack(processed, dim=1)  # (C, T, H, W)
        return clip.unsqueeze(0).to(self.device)  # (1, C, T, H, W)

    def _split_clips(self, frames: np.ndarray) -> List[np.ndarray]:
        """Split a sequence of frames into non-overlapping clips.

        Args:
            frames: Array of shape (T, H, W, C) or (T, C, H, W).

        Returns:
            List of clip arrays, each of length self.clip_length.
        """
        total = frames.shape[0]
        clips = []
        for start in range(0, total - self.clip_length + 1, self.clip_length):
            clips.append(frames[start : start + self.clip_length])
        # If there's a remaining partial clip, pad by repeating the last frame
        remainder = total % self.clip_length
        if remainder > 0 and total >= self.clip_length:
            # Already handled full clips above; skip partial
            pass
        elif total < self.clip_length:
            # Pad the single short clip
            pad_count = self.clip_length - total
            last_frame = frames[-1:]
            padding = np.repeat(last_frame, pad_count, axis=0)
            clips.append(np.concatenate([frames, padding], axis=0))
        return clips

    @torch.no_grad()
    def _forward_backbone(self, x: torch.Tensor) -> torch.Tensor:
        """Run input through backbone blocks (excluding head).

        Args:
            x: Tensor of shape (B, C, T, H, W).

        Returns:
            Feature map of shape (B, D, T', H', W').
        """
        for block in self._backbone:
            x = block(x)
        return x

    @torch.no_grad()
    def extract_frames(self, frames: np.ndarray) -> torch.Tensor:
        """Extract per-frame features from a sequence of frames.

        Processes frames through the backbone, pools spatially per time-step,
        and returns one feature vector per input frame.

        Args:
            frames: Array of shape (T, H, W, C) with uint8 or float values.

        Returns:
            Tensor of shape (T, feature_dim) with per-frame features.
        """
        clips = self._split_clips(frames)
        frame_feats = []
        for clip_frames in clips:
            x = self._preprocess(clip_frames)
            feat_map = self._forward_backbone(x)  # (1, D, T', H', W')
            # Pool spatially, keep temporal: (1, D, T') -> (T', D)
            pooled = feat_map.mean(dim=[-2, -1]).squeeze(0).permute(1, 0)
            frame_feats.append(pooled.cpu())

        all_feats = torch.cat(frame_feats, dim=0)
        # Trim to original frame count
        return all_feats[: frames.shape[0]]

    @torch.no_grad()
    def extract_temporal_features(self, frames: np.ndarray) -> torch.Tensor:
        """Extract temporal features retaining the time dimension per clip.

        Args:
            frames: Array of shape (T, H, W, C).

        Returns:
            Tensor of shape (num_clips, T', feature_dim) where T' is the
            temporal resolution after backbone processing.
        """
        clips = self._split_clips(frames)
        temporal_feats = []
        for clip_frames in clips:
            x = self._preprocess(clip_frames)
            feat_map = self._forward_backbone(x)  # (1, D, T', H', W')
            # Pool spatially, keep temporal: (1, D, T') -> (1, T', D)
            pooled = feat_map.mean(dim=[-2, -1]).squeeze(0).permute(1, 0)
            temporal_feats.append(pooled.unsqueeze(0).cpu())
        return torch.cat(temporal_feats, dim=0)

    @torch.no_grad()
    def extract_clip_features(self, frames: np.ndarray) -> torch.Tensor:
        """Extract a single feature vector per clip via global average pooling.

        Args:
            frames: Array of shape (T, H, W, C).

        Returns:
            Tensor of shape (num_clips, feature_dim).
        """
        clips = self._split_clips(frames)
        clip_feats = []
        for clip_frames in clips:
            x = self._preprocess(clip_frames)
            feat_map = self._forward_backbone(x)  # (1, D, T', H', W')
            pooled = self._head_pool(feat_map).flatten(1)  # (1, D)
            clip_feats.append(pooled.cpu())
        return torch.cat(clip_feats, dim=0)

    @torch.no_grad()
    def extract_all(self, frames: np.ndarray) -> VideoFeatures:
        """Extract frame-level, clip-level, and temporal features at once.

        Args:
            frames: Array of shape (T, H, W, C).

        Returns:
            VideoFeatures dataclass.
        """
        clips = self._split_clips(frames)
        frame_feats = []
        clip_feats = []
        temporal_feats = []

        for clip_frames in clips:
            x = self._preprocess(clip_frames)
            feat_map = self._forward_backbone(x)  # (1, D, T', H', W')

            # Clip-level: global pool
            clip_pooled = self._head_pool(feat_map).flatten(1)  # (1, D)
            clip_feats.append(clip_pooled.cpu())

            # Temporal: pool spatial, keep time
            spatial_pooled = feat_map.mean(dim=[-2, -1]).squeeze(0).permute(
                1, 0
            )  # (T', D)
            temporal_feats.append(spatial_pooled.unsqueeze(0).cpu())

            # Frame-level: same as spatial_pooled
            frame_feats.append(spatial_pooled.cpu())

        return VideoFeatures(
            frame_features=torch.cat(frame_feats, dim=0)[: frames.shape[0]],
            clip_features=torch.cat(clip_feats, dim=0),
            temporal_features=torch.cat(temporal_feats, dim=0),
        )

    @torch.no_grad()
    def extract_batch(
        self, batch: List[np.ndarray]
    ) -> List[VideoFeatures]:
        """Extract features from multiple video frame sequences.

        Args:
            batch: List of frame arrays, each of shape (T, H, W, C).

        Returns:
            List of VideoFeatures, one per video.
        """
        return [self.extract_all(frames) for frames in batch]
