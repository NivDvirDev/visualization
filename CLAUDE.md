# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SYNESTHESIA is a psychoacoustic visualization system that transforms audio into visual representations using cochlear spiral patterns. The project combines audio signal processing (originally MATLAB, now Python) with deep learning classification.

## Project Structure

- `04_Code/synesthesia2/` - Main Python visualization pipeline (SYNESTHESIA 2.0/3.0)
- `04_Code/modern_classifier/` - PyTorch Vision Transformer (ViT) and Audio Spectrogram Transformer (AST) classifiers
- `04_Code/Mesh3/` - Original MATLAB implementation
- `04_Code/synesthesia2/synesthesia_eval/` - Evaluation framework (auto-labeling, dataset, scoring)
- `04_Code/synesthesia2/synesthesia_eval/web-labeler/` - Crowd-sourcing labeling platform (Node.js/React)
- `VISUALIZATION_LAWS.md` - Research-validated visualization parameters

Component-specific instructions are in `.claude/rules/` (web-labeler, evaluation, classifier, visualization).

## Commands

### Video Generation

```bash
# Generate visualization from audio
cd 04_Code/synesthesia2
python synesthesia_cli.py input.wav -o output.mp4

# 4K output
python synesthesia_cli.py input.wav -o output.mp4 --4k

# Specific time range
python synesthesia_cli.py input.wav -o output.mp4 --start 30 --duration 60

# Demo with synthetic audio
python synesthesia_cli.py --demo -o demo.mp4
```

### Classifier Training

```bash
cd 04_Code/modern_classifier
pip install -r requirements.txt

# Train ViT classifier on spiral visualizations
python train.py --model vit --data_dir ../data --epochs 50

# Train smaller model (limited GPU memory)
python train.py --model vit-small --data_dir ../data --epochs 50

# Evaluate with attention visualization
python evaluate.py --model vit --checkpoint checkpoints/best_model.pt --visualize_attention
```

### Research Framework

```bash
cd 04_Code/synesthesia2/research

# Build synthetic audio dataset
python research_cli.py build-dataset -o ./data -n 100

# Run parameter study
python research_cli.py run-study -d ./data/metadata.json -o ./experiments --space spiral

# Full research pipeline
python research_cli.py full-pipeline -o ./research --num-experiments 20
```

### Evaluation & Labeling

```bash
# Auto-label clips with Gemini AI
export GEMINI_API_KEY="your-key"
cd 04_Code/synesthesia2
.venv/bin/python synesthesia_eval/tools/auto_labeler.py

# Web labeler (live): https://synesthesia-labeler.onrender.com
# Local dev:
cd 04_Code/synesthesia2/synesthesia_eval/web-labeler
cd server && npm run dev   # Backend (port 3001)
cd client && npm start     # Frontend (port 3000)
```

## Architecture

### Audio Analysis Pipeline

`AudioAnalyzer` (audio_analyzer.py) extracts frequency data using:
1. Logarithmically-spaced frequency bins (20Hz-8kHz) matching cochlear tonotopy
2. ISO 226 equal-loudness contour normalization
3. Complex exponential kernel for frequency analysis (ported from MATLAB's record15_LEF.m)
4. Optional GPU acceleration via CuPy

### Visualization Pipeline

`VideoGenerator` orchestrates:
1. `AudioAnalyzer` - Extract amplitude/phase per frame
2. `FastSpiralRenderer` - Render 2D cochlear spiral using PIL
3. FFmpeg - Encode frames with synchronized audio

### Classification Models

- `ViTClassifier` - Vision Transformer using timm library with attention extraction for overlay visualization
- `ASTClassifier` - Audio Spectrogram Transformer adapted for spiral images

## Key Parameters (from VISUALIZATION_LAWS.md)

These are research-validated optimal values:
- Trail length: 10 frames (decay: 0.70)
- Color mapping: Rainbow with mel-scale normalization, saturation 0.95
- Harmony blend time: 4.0 seconds
- Rhythm intensity: 0.50
- Atmosphere window: 60 seconds
- Spiral: 3.5 turns, logarithmic frequency mapping

## Dependencies

Core: torch, torchvision, torchaudio, timm, transformers, librosa, numpy, scipy, Pillow
Video: FFmpeg (system installation required)
GPU (optional): CuPy for audio analysis acceleration
