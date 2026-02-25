#!/usr/bin/env python3
"""
add_clip.py — Add a YouTube video segment to the Synesthesia dataset.

Usage:
    python add_clip.py <youtube_url> --start <seconds> --duration <seconds> [--description <text>]

Examples:
    python add_clip.py "https://youtu.be/dQw4w9WgXcQ?t=83" --start 83 --duration 30
    python add_clip.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --start 30 --duration 45 --description "great_drop"

Output (JSON on stdout, for bot to parse):
    {"success": true, "id": "124", "filename": "124_yt_dQw4w9WgXcQ.mp4", "start": 83, "end": 113}
    {"success": false, "error": "..."}
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs

CLIPS_DIR = Path(__file__).parent.parent / "data" / "clips"
METADATA_FILE = CLIPS_DIR / "metadata.json"


def parse_youtube_url(url: str) -> tuple[str, int]:
    """Extract (video_id, start_seconds) from a YouTube URL."""
    # youtu.be short links
    short = re.match(r'https?://youtu\.be/([A-Za-z0-9_-]{11})', url)
    if short:
        video_id = short.group(1)
        t = re.search(r'[?&]t=(\d+)', url)
        return video_id, int(t.group(1)) if t else 0

    # youtube.com links
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    video_id = qs.get('v', [None])[0]
    if not video_id:
        raise ValueError(f"Could not extract video ID from URL: {url}")

    t_param = qs.get('t', ['0'])[0]
    start = int(re.sub(r'\D', '', t_param) or '0')
    return video_id, start


def next_clip_id(metadata: dict) -> str:
    """Return the next clip ID as a zero-padded string."""
    existing_ids = [int(c['id']) for c in metadata['clips'] if c['id'].isdigit()]
    next_id = max(existing_ids, default=0) + 1
    return str(next_id).zfill(2) if next_id < 100 else str(next_id)


def download_clip(url: str, start: int, end: int, output_path: Path) -> bool:
    """Download a video segment using yt-dlp."""
    section = f"*{start}-{end}"
    cmd = [
        "yt-dlp",
        "--download-sections", section,
        "--force-keyframes-at-cuts",
        "-f", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]",
        "--merge-output-format", "mp4",
        "-o", str(output_path),
        "--no-playlist",
        "--quiet",
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {result.stderr.strip()}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Add a YouTube clip to the Synesthesia dataset")
    parser.add_argument("url", help="YouTube URL (may include ?t= timestamp)")
    parser.add_argument("--start", type=int, default=None, help="Start time in seconds (overrides ?t= in URL)")
    parser.add_argument("--duration", type=int, default=30, help="Clip duration in seconds (default: 30)")
    parser.add_argument("--description", type=str, default=None, help="Short description for filename/metadata")
    args = parser.parse_args()

    try:
        video_id, url_start = parse_youtube_url(args.url)
        start = args.start if args.start is not None else url_start
        end = start + args.duration

        # Load metadata
        with open(METADATA_FILE) as f:
            metadata = json.load(f)

        clip_id = next_clip_id(metadata)
        desc = args.description or f"yt_{video_id}"
        desc_clean = re.sub(r'[^\w]', '_', desc).strip('_').lower()
        filename = f"{clip_id}_{desc_clean}.mp4"
        output_path = CLIPS_DIR / filename

        # Download
        canonical_url = f"https://www.youtube.com/watch?v={video_id}"
        download_clip(canonical_url, start, end, output_path)

        # Get file size
        size_mb = round(output_path.stat().st_size / 1024 / 1024, 2) if output_path.exists() else None

        # Build new clip entry
        new_clip = {
            "id": clip_id,
            "filename": filename,
            "description": desc_clean,
            "categories": {
                "sync_quality": "unknown",
                "visual_style": "unknown",
                "music_genre": "unknown",
                "energy": "unknown"
            },
            "size_mb": size_mb,
            "annotations": {
                "sync_score": None,
                "alignment_score": None,
                "aesthetic_score": None,
                "annotator": None
            },
            "youtube_source": {
                "video_id": video_id,
                "url": canonical_url,
                "start_time": start,
                "end_time": end
            }
        }

        metadata["clips"].append(new_clip)
        metadata["total_clips"] = len(metadata["clips"])

        with open(METADATA_FILE, "w") as f:
            json.dump(metadata, f, indent=2)

        print(json.dumps({
            "success": True,
            "id": clip_id,
            "filename": filename,
            "video_id": video_id,
            "start": start,
            "end": end,
            "size_mb": size_mb
        }))

    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
