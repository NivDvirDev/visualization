"""
Enrichment module — pulls extra metadata for clips.

Three sources:
  1. yt-dlp --dump-json  →  heatmap peaks + chapters + title/channel
  2. youtube-transcript-api  →  transcript snippet near the clip
  3. Spotify Web API  →  BPM, key, valence, energy, danceability

Usage:
    from enrichment import enrich_clip
    clip = enrich_clip(clip, sources=["yt", "spotify"])
"""

import json
import os
import re
import subprocess
from typing import Optional

# ---------------------------------------------------------------------------
# yt-dlp helpers
# ---------------------------------------------------------------------------

def _yt_dump(url: str) -> dict:
    """Run yt-dlp --dump-json and return parsed dict."""
    result = subprocess.run(
        ["yt-dlp", "--dump-json", "--no-download", url],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {result.stderr[:200]}")
    return json.loads(result.stdout)


def get_yt_metadata(url: str) -> dict:
    """Return title, channel, duration, heatmap_peak, chapters from yt-dlp."""
    info = _yt_dump(url)

    # Heatmap peak
    heatmap = info.get("heatmap") or []
    heatmap_peak = None
    if heatmap:
        peak_entry = max(heatmap, key=lambda x: x.get("value", 0))
        # Use midpoint of the peak bucket
        heatmap_peak = round(
            (peak_entry["start_time"] + peak_entry["end_time"]) / 2
        )

    # Chapters
    chapters = [
        {
            "title": ch.get("title", ""),
            "start_time": int(ch.get("start_time", 0)),
            "end_time": int(ch.get("end_time", 0)),
        }
        for ch in (info.get("chapters") or [])
    ]

    return {
        "title": info.get("title"),
        "channel": info.get("uploader") or info.get("channel"),
        "duration": info.get("duration"),
        "heatmap_peak": heatmap_peak,
        "chapters": chapters,
        "heatmap_raw": heatmap,  # full data, not stored in clip but returned here
    }


def suggest_clip_window(heatmap_peak: int, window: int = 30) -> tuple:
    """Given a heatmap peak second, suggest (start, end) window around it."""
    half = window // 2
    start = max(0, heatmap_peak - half)
    end = heatmap_peak + (window - half)
    return start, end


# ---------------------------------------------------------------------------
# Transcript (youtube-transcript-api)
# ---------------------------------------------------------------------------

def get_transcript_snippet(video_id: str, start: int, end: int, context: int = 5) -> Optional[str]:
    """Return transcript text around the clip window."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return None

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "he", "auto"])
    except Exception:
        return None

    snippets = []
    for entry in transcript:
        t = entry["start"]
        if (start - context) <= t <= (end + context):
            snippets.append(entry["text"])

    return " ".join(snippets) if snippets else None


# ---------------------------------------------------------------------------
# Spotify enrichment
# ---------------------------------------------------------------------------

def _load_dotenv():
    """Load .env from the yt_clips directory if present."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip())


def _init_spotify():
    """Return a spotipy client or raise ImportError/RuntimeError."""
    _load_dotenv()
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials
    except ImportError:
        raise ImportError("spotipy not installed. Run: pip install spotipy")

    client_id = os.environ.get("SPOTIPY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIPY_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError(
            "Set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET env vars.\n"
            "Get them at: https://developer.spotify.com/dashboard"
        )

    auth = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    return spotipy.Spotify(auth_manager=auth)


def _parse_artist_title(raw_title: str) -> tuple:
    """
    Try to split 'Artist - Title' or 'Title (Artist)' patterns.
    Returns (artist, title) or (None, raw_title).
    """
    # Common pattern: "Artist - Title" or "Artist – Title"
    m = re.match(r"^(.+?)\s*[-–]\s*(.+)$", raw_title)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return None, raw_title


def get_spotify_features(title: str, artist: str = None) -> Optional[dict]:
    """
    Search Spotify for the track and return audio features.
    Returns dict with: track_id, track_title, artist, bpm, key, valence, energy, danceability
    Returns None if not found or credentials missing.
    """
    try:
        sp = _init_spotify()
    except (ImportError, RuntimeError) as e:
        print(f"[spotify] skipped: {e}")
        return None

    # Build search query
    if artist:
        query = f"artist:{artist} track:{title}"
    else:
        # Try to parse artist from title
        parsed_artist, parsed_title = _parse_artist_title(title)
        if parsed_artist:
            query = f"artist:{parsed_artist} track:{parsed_title}"
        else:
            query = title

    results = sp.search(q=query, type="track", limit=1)
    items = results.get("tracks", {}).get("items", [])
    if not items:
        # Fallback: plain search
        results = sp.search(q=title, type="track", limit=1)
        items = results.get("tracks", {}).get("items", [])
    if not items:
        print(f"[spotify] no track found for: {title!r}")
        return None

    track = items[0]
    track_id = track["id"]

    result = {
        "track_id": track_id,
        "track_title": track["name"],
        "artist": track["artists"][0]["name"],
        "album": track["album"]["name"],
        "release_date": track["album"].get("release_date"),
        "popularity": track.get("popularity"),
        "spotify_url": track["external_urls"].get("spotify"),
    }

    # Audio features deprecated for new apps (post Nov 2024) — try anyway
    try:
        features = sp.audio_features([track_id])[0]
        if features:
            KEY_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            key_num = features.get("key", -1)
            result.update({
                "bpm": round(features["tempo"]),
                "key": KEY_NAMES[key_num] if 0 <= key_num < 12 else "unknown",
                "mode": "major" if features.get("mode") == 1 else "minor",
                "valence": round(features["valence"], 3),
                "energy": round(features["energy"], 3),
                "danceability": round(features["danceability"], 3),
                "loudness_db": round(features["loudness"], 1),
            })
    except Exception:
        pass  # audio_features not available for this app

    return result


# ---------------------------------------------------------------------------
# Combined enricher
# ---------------------------------------------------------------------------

def enrich_clip(clip: dict, sources: list = None) -> dict:
    """
    Enrich a clip dict in-place. sources can include "yt", "spotify", "transcript".
    Default: all three.
    Returns updated clip.
    """
    if sources is None:
        sources = ["yt", "transcript"]  # Spotify disabled — no Premium subscription (403)

    if "yt" in sources:
        print(f"[yt] fetching metadata for {clip['video_id']}...")
        try:
            meta = get_yt_metadata(clip["url"])
            clip["title"] = clip["title"] or meta["title"]
            clip["channel"] = clip["channel"] or meta["channel"]
            clip["duration"] = clip["duration"] or meta["duration"]
            if meta["heatmap_peak"] is not None:
                clip["heatmap_peak"] = meta["heatmap_peak"]
            if meta["chapters"]:
                clip["chapters"] = meta["chapters"]
            print(f"  title: {clip['title']}")
            print(f"  heatmap peak: {clip['heatmap_peak']}s")
            if clip["chapters"]:
                print(f"  chapters: {len(clip['chapters'])} found")
        except Exception as e:
            print(f"  [yt] error: {e}")

    if "transcript" in sources:
        print(f"[transcript] fetching for {clip['video_id']}...")
        snippet = get_transcript_snippet(
            clip["video_id"], clip["start"], clip["end"]
        )
        if snippet:
            clip["transcript_snippet"] = snippet
            print(f"  snippet: {snippet[:80]}...")
        else:
            print("  no transcript available")

    if "spotify" in sources and clip.get("title"):
        print(f"[spotify] searching for: {clip['title']!r}...")
        features = get_spotify_features(clip["title"])
        if features:
            clip["spotify"] = features
            print(f"  found: {features['artist']} – {features['track_title']}")
            print(f"  BPM={features['bpm']}  key={features['key']} {features['mode']}  "
                  f"energy={features['energy']}  valence={features['valence']}")
        else:
            print("  not found on Spotify")

    return clip
