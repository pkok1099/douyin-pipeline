#!/usr/bin/env node
/**
 * Upload video to TikTok via browser automation (Puppeteer)
 * Usage: node upload-tiktok.js <video_file> <title>
 * 
 * Requires: puppeteer, fs
 * Cookies: tiktok-cookies.json (exported from logged-in browser)
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const VIDEO = process.argv[2];
const TITLE = process.argv[3] || 'Untitled';

if (!VIDEO || !fs.existsSync(VIDEO)) {
  console.error('Usage: node upload-tiktok.js <video_file> <title>');
  process.exit(1);
}

(async () => {
  const browser = await puppeteer.launch({
    headless: false, // TikTok needs visible browser
    args: ['--no-sandbox']
  });
  const page = await browser.newPage();

  // Load cookies if available
  const cookieFile = 'tiktok-cookies.json';
  if (fs.existsSync(cookieFile)) {
    const cookies = JSON.parse(fs.readFileSync(cookieFile, 'utf-8'));
    await page.setCookie(...cookies);
  }

  console.log('=== Uploading to TikTok:', TITLE, '===');

  await page.goto('https://www.tiktok.com/upload', { waitUntil: 'networkidle2' });

  // Wait for upload input
  const uploadInput = await page.waitForSelector('input[type="file"]', { timeout: 30000 });
  await uploadInput.uploadFile(path.resolve(VIDEO));

  // Wait for upload to complete
  await page.waitForSelector('[data-e2e="upload-title-input"]', { timeout: 120000 });

  // Fill title
  const titleInput = await page.$('[data-e2e="upload-title-input"]');
  await titleInput.click();
  await titleInput.type(TITLE);

  // Click post
  const postBtn = await page.$('[data-e2e="upload-post"]');
  await postBtn.click();

  // Wait for confirmation
  await page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 60000 });

  console.log('=== TikTok upload done ===');
  await browser.close();
})().catch(err => {
  console.error('TikTok upload failed:', err.message);
  process.exit(1);
});
