"""
Evaluation script with confusion matrix and attention visualization.

Usage:
    python evaluate.py --checkpoint checkpoints/best_model.pt --data_dir ../data
    python evaluate.py --checkpoint checkpoints/best_model.pt --visualize_attention
"""

import argparse
from pathlib import Path
from typing import List, Optional, Dict

import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    confusion_matrix, classification_report,
    precision_recall_fscore_support, accuracy_score
)
from tqdm import tqdm

from config import get_config
from dataset import get_transforms, SpiralVisualizationDataset
from models import create_vit_model, create_ast_model


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate classifier")

    parser.add_argument("--checkpoint", type=str, required=True,
                        help="Path to model checkpoint")
    parser.add_argument("--data_dir", type=str, default="../data/test",
                        help="Path to test data")
    parser.add_argument("--output_dir", type=str, default="evaluation_results",
                        help="Output directory for results")
    parser.add_argument("--batch_size", type=int, default=32,
                        help="Batch size")
    parser.add_argument("--device", type=str, default="auto",
                        help="Device")

    # Visualization options
    parser.add_argument("--visualize_attention", action="store_true",
                        help="Generate attention visualizations")
    parser.add_argument("--num_attention_samples", type=int, default=10,
                        help="Number of samples to visualize attention for")
    parser.add_argument("--visualize_errors", action="store_true",
                        help="Visualize misclassified samples")

    return parser.parse_args()


def load_model(checkpoint_path: str, device: str) -> nn.Module:
    """Load model from checkpoint."""
    checkpoint = torch.load(checkpoint_path, map_location=device)

    # Infer model type from config or checkpoint
    config = checkpoint.get("config", {})
    num_classes = config.get("num_classes", 10)

    # Try to determine model type
    state_dict = checkpoint["model_state_dict"]

    # Check for ViT-specific keys
    if any("backbone" in k and "blocks" in k for k in state_dict.keys()):
        model = create_vit_model(num_classes=num_classes, model_size="small")
    else:
        model = create_ast_model(num_classes=num_classes, use_simple=True)

    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    return model


def evaluate(
    model: nn.Module,
    dataloader,
    device: str,
    class_names: Optional[List[str]] = None
) -> Dict:
    """
    Evaluate model and return metrics.

    Returns:
        Dictionary with metrics and predictions
    """
    model.eval()
    all_preds = []
    all_labels = []
    all_probs = []

    with torch.no_grad():
        for images, labels in tqdm(dataloader, desc="Evaluating"):
            images = images.to(device)

            outputs = model(images)
            probs = torch.softmax(outputs, dim=1)
            _, preds = outputs.max(1)

            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.numpy())
            all_probs.extend(probs.cpu().numpy())

    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)
    all_probs = np.array(all_probs)

    # Calculate metrics
    accuracy = accuracy_score(all_labels, all_preds)
    precision, recall, f1, _ = precision_recall_fscore_support(
        all_labels, all_preds, average='weighted'
    )

    # Per-class metrics
    per_class_precision, per_class_recall, per_class_f1, support = \
        precision_recall_fscore_support(all_labels, all_preds, average=None)

    # Confusion matrix
    cm = confusion_matrix(all_labels, all_preds)

    # Classification report
    if class_names:
        report = classification_report(all_labels, all_preds, target_names=class_names)
    else:
        report = classification_report(all_labels, all_preds)

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "per_class_precision": per_class_precision,
        "per_class_recall": per_class_recall,
        "per_class_f1": per_class_f1,
        "confusion_matrix": cm,
        "classification_report": report,
        "predictions": all_preds,
        "labels": all_labels,
        "probabilities": all_probs
    }


def plot_confusion_matrix(
    cm: np.ndarray,
    class_names: List[str],
    save_path: str,
    normalize: bool = True
):
    """Plot confusion matrix."""
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

    plt.figure(figsize=(12, 10))
    sns.heatmap(
        cm,
        annot=True,
        fmt='.2f' if normalize else 'd',
        cmap='Blues',
        xticklabels=class_names,
        yticklabels=class_names
    )
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title('Confusion Matrix')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()


def plot_per_class_metrics(
    metrics: Dict,
    class_names: List[str],
    save_path: str
):
    """Plot per-class precision, recall, F1."""
    x = np.arange(len(class_names))
    width = 0.25

    fig, ax = plt.subplots(figsize=(14, 6))

    ax.bar(x - width, metrics["per_class_precision"], width, label='Precision')
    ax.bar(x, metrics["per_class_recall"], width, label='Recall')
    ax.bar(x + width, metrics["per_class_f1"], width, label='F1')

    ax.set_xlabel('Class')
    ax.set_ylabel('Score')
    ax.set_title('Per-Class Metrics')
    ax.set_xticks(x)
    ax.set_xticklabels(class_names, rotation=45, ha='right')
    ax.legend()
    ax.set_ylim(0, 1)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()


def visualize_attention_samples(
    model: nn.Module,
    dataset,
    device: str,
    output_dir: Path,
    num_samples: int = 10,
    class_names: Optional[List[str]] = None
):
    """Visualize attention maps for sample images."""
    from models.vit_classifier import visualize_attention

    output_dir.mkdir(parents=True, exist_ok=True)

    # Get random samples
    indices = np.random.choice(len(dataset), min(num_samples, len(dataset)), replace=False)

    for i, idx in enumerate(indices):
        image, label = dataset[idx]
        image = image.unsqueeze(0).to(device)

        # Get prediction
        with torch.no_grad():
            output = model(image)
            pred = output.argmax(1).item()
            prob = torch.softmax(output, dim=1)[0, pred].item()

        # Get class names
        true_name = class_names[label] if class_names else str(label)
        pred_name = class_names[pred] if class_names else str(pred)

        # Visualize attention
        save_path = output_dir / f"attention_{i}_{true_name}_pred_{pred_name}.png"
        visualize_attention(model, image, save_path=str(save_path))

        print(f"Saved attention visualization: {save_path}")


def visualize_errors(
    metrics: Dict,
    dataset,
    output_dir: Path,
    class_names: Optional[List[str]] = None,
    max_errors: int = 20
):
    """Visualize misclassified samples."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find errors
    errors = np.where(metrics["predictions"] != metrics["labels"])[0]

    if len(errors) == 0:
        print("No errors to visualize!")
        return

    # Sample errors
    error_indices = errors[:min(max_errors, len(errors))]

    fig, axes = plt.subplots(4, 5, figsize=(20, 16))
    axes = axes.flatten()

    for i, idx in enumerate(error_indices):
        if i >= len(axes):
            break

        image, _ = dataset[idx]

        # Denormalize
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        img_np = image.permute(1, 2, 0).numpy()
        img_np = img_np * std + mean
        img_np = np.clip(img_np, 0, 1)

        true_label = metrics["labels"][idx]
        pred_label = metrics["predictions"][idx]
        prob = metrics["probabilities"][idx][pred_label]

        true_name = class_names[true_label] if class_names else str(true_label)
        pred_name = class_names[pred_label] if class_names else str(pred_label)

        axes[i].imshow(img_np)
        axes[i].set_title(f"True: {true_name}\nPred: {pred_name} ({prob:.2f})", fontsize=10)
        axes[i].axis('off')

    # Hide unused axes
    for i in range(len(error_indices), len(axes)):
        axes[i].axis('off')

    plt.tight_layout()
    plt.savefig(output_dir / "misclassified_samples.png", dpi=150)
    plt.close()

    print(f"Saved error visualization with {len(error_indices)} samples")


def main():
    args = parse_args()

    # Device
    if args.device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        device = args.device
    print(f"Using device: {device}")

    # Output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load model
    print(f"\nLoading model from {args.checkpoint}...")
    model = load_model(args.checkpoint, device)

    # Load data
    print(f"\nLoading data from {args.data_dir}...")
    config = get_config()
    transform = get_transforms(config["augmentation"], is_training=False)

    dataset = SpiralVisualizationDataset(
        args.data_dir,
        transform=transform
    )

    dataloader = torch.utils.data.DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=4
    )

    class_names = dataset.classes
    print(f"Classes: {class_names}")

    # Evaluate
    print("\nEvaluating...")
    metrics = evaluate(model, dataloader, device, class_names)

    # Print results
    print("\n" + "="*50)
    print("EVALUATION RESULTS")
    print("="*50)
    print(f"\nOverall Accuracy: {metrics['accuracy']*100:.2f}%")
    print(f"Precision (weighted): {metrics['precision']*100:.2f}%")
    print(f"Recall (weighted): {metrics['recall']*100:.2f}%")
    print(f"F1 Score (weighted): {metrics['f1']*100:.2f}%")
    print("\nClassification Report:")
    print(metrics['classification_report'])

    # Save results
    results_file = output_dir / "evaluation_results.txt"
    with open(results_file, 'w') as f:
        f.write("EVALUATION RESULTS\n")
        f.write("="*50 + "\n\n")
        f.write(f"Checkpoint: {args.checkpoint}\n")
        f.write(f"Data: {args.data_dir}\n\n")
        f.write(f"Overall Accuracy: {metrics['accuracy']*100:.2f}%\n")
        f.write(f"Precision (weighted): {metrics['precision']*100:.2f}%\n")
        f.write(f"Recall (weighted): {metrics['recall']*100:.2f}%\n")
        f.write(f"F1 Score (weighted): {metrics['f1']*100:.2f}%\n\n")
        f.write("Classification Report:\n")
        f.write(metrics['classification_report'])

    print(f"\nResults saved to {results_file}")

    # Plot confusion matrix
    plot_confusion_matrix(
        metrics["confusion_matrix"],
        class_names,
        output_dir / "confusion_matrix.png"
    )
    print(f"Confusion matrix saved to {output_dir / 'confusion_matrix.png'}")

    # Plot per-class metrics
    plot_per_class_metrics(
        metrics,
        class_names,
        output_dir / "per_class_metrics.png"
    )
    print(f"Per-class metrics saved to {output_dir / 'per_class_metrics.png'}")

    # Visualize attention
    if args.visualize_attention:
        print("\nGenerating attention visualizations...")
        visualize_attention_samples(
            model, dataset, device,
            output_dir / "attention",
            num_samples=args.num_attention_samples,
            class_names=class_names
        )

    # Visualize errors
    if args.visualize_errors:
        print("\nVisualizing misclassified samples...")
        visualize_errors(
            metrics, dataset,
            output_dir / "errors",
            class_names=class_names
        )

    print(f"\nAll results saved to {output_dir}")


if __name__ == "__main__":
    main()
