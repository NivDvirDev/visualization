# Quick Start Guide: Modern Classifier for Psychoacoustic Visual Recognition

This guide will help you get started with training modern neural networks (ViT, AST) on your spiral cochlear visualizations.

## What's Included

```
modern_classifier/
├── generate_spiral.py     # Convert audio → spiral images (Python replacement for MATLAB)
├── train_simple.py        # Simple training script (works everywhere)
├── train.py               # Full training script (needs GPU for best results)
├── evaluate.py            # Evaluation with confusion matrix & attention maps
├── config.py              # Configuration settings
├── dataset.py             # Data loading utilities
├── models/
│   ├── vit_classifier.py  # Vision Transformer
│   └── ast_classifier.py  # Audio Spectrogram Transformer
├── data/                  # Demo dataset (auto-generated)
└── checkpoints/           # Saved models
```

---

## Quick Start (5 minutes)

### Step 1: Install Dependencies

```bash
pip install torch torchvision timm pillow numpy scikit-learn tqdm
```

### Step 2: Generate Demo Data

```bash
python generate_spiral.py demo --output_dir data --num_classes 5 --samples 100
```

### Step 3: Train

```bash
python train_simple.py --data_dir data --epochs 10
```

### Step 4: Check Results

After training, you'll see:
- Best validation accuracy printed to console
- Model saved to `checkpoints/best_model_simple.pt`

---

## Using Your Own Audio Data

### Option A: Generate from Audio Files

If you have audio files organized by instrument:

```
my_audio/
├── piano/
│   ├── song1.wav
│   ├── song2.wav
├── guitar/
│   ├── song1.wav
└── ...
```

Run:
```bash
# Install librosa for audio processing
pip install librosa

# Generate spiral visualization dataset
python generate_spiral.py batch --input_dir my_audio --output_dir data --max_frames 50
```

### Option B: Use Existing Frames

If you already have spiral visualization frames from the MATLAB pipeline:

1. Organize them into folders by class:
```
data/
├── train/
│   ├── piano/
│   │   ├── frame_001.jpg
│   │   └── ...
│   └── guitar/
│       └── ...
└── val/
    ├── piano/
    └── guitar/
```

2. Run training directly:
```bash
python train_simple.py --data_dir data --epochs 20
```

---

## Training on GPU (Recommended for Real Results)

For best results, train on a machine with GPU:

```bash
# Using ViT (recommended)
python train.py --model vit-small --data_dir data --epochs 50 --batch_size 32 --pretrained

# Using AST
python train.py --model ast --data_dir data --epochs 50 --batch_size 32
```

### Expected Results

| Model | Demo Data (5 classes) | Real Data (10 instruments) |
|-------|----------------------|---------------------------|
| Simple CNN | 85-90% | 70-80% |
| ViT-small | 90-95% | 80-90% |
| AST | 92-97% | 85-95% |

*Note: Real data results depend on dataset size and quality*

---

## Evaluating Your Model

```bash
python evaluate.py --checkpoint checkpoints/best_model_simple.pt --data_dir data/val

# With attention visualization (ViT only)
python evaluate.py --checkpoint checkpoints/best_model.pt --visualize_attention
```

This generates:
- `evaluation_results/confusion_matrix.png` - See which classes are confused
- `evaluation_results/per_class_metrics.png` - Precision/recall per instrument
- `evaluation_results/attention/` - What the model focuses on (ViT only)

---

## Next Steps

1. **Expand dataset**: More samples per class = better generalization
2. **Try ViT**: Once you have real data, train ViT for better results
3. **Analyze attention**: See what visual features the model uses
4. **Compare to baseline**: Beat the original 65-70% instrument accuracy!

---

## Troubleshooting

**"No module named 'timm'"**
```bash
pip install timm
```

**"CUDA out of memory"**
- Reduce batch size: `--batch_size 8`
- Use smaller model: `--model vit-tiny`

**"librosa not found"**
```bash
pip install librosa soundfile
```

**Training is slow (CPU only)**
- This is normal without GPU
- Use `train_simple.py` for faster iteration
- For real training, use Google Colab (free GPU) or cloud GPU

---

## Files You Can Delete

- `data/` - Regenerate anytime with `generate_spiral.py demo`
- `checkpoints/` - Models from training
- `logs/` - TensorBoard logs
- `evaluation_results/` - Evaluation outputs
