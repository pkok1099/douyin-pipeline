#!/usr/bin/env python
"""
Douyin video downloader - direct API approach
No browser needed, uses mobile API endpoints
"""

import os
import sys
import json
import time
import random
import hashlib
import argparse
import urllib.request
import urllib.parse
import urllib.error

# Douyin mobile API
DOUYIN_API = "https://www.douyin.com/aweme/v1/web/"
USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 "
    "Mobile/15E148 Safari/604.1"
)

DOWNLOAD_DIR = "./downloads"


def getrandom_salt(length=16):
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join(random.choice(chars) for _ in range(length))


def get_user_agent():
    return USER_AGENT


def build_request(url, params=None):
    """Build request with proper headers"""
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"

    req = urllib.request.Request(url)
    req.add_header("User-Agent", get_user_agent())
    req.add_header("Referer", "https://www.douyin.com/")
    req.add_header("Accept", "application/json, text/plain, */*")
    # Cookie with msToken for bypass
    ms_token = getrandom_salt(105)
    req.add_header("Cookie", f"msToken={ms_token}")

    return req


def fetch_api(url, params=None, retry=3):
    """Fetch API with retry"""
    for attempt in range(retry):
        try:
            req = build_request(url, params)
            resp = urllib.request.urlopen(req, timeout=30)
            data = resp.read().decode("utf-8")
            return json.loads(data)
        except urllib.error.HTTPError as e:
            if e.code == 403:
                print(f"  [WARN] 403 Forbidden, attempt {attempt+1}/{retry}")
                time.sleep(2 ** attempt)
                continue
            raise
        except Exception as e:
            print(f"  [WARN] Error: {e}, attempt {attempt+1}/{retry}")
            time.sleep(2 ** attempt)
    return None


def search_hashtag(keyword, count=20):
    """Search videos by hashtag/keyword"""
    url = f"{DOUYIN_API}general/search/single/"
    params = {
        "keyword": keyword,
        "search_channel": "aweme_general",
        "query_correct_type": "1",
        "is_filter_search": "0",
        "from_group_id": "",
        "offset": "0",
        "count": str(count),
        "type": "1",
        "publish_time": "0",
        "sort_type": "0",
        "is_pull_refresh": "1",
    }

    data = fetch_api(url, params)
    if not data:
        return []

    videos = []
    for item in data.get("data", []):
        aweme = item.get("aweme_info", {})
        if not aweme:
            continue

        video_id = aweme.get("aweme_id", "")
        title = aweme.get("desc", "")[:80]
        author = aweme.get("author", {}).get("nickname", "unknown")

        # Get download URL
        play_addr = aweme.get("video", {}).get("play_addr", {})
        download_url = play_addr.get("url_list", [None])[0]

        if download_url:
            # Remove watermark by replacing playwm with play
            download_url = download_url.replace("playwm", "play")
            videos.append({
                "id": video_id,
                "title": title,
                "author": author,
                "url": download_url,
            })

    return videos


def download_video(video, output_dir):
    """Download a single video"""
    video_id = video["id"]
    title = video["title"]
    url = video["url"]

    # Sanitize filename
    safe_title = "".join(c for c in title if c.isalnum() or c in " _-").strip()
    filename = f"{video_id}_{safe_title[:50]}.mp4"
    filepath = os.path.join(output_dir, filename)

    if os.path.exists(filepath):
        print(f"  [SKIP] Already exists: {filename}")
        return filepath

    print(f"  [DOWNLOAD] {title[:60]}...")
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", USER_AGENT)
        resp = urllib.request.urlopen(req, timeout=120)

        with open(filepath, "wb") as f:
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                f.write(chunk)

        size = os.path.getsize(filepath)
        print(f"  [OK] {filename} ({size // 1024} KB)")
        return filepath
    except Exception as e:
        print(f"  [FAIL] {filename}: {e}")
        if os.path.exists(filepath):
            os.remove(filepath)
        return None


def main():
    parser = argparse.ArgumentParser(description="Douyin video downloader")
    parser.add_argument("--hashtag", "-t", required=True, help="Hashtag/keyword to search")
    parser.add_argument("--limit", "-l", type=int, default=10, help="Max videos to download")
    parser.add_argument("--output", "-o", default=DOWNLOAD_DIR, help="Output directory")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    print(f"=== Douyin Downloader ===")
    print(f"Hashtag: #{args.hashtag}")
    print(f"Limit: {args.limit}")
    print(f"Output: {args.output}")
    print()

    # Search
    print(f"[1/2] Searching for #{args.hashtag}...")
    videos = search_hashtag(args.hashtag, args.limit)

    if not videos:
        print("No videos found. Douyin may have changed their API.")
        print("Try again later or use a different keyword.")
        sys.exit(1)

    print(f"Found: {len(videos)} videos")
    print()

    # Download
    print(f"[2/2] Downloading videos...")
    downloaded = 0
    for i, video in enumerate(videos, 1):
        print(f"[{i}/{len(videos)}] @{video['author']}: {video['title'][:60]}")
        if download_video(video, args.output):
            downloaded += 1
        time.sleep(random.uniform(1, 3))  # Rate limit

    print()
    print(f"=== Done: {downloaded}/{len(videos)} videos downloaded ===")
    print(f"Files saved to: {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
