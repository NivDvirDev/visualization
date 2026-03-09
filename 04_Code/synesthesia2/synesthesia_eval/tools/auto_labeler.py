#!/usr/bin/env python3
"""
Auto-Labeling Tool for Synesthesia Evaluation using Google Gemini
Uses Gemini's multimodal capabilities to analyze video+audio and rate clips.

Requirements:
    pip install google-genai

Usage:
    python tools/auto_labeler.py                    # Process all unlabeled clips
    python tools/auto_labeler.py --clip 01          # Process specific clip
    python tools/auto_labeler.py --all              # Re-process all clips
    python tools/auto_labeler.py --dry-run          # Preview without saving
"""

import json
import argparse
import re
import shutil
import tempfile
import time
from pathlib import Path
from typing import Optional
import os

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("❌ Missing google-genai package. Install with:")
    print("   pip install google-genai")
    exit(1)

# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
CLIPS_DIR = DATA_DIR / "clips"
METADATA_FILE = CLIPS_DIR / "metadata.json"
LABELS_FILE = DATA_DIR / "labels.json"
AUTO_LABELS_FILE = DATA_DIR / "auto_labels.json"  # Separate file for AI labels

# Gemini model - using Flash for speed and cost efficiency
MODEL = "gemini-2.5-flash-lite"  # trying lite variant for separate quota

# Rating prompt
RATING_PROMPT = """You are an expert evaluator of music visualization videos (synesthesia-style audio visualizations).

Analyze this video clip and rate it on the following 4 criteria. Each rating should be 1-5.

## Rating Criteria:

### 1. Sync Quality (sync_quality)
How well does the visual sync with the audio beat/rhythm?
- 1 = Poor - No visible sync with music
- 2 = Weak - Occasional sync moments
- 3 = Medium - Some sync visible but inconsistent
- 4 = Good - Clear sync most of the time
- 5 = Excellent - Perfect beat sync throughout

### 2. Visual-Audio Alignment (visual_audio_alignment)
Do visual elements match audio characteristics? (loud=bright, bass=movement, etc.)
- 1 = Poor - No correlation between audio and visuals
- 2 = Weak - Occasional match
- 3 = Medium - Some alignment visible
- 4 = Good - Clear correlation
- 5 = Excellent - Perfect match, visuals feel driven by audio

### 3. Aesthetic Quality (aesthetic_quality)
Overall visual appeal and artistic quality
- 1 = Poor - Ugly, broken, or unpleasant
- 2 = Below Average - Basic, uninteresting
- 3 = Average - Acceptable, nothing special
- 4 = Good - Pleasing, well-designed
- 5 = Excellent - Beautiful, artistic, impressive

### 4. Motion Smoothness (motion_smoothness)
How smooth and natural is the visual motion?
- 1 = Jerky/Choppy - Stuttering, jarring transitions
- 2 = Somewhat rough - Noticeable issues
- 3 = Acceptable - Minor issues
- 4 = Smooth - Fluid motion
- 5 = Very smooth - Perfectly fluid, natural motion

## Response Format:
Respond with ONLY a JSON object in this exact format:
```json
{
    "sync_quality": <1-5>,
    "visual_audio_alignment": <1-5>,
    "aesthetic_quality": <1-5>,
    "motion_smoothness": <1-5>,
    "notes": "<brief explanation of your ratings, max 100 words>"
}
```

Do not include any text outside the JSON block."""


def load_metadata() -> dict:
    """Load clip metadata"""
    if METADATA_FILE.exists():
        with open(METADATA_FILE) as f:
            return json.load(f)
    return {"clips": []}


def load_labels(auto: bool = True) -> dict:
    """Load existing labels"""
    file = AUTO_LABELS_FILE if auto else LABELS_FILE
    if file.exists():
        with open(file) as f:
            return json.load(f)
    return {}


def save_labels(labels: dict, auto: bool = True):
    """Save labels to file"""
    file = AUTO_LABELS_FILE if auto else LABELS_FILE
    with open(file, 'w') as f:
        json.dump(labels, f, indent=2, ensure_ascii=False)
    print(f"💾 Saved to {file.name}")


def get_unlabeled_clips(metadata: dict, labels: dict) -> list:
    """Get list of clips that haven't been labeled"""
    unlabeled = []
    for clip in metadata.get("clips", []):
        clip_id = clip.get("id", clip.get("filename", ""))
        if clip_id not in labels:
            unlabeled.append(clip)
    return unlabeled


def sanitize_filename(name: str) -> str:
    """Replace non-ASCII characters with underscores for API compatibility."""
    return re.sub(r'[^\x20-\x7E]', '_', name)


def analyze_clip(client: genai.Client, video_path: Path, clip_id: str) -> Optional[dict]:
    """Analyze a single video clip using Gemini"""
    print(f"\n🎬 Analyzing clip {clip_id}: {video_path.name}")

    if not video_path.exists():
        print(f"   ❌ File not found: {video_path}")
        return None

    temp_dir = None
    try:
        # Copy to temp path with ASCII-safe name if filename has non-ASCII chars
        safe_name = sanitize_filename(video_path.name)
        if safe_name != video_path.name:
            temp_dir = tempfile.mkdtemp()
            upload_path = Path(temp_dir) / safe_name
            shutil.copy2(video_path, upload_path)
        else:
            upload_path = video_path

        # Upload the video file
        print(f"   📤 Uploading video...")
        video_file = client.files.upload(file=upload_path)
        
        # Wait for processing
        print(f"   ⏳ Processing...")
        while video_file.state == "PROCESSING":
            time.sleep(2)
            video_file = client.files.get(name=video_file.name)
        
        if video_file.state == "FAILED":
            print(f"   ❌ Video processing failed")
            return None
        
        # Generate content with the video
        print(f"   🤖 Analyzing with Gemini...")
        response = client.models.generate_content(
            model=MODEL,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_uri(
                            file_uri=video_file.uri,
                            mime_type=video_file.mime_type
                        ),
                        types.Part.from_text(text=RATING_PROMPT)
                    ]
                )
            ],
            config=types.GenerateContentConfig(
                temperature=0.3,  # Lower temp for more consistent ratings
                max_output_tokens=1024  # Increased for complete responses
            )
        )
        
        # Parse the response
        response_text = response.text.strip()
        
        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text
        
        result = json.loads(json_str)
        
        # Validate ratings
        for key in ["sync_quality", "visual_audio_alignment", "aesthetic_quality", "motion_smoothness"]:
            if key not in result or not isinstance(result[key], int) or not 1 <= result[key] <= 5:
                print(f"   ⚠️ Invalid rating for {key}: {result.get(key)}")
                return None
        
        result["model"] = MODEL
        result["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        
        print(f"   ✅ Ratings: sync={result['sync_quality']}, align={result['visual_audio_alignment']}, "
              f"aesthetic={result['aesthetic_quality']}, motion={result['motion_smoothness']}")
        
        # Cleanup uploaded file
        try:
            client.files.delete(name=video_file.name)
        except:
            pass
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"   ❌ Failed to parse response: {e}")
        print(f"   Response was: {response_text[:500]}")
        return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None
    finally:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)


def push_to_huggingface(labels: dict, dataset_id: str):
    """Push auto_labels.json to HuggingFace dataset."""
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        print("\n⚠️ HF_TOKEN not set. Skipping HuggingFace push.")
        print("   Set HF_TOKEN environment variable with a write-access token.")
        return

    try:
        from huggingface_hub import HfApi
    except ImportError:
        print("\n⚠️ huggingface_hub not installed. Skipping HuggingFace push.")
        print("   Install with: pip install huggingface_hub")
        return

    print(f"\n📤 Pushing auto_labels.json to HuggingFace ({dataset_id})...")
    try:
        api = HfApi(token=hf_token)
        api.upload_file(
            path_or_fileobj=str(AUTO_LABELS_FILE),
            path_in_repo="data/auto_labels.json",
            repo_id=dataset_id,
            repo_type="dataset",
            commit_message=f"Update auto_labels.json ({len(labels)} entries)",
        )
        print(f"   ✅ Pushed {len(labels)} labels to {dataset_id}")
    except Exception as e:
        print(f"   ❌ HuggingFace push failed: {e}")


def main():
    global MODEL
    
    parser = argparse.ArgumentParser(description="Auto-label Synesthesia clips using Gemini AI")
    parser.add_argument("--clip", type=str, help="Process specific clip ID")
    parser.add_argument("--all", action="store_true", help="Re-process all clips (overwrite)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without saving")
    parser.add_argument("--model", type=str, default=MODEL, help=f"Gemini model to use (default: {MODEL})")
    parser.add_argument("--limit", type=int, help="Limit number of clips to process")
    parser.add_argument("--push-hf", action="store_true",
                        help="Push auto_labels.json to HuggingFace after labeling")
    parser.add_argument("--hf-dataset", type=str, default="NivDvir/synesthesia-eval",
                        help="HuggingFace dataset ID (default: NivDvir/synesthesia-eval)")
    args = parser.parse_args()
    
    MODEL = args.model
    
    print("🎵 Synesthesia Auto-Labeler (Gemini AI)")
    print("=" * 50)
    
    # Check for API key
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        # Try to read from common config locations
        config_paths = [
            Path.home() / ".config" / "google" / "api_key.txt",
            Path.home() / ".gemini_api_key",
        ]
        for p in config_paths:
            if p.exists():
                api_key = p.read_text().strip()
                break
    
    if not api_key:
        print("\n❌ No API key found!")
        print("Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable")
        print("Get a key from: https://aistudio.google.com/apikey")
        return
    
    # Initialize Gemini client
    client = genai.Client(api_key=api_key)
    print(f"🤖 Using model: {MODEL}")
    
    # Load data
    metadata = load_metadata()
    labels = load_labels(auto=True)
    
    all_clips = metadata.get("clips", [])
    print(f"📁 Total clips: {len(all_clips)}")
    print(f"🏷️ Already labeled: {len(labels)}")
    
    # Determine which clips to process
    if args.clip:
        clips_to_process = [c for c in all_clips if c.get("id") == args.clip]
        if not clips_to_process:
            print(f"❌ Clip '{args.clip}' not found")
            return
    elif args.all:
        clips_to_process = all_clips
    else:
        clips_to_process = get_unlabeled_clips(metadata, labels)
    
    if args.limit:
        clips_to_process = clips_to_process[:args.limit]
    
    print(f"📋 Clips to process: {len(clips_to_process)}")
    
    if not clips_to_process:
        print("\n✅ All clips are already labeled!")
        return
    
    if args.dry_run:
        print("\n🔍 Dry run mode - no changes will be saved")
        for clip in clips_to_process:
            print(f"  Would process: {clip.get('id')} - {clip.get('filename')}")
        return
    
    # Process clips
    processed = 0
    failed = 0
    
    for i, clip in enumerate(clips_to_process):
        clip_id = clip.get("id", clip.get("filename", "unknown"))
        filename = clip.get("filename", f"{clip_id}.mp4")
        video_path = CLIPS_DIR / filename
        
        print(f"\n[{i+1}/{len(clips_to_process)}]", end="")
        
        result = analyze_clip(client, video_path, clip_id)
        
        if result:
            labels[clip_id] = result
            save_labels(labels, auto=True)
            processed += 1
        else:
            failed += 1
        
        # Rate limiting - be nice to the API
        if i < len(clips_to_process) - 1:
            time.sleep(1)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Summary:")
    print(f"   ✅ Processed: {processed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📁 Total labeled: {len(labels)}")
    print(f"\n💾 Results saved to: {AUTO_LABELS_FILE}")

    # Push to HuggingFace if requested
    if args.push_hf and processed > 0:
        push_to_huggingface(labels, args.hf_dataset)


if __name__ == "__main__":
    main()
