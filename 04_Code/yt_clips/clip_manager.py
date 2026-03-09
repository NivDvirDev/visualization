"""
Clip Manager — core storage layer for the YouTube clips dataset.

Schema for each clip entry:
{
    "id": "uuid4",
    "url": "https://www.youtube.com/watch?v=...",
    "video_id": "...",
    "title": "...",
    "channel": "...",
    "duration": 240,           # seconds
    "start": 83,               # clip start (seconds)
    "end": 113,                # clip end (seconds)
    "added_at": "ISO8601",
    "notes": "...",
    "tags": [],
    "heatmap_peak": null,      # seconds — YouTube Most Replayed peak
    "chapters": [],            # [{title, start_time, end_time}]
    "spotify": null,           # {track_id, bpm, key, valence, energy, danceability, title, artist}
    "transcript_snippet": null # text near the clip timestamps
}
"""

import json
import uuid
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent.parent.parent / "05_Data" / "yt_clips_db.json"


def _load_db() -> dict:
    if DB_PATH.exists():
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"clips": [], "version": 1}


def _save_db(db: dict):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def _extract_video_id(url: str) -> Optional[str]:
    patterns = [
        r"(?:v=|youtu\.be/|embed/|shorts/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    return None


def add_clip(
    url: str,
    start: int,
    end: int,
    notes: str = "",
    tags: list = None,
) -> dict:
    """Add a new clip to the database. Returns the created clip dict."""
    db = _load_db()
    video_id = _extract_video_id(url)
    if not video_id:
        raise ValueError(f"Could not extract video ID from URL: {url}")

    # Check for duplicate
    for clip in db["clips"]:
        if clip["video_id"] == video_id and clip["start"] == start:
            print(f"[warn] Clip already exists with id={clip['id']}")
            return clip

    clip = {
        "id": str(uuid.uuid4())[:8],
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "video_id": video_id,
        "title": None,
        "channel": None,
        "duration": None,
        "start": start,
        "end": end,
        "added_at": datetime.now(timezone.utc).isoformat(),
        "notes": notes,
        "tags": tags or [],
        "heatmap_peak": None,
        "chapters": [],
        "spotify": None,
        "transcript_snippet": None,
    }
    db["clips"].append(clip)
    _save_db(db)
    return clip


def update_clip(clip_id: str, **fields) -> dict:
    """Update fields on an existing clip."""
    db = _load_db()
    for clip in db["clips"]:
        if clip["id"] == clip_id:
            clip.update(fields)
            _save_db(db)
            return clip
    raise KeyError(f"Clip not found: {clip_id}")


def get_clip(clip_id: str) -> dict:
    db = _load_db()
    for clip in db["clips"]:
        if clip["id"] == clip_id:
            return clip
    raise KeyError(f"Clip not found: {clip_id}")


def list_clips(tag: str = None) -> list:
    db = _load_db()
    clips = db["clips"]
    if tag:
        clips = [c for c in clips if tag in c.get("tags", [])]
    return clips


def remove_clip(clip_id: str):
    db = _load_db()
    before = len(db["clips"])
    db["clips"] = [c for c in db["clips"] if c["id"] != clip_id]
    if len(db["clips"]) == before:
        raise KeyError(f"Clip not found: {clip_id}")
    _save_db(db)


def stats() -> dict:
    db = _load_db()
    clips = db["clips"]
    total_duration = sum((c["end"] - c["start"]) for c in clips if c["end"] and c["start"])
    has_spotify = sum(1 for c in clips if c.get("spotify"))
    has_heatmap = sum(1 for c in clips if c.get("heatmap_peak") is not None)
    all_tags = {}
    for c in clips:
        for t in c.get("tags", []):
            all_tags[t] = all_tags.get(t, 0) + 1
    return {
        "total_clips": len(clips),
        "total_duration_seconds": total_duration,
        "with_spotify": has_spotify,
        "with_heatmap": has_heatmap,
        "tags": all_tags,
    }
