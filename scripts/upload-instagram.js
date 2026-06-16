#!/usr/bin/env node
/**
 * Upload video to Instagram Reels via browser automation (Puppeteer)
 * Usage: node upload-instagram.js <video_file> <caption>
 * 
 * Requires: puppeteer, fs
 * Cookies: instagram-cookies.json (exported from logged-in browser)
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const VIDEO = process.argv[2];
const CAPTION = process.argv[3] || '';

if (!VIDEO || !fs.existsSync(VIDEO)) {
  console.error('Usage: node upload-instagram.js <video_file> <caption>');
  process.exit(1);
}

(async () => {
  const browser = await puppeteer.launch({
    headless: false,
    args: ['--no-sandbox']
  });
  const page = await browser.newPage();

  // Load cookies
  const cookieFile = 'instagram-cookies.json';
  if (fs.existsSync(cookieFile)) {
    const cookies = JSON.parse(fs.readFileSync(cookieFile, 'utf-8'));
    await page.setCookie(...cookies);
  }

  console.log('=== Uploading to Instagram Reels ===');

  await page.goto('https://www.instagram.com/', { waitUntil: 'networkidle2' });

  // Click "New post" button
  await page.waitForSelector('[aria-label="New post"]', { timeout: 30000 });
  await page.click('[aria-label="New post"]');

  // Wait for file input
  const uploadInput = await page.waitForSelector('input[type="file"]', { timeout: 30000 });
  await uploadInput.uploadFile(path.resolve(VIDEO));

  // Wait for upload
  await page.waitForSelector('[aria-label="Next"]', { timeout: 120000 });
  await page.click('[aria-label="Next"]');

  // Skip filters
  await page.waitForSelector('[aria-label="Next"]', { timeout: 30000 });
  await page.click('[aria-label="Next"]');

  // Fill caption
  if (CAPTION) {
    const captionBox = await page.waitForSelector('[aria-label="Write a caption..."]', { timeout: 30000 });
    await captionBox.click();
    await captionBox.type(CAPTION);
  }

  // Share
  await page.waitForSelector('button >> text=Share', { timeout: 30000 });
  await page.click('button >> text=Share');

  // Wait for confirmation
  await page.waitForSelector('text=Your post has been shared', { timeout: 60000 });

  console.log('=== Instagram upload done ===');
  await browser.close();
})().catch(err => {
  console.error('Instagram upload failed:', err.message);
  process.exit(1);
});
