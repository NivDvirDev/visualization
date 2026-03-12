#!/usr/bin/env python3
"""
push_to_hf.py — Push clips and metadata to HuggingFace dataset.

Uploads all video clips and metadata files to the HuggingFace dataset
repository (NivDvir/synesthesia-eval).

Usage:
    export HF_TOKEN="hf_..."
    python push_to_hf.py                # Upload all clips + metadata
    python push_to_hf.py --dry-run      # Preview what would be uploaded
    python push_to_hf.py --metadata-only # Only upload metadata/labels (no videos)
"""

import argparse
import json
import os
import sys
from pathlib import Path

DATASET_ID = "NivDvir/synesthesia-eval"
DATA_DIR = Path(__file__).parent.parent / "data"
CLIPS_DIR = DATA_DIR / "clips"
METADATA_FILE = CLIPS_DIR / "metadata.json"
AUTO_LABELS_FILE = DATA_DIR / "auto_labels.json"
UNIFIED_LABELS_FILE = DATA_DIR / "unified_labels.json"


def get_hf_api():
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        print("ERROR: HF_TOKEN environment variable not set.")
        print("Get a write token from: https://huggingface.co/settings/tokens")
        sys.exit(1)

    from huggingface_hub import HfApi
    return HfApi(token=hf_token)


def get_existing_files(api):
    """Get list of files already in the HF repo."""
    try:
        files = api.list_repo_files(repo_id=DATASET_ID, repo_type="dataset")
        return set(files)
    except Exception:
        return set()


def main():
    parser = argparse.ArgumentParser(description="Push clips to HuggingFace")
    parser.add_argument("--dry-run", action="store_true", help="Preview without uploading")
    parser.add_argument("--metadata-only", action="store_true", help="Only upload metadata files")
    parser.add_argument("--force", action="store_true", help="Re-upload all files even if they exist")
    args = parser.parse_args()

    if not args.dry_run:
        api = get_hf_api()

    # Collect files to upload
    uploads = []

    # Metadata files
    for meta_file, repo_path in [
        (METADATA_FILE, "data/clips/metadata.json"),
        (AUTO_LABELS_FILE, "data/auto_labels.json"),
        (UNIFIED_LABELS_FILE, "data/unified_labels.json"),
    ]:
        if meta_file.exists():
            uploads.append((meta_file, repo_path))

    # Video clips
    if not args.metadata_only:
        for clip in sorted(CLIPS_DIR.glob("*.mp4")):
            uploads.append((clip, f"data/clips/{clip.name}"))

    print(f"Files to upload: {len(uploads)}")
    print(f"  Metadata: {sum(1 for _, p in uploads if not p.endswith('.mp4'))}")
    print(f"  Videos:   {sum(1 for _, p in uploads if p.endswith('.mp4'))}")

    if args.dry_run:
        for local, remote in uploads:
            size = local.stat().st_size / 1024 / 1024
            print(f"  {remote} ({size:.1f} MB)")
        print("\n[DRY RUN] No files uploaded.")
        return

    # Check what's already uploaded to skip duplicates
    existing = set()
    if not args.force:
        print("Checking existing files on HuggingFace...")
        existing = get_existing_files(api)
        print(f"  {len(existing)} files already in repo")

    uploaded = 0
    skipped = 0
    failed = 0

    for i, (local_path, repo_path) in enumerate(uploads, 1):
        size_mb = local_path.stat().st_size / 1024 / 1024

        # Skip if already exists (unless --force or it's a metadata file)
        is_metadata = not repo_path.endswith('.mp4')
        if repo_path in existing and not args.force and not is_metadata:
            skipped += 1
            continue

        print(f"[{i}/{len(uploads)}] Uploading: {repo_path} ({size_mb:.1f} MB)...")
        try:
            api.upload_file(
                path_or_fileobj=str(local_path),
                path_in_repo=repo_path,
                repo_id=DATASET_ID,
                repo_type="dataset",
                commit_message=f"Update {repo_path}",
            )
            uploaded += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            failed += 1

    print(f"\nDone! Uploaded: {uploaded}, Skipped: {skipped}, Failed: {failed}")


if __name__ == "__main__":
    main()
