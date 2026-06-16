#!/usr/bin/env python3
"""
SaveTik.co Douyin/TikTok downloader
Uses their API to get download links without browser
"""

import os
import sys
import json
import time
import re
import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar

SAVETIK_URL = "https://savetik.co"
API_SEARCH = f"{SAVETIK_URL}/api/ajaxSearch"
USER_AGENT = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36"
DOWNLOAD_DIR = "./downloads"


def get_cookies():
    """Get session cookies from savetik.co"""
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    req = urllib.request.Request(SAVETIK_URL)
    req.add_header("User-Agent", USER_AGENT)

    try:
        resp = opener.open(req, timeout=30)
        resp.read()
        return opener, cj
    except Exception as e:
        print(f"Failed to get cookies: {e}")
        return None, None


def search_video(opener, url, lang="id"):
    """Search for video download link via API"""
    data = urllib.parse.urlencode({
        "q": url,
        "lang": lang,
        "cftoken": ""
    }).encode()

    req = urllib.request.Request(API_SEARCH, data=data, method="POST")
    req.add_header("User-Agent", USER_AGENT)
    req.add_header("Referer", f"{SAVETIK_URL}/id/douyin-downloader")
    req.add_header("X-Requested-With", "XMLHttpRequest")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        resp = opener.open(req, timeout=30)
        raw = resp.read().decode("utf-8")
        result = json.loads(raw)
        return result
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print("  [WARN] Rate limited, waiting 10s...")
            time.sleep(10)
            return search_video(opener, url, lang)
        print(f"  [ERROR] HTTP {e.code}")
        return None
    except Exception as e:
        print(f"  [ERROR] {e}")
        return None


def parse_download_links(html):
    """Extract download links from API response HTML"""
    links = []

    # Pattern: href="URL" from download buttons (snapcdn.app/get?token=)
    snap_links = re.findall(r'href=["\'](https?://dl\.snapcdn\.app/get\?token=[^"\']+)["\']', html)
    links.extend(snap_links)

    # Pattern: href="URL" with tiktokcdn
    cdn_links = re.findall(r'href=["\'](https?://[^"\']*tiktokcdn[^"\']*)["\']', html)
    links.extend(cdn_links)

    # Pattern: data-src for video
    data_src = re.findall(r'data-src=["\'](https?://[^"\']+)["\']', html)
    links.extend(data_src)

    # Fallback: any href with video/mp4/video content
    all_hrefs = re.findall(r'href=["\'](https?://[^"\']+)["\']', html)
    for h in all_hrefs:
        if any(k in h for k in ['snapcdn', 'tiktokcdn', 'mp4', 'video']):
            if h not in links:
                links.append(h)

    # Deduplicate preserving order
    seen = set()
    unique = []
    for l in links:
        if l not in seen:
            seen.add(l)
            unique.append(l)

    return unique


def parse_video_info(html):
    """Extract video metadata from response"""
    info = {}

    # Author
    author_match = re.findall(r'class="(?:author|user|nickname)"[^>]*>([^<]+)<', html)
    if author_match:
        info["author"] = author_match[0].strip()

    # Title/desc
    title_match = re.findall(r'class="(?:title|desc)"[^>]*>([^<]+)<', html)
    if title_match:
        info["title"] = title_match[0].strip()

    # Thumbnail
    thumb_match = re.findall(r'src=["\'](https?://[^"\']+\.(?:jpg|jpeg|webp)[^"\']*)["\']', html)
    if thumb_match:
        info["thumbnail"] = thumb_match[0]

    return info


def download_file(url, filepath):
    """Download file with progress, following redirects"""
    try:
        # Handle snapCDN token URLs - need to follow redirect
        req = urllib.request.Request(url)
        req.add_header("User-Agent", USER_AGENT)
        req.add_header("Referer", SAVETIK_URL + "/")

        # Don't follow redirects automatically - snapCDN returns 302
        opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler())
        resp = opener.open(req, timeout=120)

        total = resp.headers.get("Content-Length")
        downloaded = 0

        with open(filepath, "wb") as f:
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)

                if total:
                    pct = downloaded / int(total) * 100
                    print(f"\r  [{pct:.1f}%]", end="", flush=True)

        if total:
            print()

        # Check if we got actual video (not HTML error page)
        size = os.path.getsize(filepath)
        if size < 10000:  # Less than 10KB is probably not a video
            with open(filepath, "rb") as f:
                header = f.read(100)
                if b"<html" in header.lower() or b"<!doctype" in header.lower():
                    print(f"  [FAIL] Got HTML instead of video")
                    os.remove(filepath)
                    return False

        return True
    except Exception as e:
        print(f"\n  [FAIL] {e}")
        if os.path.exists(filepath):
            os.remove(filepath)
        return False


def download_from_url(video_url, output_dir=DOWNLOAD_DIR):
    """Main: download video from Douyin/TikTok URL"""
    os.makedirs(output_dir, exist_ok=True)

    print(f"[{video_url[:60]}]")

    # Get session
    print("  Getting session...")
    opener, cj = get_cookies()
    if not opener:
        return None

    # Search
    print("  Searching...")
    result = search_video(opener, video_url)
    if not result:
        return None

    if result.get("status") != "ok":
        msg = result.get("msg", "Unknown error")
        print(f"  [FAIL] API error: {msg}")
        return None

    data = result.get("data", "")
    if not data:
        print("  [FAIL] No data returned")
        return None

    # Parse
    info = parse_video_info(data)
    links = parse_download_links(data)

    if not links:
        print("  [FAIL] No download links found")
        # Save raw HTML for debugging
        with open(f"{output_dir}/debug.html", "w") as f:
            f.write(data)
        print(f"  [DEBUG] Saved response to {output_dir}/debug.html")
        return None

    # Info
    if info.get("author"):
        print(f"  Author: {info['author']}")
    if info.get("title"):
        print(f"  Title: {info['title'][:60]}")
    print(f"  Download links: {len(links)}")

    # Pick best link: prefer snapcdn with token, then HD, then first
    dl_url = None
    for l in links:
        if "snapcdn" in l and "token=" in l:
            dl_url = l
            break
    if not dl_url:
        dl_url = links[0]

    print(f"  Downloading: {dl_url[:80]}...")

    # Generate filename
    author = info.get("author", "unknown")
    title = info.get("title", "")[:30]
    safe_title = "".join(c for c in title if c.isalnum() or c in " _-").strip()
    filename = f"{author}_{safe_title}.mp4"
    filepath = os.path.join(output_dir, filename)

    if os.path.exists(filepath):
        print(f"  [SKIP] Already exists")
        return filepath

    success = download_file(dl_url, filepath)
    if success:
        size = os.path.getsize(filepath) // 1024
        print(f"  [OK] {filename} ({size} KB)")
        return filepath

    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 savetik-dl.py <url1> [url2] ...")
        print("   or: python3 savetik-dl.py --file <urls.txt>")
        sys.exit(1)

    urls = []

    if sys.argv[1] == "--file":
        file_path = sys.argv[2]
        with open(file_path) as f:
            urls = [line.strip() for line in f if line.strip()]
    else:
        urls = sys.argv[1:]

    print(f"=== SaveTik Downloader ===")
    print(f"URLs: {len(urls)}")
    print(f"Output: {DOWNLOAD_DIR}")
    print()

    success = 0
    failed = 0

    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}]")
        result = download_from_url(url)
        if result:
            success += 1
        else:
            failed += 1

        # Rate limit
        if i < len(urls):
            wait = 3
            print(f"  Waiting {wait}s...")
            time.sleep(wait)

    print()
    print(f"=== Done: {success} OK, {failed} failed ===")


if __name__ == "__main__":
    main()
