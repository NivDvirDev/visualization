"""
Dataset module for loading spiral cochlear visualizations.
Handles both image folders and video frames.
"""

import os
from pathlib import Path
from typing import Optional, Tuple, List, Callable

import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
import numpy as np

from config import DataConfig, AugmentationConfig


class SpiralVisualizationDataset(Dataset):
    """
    Dataset for spiral cochlear visualization images.

    Expects data organized as:
        data_dir/
            class_1/
                image_001.jpg
                image_002.jpg
            class_2/
                ...

    Or for video frames:
        data_dir/
            class_1/
                video_1/
                    frame_001.jpg
                    frame_002.jpg
                video_2/
                    ...
            class_2/
                ...
    """

    def __init__(
        self,
        data_dir: str,
        transform: Optional[Callable] = None,
        classes: Optional[List[str]] = None,
        flatten_videos: bool = True
    ):
        """
        Args:
            data_dir: Root directory containing class folders
            transform: Optional transform to apply to images
            classes: Optional list of class names (inferred from folders if None)
            flatten_videos: If True, treat each frame as separate sample
        """
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.flatten_videos = flatten_videos

        # Get class names
        if classes is not None:
            self.classes = classes
        else:
            self.classes = sorted([
                d.name for d in self.data_dir.iterdir()
                if d.is_dir() and not d.name.startswith('.')
            ])

        self.class_to_idx = {cls: idx for idx, cls in enumerate(self.classes)}

        # Collect all image paths and labels
        self.samples = self._collect_samples()

        print(f"Loaded {len(self.samples)} samples from {len(self.classes)} classes")

    def _collect_samples(self) -> List[Tuple[Path, int]]:
        """Collect all image paths and their labels."""
        samples = []
        valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}

        for class_name in self.classes:
            class_dir = self.data_dir / class_name
            if not class_dir.exists():
                print(f"Warning: Class directory not found: {class_dir}")
                continue

            class_idx = self.class_to_idx[class_name]

            # Walk through directory (handles nested video folders)
            for root, _, files in os.walk(class_dir):
                for file in files:
                    if Path(file).suffix.lower() in valid_extensions:
                        samples.append((Path(root) / file, class_idx))

        return samples

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        img_path, label = self.samples[idx]

        # Load image
        image = Image.open(img_path).convert('RGB')

        # Apply transforms
        if self.transform:
            image = self.transform(image)

        return image, label


class VideoSequenceDataset(Dataset):
    """
    Dataset that returns sequences of frames (for temporal modeling).

    Each sample is a sequence of consecutive frames from a video.
    """

    def __init__(
        self,
        data_dir: str,
        sequence_length: int = 16,
        transform: Optional[Callable] = None,
        classes: Optional[List[str]] = None,
        stride: int = 1
    ):
        """
        Args:
            data_dir: Root directory containing class/video folders
            sequence_length: Number of frames per sequence
            transform: Transform to apply to each frame
            classes: Optional list of class names
            stride: Stride between sequences (for data augmentation)
        """
        self.data_dir = Path(data_dir)
        self.sequence_length = sequence_length
        self.transform = transform
        self.stride = stride

        # Get class names
        if classes is not None:
            self.classes = classes
        else:
            self.classes = sorted([
                d.name for d in self.data_dir.iterdir()
                if d.is_dir() and not d.name.startswith('.')
            ])

        self.class_to_idx = {cls: idx for idx, cls in enumerate(self.classes)}

        # Collect video sequences
        self.sequences = self._collect_sequences()

        print(f"Loaded {len(self.sequences)} sequences from {len(self.classes)} classes")

    def _collect_sequences(self) -> List[Tuple[List[Path], int]]:
        """Collect sequences of frames."""
        sequences = []
        valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}

        for class_name in self.classes:
            class_dir = self.data_dir / class_name
            if not class_dir.exists():
                continue

            class_idx = self.class_to_idx[class_name]

            # Each subdirectory is a video
            for video_dir in class_dir.iterdir():
                if not video_dir.is_dir():
                    continue

                # Get sorted frame paths
                frames = sorted([
                    f for f in video_dir.iterdir()
                    if f.suffix.lower() in valid_extensions
                ])

                # Create sequences with stride
                for start_idx in range(0, len(frames) - self.sequence_length + 1, self.stride):
                    sequence = frames[start_idx:start_idx + self.sequence_length]
                    sequences.append((sequence, class_idx))

        return sequences

    def __len__(self) -> int:
        return len(self.sequences)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        frame_paths, label = self.sequences[idx]

        # Load and transform all frames
        frames = []
        for path in frame_paths:
            image = Image.open(path).convert('RGB')
            if self.transform:
                image = self.transform(image)
            frames.append(image)

        # Stack into tensor: (T, C, H, W)
        frames_tensor = torch.stack(frames)

        return frames_tensor, label


def get_transforms(
    aug_config: AugmentationConfig,
    image_size: int = 224,
    is_training: bool = True
) -> transforms.Compose:
    """
    Get image transforms based on configuration.

    Args:
        aug_config: Augmentation configuration
        image_size: Target image size
        is_training: Whether to apply training augmentations
    """
    if is_training:
        transform_list = [
            transforms.Resize((image_size, image_size)),
            transforms.RandomResizedCrop(
                image_size,
                scale=aug_config.random_crop_scale
            ),
        ]

        if aug_config.random_horizontal_flip:
            transform_list.append(transforms.RandomHorizontalFlip())

        if aug_config.random_rotation > 0:
            transform_list.append(
                transforms.RandomRotation(aug_config.random_rotation)
            )

        if aug_config.color_jitter:
            transform_list.append(transforms.ColorJitter(
                brightness=aug_config.color_jitter_brightness,
                contrast=aug_config.color_jitter_contrast,
                saturation=aug_config.color_jitter_saturation,
                hue=aug_config.color_jitter_hue
            ))

        transform_list.extend([
            transforms.ToTensor(),
            transforms.Normalize(
                mean=aug_config.normalize_mean,
                std=aug_config.normalize_std
            )
        ])
    else:
        # Validation/test transforms (no augmentation)
        transform_list = [
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=aug_config.normalize_mean,
                std=aug_config.normalize_std
            )
        ]

    return transforms.Compose(transform_list)


def create_dataloaders(
    data_config: DataConfig,
    aug_config: AugmentationConfig,
    batch_size: int = 32
) -> Tuple[DataLoader, DataLoader, Optional[DataLoader]]:
    """
    Create train, validation, and test dataloaders.

    Expects data organized as:
        data_dir/
            train/
                class_1/
                class_2/
            val/
                ...
            test/ (optional)
                ...

    Args:
        data_config: Data configuration
        aug_config: Augmentation configuration
        batch_size: Batch size

    Returns:
        Tuple of (train_loader, val_loader, test_loader)
    """
    data_dir = Path(data_config.data_dir)

    # Get transforms
    train_transform = get_transforms(aug_config, data_config.image_size, is_training=True)
    val_transform = get_transforms(aug_config, data_config.image_size, is_training=False)

    # Create datasets
    train_dataset = SpiralVisualizationDataset(
        data_dir / "train",
        transform=train_transform,
        classes=data_config.classes
    )

    val_dataset = SpiralVisualizationDataset(
        data_dir / "val",
        transform=val_transform,
        classes=data_config.classes
    )

    # Test dataset (optional)
    test_dataset = None
    test_dir = data_dir / "test"
    if test_dir.exists():
        test_dataset = SpiralVisualizationDataset(
            test_dir,
            transform=val_transform,
            classes=data_config.classes
        )

    # Create dataloaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=data_config.num_workers,
        pin_memory=data_config.pin_memory,
        drop_last=True
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=data_config.num_workers,
        pin_memory=data_config.pin_memory
    )

    test_loader = None
    if test_dataset:
        test_loader = DataLoader(
            test_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=data_config.num_workers,
            pin_memory=data_config.pin_memory
        )

    return train_loader, val_loader, test_loader


def create_dataloaders_from_single_folder(
    data_dir: str,
    aug_config: AugmentationConfig,
    image_size: int = 224,
    batch_size: int = 32,
    train_split: float = 0.8,
    num_workers: int = 4
) -> Tuple[DataLoader, DataLoader]:
    """
    Create dataloaders from a single folder (auto-split into train/val).

    Useful when you have:
        data_dir/
            class_1/
            class_2/

    And want to automatically split into train/val.
    """
    from sklearn.model_selection import train_test_split

    # Get all samples
    full_dataset = SpiralVisualizationDataset(
        data_dir,
        transform=None  # Will apply transforms separately
    )

    # Split indices
    indices = list(range(len(full_dataset)))
    labels = [full_dataset.samples[i][1] for i in indices]

    train_indices, val_indices = train_test_split(
        indices,
        train_size=train_split,
        stratify=labels,
        random_state=42
    )

    # Create transforms
    train_transform = get_transforms(aug_config, image_size, is_training=True)
    val_transform = get_transforms(aug_config, image_size, is_training=False)

    # Create subset datasets with different transforms
    class SubsetWithTransform(Dataset):
        def __init__(self, dataset, indices, transform):
            self.dataset = dataset
            self.indices = indices
            self.transform = transform

        def __len__(self):
            return len(self.indices)

        def __getitem__(self, idx):
            img_path, label = self.dataset.samples[self.indices[idx]]
            image = Image.open(img_path).convert('RGB')
            if self.transform:
                image = self.transform(image)
            return image, label

    train_dataset = SubsetWithTransform(full_dataset, train_indices, train_transform)
    val_dataset = SubsetWithTransform(full_dataset, val_indices, val_transform)

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True
    )

    return train_loader, val_loader


if __name__ == "__main__":
    # Test the dataset
    from config import get_config

    config = get_config()

    # Test with sample data structure
    print("Testing dataset loading...")
    print(f"Looking for data in: {config['data'].data_dir}")

    # Create a simple test
    transform = get_transforms(config['augmentation'], is_training=True)
    print(f"Transform pipeline: {transform}")
