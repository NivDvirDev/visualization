"""
Training script for modern classifiers on spiral visualizations.

Usage:
    python train.py --model vit --data_dir ../data --epochs 50
    python train.py --model ast --data_dir ../data --epochs 50 --batch_size 16
"""

import argparse
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

import torch
import torch.nn as nn
import torch.optim as optim
from torch.cuda.amp import GradScaler, autocast
from torch.utils.tensorboard import SummaryWriter
from tqdm import tqdm
import numpy as np

from config import get_config, DataConfig, TrainingConfig, AugmentationConfig
from dataset import (
    create_dataloaders,
    create_dataloaders_from_single_folder,
    get_transforms,
    SpiralVisualizationDataset
)
from models import create_vit_model, create_ast_model


def parse_args():
    parser = argparse.ArgumentParser(description="Train classifier on spiral visualizations")

    # Model
    parser.add_argument("--model", type=str, default="vit",
                        choices=["vit", "vit-small", "vit-tiny", "ast"],
                        help="Model architecture")
    parser.add_argument("--pretrained", action="store_true", default=False,
                        help="Use pretrained weights (requires internet)")
    parser.add_argument("--no_pretrained", action="store_true", default=False,
                        help="Explicitly disable pretrained weights")
    parser.add_argument("--freeze_backbone", action="store_true",
                        help="Freeze backbone, only train classifier head")

    # Data
    parser.add_argument("--data_dir", type=str, default="../data",
                        help="Path to data directory")
    parser.add_argument("--image_size", type=int, default=224,
                        help="Input image size")
    parser.add_argument("--num_classes", type=int, default=10,
                        help="Number of classes")

    # Training
    parser.add_argument("--epochs", type=int, default=50,
                        help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=32,
                        help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4,
                        help="Learning rate")
    parser.add_argument("--weight_decay", type=float, default=0.01,
                        help="Weight decay")

    # Hardware
    parser.add_argument("--device", type=str, default="auto",
                        help="Device (cuda, cpu, or auto)")
    parser.add_argument("--num_workers", type=int, default=4,
                        help="Number of data loading workers")
    parser.add_argument("--use_amp", action="store_true", default=True,
                        help="Use automatic mixed precision")

    # Checkpointing
    parser.add_argument("--checkpoint_dir", type=str, default="checkpoints",
                        help="Directory to save checkpoints")
    parser.add_argument("--resume", type=str, default=None,
                        help="Path to checkpoint to resume from")

    # Logging
    parser.add_argument("--log_dir", type=str, default="logs",
                        help="TensorBoard log directory")
    parser.add_argument("--experiment_name", type=str, default=None,
                        help="Experiment name for logging")

    return parser.parse_args()


class Trainer:
    """Training manager."""

    def __init__(
        self,
        model: nn.Module,
        train_loader,
        val_loader,
        config: Dict[str, Any],
        device: str = "cuda"
    ):
        self.model = model.to(device)
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.config = config
        self.device = device

        # Loss function
        self.criterion = nn.CrossEntropyLoss()

        # Optimizer
        self.optimizer = optim.AdamW(
            model.parameters(),
            lr=config["lr"],
            weight_decay=config["weight_decay"]
        )

        # Learning rate scheduler
        self.scheduler = optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer,
            T_max=config["epochs"],
            eta_min=config["lr"] * 0.01
        )

        # Mixed precision
        self.scaler = GradScaler() if config.get("use_amp", True) else None

        # Checkpointing
        self.checkpoint_dir = Path(config["checkpoint_dir"])
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Logging
        log_dir = Path(config["log_dir"])
        experiment_name = config.get("experiment_name") or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.writer = SummaryWriter(log_dir / experiment_name)

        # Tracking
        self.best_val_acc = 0.0
        self.current_epoch = 0

    def train_epoch(self) -> Dict[str, float]:
        """Train for one epoch."""
        self.model.train()
        total_loss = 0.0
        correct = 0
        total = 0

        pbar = tqdm(self.train_loader, desc=f"Epoch {self.current_epoch}")

        for batch_idx, (images, labels) in enumerate(pbar):
            images = images.to(self.device)
            labels = labels.to(self.device)

            # Forward pass
            self.optimizer.zero_grad()

            if self.scaler:
                with autocast():
                    outputs = self.model(images)
                    loss = self.criterion(outputs, labels)

                self.scaler.scale(loss).backward()
                self.scaler.step(self.optimizer)
                self.scaler.update()
            else:
                outputs = self.model(images)
                loss = self.criterion(outputs, labels)
                loss.backward()
                self.optimizer.step()

            # Track metrics
            total_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

            # Update progress bar
            pbar.set_postfix({
                "loss": f"{loss.item():.4f}",
                "acc": f"{100.*correct/total:.2f}%"
            })

        avg_loss = total_loss / len(self.train_loader)
        accuracy = 100. * correct / total

        return {"loss": avg_loss, "accuracy": accuracy}

    @torch.no_grad()
    def validate(self) -> Dict[str, float]:
        """Validate the model."""
        self.model.eval()
        total_loss = 0.0
        correct = 0
        total = 0

        for images, labels in tqdm(self.val_loader, desc="Validating"):
            images = images.to(self.device)
            labels = labels.to(self.device)

            outputs = self.model(images)
            loss = self.criterion(outputs, labels)

            total_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

        avg_loss = total_loss / len(self.val_loader)
        accuracy = 100. * correct / total

        return {"loss": avg_loss, "accuracy": accuracy}

    def save_checkpoint(self, filename: str, is_best: bool = False):
        """Save checkpoint."""
        checkpoint = {
            "epoch": self.current_epoch,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "scheduler_state_dict": self.scheduler.state_dict(),
            "best_val_acc": self.best_val_acc,
            "config": self.config
        }

        torch.save(checkpoint, self.checkpoint_dir / filename)

        if is_best:
            torch.save(checkpoint, self.checkpoint_dir / "best_model.pt")

    def load_checkpoint(self, path: str):
        """Load checkpoint."""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
        self.current_epoch = checkpoint["epoch"]
        self.best_val_acc = checkpoint["best_val_acc"]
        print(f"Loaded checkpoint from epoch {self.current_epoch}")

    def train(self, num_epochs: int):
        """Full training loop."""
        print(f"\nStarting training for {num_epochs} epochs")
        print(f"Device: {self.device}")
        print(f"Model parameters: {sum(p.numel() for p in self.model.parameters()):,}")
        print(f"Trainable parameters: {sum(p.numel() for p in self.model.parameters() if p.requires_grad):,}")
        print("-" * 50)

        for epoch in range(self.current_epoch, num_epochs):
            self.current_epoch = epoch

            # Train
            train_metrics = self.train_epoch()

            # Validate
            val_metrics = self.validate()

            # Update scheduler
            self.scheduler.step()

            # Log metrics
            self.writer.add_scalar("Loss/train", train_metrics["loss"], epoch)
            self.writer.add_scalar("Loss/val", val_metrics["loss"], epoch)
            self.writer.add_scalar("Accuracy/train", train_metrics["accuracy"], epoch)
            self.writer.add_scalar("Accuracy/val", val_metrics["accuracy"], epoch)
            self.writer.add_scalar("LR", self.scheduler.get_last_lr()[0], epoch)

            # Print summary
            print(f"\nEpoch {epoch}/{num_epochs-1}")
            print(f"  Train Loss: {train_metrics['loss']:.4f}, Acc: {train_metrics['accuracy']:.2f}%")
            print(f"  Val Loss: {val_metrics['loss']:.4f}, Acc: {val_metrics['accuracy']:.2f}%")

            # Save checkpoint
            is_best = val_metrics["accuracy"] > self.best_val_acc
            if is_best:
                self.best_val_acc = val_metrics["accuracy"]
                print(f"  New best accuracy: {self.best_val_acc:.2f}%")

            self.save_checkpoint(f"checkpoint_epoch_{epoch}.pt", is_best)

        print("\nTraining complete!")
        print(f"Best validation accuracy: {self.best_val_acc:.2f}%")

        self.writer.close()


def main():
    args = parse_args()

    # Device
    if args.device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        device = args.device
    print(f"Using device: {device}")

    # Get config
    config = get_config()

    # Create model
    print(f"\nCreating {args.model} model...")
    if args.model.startswith("vit"):
        size_map = {"vit": "base", "vit-small": "small", "vit-tiny": "tiny"}
        model = create_vit_model(
            num_classes=args.num_classes,
            model_size=size_map.get(args.model, "base"),
            pretrained=args.pretrained,
            freeze_backbone=args.freeze_backbone
        )
    elif args.model == "ast":
        model = create_ast_model(
            num_classes=args.num_classes,
            pretrained=args.pretrained,
            use_simple=True  # Use simplified version for images
        )
    else:
        raise ValueError(f"Unknown model: {args.model}")

    # Create dataloaders
    print(f"\nLoading data from {args.data_dir}...")
    data_path = Path(args.data_dir)

    # Update augmentation config
    config["augmentation"].normalize_mean = (0.485, 0.456, 0.406)
    config["augmentation"].normalize_std = (0.229, 0.224, 0.225)

    # Check data structure
    if (data_path / "train").exists() and (data_path / "val").exists():
        # Pre-split data
        config["data"].data_dir = str(data_path)
        config["data"].image_size = args.image_size
        train_loader, val_loader, _ = create_dataloaders(
            config["data"],
            config["augmentation"],
            batch_size=args.batch_size
        )
    else:
        # Auto-split data
        train_loader, val_loader = create_dataloaders_from_single_folder(
            str(data_path),
            config["augmentation"],
            image_size=args.image_size,
            batch_size=args.batch_size,
            num_workers=args.num_workers
        )

    # Training config
    train_config = {
        "epochs": args.epochs,
        "lr": args.lr,
        "weight_decay": args.weight_decay,
        "use_amp": args.use_amp and device == "cuda",
        "checkpoint_dir": args.checkpoint_dir,
        "log_dir": args.log_dir,
        "experiment_name": args.experiment_name or f"{args.model}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    }

    # Create trainer
    trainer = Trainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        config=train_config,
        device=device
    )

    # Resume from checkpoint if specified
    if args.resume:
        trainer.load_checkpoint(args.resume)

    # Train
    trainer.train(args.epochs)


if __name__ == "__main__":
    main()
