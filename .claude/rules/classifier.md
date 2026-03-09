---
paths:
  - "04_Code/modern_classifier/**"
---

# AI Classifier

Vision Transformer (ViT) and Audio Spectrogram Transformer (AST) for instrument recognition from spiral visualization frames.

## Status

- **ViT accuracy:** 100% instrument recognition on spiral frames
- Fine-tuned using timm library with attention rollout for explainability
- AST variant available for audio spectrogram inputs

## Commands

```bash
cd 04_Code/modern_classifier
pip install -r requirements.txt

# Train
python train.py --model vit --data_dir ../data --epochs 50
python train.py --model vit-small --data_dir ../data --epochs 50

# Evaluate with attention visualization
python evaluate.py --model vit --checkpoint checkpoints/best_model.pt --visualize_attention
```

## Key Files

| File | Description |
|------|-------------|
| train.py | ViT/AST training loop |
| evaluate.py | Evaluation + attention visualization |
| config.py | Model configuration |
| dataset.py | Data loading utilities |
| checkpoints/ | Saved model weights |
