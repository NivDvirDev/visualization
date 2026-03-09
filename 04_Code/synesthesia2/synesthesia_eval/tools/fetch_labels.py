#!/usr/bin/env python3
"""
Fetch and unify all labels from HuggingFace into a single local file.

Pulls auto_labels.json and community_labels.json from the HuggingFace dataset,
merges them into a unified format, and writes to data/unified_labels.json.

Usage:
    python tools/fetch_labels.py                          # Fetch and merge
    python tools/fetch_labels.py --dry-run                # Preview without saving
    python tools/fetch_labels.py --dataset NivDvir/synesthesia-eval
    python tools/fetch_labels.py --export-csv             # Also export as CSV
"""

import argparse
import csv
import json
import os
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
UNIFIED_FILE = DATA_DIR / "unified_labels.json"
CSV_FILE = DATA_DIR / "unified_labels.csv"

DEFAULT_DATASET = "NivDvir/synesthesia-eval"


def fetch_json(url: str, token: str | None = None) -> dict | list | None:
    """Fetch JSON from a URL, returning None on 404."""
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def fetch_and_merge(dataset_id: str, token: str | None = None) -> dict:
    """Fetch auto and community labels from HuggingFace and merge them.

    Returns a dict keyed by clip_id with structure:
        {
            "clip_id": {
                "auto": { scores + model + timestamp },
                "human": [ { scores + user + timestamp }, ... ],
                "best": { averaged scores from best available source }
            }
        }
    """
    hf_base = f"https://huggingface.co/datasets/{dataset_id}/resolve/main"

    print(f"Fetching auto_labels.json from {dataset_id}...")
    auto_labels = fetch_json(f"{hf_base}/data/auto_labels.json", token) or {}
    print(f"  Found {len(auto_labels)} auto labels")

    print(f"Fetching community_labels.json from {dataset_id}...")
    community_raw = fetch_json(f"{hf_base}/data/community_labels.json", token) or []
    print(f"  Found {len(community_raw)} community label entries")

    # Index community labels by clip_id
    community_by_clip: dict[str, list[dict]] = {}
    for entry in community_raw:
        cid = entry.get("clip_id", "")
        community_by_clip.setdefault(cid, []).append(entry)

    # Merge
    all_clip_ids = sorted(set(list(auto_labels.keys()) + list(community_by_clip.keys())))
    unified = {}

    for clip_id in all_clip_ids:
        entry: dict = {"clip_id": clip_id, "auto": None, "human": [], "best": None}

        # Auto labels
        if clip_id in auto_labels:
            entry["auto"] = auto_labels[clip_id]

        # Human labels
        if clip_id in community_by_clip:
            entry["human"] = community_by_clip[clip_id]

        # Compute "best" — prefer averaged human, fall back to auto
        if entry["human"]:
            scores = {
                "sync_quality": [], "visual_audio_alignment": [],
                "aesthetic_quality": [], "motion_smoothness": [],
            }
            for he in entry["human"]:
                s = he.get("scores", he)
                for k in scores:
                    if k in s and s[k] is not None:
                        scores[k].append(float(s[k]))

            entry["best"] = {
                "sync_quality": round(sum(v) / len(v), 1) if (v := scores["sync_quality"]) else 3,
                "visual_audio_alignment": round(sum(v) / len(v), 1) if (v := scores["visual_audio_alignment"]) else 3,
                "aesthetic_quality": round(sum(v) / len(v), 1) if (v := scores["aesthetic_quality"]) else 3,
                "motion_smoothness": round(sum(v) / len(v), 1) if (v := scores["motion_smoothness"]) else 3,
                "source": "human",
                "num_annotators": len(entry["human"]),
            }
        elif entry["auto"]:
            a = entry["auto"]
            entry["best"] = {
                "sync_quality": a.get("sync_quality", 3),
                "visual_audio_alignment": a.get("visual_audio_alignment", 3),
                "aesthetic_quality": a.get("aesthetic_quality", 3),
                "motion_smoothness": a.get("motion_smoothness", 3),
                "source": "auto",
                "num_annotators": 1,
            }

        unified[clip_id] = entry

    return unified


def export_csv(unified: dict, output_path: Path):
    """Export unified labels as CSV for DatasetLoader.load_from_csv()."""
    rows = []
    for clip_id, entry in sorted(unified.items()):
        best = entry.get("best")
        if not best:
            continue
        rows.append({
            "sample_id": clip_id,
            "video_path": "",  # Filled by loader
            "audio_path": "",
            "sync_score": best["sync_quality"],
            "alignment_score": best["visual_audio_alignment"],
            "aesthetic_score": best["aesthetic_quality"],
            "motion_smoothness_score": best["motion_smoothness"],
            "source": best["source"],
            "num_annotators": best["num_annotators"],
        })

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Exported {len(rows)} entries to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Fetch and unify labels from HuggingFace")
    parser.add_argument("--dataset", type=str, default=DEFAULT_DATASET,
                        help=f"HuggingFace dataset ID (default: {DEFAULT_DATASET})")
    parser.add_argument("--dry-run", action="store_true", help="Preview without saving")
    parser.add_argument("--export-csv", action="store_true", help="Also export as CSV")
    args = parser.parse_args()

    token = os.environ.get("HF_TOKEN")

    print("=" * 50)
    print("Synesthesia Label Fetcher")
    print("=" * 50)

    unified = fetch_and_merge(args.dataset, token)

    # Summary
    auto_count = sum(1 for e in unified.values() if e["auto"])
    human_count = sum(1 for e in unified.values() if e["human"])
    both_count = sum(1 for e in unified.values() if e["auto"] and e["human"])

    print(f"\nUnified: {len(unified)} clips")
    print(f"  Auto labels:  {auto_count}")
    print(f"  Human labels: {human_count}")
    print(f"  Both:         {both_count}")

    if args.dry_run:
        print("\nDry run — not saving.")
        for clip_id, entry in sorted(unified.items())[:5]:
            best = entry.get("best", {})
            print(f"  {clip_id}: sync={best.get('sync_quality')}, "
                  f"align={best.get('visual_audio_alignment')}, "
                  f"aesthetic={best.get('aesthetic_quality')}, "
                  f"motion={best.get('motion_smoothness')} "
                  f"[{best.get('source')}]")
        if len(unified) > 5:
            print(f"  ... and {len(unified) - 5} more")
        return

    # Save
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(UNIFIED_FILE, "w") as f:
        json.dump(unified, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to {UNIFIED_FILE}")

    if args.export_csv:
        export_csv(unified, CSV_FILE)


if __name__ == "__main__":
    main()
