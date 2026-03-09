---
license: cc-by-nc-sa-4.0
task_categories:
  - video-classification
  - audio-classification
language:
  - en
tags:
  - audio-visualization
  - synesthesia
  - spectrograms
  - psychoacoustics
  - video-quality-assessment
  - music-visualization
pretty_name: Synesthesia Eval - Audio Visualization Quality Dataset
size_categories:
  - n<1K
---

# Synesthesia Eval: Audio Visualization Quality Dataset

## Dataset Description

A curated dataset of ~123 audio/video clips for evaluating the quality of audio visualization systems. Each clip depicts an audio-reactive visualization and is rated on four quality dimensions by an automated labeler (Google Gemini).

This dataset supports research in audio-visual correspondence, perceptual quality assessment, and music visualization evaluation.

### Key Features

- **29 curated clips** (MP4 with audio) from diverse visualization styles
- **4-dimension quality ratings** (1-5 scale) per clip
- **Textual rationale** for each rating
- Sources include cochlear spiral renderings, spectrograms, reactive visuals, and competitor outputs

## Quality Dimensions

| Dimension | Description |
|-----------|-------------|
| `sync_quality` | How well visuals synchronize with beat/rhythm (1=none, 5=perfect) |
| `visual_audio_alignment` | How well visuals semantically match audio characteristics (1=none, 5=perfect) |
| `aesthetic_quality` | Overall visual appeal and production quality (1=poor, 5=excellent) |
| `motion_smoothness` | Fluidity and naturalness of visual motion (1=choppy, 5=smooth) |

## Dataset Structure

```
synesthesia_eval/
├── data/
│   ├── clips/
│   │   ├── metadata.json          # Clip catalog (id, filename, source, categories)
│   │   └── *.mp4                  # Video files
│   ├── auto_labels.json           # Gemini-generated quality ratings
│   └── labels.json                # Manual labels (placeholder)
```

### Metadata Format (`metadata.json`)

```json
{
  "dataset": "synesthesia_eval_youtube_v1",
  "version": "1.0",
  "total_clips": 29,
  "clips": [
    {
      "id": "001",
      "filename": "001_example.mp4",
      "description": "Example visualization",
      "source": "youtube_playlist",
      "categories": {
        "sync_quality": "unknown",
        "visual_style": "youtube_curated",
        "music_genre": "various",
        "energy": "various"
      }
    }
  ]
}
```

### Labels Format (`auto_labels.json`)

```json
{
  "001": {
    "sync_quality": 4,
    "visual_audio_alignment": 4,
    "aesthetic_quality": 5,
    "motion_smoothness": 4,
    "notes": "Detailed rationale for the ratings...",
    "model": "gemini-2.5-flash-lite",
    "timestamp": "2026-02-24T02:00:15Z"
  }
}
```

## Usage

### Loading with Python

```python
import json
from pathlib import Path

data_dir = Path("synesthesia_eval/data")

# Load metadata
with open(data_dir / "clips" / "metadata.json") as f:
    metadata = json.load(f)

# Load labels
with open(data_dir / "auto_labels.json") as f:
    labels = json.load(f)

# Iterate over labeled clips
for clip in metadata["clips"]:
    clip_id = clip["id"]
    if clip_id in labels:
        video_path = data_dir / "clips" / clip["filename"]
        rating = labels[clip_id]
        print(f"Clip {clip_id}: sync={rating['sync_quality']}, "
              f"aesthetic={rating['aesthetic_quality']}")
```

### Loading with Hugging Face Datasets

```python
from datasets import load_dataset

dataset = load_dataset("nivdvir/synesthesia-eval")
```

### Composite Score

The dataset defines a composite quality score:

```
composite = 0.40 * sync_quality + 0.35 * visual_audio_alignment + 0.25 * aesthetic_quality
```

## Dataset Creation

### Source Data

Clips were curated from:
- Synesthesia project outputs (cochlear spiral visualizations)
- YouTube music visualization compilations
- Synthetic test variations (good/poor sync)

### Annotations

Labels were generated using Google Gemini (gemini-2.5-flash-lite) via multimodal video understanding. The model watches each clip and produces structured quality ratings with textual justification.

## Intended Use

- Benchmarking audio visualization quality metrics
- Training quality prediction models for music visualizers
- Research in audio-visual correspondence and perceptual evaluation

## Limitations

- Labels are AI-generated (single annotator) without human validation
- Dataset is small (~29 labeled clips); intended as a seed for larger collection
- Clips are biased toward electronic/EDM music genres
- Quality ratings are subjective and may not generalize across cultures

## Citation

```bibtex
@dataset{dvir2026synesthesia_eval,
  author    = {Dvir, Niv},
  title     = {Synesthesia Eval: Audio Visualization Quality Dataset},
  year      = {2026},
  publisher = {Hugging Face},
  url       = {https://huggingface.co/datasets/nivdvir/synesthesia-eval},
  license   = {CC-BY-NC-SA-4.0}
}
```

## License

This dataset is released under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
