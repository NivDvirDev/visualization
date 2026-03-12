#!/usr/bin/env python3
"""
sync_playlist.py — Sync the synesthesia-eval clips to a YouTube playlist.

Downloads new clips, removes clips not in the playlist, renumbers everything
sequentially in playlist order, and regenerates metadata.json.

Usage:
    python sync_playlist.py <playlist_url> [--dry-run] [--skip <video_id> ...]
    python sync_playlist.py "https://youtube.com/playlist?list=PLpkBXaYFttw_UnR3RZ9fbTvOh-vsBQ3Y4" --dry-run
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from difflib import SequenceMatcher
from pathlib import Path

CLIPS_DIR = Path(__file__).parent.parent / "data" / "clips"
METADATA_FILE = CLIPS_DIR / "metadata.json"
AUTO_LABELS_FILE = Path(__file__).parent.parent / "data" / "auto_labels.json"
UNIFIED_LABELS_FILE = Path(__file__).parent.parent / "data" / "unified_labels.json"


def fetch_playlist(playlist_url: str) -> list[dict]:
    """Fetch playlist video metadata via yt-dlp."""
    cmd = [
        "yt-dlp", "--flat-playlist",
        "--print", "%(id)s\t%(title)s\t%(duration)s\t%(channel)s",
        playlist_url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp playlist fetch failed: {result.stderr.strip()}")

    videos = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            videos.append({
                "video_id": parts[0],
                "title": parts[1],
                "duration": int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None,
                "channel": parts[3] if len(parts) > 3 else None,
            })
    return videos


def sanitize_title(title: str, max_len: int = 50) -> str:
    """Sanitize and truncate title for filename use."""
    # Replace characters that are invalid in filenames
    sanitized = re.sub(r'[/\\:*?"<>|]', '_', title)
    return sanitized[:max_len]


def match_existing_clip(title: str, existing_files: dict[str, Path]) -> str | None:
    """Find an existing clip file that matches a video title.

    Returns the existing filename if matched, None otherwise.
    existing_files: {description_part: full_path}
    """
    truncated = sanitize_title(title)
    for desc, path in existing_files.items():
        # Direct match on truncated title
        if desc == truncated:
            return str(path.name)
        # Fuzzy match for slight differences
        ratio = SequenceMatcher(None, desc.lower(), truncated.lower()).ratio()
        if ratio > 0.85:
            return str(path.name)
    return None


def download_video(video_id: str, output_path: Path) -> bool:
    """Download a full video using yt-dlp."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    cmd = [
        "yt-dlp",
        "-f", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]",
        "--merge-output-format", "mp4",
        "-o", str(output_path),
        "--no-playlist",
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  WARNING: yt-dlp failed for {video_id}: {result.stderr.strip()[:200]}", file=sys.stderr)
        return False
    return True


def build_existing_files_map() -> dict[str, Path]:
    """Build a map of {description_part: file_path} from existing clips."""
    existing = {}
    for f in CLIPS_DIR.glob("*.mp4"):
        # Strip the numeric prefix: "002_Some Title.mp4" -> "Some Title"
        match = re.match(r'^\d+_(.*?)\.mp4$', f.name)
        if match:
            existing[match.group(1)] = f
    return existing


def main():
    parser = argparse.ArgumentParser(description="Sync eval clips to a YouTube playlist")
    parser.add_argument("playlist_url", help="YouTube playlist URL")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without downloading/deleting")
    parser.add_argument("--skip", nargs="*", default=[], help="Video IDs to skip")
    args = parser.parse_args()

    print("Fetching playlist metadata...")
    playlist_videos = fetch_playlist(args.playlist_url)
    print(f"Found {len(playlist_videos)} videos in playlist")

    # Filter out skipped videos
    if args.skip:
        before = len(playlist_videos)
        playlist_videos = [v for v in playlist_videos if v["video_id"] not in args.skip]
        print(f"Skipped {before - len(playlist_videos)} video(s)")

    # Build map of existing clips
    existing_files = build_existing_files_map()
    available_files = dict(existing_files)  # Copy that gets consumed during matching
    print(f"Found {len(existing_files)} existing clips")

    # Match existing clips to playlist (consume matches to prevent double-matching)
    matched = {}  # video_id -> existing_filename
    to_download = []  # videos needing download
    for v in playlist_videos:
        existing_name = match_existing_clip(v["title"], available_files)
        if existing_name:
            matched[v["video_id"]] = existing_name
            # Remove from available pool so it can't be matched again
            desc_to_remove = None
            for desc, path in available_files.items():
                if path.name == existing_name:
                    desc_to_remove = desc
                    break
            if desc_to_remove:
                del available_files[desc_to_remove]
        else:
            to_download.append(v)

    # Find clips to remove (existing but not in playlist)
    matched_filenames = set(matched.values())
    all_existing_filenames = {f.name for f in CLIPS_DIR.glob("*.mp4")}
    to_remove = all_existing_filenames - matched_filenames

    print(f"\n=== Sync Summary ===")
    print(f"Playlist videos: {len(playlist_videos)}")
    print(f"Already have:    {len(matched)}")
    print(f"To download:     {len(to_download)}")
    print(f"To remove:       {len(to_remove)}")

    if to_remove:
        print(f"\nClips to REMOVE:")
        for name in sorted(to_remove):
            print(f"  - {name}")

    if to_download:
        print(f"\nClips to DOWNLOAD:")
        for v in to_download:
            dur = f" ({v['duration']}s)" if v['duration'] else ""
            print(f"  + {v['title']}{dur}")

    if args.dry_run:
        print("\n[DRY RUN] No changes made.")
        return

    # --- Execute changes ---

    # 1. Remove clips not in playlist
    for name in to_remove:
        path = CLIPS_DIR / name
        print(f"Removing: {name}")
        path.unlink()

    # 2. Download missing clips (to temp names first)
    temp_downloads = {}  # video_id -> temp_path
    for i, v in enumerate(to_download, 1):
        # Use a temp name to avoid conflicts during renumbering
        temp_name = f"_temp_{v['video_id']}.mp4"
        temp_path = CLIPS_DIR / temp_name
        if temp_path.exists():
            print(f"[{i}/{len(to_download)}] Already downloaded: {v['title'][:60]}")
            temp_downloads[v["video_id"]] = temp_path
        else:
            print(f"[{i}/{len(to_download)}] Downloading: {v['title'][:60]}...")
            if download_video(v["video_id"], temp_path):
                temp_downloads[v["video_id"]] = temp_path
            else:
                print(f"  FAILED - skipping")

    # 3. Renumber everything in playlist order
    #    Strategy: move all files to a staging dir, then move back with new names
    print("\nRenumbering clips in playlist order...")

    staging_dir = CLIPS_DIR / "_staging"
    staging_dir.mkdir(exist_ok=True)

    # Load old metadata to map old IDs for label preservation
    old_metadata = {}
    if METADATA_FILE.exists():
        with open(METADATA_FILE) as f:
            old_meta = json.load(f)
            for clip in old_meta.get("clips", []):
                old_metadata[clip["filename"]] = clip["id"]

    # Move all matched existing clips and temp downloads to staging
    # keyed by video_id -> staging_path
    staged = {}

    for video_id, old_name in matched.items():
        old_path = CLIPS_DIR / old_name
        if old_path.exists():
            staged_path = staging_dir / f"{video_id}.mp4"
            shutil.move(str(old_path), str(staged_path))
            staged[video_id] = staged_path

    for video_id, temp_path in temp_downloads.items():
        if temp_path.exists():
            staged_path = staging_dir / f"{video_id}.mp4"
            shutil.move(str(temp_path), str(staged_path))
            staged[video_id] = staged_path

    # Also stage any _renaming_ files (from previous failed runs)
    for f in CLIPS_DIR.glob("_renaming_*.mp4"):
        staged_path = staging_dir / f.name
        shutil.move(str(f), str(staged_path))

    new_clips = []
    id_mapping = {}  # old_id -> new_id (for label migration)

    for idx, v in enumerate(playlist_videos, 1):
        new_id = str(idx).zfill(3)
        title_safe = sanitize_title(v["title"])
        new_filename = f"{new_id}_{title_safe}.mp4"
        new_path = CLIPS_DIR / new_filename

        if v["video_id"] not in staged:
            print(f"  WARNING: No file for {v['title'][:40]} — skipped")
            continue

        shutil.move(str(staged[v["video_id"]]), str(new_path))

        # Track ID mapping for label migration
        if v["video_id"] in matched:
            old_name = matched[v["video_id"]]
            if old_name in old_metadata:
                id_mapping[old_metadata[old_name]] = new_id

        size_mb = round(new_path.stat().st_size / 1024 / 1024, 2) if new_path.exists() else None

        new_clips.append({
            "id": new_id,
            "filename": new_filename,
            "description": v["title"],
            "source": "youtube_playlist",
            "categories": {
                "sync_quality": "unknown",
                "visual_style": "youtube_curated",
                "music_genre": "various",
                "energy": "various",
            },
            "size_mb": size_mb,
            "youtube_source": {
                "video_id": v["video_id"],
                "url": f"https://www.youtube.com/watch?v={v['video_id']}",
                "channel": v["channel"],
                "duration": v["duration"],
            },
        })

    # Clean up staging dir
    for f in staging_dir.glob("*"):
        f.unlink()
    staging_dir.rmdir()

    # 4. Write new metadata
    new_metadata = {
        "dataset": "synesthesia_eval_youtube_v2",
        "version": "2.0",
        "playlist_url": f"https://youtube.com/playlist?list=PLpkBXaYFttw_UnR3RZ9fbTvOh-vsBQ3Y4",
        "total_clips": len(new_clips),
        "clips": new_clips,
    }
    with open(METADATA_FILE, "w") as f:
        json.dump(new_metadata, f, indent=2, ensure_ascii=False)
    print(f"\nWrote metadata.json with {len(new_clips)} clips")

    # 5. Migrate labels (remap old IDs to new IDs)
    for label_file in [AUTO_LABELS_FILE, UNIFIED_LABELS_FILE]:
        if not label_file.exists():
            continue
        with open(label_file) as f:
            old_labels = json.load(f)

        new_labels = {}
        for old_id, label_data in old_labels.items():
            if old_id in id_mapping:
                new_labels[id_mapping[old_id]] = label_data
            # else: clip was removed, drop the label

        with open(label_file, "w") as f:
            json.dump(new_labels, f, indent=2, ensure_ascii=False)
        migrated = len(new_labels)
        dropped = len(old_labels) - migrated
        print(f"Updated {label_file.name}: {migrated} labels kept, {dropped} dropped")

    # Clean up any leftover temp files
    for tmp in CLIPS_DIR.glob("_temp_*.mp4"):
        tmp.unlink()

    print(f"\nDone! {len(new_clips)} clips ready in {CLIPS_DIR}")


if __name__ == "__main__":
    main()
