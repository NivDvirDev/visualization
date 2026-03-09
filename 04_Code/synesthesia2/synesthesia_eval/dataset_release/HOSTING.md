# Dataset Hosting Setup

This directory contains everything needed to publish the Synesthesia Eval dataset to HuggingFace Hub and Zenodo.

## Files

| File | Purpose |
|------|---------|
| `README.md` | HuggingFace dataset card (YAML front matter + description) |
| `.zenodo.json` | Zenodo deposition metadata (creator, keywords, license) |
| `LICENSE` | CC-BY-NC-SA 4.0 license reference |
| `upload.sh` | Upload script for both platforms |

## Quick Start

### HuggingFace

```bash
# 1. Install and authenticate
pip install huggingface_hub
huggingface-cli login

# 2. Upload
./upload.sh huggingface
```

The script creates the repo `nivdvir/synesthesia-eval`, uploads the dataset card, labels, metadata, and all video clips.

### Zenodo

```bash
# 1. Get a personal access token from:
#    https://zenodo.org/account/settings/applications/

# 2. Export token and upload
export ZENODO_TOKEN="your-token-here"
./upload.sh zenodo
```

The script creates a **draft** deposition on Zenodo. Review it at the printed URL before publishing. This gives you a citable DOI.

### Both Platforms

```bash
./upload.sh all
```

## What Gets Uploaded

- `data/clips/*.mp4` - Video files
- `data/clips/metadata.json` - Clip catalog
- `data/auto_labels.json` - Gemini quality ratings
- `data/labels.json` - Manual labels (if non-empty)
- `README.md` and `LICENSE`

## After Publishing

1. **HuggingFace** - Dataset is immediately browsable at `https://huggingface.co/datasets/nivdvir/synesthesia-eval`
2. **Zenodo** - Review the draft, then click "Publish" to mint a DOI
3. Update the citation in `README.md` with the Zenodo DOI once published
