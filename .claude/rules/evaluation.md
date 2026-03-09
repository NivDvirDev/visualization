---
paths:
  - "04_Code/synesthesia2/synesthesia_eval/**"
---

# Evaluation System

Automated quality evaluation for synesthesia visualization videos.

## Data Flow (HuggingFace = single source of truth)

```
auto_labeler.py --push-hf → HuggingFace ← web-labeler (pushLabels)
                                  ↓
                        fetch_labels.py (unified_labels.json)
                                  ↓
                   DatasetLoader.load_from_huggingface()
                                  ↓
                   ScoringModel / Validation / Metrics
```

## Dataset

- **HuggingFace:** https://huggingface.co/datasets/NivDvir/synesthesia-eval
- **Clips:** 29 MP4 clips (target: 80-150 for robust training)
- **License:** CC-BY-NC-SA 4.0
- **Coverage:** ~38% of test matrix. Missing: poor sync, ambient music, classical

## Rating Dimensions (1-5 each)

1. **Sync Quality** — visual sync with beat/rhythm
2. **Visual-Audio Alignment** — visuals match audio characteristics
3. **Aesthetic Quality** — overall visual appeal
4. **Motion Smoothness** — fluid, natural motion

## Key Tools

```bash
export GEMINI_API_KEY="your-key-here"
export HF_TOKEN="your-hf-write-token"
cd /Users/guydvir/Project/04_Code/synesthesia2

# Auto-label clips with Gemini AI
.venv/bin/python synesthesia_eval/tools/auto_labeler.py              # All unlabeled
.venv/bin/python synesthesia_eval/tools/auto_labeler.py --push-hf    # Label + push to HF

# Fetch all labels (auto + human) from HuggingFace
.venv/bin/python synesthesia_eval/tools/fetch_labels.py              # Fetch + merge
.venv/bin/python synesthesia_eval/tools/fetch_labels.py --export-csv # Also export CSV

# Load dataset in Python
from synesthesia_eval.dataset.dataset_loader import DatasetLoader
dl = DatasetLoader().load_from_huggingface()                    # From HuggingFace
dl = DatasetLoader().load_from_clips_dir("data/clips", "data/auto_labels.json")  # Local
```

## Scoring Model (NOT STARTED)

- Pipeline: `synesthesia_eval/pipeline/scoring_model.py`
- Plan: Ridge regression with ~10 features
- Needs 50+ labeled clips minimum

## Structure

```
synesthesia_eval/
├── data/clips/              # 123 video clips
├── data/auto_labels.json    # Gemini AI labels
├── data/unified_labels.json # Merged auto + human labels (from fetch_labels.py)
├── tools/auto_labeler.py    # Gemini auto-labeling + HF push
├── tools/fetch_labels.py    # Unified label fetcher from HF
├── dataset/                 # Dataset loading (local, CSV, HuggingFace)
├── extractors/              # Feature extraction
├── metrics/                 # Evaluation metrics
├── pipeline/                # Processing pipeline + scoring model
├── validation/              # Cross-validation + reliability
└── web-labeler/             # Crowd-sourcing platform (see web-labeler rule)
```
