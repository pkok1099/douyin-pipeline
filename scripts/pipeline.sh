#!/bin/bash
# Full pipeline: Douyin → TikTok/YouTube/Instagram
# Usage: ./pipeline.sh <hashtag> [platforms]
# 
# Platforms: tiktok,youtube,instagram (comma-separated, default: all)
# Example: ./pipeline.sh "美食" tiktok,youtube

set -euo pipefail

HASHTAG="${1:?Usage: $0 <hashtag> [platforms]}"
PLATFORMS="${2:-tiktok,youtube,instagram}"
DOWNLOAD_DIR="./downloads/${HASHTAG}_$(date +%Y%m%d_%H%M%S)"
LIMIT=10

mkdir -p "$DOWNLOAD_DIR"

echo "========================================="
echo "  Douyin → Multi-Platform Pipeline"
echo "  Hashtag: #${HASHTAG}"
echo "  Platforms: ${PLATFORMS}"
echo "========================================="

# Step 1: Download from Douyin
echo ""
echo "=== Step 1: Downloading from Douyin ==="
douyin-dl --hashtag "$HASHTAG" --limit "$LIMIT" -o "$DOWNLOAD_DIR/"

# Count downloaded files
VIDEO_COUNT=$(find "$DOWNLOAD_DIR" -name "*.mp4" | wc -l)
echo "Downloaded: $VIDEO_COUNT videos"

if [ "$VIDEO_COUNT" -eq 0 ]; then
  echo "No videos downloaded. Exiting."
  exit 0
fi

# Step 2: Upload to selected platforms
echo ""
echo "=== Step 2: Uploading to platforms ==="

IFS=',' read -ra PLATFORM_LIST <<< "$PLATFORMS"

for VIDEO in "$DOWNLOAD_DIR"/*.mp4; do
  [ -f "$VIDEO" ] || continue
  
  FILENAME=$(basename "$VIDEO" .mp4)
  TITLE="#${HASHTAG} - ${FILENAME}"
  
  for PLATFORM in "${PLATFORM_LIST[@]}"; do
    PLATFORM=$(echo "$PLATFORM" | xargs) # trim whitespace
    
    case "$PLATFORM" in
      tiktok)
        echo "--- Uploading to TikTok: $FILENAME ---"
        node scripts/upload-tiktok.js "$VIDEO" "$TITLE" || echo "TikTok upload failed for $FILENAME"
        ;;
      youtube)
        echo "--- Uploading to YouTube: $FILENAME ---"
        bash scripts/upload-youtube.sh "$VIDEO" "$TITLE" || echo "YouTube upload failed for $FILENAME"
        ;;
      instagram)
        echo "--- Uploading to Instagram: $FILENAME ---"
        node scripts/upload-instagram.js "$VIDEO" "$TITLE" || echo "Instagram upload failed for $FILENAME"
        ;;
      *)
        echo "Unknown platform: $PLATFORM"
        ;;
    esac
  done
done

echo ""
echo "========================================="
echo "  Pipeline complete!"
echo "  Videos: $VIDEO_COUNT"
echo "  Platforms: $PLATFORMS"
echo "========================================="
