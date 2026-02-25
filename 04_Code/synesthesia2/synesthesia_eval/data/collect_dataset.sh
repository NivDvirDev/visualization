#!/bin/bash
# Dataset collection script for Synesthesia Eval
# Collects music visualization clips from YouTube

DATA_DIR="/Users/guydvir/Project/04_Code/synesthesia2/synesthesia_eval/data/raw"
CLIPS_DIR="/Users/guydvir/Project/04_Code/synesthesia2/synesthesia_eval/data/clips"

mkdir -p "$DATA_DIR"/{good,various,spectrogram,amateur}
mkdir -p "$CLIPS_DIR"

# Search queries for different categories
declare -A QUERIES=(
    ["good"]="best music visualization 4k"
    ["spectrogram"]="spectrogram music video"
    ["reactive"]="audio reactive visualization"
    ["electronic"]="electronic music visualizer"
    ["amateur"]="music visualizer tutorial"
)

# Function to download and clip video
download_clip() {
    local url=$1
    local output_dir=$2
    local video_id=$3
    
    echo "Downloading: $video_id to $output_dir"
    
    # Download best quality under 1080p, max 2 minutes
    yt-dlp "$url" \
        -f "bestvideo[height<=1080]+bestaudio/best[height<=1080]" \
        --max-downloads 1 \
        --download-sections "*0:00-0:30" \
        -o "$output_dir/${video_id}.%(ext)s" \
        --no-playlist \
        2>/dev/null
}

echo "=== Synesthesia Dataset Collector ==="
echo ""

# Search and collect video IDs
for category in "${!QUERIES[@]}"; do
    query="${QUERIES[$category]}"
    echo "Searching: $query -> $category/"
    
    yt-dlp "ytsearch10:$query" \
        --flat-playlist \
        --print "%(id)s" \
        2>/dev/null > "$DATA_DIR/$category/video_ids.txt"
    
    count=$(wc -l < "$DATA_DIR/$category/video_ids.txt" | tr -d ' ')
    echo "  Found: $count videos"
done

echo ""
echo "Video IDs saved. Run with --download to fetch videos."
