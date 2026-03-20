#!/usr/bin/env bash
# deploy.sh — Build, commit to BOTH repos, and deploy to Render.
# Usage: ./scripts/deploy.sh "commit message"
#
# This script exists because the web-labeler lives in TWO git repos:
#   1. Nested repo (synesthesia-labeler) — Render deploys from HERE
#   2. Parent monorepo (visualization) — keeps history in sync
# Pushing only to the parent will NOT deploy. This script handles both.

set -euo pipefail

LABELER_DIR="$(cd "$(dirname "$0")/.." && pwd)"
MONO_DIR="$(cd "$LABELER_DIR/../.." && pwd)"
COMMIT_MSG="${1:?Usage: ./scripts/deploy.sh \"commit message\"}"

echo "=== Step 1: Build client ==="
cd "$LABELER_DIR/client"
npm run build
echo ""

echo "=== Step 2: Stage and commit in NESTED repo (Render source) ==="
cd "$LABELER_DIR"
git add -A
if git diff --cached --quiet; then
  echo "No changes to commit in nested repo."
else
  git commit -m "$COMMIT_MSG"
  echo ""
  echo "=== Step 3: Push nested repo → triggers Render deploy ==="
  git push origin main
fi
echo ""

echo "=== Step 4: Stage and commit in PARENT monorepo ==="
cd "$MONO_DIR"
git add synesthesia_eval/web-labeler/
if git diff --cached --quiet; then
  echo "No changes to commit in monorepo."
else
  git commit -m "$COMMIT_MSG"
  echo ""
  echo "=== Step 5: Push monorepo ==="
  git push origin main
fi
echo ""

echo "=== Step 6: Verify deploy ==="
echo "Waiting 10s for Render to start building..."
sleep 10
BUNDLE=$(curl -s https://synesthesia-labeler.onrender.com/ | grep -o 'main\.[a-f0-9]*\.js' || echo "UNKNOWN")
echo "Current JS bundle: $BUNDLE"
echo ""
echo "Deploy initiated. Render free tier takes ~3-5 min to go live."
echo "Verify at: https://synesthesia-labeler.onrender.com"
