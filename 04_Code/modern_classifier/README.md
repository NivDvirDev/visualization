# Modern Classifier for Psychoacoustic Visual Recognition

This module provides PyTorch implementations of Vision Transformer (ViT) and Audio Spectrogram Transformer (AST) for classifying your spiral cochlear visualizations.

## Project Structure

```
modern_classifier/
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── config.py             # Configuration settings
├── dataset.py            # Data loading for spiral visualizations
├── models/
│   ├── __init__.py
│   ├── vit_classifier.py  # Vision Transformer implementation
│   └── ast_classifier.py  # Audio Spectrogram Transformer implementation
├── train.py              # Training script
├── evaluate.py           # Evaluation and analysis
└── demo.py               # Real-time inference demo
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Prepare Your Data

Organize your spiral visualization images:
```
data/
├── train/
│   ├── piano/
│   │   ├── frame_001.jpg
│   │   └── ...
│   ├── guitar/
│   └── ...
└── val/
    ├── piano/
    └── ...
```

### 3. Train the Model

```bash
# Train ViT (recommended to start)
python train.py --model vit --data_dir ../data --epochs 50

# Train AST
python train.py --model ast --data_dir ../data --epochs 50
```

### 4. Evaluate

```bash
python evaluate.py --model vit --checkpoint checkpoints/best_model.pt
```

## Model Options

| Model | Description | Best For |
|-------|-------------|----------|
| `vit` | Vision Transformer (ViT-B/16) | General image classification, good starting point |
| `ast` | Audio Spectrogram Transformer | Audio-optimized, may need adaptation for spirals |
| `vit-small` | Smaller ViT variant | Limited GPU memory |

## Expected Results

Based on similar work, you should expect:
- **ViT**: 75-85% accuracy on instrument classification
- **AST**: 80-90% accuracy (if spiral format is compatible)
- **Your current CNN**: ~65-70% (baseline to beat)

## Next Steps After Training

1. **Attention Analysis**: Use `evaluate.py --visualize_attention` to see what the model focuses on
2. **Error Analysis**: Identify which instruments are confused
3. **Real-time Demo**: Run `demo.py` for live classification
