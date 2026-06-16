#!/bin/bash
# Douyin auto-downloader using jiji262/douyin-downloader
# Usage: ./douyin-dl.sh [hashtag|user|url] [type] [limit]

set -euo pipefail

DOWNLOAD_DIR="${DOWNLOAD_DIR:-./downloads}"
LIMIT="${3:-20}"

mkdir -p "$DOWNLOAD_DIR"

case "${2:-hashtag}" in
  hashtag)
    echo "=== Downloading hashtag: #$1 (limit: $LIMIT) ==="
    douyin-dl --hashtag "$1" --limit "$LIMIT" -o "$DOWNLOAD_DIR/"
    ;;
  user)
    echo "=== Downloading user: $1 ==="
    douyin-dl --user "$1" -o "$DOWNLOAD_DIR/"
    ;;
  url)
    echo "=== Downloading URL: $1 ==="
    douyin-dl "$1" -o "$DOWNLOAD_DIR/"
    ;;
  *)
    echo "Usage: $0 <query> [hashtag|user|url] [limit]"
    exit 1
    ;;
esac

echo "=== Done. Files in $DOWNLOAD_DIR ==="
ls -la "$DOWNLOAD_DIR/"
