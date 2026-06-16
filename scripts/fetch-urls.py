#!/usr/bin/env python3
"""
Fetch video URLs from TikTok/Douin trending/explore pages
"""

import os
import sys
import json
import re
import urllib.request
import urllib.parse
import time

USER_AGENT = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36"


def fetch_trending_tiktok():
    """Fetch trending video URLs from TikTok explore page"""
    urls = []
    
    # TikTok explore page
    explore_url = "https://www.tiktok.com/foryou"
    
    try:
        req = urllib.request.Request(explore_url)
        req.add_header("User-Agent", USER_AGENT)
        resp = urllib.request.urlopen(req, timeout=30)
        html = resp.read().decode("utf-8")
        
        # Extract video URLs from page
        # Pattern: /@username/video/VIDEO_ID
        video_urls = re.findall(r'href="(https://www\.tiktok\.com/@[^/]+/video/\d+)"', html)
        urls.extend(video_urls)
        
        # Also look for short links
        short_urls = re.findall(r'href="(https://vm\.tiktok\.com/[^"]+)"', html)
        urls.extend(short_urls)
        
        # Deduplicate
        urls = list(dict.fromkeys(urls))
        
    except Exception as e:
        print(f"[WARN] TikTok trending failed: {e}")
    
    return urls


def fetch_trending_douyin():
    """Fetch trending video URLs from Douyin explore page"""
    urls = []
    
    # Douyin explore/discover page
    explore_url = "https://www.douyin.com/discover"
    
    try:
        req = urllib.request.Request(explore_url)
        req.add_header("User-Agent", USER_AGENT)
        resp = urllib.request.urlopen(req, timeout=30)
        html = resp.read().decode("utf-8")
        
        # Extract video URLs
        # Pattern: /video/VIDEO_ID
        video_urls = re.findall(r'href="(https://www\.douyin\.com/video/\d+)"', html)
        urls.extend(video_urls)
        
        # Short links
        short_urls = re.findall(r'href="(https://v\.douyin\.com/[^"]+)"', html)
        urls.extend(short_urls)
        
        # Deduplicate
        urls = list(dict.fromkeys(urls))
        
    except Exception as e:
        print(f"[WARN] Douyin trending failed: {e}")
    
    return urls


def search_tiktok_hashtag(hashtag, count=20):
    """Search TikTok by hashtag"""
    urls = []
    
    search_url = f"https://www.tiktok.com/tag/{hashtag}"
    
    try:
        req = urllib.request.Request(search_url)
        req.add_header("User-Agent", USER_AGENT)
        resp = urllib.request.urlopen(req, timeout=30)
        html = resp.read().decode("utf-8")
        
        # Extract video URLs
        video_urls = re.findall(r'href="(https://www\.tiktok\.com/@[^/]+/video/\d+)"', html)
        urls.extend(video_urls)
        
        # Deduplicate and limit
        urls = list(dict.fromkeys(urls))[:count]
        
    except Exception as e:
        print(f"[WARN] TikTok hashtag search failed: {e}")
    
    return urls


def search_douyin_hashtag(hashtag, count=20):
    """Search Douyin by hashtag"""
    urls = []
    
    # Douyin search API
    search_url = f"https://www.douyin.com/search/{urllib.parse.quote(hashtag)}"
    
    try:
        req = urllib.request.Request(search_url)
        req.add_header("User-Agent", USER_AGENT)
        resp = urllib.request.urlopen(req, timeout=30)
        html = resp.read().decode("utf-8")
        
        # Extract video URLs
        video_urls = re.findall(r'href="(https://www\.douyin\.com/video/\d+)"', html)
        urls.extend(video_urls)
        
        # Deduplicate and limit
        urls = list(dict.fromkeys(urls))[:count]
        
    except Exception as e:
        print(f"[WARN] Douyin hashtag search failed: {e}")
    
    return urls


def main():
    print("=== Fetching video URLs ===\n")
    
    all_urls = {}
    
    # 1. TikTok trending
    print("[1/4] TikTok trending...")
    urls = fetch_trending_tiktok()
    print(f"  Found: {len(urls)} URLs")
    all_urls["tiktok_trending"] = urls
    
    time.sleep(2)
    
    # 2. Douyin trending
    print("[2/4] Douyin trending...")
    urls = fetch_trending_douyin()
    print(f"  Found: {len(urls)} URLs")
    all_urls["douyin_trending"] = urls
    
    time.sleep(2)
    
    # 3. TikTok hashtag
    print("[3/4] TikTok hashtag search...")
    hashtags = ["fyp", "viral", "trending"]
    tiktag_urls = []
    for tag in hashtags:
        urls = search_tiktok_hashtag(tag, 10)
        tiktag_urls.extend(urls)
        time.sleep(1)
    tiktag_urls = list(dict.fromkeys(tiktag_urls))
    print(f"  Found: {len(tiktag_urls)} URLs")
    all_urls["tiktok_hashtag"] = tiktag_urls
    
    time.sleep(2)
    
    # 4. Douyin hashtag
    print("[4/4] Douyin hashtag search...")
    hashtags = ["美食", "旅行", "搞笑"]
    douyin_urls = []
    for tag in hashtags:
        urls = search_douyin_hashtag(tag, 10)
        douyin_urls.extend(urls)
        time.sleep(1)
    douyin_urls = list(dict.fromkeys(douyin_urls))
    print(f"  Found: {len(douyin_urls)} URLs")
    all_urls["douyin_hashtag"] = douyin_urls
    
    # Combine all
    combined = []
    for category, urls in all_urls.items():
        combined.extend(urls)
    combined = list(dict.fromkeys(combined))
    
    print(f"\n=== Total: {len(combined)} unique URLs ===")
    
    # Save to file
    output_file = "urls.txt"
    with open(output_file, "w") as f:
        for url in combined:
            f.write(url + "\n")
    
    print(f"Saved to: {output_file}")
    
    # Also save JSON with categories
    with open("urls.json", "w") as f:
        json.dump(all_urls, f, indent=2, ensure_ascii=False)
    
    print("Saved details to: urls.json")
    
    # Print first 10
    print(f"\nFirst 10 URLs:")
    for url in combined[:10]:
        print(f"  {url}")


if __name__ == "__main__":
    main()
