#!/usr/bin/env python3
"""
Simple Video Labeling Tool for Synesthesia Evaluation
Uses Streamlit for easy UI

Run with: streamlit run tools/labeler.py
"""

import streamlit as st
import json
from pathlib import Path
import random

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
CLIPS_DIR = DATA_DIR / "clips"
METADATA_FILE = DATA_DIR / "clips" / "metadata.json"
LABELS_FILE = DATA_DIR / "labels.json"

# Label definitions
LABELS = {
    "sync_quality": {
        "name": "🎵 Sync Quality",
        "description": "How well does the visual sync with the audio beat/rhythm?",
        "options": [
            (1, "Poor - No visible sync"),
            (2, "Weak - Occasional sync"),
            (3, "Medium - Some sync visible"),
            (4, "Good - Clear sync most of time"),
            (5, "Excellent - Perfect beat sync")
        ]
    },
    "visual_audio_alignment": {
        "name": "🎨 Visual-Audio Alignment", 
        "description": "Do visual elements match audio characteristics (loud=bright, bass=movement)?",
        "options": [
            (1, "Poor - No correlation"),
            (2, "Weak - Occasional match"),
            (3, "Medium - Some alignment"),
            (4, "Good - Clear correlation"),
            (5, "Excellent - Perfect match")
        ]
    },
    "aesthetic_quality": {
        "name": "✨ Aesthetic Quality",
        "description": "Overall visual appeal and artistic quality",
        "options": [
            (1, "Poor - Ugly/broken"),
            (2, "Below Average"),
            (3, "Average - Acceptable"),
            (4, "Good - Pleasing"),
            (5, "Excellent - Beautiful")
        ]
    },
    "motion_smoothness": {
        "name": "🌊 Motion Smoothness",
        "description": "How smooth and natural is the visual motion?",
        "options": [
            (1, "Jerky/Choppy"),
            (2, "Somewhat rough"),
            (3, "Acceptable"),
            (4, "Smooth"),
            (5, "Very smooth/fluid")
        ]
    }
}


def load_metadata():
    """Load clip metadata"""
    if METADATA_FILE.exists():
        with open(METADATA_FILE) as f:
            return json.load(f)
    return {"clips": []}


def load_labels():
    """Load existing labels"""
    if LABELS_FILE.exists():
        with open(LABELS_FILE) as f:
            return json.load(f)
    return {}


def save_labels(labels):
    """Save labels to file"""
    with open(LABELS_FILE, 'w') as f:
        json.dump(labels, f, indent=2)


def get_unlabeled_clips(metadata, labels):
    """Get list of clips that haven't been fully labeled"""
    unlabeled = []
    for clip in metadata.get("clips", []):
        clip_id = clip.get("id", clip.get("filename", ""))
        if clip_id not in labels or len(labels[clip_id]) < len(LABELS):
            unlabeled.append(clip)
    return unlabeled


def main():
    st.set_page_config(
        page_title="Synesthesia Labeler",
        page_icon="🎵",
        layout="wide"
    )
    
    st.title("🎵 Synesthesia Video Labeling Tool")
    
    # Load data
    metadata = load_metadata()
    labels = load_labels()
    
    all_clips = metadata.get("clips", [])
    unlabeled = get_unlabeled_clips(metadata, labels)
    
    # Stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Clips", len(all_clips))
    with col2:
        st.metric("Labeled", len(all_clips) - len(unlabeled))
    with col3:
        st.metric("Remaining", len(unlabeled))
    
    st.progress((len(all_clips) - len(unlabeled)) / max(len(all_clips), 1))
    
    # Sidebar - clip selection
    st.sidebar.header("📁 Clip Selection")
    
    mode = st.sidebar.radio("Mode", ["Unlabeled Only", "All Clips", "Review Labeled"])
    
    if mode == "Unlabeled Only":
        available_clips = unlabeled
    elif mode == "Review Labeled":
        available_clips = [c for c in all_clips if c.get("id", c.get("filename", "")) in labels]
    else:
        available_clips = all_clips
    
    if not available_clips:
        st.success("🎉 All clips have been labeled!" if mode == "Unlabeled Only" else "No clips available")
        return
    
    # Clip selector
    clip_names = [c.get("id", c.get("filename", "unknown")) for c in available_clips]
    
    if st.sidebar.button("🎲 Random Clip"):
        st.session_state.clip_idx = random.randint(0, len(available_clips) - 1)
    
    clip_idx = st.sidebar.selectbox(
        "Select Clip",
        range(len(clip_names)),
        format_func=lambda i: clip_names[i],
        index=st.session_state.get("clip_idx", 0)
    )
    
    current_clip = available_clips[clip_idx]
    clip_id = current_clip.get("id", current_clip.get("filename", ""))
    
    # Main content - two columns
    left_col, right_col = st.columns([2, 1])
    
    with left_col:
        st.subheader(f"📹 {clip_id}")
        
        # Video player
        video_path = CLIPS_DIR / current_clip.get("filename", f"{clip_id}.mp4")
        if video_path.exists():
            st.video(str(video_path))
        else:
            st.error(f"Video not found: {video_path}")
        
        # Clip metadata
        with st.expander("📋 Clip Info"):
            st.json(current_clip)
    
    with right_col:
        st.subheader("🏷️ Labels")
        
        # Get existing labels for this clip
        clip_labels = labels.get(clip_id, {})
        
        # Label inputs
        new_labels = {}
        for key, config in LABELS.items():
            st.markdown(f"**{config['name']}**")
            st.caption(config['description'])
            
            options = config['options']
            current_val = clip_labels.get(key, 0)
            
            # Find index of current value
            idx = 0
            for i, (val, _) in enumerate(options):
                if val == current_val:
                    idx = i
                    break
            
            selected = st.radio(
                key,
                options,
                index=idx if current_val > 0 else None,
                format_func=lambda x: f"{x[0]} - {x[1]}",
                key=f"radio_{key}_{clip_id}",
                horizontal=True
            )
            
            if selected:
                new_labels[key] = selected[0]
            
            st.divider()
        
        # Notes
        notes = st.text_area(
            "📝 Notes (optional)",
            value=clip_labels.get("notes", ""),
            key=f"notes_{clip_id}"
        )
        if notes:
            new_labels["notes"] = notes
        
        # Save button
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Labels", type="primary", use_container_width=True):
                if len(new_labels) >= len(LABELS):
                    labels[clip_id] = new_labels
                    save_labels(labels)
                    st.success("✅ Saved!")
                    st.balloons()
                else:
                    st.warning("⚠️ Please rate all categories")
        
        with col2:
            if st.button("⏭️ Skip", use_container_width=True):
                st.session_state.clip_idx = (clip_idx + 1) % len(available_clips)
                st.rerun()
    
    # Keyboard shortcuts info
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⌨️ Tips")
    st.sidebar.markdown("""
    - Use number keys 1-5 for quick rating
    - Click Random for variety
    - Save often!
    """)
    
    # Export option
    st.sidebar.markdown("---")
    if st.sidebar.button("📥 Export Labels JSON"):
        st.sidebar.download_button(
            "Download labels.json",
            json.dumps(labels, indent=2),
            "labels.json",
            "application/json"
        )


if __name__ == "__main__":
    main()
