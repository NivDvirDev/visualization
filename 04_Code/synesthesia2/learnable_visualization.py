"""
SYNESTHESIA 3.0 - Learnable Visualization Module
=================================================
Phase IV: End-to-end learnable visualization parameters.

Instead of hand-coded visualization rules, this module learns:
1. Frequency-to-Position mapping (spiral geometry)
2. Frequency-to-Color mapping (chromesthesia rules)
3. Amplitude-to-Size mapping (visual emphasis)
4. Temporal-to-Effect mapping (how temporal features affect visuals)

The key innovation: visualization parameters are neural network outputs
that are optimized end-to-end with classification performance.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass
import math


@dataclass
class LearnableVizConfig:
    """Configuration for learnable visualization."""
    # Audio input
    num_frequency_bins: int = 381
    frame_rate: int = 30

    # Spiral parameters (learnable bounds)
    min_radius: float = 0.1
    max_radius: float = 0.9
    min_turns: float = 3.0
    max_turns: float = 10.0

    # Color parameters
    color_embedding_dim: int = 64

    # Output
    output_width: int = 224
    output_height: int = 224

    # Regularization
    smoothness_weight: float = 0.1
    prior_weight: float = 0.05  # Weight for staying close to hand-crafted


class LearnablePositionEncoder(nn.Module):
    """
    Learns the frequency-to-position mapping for the spiral.

    Instead of fixed Fermat spiral, learns optimal positions for each
    frequency bin based on classification performance.
    """

    def __init__(self, config: LearnableVizConfig):
        super().__init__()
        self.config = config

        # MLP to learn frequency -> (x, y) mapping
        self.position_net = nn.Sequential(
            nn.Linear(1, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, 2),  # (x, y) in [-1, 1]
            nn.Tanh()
        )

        # Learnable spiral parameters
        self.num_turns = nn.Parameter(torch.tensor(7.0))
        self.spiral_scale = nn.Parameter(torch.tensor(0.85))

        # Initialize close to Fermat spiral
        self._init_from_fermat()

    def _init_from_fermat(self):
        """Initialize network to approximate Fermat spiral."""
        # This helps training start from a good point
        with torch.no_grad():
            # Small random initialization
            for layer in self.position_net:
                if isinstance(layer, nn.Linear):
                    nn.init.xavier_uniform_(layer.weight, gain=0.1)
                    nn.init.zeros_(layer.bias)

    def get_fermat_prior(self, freq_indices: torch.Tensor) -> torch.Tensor:
        """Compute Fermat spiral positions as prior."""
        t = freq_indices.float() / self.config.num_frequency_bins
        theta = t * self.num_turns * 2 * math.pi
        r = torch.sqrt(t) * self.spiral_scale

        x = r * torch.cos(theta)
        y = r * torch.sin(theta)

        return torch.stack([x, y], dim=-1)

    def forward(self, freq_indices: torch.Tensor,
                rotation: float = 0.0) -> torch.Tensor:
        """
        Compute positions for frequency bins.

        Args:
            freq_indices: [batch, num_freqs] or [num_freqs] - indices 0 to num_bins-1
            rotation: Rotation angle in radians

        Returns:
            [batch, num_freqs, 2] or [num_freqs, 2] - (x, y) positions in [-1, 1]
        """
        # Normalize frequency indices to [0, 1]
        t = freq_indices.float() / self.config.num_frequency_bins

        # Get learned position offset
        t_input = t.unsqueeze(-1)  # [..., 1]
        learned_offset = self.position_net(t_input)  # [..., 2]

        # Get Fermat prior
        prior_pos = self.get_fermat_prior(freq_indices)

        # Combine: prior + small learned offset
        positions = prior_pos + 0.1 * learned_offset

        # Apply rotation
        if rotation != 0:
            cos_r, sin_r = math.cos(rotation), math.sin(rotation)
            x = positions[..., 0] * cos_r - positions[..., 1] * sin_r
            y = positions[..., 0] * sin_r + positions[..., 1] * cos_r
            positions = torch.stack([x, y], dim=-1)

        return positions


class LearnableColorEncoder(nn.Module):
    """
    Learns the frequency-to-color mapping.

    Instead of fixed chromesthesia colors, learns optimal color assignments
    that maximize class separability.
    """

    def __init__(self, config: LearnableVizConfig):
        super().__init__()
        self.config = config

        # Embedding for each frequency bin
        self.freq_embedding = nn.Embedding(
            config.num_frequency_bins,
            config.color_embedding_dim
        )

        # MLP to produce RGB from embedding
        self.color_net = nn.Sequential(
            nn.Linear(config.color_embedding_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 3),  # RGB
            nn.Sigmoid()  # Output in [0, 1]
        )

        # Initialize with chromesthesia prior
        self._init_from_chromesthesia()

    def _init_from_chromesthesia(self):
        """Initialize to approximate chromesthesia colors."""
        # Chromesthesia: low freq = blue, mid = green/yellow, high = red
        with torch.no_grad():
            for i in range(self.config.num_frequency_bins):
                t = i / self.config.num_frequency_bins
                # HSV-like mapping
                hue = t * 0.8  # 0 to 0.8 (red to blue)
                self.freq_embedding.weight[i] = torch.randn(self.config.color_embedding_dim) * 0.1
                self.freq_embedding.weight[i, 0] = hue * 2 - 1  # Store hue hint

    def forward(self, freq_indices: torch.Tensor,
                amplitude: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Compute colors for frequency bins.

        Args:
            freq_indices: [...] - frequency bin indices
            amplitude: [...] - optional amplitude for brightness modulation

        Returns:
            [..., 3] - RGB colors in [0, 1]
        """
        # Get embeddings
        embeddings = self.freq_embedding(freq_indices)

        # Compute base colors
        colors = self.color_net(embeddings)

        # Modulate by amplitude if provided
        if amplitude is not None:
            # Brightness modulation
            brightness = 0.3 + 0.7 * amplitude.unsqueeze(-1)
            colors = colors * brightness

        return colors


class LearnableAmplitudeEncoder(nn.Module):
    """
    Learns the amplitude-to-visual-size mapping.

    Learns non-linear scaling that emphasizes discriminative features.
    """

    def __init__(self, config: LearnableVizConfig):
        super().__init__()

        # Per-frequency importance weights
        self.importance_weights = nn.Parameter(
            torch.ones(config.num_frequency_bins)
        )

        # Non-linear amplitude transformation
        self.amp_transform = nn.Sequential(
            nn.Linear(1, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Softplus()  # Ensures positive output
        )

        # Base and max sizes
        self.base_size = nn.Parameter(torch.tensor(2.0))
        self.size_scale = nn.Parameter(torch.tensor(8.0))

    def forward(self, amplitude: torch.Tensor,
                freq_indices: torch.Tensor) -> torch.Tensor:
        """
        Compute visual sizes for amplitude values.

        Args:
            amplitude: [...] - amplitude values
            freq_indices: [...] - corresponding frequency indices

        Returns:
            [...] - visual sizes
        """
        # Apply frequency-specific importance
        importance = F.softplus(self.importance_weights[freq_indices])
        weighted_amp = amplitude * importance

        # Non-linear transformation
        amp_input = weighted_amp.unsqueeze(-1)
        transformed = self.amp_transform(amp_input).squeeze(-1)

        # Compute final size
        sizes = self.base_size + self.size_scale * transformed

        return sizes


class LearnableTemporalEffects(nn.Module):
    """
    Learns how temporal features should affect visualization.

    Maps extracted temporal features (pitch, beat, chord, energy)
    to visual effects (trail intensity, pulse amount, aura color, etc.)
    """

    def __init__(self, config: LearnableVizConfig):
        super().__init__()

        # Melody trail parameters
        self.melody_net = nn.Sequential(
            nn.Linear(2, 32),  # (pitch, confidence)
            nn.ReLU(),
            nn.Linear(32, 4),  # (trail_alpha, trail_size, glow_radius, glow_intensity)
            nn.Sigmoid()
        )

        # Rhythm pulse parameters
        self.rhythm_net = nn.Sequential(
            nn.Linear(2, 32),  # (beat_strength, is_downbeat)
            nn.ReLU(),
            nn.Linear(32, 3),  # (scale_amount, brightness_boost, pulse_decay)
            nn.Sigmoid()
        )

        # Harmony aura parameters
        self.harmony_net = nn.Sequential(
            nn.Linear(12, 32),  # chroma (12 pitch classes)
            nn.ReLU(),
            nn.Linear(32, 3),  # RGB for background
            nn.Sigmoid()
        )

        # Atmosphere parameters
        self.atmosphere_net = nn.Sequential(
            nn.Linear(3, 32),  # (energy, tension, brightness)
            nn.ReLU(),
            nn.Linear(32, 4),  # (rotation_speed, particle_scale, blur, warmth)
            nn.Sigmoid()
        )

    def forward(self, temporal_features: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """
        Compute visual effects from temporal features.

        Args:
            temporal_features: Dictionary with pitch, beat, chroma, atmosphere

        Returns:
            Dictionary with visual effect parameters
        """
        effects = {}

        # Melody effects
        if 'pitch' in temporal_features and 'pitch_confidence' in temporal_features:
            melody_input = torch.stack([
                temporal_features['pitch'] / 2000,  # Normalize
                temporal_features['pitch_confidence']
            ], dim=-1)
            melody_params = self.melody_net(melody_input)
            effects['trail_alpha'] = melody_params[..., 0]
            effects['trail_size'] = 3 + 10 * melody_params[..., 1]
            effects['glow_radius'] = 5 + 15 * melody_params[..., 2]
            effects['glow_intensity'] = melody_params[..., 3]

        # Rhythm effects
        if 'beat_strength' in temporal_features:
            is_downbeat = temporal_features.get('is_downbeat', torch.zeros_like(temporal_features['beat_strength']))
            rhythm_input = torch.stack([
                temporal_features['beat_strength'],
                is_downbeat.float()
            ], dim=-1)
            rhythm_params = self.rhythm_net(rhythm_input)
            effects['pulse_scale'] = 1.0 + 0.2 * rhythm_params[..., 0]
            effects['brightness_boost'] = 0.3 * rhythm_params[..., 1]
            effects['pulse_decay'] = 0.8 + 0.15 * rhythm_params[..., 2]

        # Harmony effects
        if 'chroma' in temporal_features:
            harmony_params = self.harmony_net(temporal_features['chroma'])
            effects['aura_color'] = harmony_params  # RGB

        # Atmosphere effects
        if 'energy' in temporal_features:
            atmos_input = torch.stack([
                temporal_features.get('energy', torch.tensor(0.5)),
                temporal_features.get('tension', torch.tensor(0.3)),
                temporal_features.get('brightness', torch.tensor(0.5))
            ], dim=-1)
            atmos_params = self.atmosphere_net(atmos_input)
            effects['rotation_speed'] = 0.5 + 1.5 * atmos_params[..., 0]
            effects['particle_scale'] = 0.8 + 0.4 * atmos_params[..., 1]
            effects['blur_amount'] = 5 * atmos_params[..., 2]
            effects['color_warmth'] = atmos_params[..., 3]

        return effects


class DifferentiableSpiralRenderer(nn.Module):
    """
    Differentiable renderer that produces spiral visualizations.

    Uses soft rasterization to enable gradients to flow through rendering.
    """

    def __init__(self, config: LearnableVizConfig):
        super().__init__()
        self.config = config

        # Learnable components
        self.position_encoder = LearnablePositionEncoder(config)
        self.color_encoder = LearnableColorEncoder(config)
        self.amplitude_encoder = LearnableAmplitudeEncoder(config)
        self.temporal_effects = LearnableTemporalEffects(config)

        # Create coordinate grid for rendering
        y_coords = torch.linspace(-1, 1, config.output_height)
        x_coords = torch.linspace(-1, 1, config.output_width)
        self.register_buffer('grid_y', y_coords.view(-1, 1).expand(-1, config.output_width))
        self.register_buffer('grid_x', x_coords.view(1, -1).expand(config.output_height, -1))

    def soft_render_points(self,
                          positions: torch.Tensor,
                          colors: torch.Tensor,
                          sizes: torch.Tensor) -> torch.Tensor:
        """
        Soft rasterization of points onto image grid.

        Args:
            positions: [num_points, 2] - (x, y) in [-1, 1]
            colors: [num_points, 3] - RGB
            sizes: [num_points] - point sizes

        Returns:
            [height, width, 3] - rendered image
        """
        num_points = positions.shape[0]
        h, w = self.config.output_height, self.config.output_width

        # Initialize image
        image = torch.zeros(h, w, 3, device=positions.device)
        weights = torch.zeros(h, w, 1, device=positions.device)

        # Soft rendering: each point contributes to nearby pixels
        for i in range(num_points):
            px, py = positions[i, 0], positions[i, 1]
            color = colors[i]
            size = sizes[i]

            # Compute distance from this point to all pixels
            dx = self.grid_x - px
            dy = self.grid_y - py
            dist_sq = dx ** 2 + dy ** 2

            # Gaussian falloff
            sigma = size / (w / 2) * 0.5  # Convert size to normalized coords
            weight = torch.exp(-dist_sq / (2 * sigma ** 2 + 1e-8))
            weight = weight.unsqueeze(-1)

            # Accumulate color contribution
            image = image + weight * color.view(1, 1, 3)
            weights = weights + weight

        # Normalize by total weight
        image = image / (weights + 1e-8)

        return image

    def forward(self,
                amplitude: torch.Tensor,
                frame_idx: int = 0,
                temporal_features: Optional[Dict[str, torch.Tensor]] = None) -> torch.Tensor:
        """
        Render a spiral visualization frame.

        Args:
            amplitude: [num_freqs] - amplitude per frequency bin
            frame_idx: Frame index for animation
            temporal_features: Optional temporal features for effects

        Returns:
            [height, width, 3] - rendered image in [0, 1]
        """
        device = amplitude.device
        num_freqs = len(amplitude)

        # Frequency indices
        freq_indices = torch.arange(num_freqs, device=device)

        # Compute rotation
        rotation = frame_idx * 0.02

        # Get positions
        positions = self.position_encoder(freq_indices, rotation)

        # Get colors
        colors = self.color_encoder(freq_indices, amplitude)

        # Get sizes
        sizes = self.amplitude_encoder(amplitude, freq_indices)

        # Apply temporal effects if provided
        if temporal_features is not None:
            effects = self.temporal_effects(temporal_features)

            # Scale by pulse
            if 'pulse_scale' in effects:
                positions = positions * effects['pulse_scale']

            # Boost brightness
            if 'brightness_boost' in effects:
                colors = colors + effects['brightness_boost'].unsqueeze(-1)
                colors = torch.clamp(colors, 0, 1)

        # Render
        image = self.soft_render_points(positions, colors, sizes)

        # Add background (from harmony aura if available)
        if temporal_features is not None and 'aura_color' in temporal_features:
            background = temporal_features['aura_color'].view(1, 1, 3) * 0.2
            image = image + background * (1 - image.sum(dim=-1, keepdim=True).clamp(0, 1))

        return torch.clamp(image, 0, 1)


class LearnableVisualizationSystem(nn.Module):
    """
    Complete learnable visualization system.

    End-to-end trainable: audio features -> learned visualization -> classification
    """

    def __init__(self, config: Optional[LearnableVizConfig] = None):
        super().__init__()
        self.config = config or LearnableVizConfig()

        # Differentiable renderer
        self.renderer = DifferentiableSpiralRenderer(self.config)

        # Simple classifier for end-to-end training
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(self.config.output_height * self.config.output_width * 3, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 128),
            nn.ReLU(),
            nn.Linear(128, 10)  # 10 instrument classes
        )

    def forward(self,
                amplitude: torch.Tensor,
                frame_idx: int = 0,
                temporal_features: Optional[Dict[str, torch.Tensor]] = None,
                return_image: bool = False) -> Dict[str, torch.Tensor]:
        """
        End-to-end forward pass.

        Args:
            amplitude: [batch, num_freqs] - amplitude data
            frame_idx: Frame index
            temporal_features: Optional temporal features
            return_image: Whether to return rendered image

        Returns:
            Dictionary with logits and optionally image
        """
        batch_size = amplitude.shape[0]

        # Render each sample
        images = []
        for i in range(batch_size):
            img = self.renderer(amplitude[i], frame_idx, temporal_features)
            images.append(img)

        images = torch.stack(images)  # [batch, h, w, 3]

        # Classify
        # Permute to [batch, 3, h, w] for classifier
        images_chw = images.permute(0, 3, 1, 2)
        logits = self.classifier(images_chw)

        output = {'logits': logits}
        if return_image:
            output['images'] = images

        return output

    def get_visualization_params(self) -> Dict[str, torch.Tensor]:
        """Get learned visualization parameters for inspection."""
        return {
            'num_turns': self.renderer.position_encoder.num_turns,
            'spiral_scale': self.renderer.position_encoder.spiral_scale,
            'importance_weights': self.renderer.amplitude_encoder.importance_weights,
            'base_size': self.renderer.amplitude_encoder.base_size,
            'size_scale': self.renderer.amplitude_encoder.size_scale,
        }


def demo_learnable_visualization():
    """Demonstrate the learnable visualization system."""
    print("=" * 60)
    print("SYNESTHESIA 3.0 - Learnable Visualization Demo")
    print("=" * 60)

    config = LearnableVizConfig(
        num_frequency_bins=128,  # Smaller for demo
        output_width=128,
        output_height=128
    )

    system = LearnableVisualizationSystem(config)
    print(f"\nSystem created with {sum(p.numel() for p in system.parameters()):,} parameters")

    # Create dummy amplitude data
    batch_size = 4
    amplitude = torch.rand(batch_size, config.num_frequency_bins)

    # Add some structure (simulate harmonics)
    for i in range(batch_size):
        fundamental_idx = 20 + i * 10
        amplitude[i, fundamental_idx] = 1.0
        for h in range(2, 5):
            if fundamental_idx * h < config.num_frequency_bins:
                amplitude[i, fundamental_idx * h] = 0.5 ** h

    print(f"\nInput amplitude shape: {amplitude.shape}")

    # Forward pass
    print("\nRendering with learnable parameters...")
    output = system(amplitude, frame_idx=0, return_image=True)

    print(f"\nOutput logits shape: {output['logits'].shape}")
    print(f"Output image shape: {output['images'].shape}")

    # Check learned parameters
    print("\nLearned visualization parameters:")
    params = system.get_visualization_params()
    for name, value in params.items():
        if value.numel() == 1:
            print(f"  {name}: {value.item():.4f}")
        else:
            print(f"  {name}: shape {value.shape}, mean={value.mean():.4f}, std={value.std():.4f}")

    # Compute loss and gradients
    print("\nComputing gradients...")
    targets = torch.randint(0, 10, (batch_size,))
    loss = F.cross_entropy(output['logits'], targets)
    loss.backward()

    # Check that gradients flow to visualization parameters
    print("\nGradient flow check:")
    for name, param in system.renderer.position_encoder.named_parameters():
        if param.grad is not None:
            print(f"  position_encoder.{name}: grad norm = {param.grad.norm():.6f}")

    for name, param in system.renderer.color_encoder.named_parameters():
        if param.grad is not None:
            print(f"  color_encoder.{name}: grad norm = {param.grad.norm():.6f}")

    # Save sample image
    sample_img = output['images'][0].detach().numpy()
    sample_img = (sample_img * 255).astype(np.uint8)

    from PIL import Image
    img = Image.fromarray(sample_img)
    img.save("learnable_viz_sample.png")
    print(f"\n✅ Sample image saved to: learnable_viz_sample.png")

    print("\n✅ Learnable visualization demo complete!")


if __name__ == "__main__":
    demo_learnable_visualization()
