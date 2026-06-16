#!/bin/bash
# Upload video to YouTube via yt-dlp (publish as unlisted/private)
# Usage: ./upload-youtube.sh <video_file> <title> <description>

set -euo pipefail

VIDEO="$1"
TITLE="${2:-Untitled}"
DESC="${3:-Uploaded via auto-upload script}"

if [ ! -f "$VIDEO" ]; then
  echo "ERROR: Video not found: $VIDEO"
  exit 1
fi

echo "=== Uploading to YouTube: $TITLE ==="

# Requires: yt-dlp + cookies.txt from YouTube login
yt-dlp \
  --cookies cookies.txt \
  --meta-title "$TITLE" \
  --meta-description "$DESC" \
  --upload \
  "$VIDEO"

echo "=== YouTube upload done ==="
