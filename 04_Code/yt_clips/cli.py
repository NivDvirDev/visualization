#!/usr/bin/env python3
"""
yt_clips CLI — manage your YouTube clips dataset.

Commands:
  add      <url> [--start S] [--end E] [--auto] [--notes TEXT] [--tags T1,T2]
  heatmap  <url>           show heatmap analysis + suggested window
  chapters <url>           list chapters from video
  enrich   [clip_id|all]   enrich with yt metadata + Spotify + transcript
  list     [--tag TAG]     list all clips
  show     <clip_id>       show clip details
  rm       <clip_id>       remove a clip
  annotate <clip_id>       open browser annotator for a clip
  stats                    show dataset statistics

Examples:
  python cli.py add "https://youtube.com/watch?v=abc" --auto
  python cli.py add "https://youtube.com/watch?v=abc" --start 83 --end 113 --notes "great drop"
  python cli.py heatmap "https://youtube.com/watch?v=abc"
  python cli.py chapters "https://youtube.com/watch?v=abc"
  python cli.py enrich all
  python cli.py list
  python cli.py annotate a1b2c3d4
"""

import argparse
import json
import sys
import webbrowser
from pathlib import Path

from clip_manager import add_clip, update_clip, get_clip, list_clips, remove_clip, stats
from enrichment import get_yt_metadata, suggest_clip_window, enrich_clip


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def fmt_time(seconds: int) -> str:
    if seconds is None:
        return "?"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def print_clip(clip: dict):
    sp = clip.get("spotify") or {}
    print(f"\n  id       : {clip['id']}")
    print(f"  url      : {clip['url']}")
    print(f"  title    : {clip.get('title') or '(unknown)'}")
    print(f"  channel  : {clip.get('channel') or '(unknown)'}")
    print(f"  window   : {fmt_time(clip['start'])} → {fmt_time(clip['end'])}  ({clip['end']-clip['start']}s)")
    print(f"  added    : {clip['added_at'][:10]}")
    if clip.get("notes"):
        print(f"  notes    : {clip['notes']}")
    if clip.get("tags"):
        print(f"  tags     : {', '.join(clip['tags'])}")
    if clip.get("heatmap_peak") is not None:
        print(f"  yt peak  : {fmt_time(clip['heatmap_peak'])}")
    if clip.get("chapters"):
        print(f"  chapters : {len(clip['chapters'])} found")
    if sp:
        print(f"  spotify  : {sp.get('artist')} – {sp.get('track_title')}")
        print(f"             BPM={sp.get('bpm')}  key={sp.get('key')} {sp.get('mode')}")
        print(f"             energy={sp.get('energy')}  valence={sp.get('valence')}  dance={sp.get('danceability')}")
    if clip.get("transcript_snippet"):
        snip = clip["transcript_snippet"][:100]
        print(f"  lyrics   : {snip}...")


def print_clip_row(clip: dict):
    title = (clip.get("title") or "(unknown)")[:40]
    sp = "✓" if clip.get("spotify") else " "
    ht = "✓" if clip.get("heatmap_peak") is not None else " "
    print(f"  {clip['id']}  {fmt_time(clip['start'])}-{fmt_time(clip['end'])}  "
          f"sp={sp} ht={ht}  {title}")


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def cmd_heatmap(args):
    print(f"Fetching yt-dlp data for: {args.url}")
    meta = get_yt_metadata(args.url)

    print(f"\nTitle   : {meta['title']}")
    print(f"Channel : {meta['channel']}")
    print(f"Duration: {fmt_time(meta['duration'])}")

    if meta["heatmap_peak"] is not None:
        start, end = suggest_clip_window(meta["heatmap_peak"], window=args.window)
        print(f"\nHeatmap peak : {fmt_time(meta['heatmap_peak'])} ({meta['heatmap_peak']}s)")
        print(f"Suggested    : --start {start} --end {end}  ({end-start}s window)")
    else:
        print("\nNo heatmap data available for this video.")

    if meta["chapters"]:
        print(f"\nChapters ({len(meta['chapters'])}):")
        for ch in meta["chapters"]:
            print(f"  {fmt_time(ch['start_time'])}  {ch['title']}")


def cmd_chapters(args):
    print(f"Fetching chapters for: {args.url}")
    meta = get_yt_metadata(args.url)

    if not meta["chapters"]:
        print("No chapters found.")
        return

    print(f"\n{meta['title']}\n{'─'*40}")
    for ch in meta["chapters"]:
        dur = ch["end_time"] - ch["start_time"]
        print(f"  {fmt_time(ch['start_time'])}  {ch['title']}  ({dur}s)")
    print(f"\nTo add a chapter as a clip:")
    print(f"  python cli.py add \"{args.url}\" --start <S> --end <E>")


def cmd_add(args):
    url = args.url

    if args.auto:
        print(f"Fetching heatmap to suggest clip window...")
        meta = get_yt_metadata(url)
        if meta["heatmap_peak"] is None:
            print("No heatmap data. Specify --start and --end manually.")
            sys.exit(1)
        start, end = suggest_clip_window(meta["heatmap_peak"], window=args.window)
        print(f"  Auto window: {fmt_time(start)} → {fmt_time(end)}")
    else:
        if args.start is None or args.end is None:
            print("Error: provide --start and --end, or use --auto")
            sys.exit(1)
        start = args.start
        end = args.end

    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []

    clip = add_clip(url=url, start=start, end=end, notes=args.notes or "", tags=tags)
    print(f"\nAdded clip: {clip['id']}")

    # Auto-enrich from yt
    sources = ["yt"]
    if not args.no_spotify:
        sources.append("spotify")
    if not args.no_transcript:
        sources.append("transcript")

    clip = enrich_clip(clip, sources=sources)
    update_clip(clip["id"], **{k: clip[k] for k in [
        "title", "channel", "duration", "heatmap_peak", "chapters",
        "spotify", "transcript_snippet"
    ]})

    print_clip(clip)
    print(f"\nSaved.")


def cmd_enrich(args):
    if args.target == "all":
        clips = list_clips()
        if not clips:
            print("No clips in database.")
            return
        print(f"Enriching {len(clips)} clips...")
        for clip in clips:
            print(f"\n{'='*40}")
            sources = ["yt", "spotify", "transcript"]
            clip = enrich_clip(clip, sources=sources)
            update_clip(clip["id"], **{k: clip[k] for k in [
                "title", "channel", "duration", "heatmap_peak", "chapters",
                "spotify", "transcript_snippet"
            ]})
    else:
        clip = get_clip(args.target)
        clip = enrich_clip(clip)
        update_clip(clip["id"], **{k: clip[k] for k in [
            "title", "channel", "duration", "heatmap_peak", "chapters",
            "spotify", "transcript_snippet"
        ]})
        print_clip(clip)


def cmd_list(args):
    clips = list_clips(tag=args.tag)
    if not clips:
        print("No clips found.")
        return
    print(f"\n{len(clips)} clips  (sp=Spotify  ht=Heatmap)\n")
    print(f"  {'ID':8}  {'Window':15}  flags  {'Title'}")
    print(f"  {'─'*8}  {'─'*15}  {'─'*5}  {'─'*35}")
    for c in clips:
        print_clip_row(c)


def cmd_show(args):
    clip = get_clip(args.clip_id)
    print_clip(clip)


def cmd_rm(args):
    clip = get_clip(args.clip_id)
    print(f"Removing: {clip['id']} — {clip.get('title') or clip['url']}")
    confirm = input("Confirm? [y/N] ")
    if confirm.lower() == "y":
        remove_clip(args.clip_id)
        print("Removed.")
    else:
        print("Cancelled.")


def cmd_annotate(args):
    clip = get_clip(args.clip_id)
    annotator_path = Path(__file__).parent / "annotator.html"
    if not annotator_path.exists():
        print("annotator.html not found.")
        sys.exit(1)

    # Build URL with query params
    file_url = (
        f"file://{annotator_path.resolve()}"
        f"?vid={clip['video_id']}"
        f"&start={clip['start']}"
        f"&end={clip['end']}"
        f"&id={clip['id']}"
    )
    print(f"Opening annotator for: {clip.get('title') or clip['video_id']}")
    print(f"  Window: {fmt_time(clip['start'])} → {fmt_time(clip['end'])}")
    webbrowser.open(file_url)


def cmd_stats(args):
    s = stats()
    print(f"\nDataset stats:")
    print(f"  Total clips      : {s['total_clips']}")
    m, sec = divmod(s["total_duration_seconds"], 60)
    print(f"  Total duration   : {m}m {sec}s")
    print(f"  With Spotify     : {s['with_spotify']}")
    print(f"  With heatmap     : {s['with_heatmap']}")
    if s["tags"]:
        print(f"  Tags:")
        for tag, count in sorted(s["tags"].items(), key=lambda x: -x[1]):
            print(f"    {tag}: {count}")


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        description="YouTube clips dataset manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # add
    p = sub.add_parser("add", help="Add a new clip")
    p.add_argument("url")
    p.add_argument("--start", type=int, help="Start time in seconds")
    p.add_argument("--end", type=int, help="End time in seconds")
    p.add_argument("--auto", action="store_true", help="Auto-detect from heatmap")
    p.add_argument("--window", type=int, default=30, help="Window size in seconds (--auto)")
    p.add_argument("--notes", type=str, default="")
    p.add_argument("--tags", type=str, default="", help="Comma-separated tags")
    p.add_argument("--no-spotify", action="store_true")
    p.add_argument("--no-transcript", action="store_true")

    # heatmap
    p = sub.add_parser("heatmap", help="Show heatmap + suggested window")
    p.add_argument("url")
    p.add_argument("--window", type=int, default=30)

    # chapters
    p = sub.add_parser("chapters", help="List video chapters")
    p.add_argument("url")

    # enrich
    p = sub.add_parser("enrich", help="Enrich clip(s) with extra metadata")
    p.add_argument("target", help="clip ID or 'all'")

    # list
    p = sub.add_parser("list", help="List all clips")
    p.add_argument("--tag", type=str, default=None)

    # show
    p = sub.add_parser("show", help="Show clip details")
    p.add_argument("clip_id")

    # rm
    p = sub.add_parser("rm", help="Remove a clip")
    p.add_argument("clip_id")

    # annotate
    p = sub.add_parser("annotate", help="Open browser annotator")
    p.add_argument("clip_id")

    # stats
    sub.add_parser("stats", help="Dataset statistics")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    dispatch = {
        "add": cmd_add,
        "heatmap": cmd_heatmap,
        "chapters": cmd_chapters,
        "enrich": cmd_enrich,
        "list": cmd_list,
        "show": cmd_show,
        "rm": cmd_rm,
        "annotate": cmd_annotate,
        "stats": cmd_stats,
    }

    handler = dispatch.get(args.command)
    if handler:
        try:
            handler(args)
        except KeyboardInterrupt:
            print("\nInterrupted.")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
