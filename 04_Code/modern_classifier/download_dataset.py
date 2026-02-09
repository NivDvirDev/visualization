"""
Download and prepare public instrument datasets for training.

Supported datasets:
1. NSynth (Google Magenta) - High quality synthesized instruments
2. IRMAS - Real instrument recordings with annotations
3. Freesound One-Shot - Diverse instrument samples

Usage:
    python download_dataset.py --dataset nsynth --output_dir data
    python download_dataset.py --dataset irmas --output_dir data
    python download_dataset.py --dataset freesound_mini --output_dir data
"""

import argparse
import os
import sys
import json
import shutil
import tarfile
import zipfile
from pathlib import Path
from typing import Optional, List, Dict
import urllib.request
from tqdm import tqdm

# Try to import optional dependencies
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False


class DownloadProgressBar(tqdm):
    """Progress bar for downloads."""
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)


def download_file(url: str, output_path: str, desc: str = "Downloading"):
    """Download file with progress bar."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc=desc) as t:
        urllib.request.urlretrieve(url, output_path, reporthook=t.update_to)

    return output_path


def extract_archive(archive_path: str, output_dir: str):
    """Extract tar.gz or zip archive."""
    archive_path = Path(archive_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Extracting {archive_path.name}...")

    if archive_path.suffix == '.gz' or str(archive_path).endswith('.tar.gz'):
        with tarfile.open(archive_path, 'r:gz') as tar:
            tar.extractall(output_dir)
    elif archive_path.suffix == '.zip':
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
    else:
        raise ValueError(f"Unknown archive format: {archive_path.suffix}")


# =============================================================================
# NSynth Dataset (Google Magenta)
# =============================================================================

NSYNTH_INFO = """
NSynth Dataset (Google Magenta)
===============================
- 305,979 musical notes from 1,006 instruments
- 4-second audio clips at 16kHz
- 11 instrument families
- High quality, professionally synthesized

Instrument families:
  bass, brass, flute, guitar, keyboard, mallet, organ, reed, string, synth_lead, vocal

Size: ~25GB (full), ~1GB (subset we'll download)

License: Creative Commons Attribution 4.0
"""

NSYNTH_URLS = {
    "test": "http://download.magenta.tensorflow.org/datasets/nsynth/nsynth-test.jsonwav.tar.gz",
    # Full dataset URLs (large):
    # "train": "http://download.magenta.tensorflow.org/datasets/nsynth/nsynth-train.jsonwav.tar.gz",
    # "valid": "http://download.magenta.tensorflow.org/datasets/nsynth/nsynth-valid.jsonwav.tar.gz",
}

NSYNTH_INSTRUMENTS = [
    "bass", "brass", "flute", "guitar", "keyboard",
    "mallet", "organ", "reed", "string", "synth_lead", "vocal"
]


def download_nsynth(output_dir: str, subset: str = "test", max_per_class: int = 200):
    """
    Download and prepare NSynth dataset.

    Args:
        output_dir: Output directory
        subset: Which subset to download ("test" recommended for quick start)
        max_per_class: Maximum samples per instrument class
    """
    print(NSYNTH_INFO)

    output_dir = Path(output_dir)
    temp_dir = output_dir / "temp_nsynth"
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Download
    url = NSYNTH_URLS.get(subset)
    if not url:
        print(f"Available subsets: {list(NSYNTH_URLS.keys())}")
        return

    archive_path = temp_dir / f"nsynth-{subset}.tar.gz"

    if not archive_path.exists():
        print(f"\nDownloading NSynth {subset} (~1GB)...")
        download_file(url, archive_path, f"NSynth {subset}")

    # Extract
    extract_dir = temp_dir / f"nsynth-{subset}"
    if not extract_dir.exists():
        extract_archive(archive_path, temp_dir)

    # Find the extracted directory
    nsynth_dir = None
    for d in temp_dir.iterdir():
        if d.is_dir() and 'nsynth' in d.name.lower():
            nsynth_dir = d
            break

    if not nsynth_dir:
        print("Error: Could not find extracted NSynth directory")
        return

    # Load metadata
    json_path = nsynth_dir / "examples.json"
    if not json_path.exists():
        print(f"Error: Metadata not found at {json_path}")
        return

    print("\nLoading metadata...")
    with open(json_path, 'r') as f:
        metadata = json.load(f)

    # Organize by instrument family
    audio_dir = nsynth_dir / "audio"

    print(f"\nOrganizing {len(metadata)} samples by instrument family...")

    # Count samples per family
    family_counts = {}
    for note_id, info in metadata.items():
        family = info['instrument_family_str']
        family_counts[family] = family_counts.get(family, 0) + 1

    print("\nSamples per instrument family:")
    for family, count in sorted(family_counts.items()):
        print(f"  {family}: {count}")

    # Create train/val split
    for split, split_ratio in [("train", 0.8), ("val", 0.2)]:
        split_dir = output_dir / split

        for family in NSYNTH_INSTRUMENTS:
            family_dir = split_dir / family
            family_dir.mkdir(parents=True, exist_ok=True)

        # Copy files
        family_copied = {f: 0 for f in NSYNTH_INSTRUMENTS}

        for note_id, info in tqdm(metadata.items(), desc=f"Creating {split} split"):
            family = info['instrument_family_str']

            if family not in NSYNTH_INSTRUMENTS:
                continue

            # Check if we've copied enough for this family
            max_for_split = int(max_per_class * split_ratio) if split == "train" else int(max_per_class * (1 - split_ratio))
            if family_copied[family] >= max_for_split:
                continue

            # Source audio file
            src_path = audio_dir / f"{note_id}.wav"
            if not src_path.exists():
                continue

            # Destination
            dst_path = split_dir / family / f"{note_id}.wav"

            # Copy (or create symlink for speed)
            if not dst_path.exists():
                shutil.copy2(src_path, dst_path)
                family_copied[family] += 1

    print(f"\nDataset created at {output_dir}")
    print("\nTo generate spiral visualizations, run:")
    print(f"  python generate_spiral.py batch --input_dir {output_dir}/train --output_dir {output_dir}_spirals/train")
    print(f"  python generate_spiral.py batch --input_dir {output_dir}/val --output_dir {output_dir}_spirals/val")

    # Cleanup option
    print(f"\nTo save disk space, you can delete the temp folder:")
    print(f"  rm -rf {temp_dir}")


# =============================================================================
# IRMAS Dataset
# =============================================================================

IRMAS_INFO = """
IRMAS Dataset (Instrument Recognition in Musical Audio Signals)
===============================================================
- Real instrument recordings from various music genres
- 11 instrument classes
- Training: 6,705 audio excerpts (3 seconds each)
- Testing: 2,874 audio excerpts (variable length)

Instruments:
  cello, clarinet, flute, acoustic guitar, electric guitar,
  organ, piano, saxophone, trumpet, violin, voice

Size: ~3GB total

License: Research use
"""

IRMAS_TRAIN_URL = "https://zenodo.org/record/1290750/files/IRMAS-TrainingData.zip"
IRMAS_TEST_URL = "https://zenodo.org/record/1290750/files/IRMAS-TestingData-Part1.zip"

IRMAS_INSTRUMENTS = {
    "cel": "cello",
    "cla": "clarinet",
    "flu": "flute",
    "gac": "acoustic_guitar",
    "gel": "electric_guitar",
    "org": "organ",
    "pia": "piano",
    "sax": "saxophone",
    "tru": "trumpet",
    "vio": "violin",
    "voi": "voice"
}


def download_irmas(output_dir: str, max_per_class: int = 200):
    """
    Download and prepare IRMAS dataset.
    """
    print(IRMAS_INFO)

    output_dir = Path(output_dir)
    temp_dir = output_dir / "temp_irmas"
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Download training data
    train_archive = temp_dir / "IRMAS-TrainingData.zip"
    if not train_archive.exists():
        print("\nDownloading IRMAS Training Data (~2GB)...")
        try:
            download_file(IRMAS_TRAIN_URL, train_archive, "IRMAS Training")
        except Exception as e:
            print(f"Download failed: {e}")
            print("\nManual download instructions:")
            print(f"1. Go to: https://zenodo.org/record/1290750")
            print(f"2. Download IRMAS-TrainingData.zip")
            print(f"3. Place it in: {temp_dir}")
            return

    # Extract
    extract_dir = temp_dir / "IRMAS-TrainingData"
    if not extract_dir.exists():
        extract_archive(train_archive, temp_dir)

    # Find the extracted directory
    irmas_dir = None
    for d in temp_dir.iterdir():
        if d.is_dir() and 'irmas' in d.name.lower():
            irmas_dir = d
            break

    if not irmas_dir:
        print("Error: Could not find extracted IRMAS directory")
        return

    # Organize files
    print("\nOrganizing files by instrument...")

    for split, split_ratio in [("train", 0.8), ("val", 0.2)]:
        for abbrev, full_name in IRMAS_INSTRUMENTS.items():
            src_dir = irmas_dir / abbrev
            if not src_dir.exists():
                # Try uppercase
                src_dir = irmas_dir / abbrev.upper()

            if not src_dir.exists():
                print(f"  Warning: {abbrev} directory not found")
                continue

            dst_dir = output_dir / split / full_name
            dst_dir.mkdir(parents=True, exist_ok=True)

            # Get all audio files
            audio_files = list(src_dir.glob("*.wav"))

            # Split
            split_idx = int(len(audio_files) * 0.8)
            if split == "train":
                files_to_copy = audio_files[:split_idx][:max_per_class]
            else:
                files_to_copy = audio_files[split_idx:][:max_per_class // 4]

            # Copy files
            for src_path in files_to_copy:
                dst_path = dst_dir / src_path.name
                if not dst_path.exists():
                    shutil.copy2(src_path, dst_path)

            print(f"  {full_name}: {len(files_to_copy)} files ({split})")

    print(f"\nDataset created at {output_dir}")


# =============================================================================
# Freesound Mini Dataset (curated subset)
# =============================================================================

FREESOUND_INFO = """
Freesound One-Shot Instruments (Mini)
=====================================
A curated collection of single-note instrument samples from Freesound.

This downloads a small, pre-curated set of samples perfect for quick experiments.

Instruments: piano, guitar, violin, flute, drums (5 classes)
Samples: ~50 per class
Size: ~50MB

Note: For larger datasets, use NSynth or IRMAS instead.
"""

# Pre-selected Freesound sample IDs (Creative Commons licensed)
FREESOUND_SAMPLES = {
    "piano": [
        # These would be actual Freesound IDs - using placeholders
        # In practice, you'd use the Freesound API
    ],
    "guitar": [],
    "violin": [],
    "flute": [],
    "drums": []
}


def download_freesound_mini(output_dir: str):
    """
    Download a mini dataset from Freesound.

    Note: This requires a Freesound API key for actual downloads.
    For now, it generates synthetic data as a placeholder.
    """
    print(FREESOUND_INFO)
    print("\n⚠️  Freesound requires API authentication.")
    print("For a quick start without API setup, we'll generate synthetic samples instead.")
    print("\nTo use real Freesound data:")
    print("1. Create account at https://freesound.org")
    print("2. Get API key from https://freesound.org/apiv2/apply")
    print("3. Set environment variable: export FREESOUND_API_KEY=your_key")

    # Generate synthetic data instead
    print("\nGenerating synthetic instrument samples...")

    from generate_spiral import generate_synthetic_demo_data
    generate_synthetic_demo_data(output_dir, num_classes=5, samples_per_class=100)

    print(f"\nSynthetic dataset created at {output_dir}")


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Download and prepare instrument datasets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download NSynth (recommended - high quality, well organized)
  python download_dataset.py --dataset nsynth --output_dir nsynth_data

  # Download IRMAS (real recordings)
  python download_dataset.py --dataset irmas --output_dir irmas_data

  # Quick synthetic demo
  python download_dataset.py --dataset demo --output_dir demo_data

After downloading, generate spiral visualizations:
  python generate_spiral.py batch --input_dir nsynth_data/train --output_dir data/train
  python generate_spiral.py batch --input_dir nsynth_data/val --output_dir data/val

Then train:
  python train_simple.py --data_dir data --epochs 20
        """
    )

    parser.add_argument("--dataset", type=str, required=True,
                        choices=["nsynth", "irmas", "freesound_mini", "demo"],
                        help="Dataset to download")
    parser.add_argument("--output_dir", type=str, default="dataset",
                        help="Output directory")
    parser.add_argument("--max_per_class", type=int, default=200,
                        help="Maximum samples per class")
    parser.add_argument("--list", action="store_true",
                        help="List available datasets and exit")

    args = parser.parse_args()

    if args.list:
        print("\nAvailable datasets:")
        print("\n1. nsynth (Recommended)")
        print(NSYNTH_INFO)
        print("\n2. irmas")
        print(IRMAS_INFO)
        print("\n3. freesound_mini / demo")
        print(FREESOUND_INFO)
        return

    if args.dataset == "nsynth":
        download_nsynth(args.output_dir, max_per_class=args.max_per_class)
    elif args.dataset == "irmas":
        download_irmas(args.output_dir, max_per_class=args.max_per_class)
    elif args.dataset in ["freesound_mini", "demo"]:
        download_freesound_mini(args.output_dir)
    else:
        print(f"Unknown dataset: {args.dataset}")
        sys.exit(1)


if __name__ == "__main__":
    main()
