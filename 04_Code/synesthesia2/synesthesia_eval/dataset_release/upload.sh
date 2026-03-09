#!/usr/bin/env bash
#
# upload.sh - Upload synesthesia_eval dataset to HuggingFace and Zenodo
#
# Prerequisites:
#   pip install huggingface_hub
#   huggingface-cli login
#
# For Zenodo:
#   export ZENODO_TOKEN="your-token"  (get from https://zenodo.org/account/settings/applications/)
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$(dirname "$SCRIPT_DIR")/data"
RELEASE_DIR="$SCRIPT_DIR"

# --- Configuration ---
HF_REPO="nivdvir/synesthesia-eval"
ZENODO_API="https://zenodo.org/api"

# ============================================================
# HuggingFace Upload
# ============================================================
upload_huggingface() {
    echo "=== Uploading to HuggingFace: $HF_REPO ==="

    # Create the dataset repo (no-op if it exists)
    huggingface-cli repo create "$HF_REPO" --type dataset 2>/dev/null || true

    # Upload dataset card
    huggingface-cli upload "$HF_REPO" "$RELEASE_DIR/README.md" README.md --repo-type dataset

    # Upload license
    huggingface-cli upload "$HF_REPO" "$RELEASE_DIR/LICENSE" LICENSE --repo-type dataset

    # Upload metadata
    huggingface-cli upload "$HF_REPO" "$DATA_DIR/clips/metadata.json" data/metadata.json --repo-type dataset

    # Upload labels
    huggingface-cli upload "$HF_REPO" "$DATA_DIR/auto_labels.json" data/auto_labels.json --repo-type dataset
    if [ -s "$DATA_DIR/labels.json" ]; then
        huggingface-cli upload "$HF_REPO" "$DATA_DIR/labels.json" data/labels.json --repo-type dataset
    fi

    # Upload video clips
    echo "Uploading video clips (this may take a while)..."
    huggingface-cli upload "$HF_REPO" "$DATA_DIR/clips/" data/clips/ --repo-type dataset \
        --include "*.mp4"

    echo "=== HuggingFace upload complete ==="
    echo "  https://huggingface.co/datasets/$HF_REPO"
}

# ============================================================
# Zenodo Upload
# ============================================================
upload_zenodo() {
    echo "=== Uploading to Zenodo ==="

    if [ -z "${ZENODO_TOKEN:-}" ]; then
        echo "Error: ZENODO_TOKEN not set"
        echo "Get one at: https://zenodo.org/account/settings/applications/"
        exit 1
    fi

    # 1. Create a new deposition
    echo "Creating Zenodo deposition..."
    RESPONSE=$(curl -s -X POST "$ZENODO_API/deposit/depositions" \
        -H "Authorization: Bearer $ZENODO_TOKEN" \
        -H "Content-Type: application/json" \
        -d @"$RELEASE_DIR/.zenodo.json")

    DEPOSITION_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
    BUCKET_URL=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['links']['bucket'])")

    echo "Deposition ID: $DEPOSITION_ID"
    echo "Bucket URL: $BUCKET_URL"

    # 2. Create a zip archive of the dataset
    ARCHIVE="/tmp/synesthesia_eval_dataset.zip"
    echo "Creating dataset archive..."
    (cd "$DATA_DIR/.." && zip -r "$ARCHIVE" \
        data/clips/metadata.json \
        data/auto_labels.json \
        data/labels.json \
        data/clips/*.mp4 \
        2>/dev/null)

    # 3. Upload the archive
    echo "Uploading archive to Zenodo..."
    curl -s -X PUT "$BUCKET_URL/synesthesia_eval_dataset.zip" \
        -H "Authorization: Bearer $ZENODO_TOKEN" \
        -H "Content-Type: application/octet-stream" \
        --data-binary @"$ARCHIVE"

    # 4. Upload metadata files
    for f in README.md LICENSE .zenodo.json; do
        curl -s -X PUT "$BUCKET_URL/$f" \
            -H "Authorization: Bearer $ZENODO_TOKEN" \
            -H "Content-Type: application/octet-stream" \
            --data-binary @"$RELEASE_DIR/$f"
    done

    rm -f "$ARCHIVE"

    echo ""
    echo "=== Zenodo deposition created (DRAFT) ==="
    echo "  Review and publish at: https://zenodo.org/deposit/$DEPOSITION_ID"
    echo "  The deposition is NOT published yet - review it on Zenodo before publishing."
}

# ============================================================
# Main
# ============================================================
usage() {
    echo "Usage: $0 {huggingface|zenodo|all}"
    echo ""
    echo "  huggingface  Upload dataset to HuggingFace Hub"
    echo "  zenodo       Upload dataset to Zenodo (creates draft)"
    echo "  all          Upload to both platforms"
}

case "${1:-}" in
    huggingface|hf)
        upload_huggingface
        ;;
    zenodo)
        upload_zenodo
        ;;
    all)
        upload_huggingface
        upload_zenodo
        ;;
    *)
        usage
        exit 1
        ;;
esac
