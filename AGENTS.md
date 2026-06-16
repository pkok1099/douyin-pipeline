# TikTok/Douyin Auto Download & Upload Pipeline

Download video Douyin → Upload ke TikTok/YouTube/Instagram.

## Struktur

```
tiktok/
├── scripts/
│   ├── douyin-dl.sh           # Download dari Douyin (by hashtag/user/url)
│   ├── pipeline.sh            # Full pipeline: download → upload
│   ├── upload-tiktok.js       # Upload ke TikTok (Puppeteer)
│   ├── upload-youtube.sh      # Upload ke YouTube (yt-dlp)
│   ├── upload-instagram.js    # Upload ke Instagram Reels (Puppeteer)
│   └── requirements.txt       # Python dependencies
├── downloads/                  # Output video (gitignored)
├── hashtags.txt               # Daftar hashtag target
└── .github/workflows/
    └── douyin-dl.yml         # GitHub Actions scheduler
```

## Cara Pakai

### 1. Download saja (Douyin)
```bash
pip install douyin-downloader

# By hashtag
./scripts/douyin-dl.sh "美食" hashtag 20

# By user
./scripts/douyin-dl.sh "https://www.douyin.com/user/xxx" user

# By URL
./scripts/douyin-dl.sh "https://www.douyin.com/video/xxx" url
```

### 2. Full Pipeline (Download + Upload)
```bash
# Semua platform
./scripts/pipeline.sh "美食"

# Pilih platform
./scripts/pipeline.sh "美食" tiktok
./scripts/pipeline.sh "美食" youtube,instagram
./scripts/pipeline.sh "美食" tiktok,youtube,instagram
```

### 3. Upload saja (video existing)
```bash
# TikTok
node scripts/upload-tiktok.js ./video.mp4 "Title"

# YouTube
bash scripts/upload-youtube.sh ./video.mp4 "Title" "Description"

# Instagram
node scripts/upload-instagram.js ./video.mp4 "Caption"
```

## Setup Upload

### YouTube
1. Install yt-dlp: `pip install yt-dlp`
2. Export cookies dari browser yang login YouTube:
   - Chrome extension: "Get cookies.txt LOCALLY"
   - Save as `cookies.txt` di folder `tiktok/`

### TikTok
1. Install Puppeteer: `npm install puppeteer`
2. Export cookies dari browser yang login TikTok:
   - Chrome extension: "EditThisCookie"
   - Export as JSON → save as `tiktok-cookies.json`

### Instagram
1. Install Puppeteer: `npm install puppeteer`
2. Export cookies dari browser yang login Instagram:
   - Chrome extension: "EditThisCookie"
   - Export as JSON → save as `instagram-cookies.json`

## GitHub Actions
- Otomatis jalan tiap 6 jam
- Manual trigger: tab Actions → "Douyin Auto Download" → Run workflow
- Input: hashtag & limit
- Output: artifact (retained 7 hari)

## Hashtag Target
Lihat `hashtags.txt` untuk daftar hashtag aktif.

## Catatan
- Gratis, no API key needed (kecuali YouTube API jika pakai official API)
- Rate limit Douyin — jangan terlalu agresif
- Video tanpa watermark
- Hanya video publik
- Upload via browser automation (Puppeteer) — butuh cookies dari akun login
