"""
Configuration settings for the modern classifier.
Adjust these based on your dataset and hardware.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import torch


@dataclass
class DataConfig:
    """Data configuration."""
    # Path to your spiral visualization data
    data_dir: str = "../data"

    # Image settings (your spiral visualizations)
    image_size: int = 224  # ViT/AST standard input size

    # Your instrument classes (update based on your dataset)
    classes: List[str] = field(default_factory=lambda: [
        "piano", "guitar", "violin", "flute", "clarinet",
        "trumpet", "saxophone", "drums", "bass", "cello"
    ])

    # Data split
    train_split: float = 0.8
    val_split: float = 0.1
    test_split: float = 0.1

    # Data loading
    num_workers: int = 4
    pin_memory: bool = True


@dataclass
class ModelConfig:
    """Model configuration."""
    # Model type: "vit", "vit-small", "ast"
    model_type: str = "vit"

    # ViT settings
    vit_model_name: str = "vit_base_patch16_224"  # From timm
    vit_pretrained: bool = True

    # AST settings
    ast_model_name: str = "MIT/ast-finetuned-audioset-10-10-0.4593"

    # Common settings
    dropout: float = 0.1
    num_classes: int = 10  # Update based on your classes


@dataclass
class TrainingConfig:
    """Training configuration."""
    # Basic training
    epochs: int = 50
    batch_size: int = 32

    # Optimizer
    learning_rate: float = 1e-4
    weight_decay: float = 0.01

    # Learning rate scheduler
    lr_scheduler: str = "cosine"  # "cosine", "step", "plateau"
    warmup_epochs: int = 5

    # Early stopping
    patience: int = 10
    min_delta: float = 0.001

    # Checkpointing
    checkpoint_dir: str = "checkpoints"
    save_best_only: bool = True

    # Logging
    log_every_n_steps: int = 10
    use_wandb: bool = False
    wandb_project: str = "psychoacoustic-visual"

    # Device
    device: str = "cuda" if torch.cuda.is_available() else "cpu"

    # Mixed precision training (faster on modern GPUs)
    use_amp: bool = True


@dataclass
class AugmentationConfig:
    """Data augmentation settings."""
    # Geometric augmentations
    random_horizontal_flip: bool = False  # Probably not useful for spiral
    random_rotation: float = 15.0  # Degrees - may help for spiral
    random_crop_scale: tuple = (0.8, 1.0)

    # Color augmentations
    color_jitter: bool = True
    color_jitter_brightness: float = 0.2
    color_jitter_contrast: float = 0.2
    color_jitter_saturation: float = 0.2
    color_jitter_hue: float = 0.1

    # Regularization
    mixup_alpha: float = 0.0  # Set > 0 to enable mixup
    cutmix_alpha: float = 0.0  # Set > 0 to enable cutmix

    # Normalize to ImageNet stats (for pretrained models)
    normalize_mean: tuple = (0.485, 0.456, 0.406)
    normalize_std: tuple = (0.229, 0.224, 0.225)


def get_config():
    """Get default configuration."""
    return {
        "data": DataConfig(),
        "model": ModelConfig(),
        "training": TrainingConfig(),
        "augmentation": AugmentationConfig()
    }


def print_config(config: dict):
    """Pretty print configuration."""
    for section_name, section in config.items():
        print(f"\n[{section_name}]")
        for key, value in vars(section).items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    config = get_config()
    print_config(config)
