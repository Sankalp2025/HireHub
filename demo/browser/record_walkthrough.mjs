import { chromium, expect } from '@playwright/test';
import { randomBytes } from 'node:crypto';
import { readFile, mkdir, mkdtemp, rename, rm, stat } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

// Run against the real local stack; never mock API responses or print credentials.
const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const media = join(root, 'docs/media');
const base = join(media, 'hirehub-browser-demo');
const resume = await readFile(join(root, 'demo/fixtures/resume.txt'), 'utf8');
const jd = await readFile(join(root, 'demo/fixtures/job_description.txt'), 'utf8');
const email = `demo+${Date.now()}@example.com`;
const password = `Demo!${randomBytes(24).toString('hex')}`;
const health = await fetch('http://localhost:8000/api/v1/health').then(r => r.json());
if (health.data?.db !== 'connected') throw new Error('Start the backend and database first.');
execFileSync('ffmpeg', ['-version'], { stdio: 'ignore' });
await mkdir(media, { recursive: true });
const scratch = await mkdtemp(join(tmpdir(), 'hirehub-browser-'));
const browser = await chromium.launch({ slowMo: 250 });
const context = await browser.newContext({
  viewport: { width: 1280, height: 800 },
  recordVideo: { dir: scratch, size: { width: 1280, height: 800 } },
});
const page = await context.newPage();
page.setDefaultTimeout(15000);
const video = page.video();
const failures = [];
page.on('pageerror', () => failures.push('Browser runtime error'));
page.on('response', response => {
  if (response.url().startsWith('http://localhost:8000/api/v1/') && !response.ok()) {
    failures.push(`API failure: ${response.status()} ${new URL(response.url()).pathname}`);
  }
});
// Observe even briefly displayed error toasts without depending on CSS classes.
await page.exposeFunction('reportDemoAlert', () => failures.push('Visible error alert'));
await page.addInitScript(() => {
  new MutationObserver(() => {
    if (document.querySelector('[role="alert"]')?.textContent.trim()) {
      window.reportDemoAlert();
    }
    const messages = document.querySelector('[role="status"][aria-live="polite"]')?.textContent;
    if (messages && /could not|failed|error|try again/i.test(messages)) window.reportDemoAlert();
  }).observe(document, { childList: true, subtree: true });
});
const pause = ms => page.waitForTimeout(ms);
async function nav(name) {
  await page.getByRole('navigation', { name: 'Primary' }).getByRole('link', { name, exact: true }).click();
}
async function showHeading(name, hold = 2200) {
  const heading = page.getByRole('heading', { name, exact: true });
  await expect(heading).toBeVisible();
  const y = await heading.evaluate(el => el.getBoundingClientRect().top + window.scrollY - 100);
  await page.evaluate(y => window.scrollTo({ top: y, behavior: 'smooth' }), y);
  await pause(hold);
}
let complete = false;
try {
  await page.goto('http://localhost:5173');
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  await pause(2000);
  await page.getByRole('link', { name: 'Create account', exact: true }).click();
  await page.getByLabel('Full name', { exact: true }).fill('Jordan Lee');
  await page.getByLabel('Email', { exact: true }).fill(email);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await pause(1200);
  await page.getByRole('button', { name: 'Create account', exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
  await pause(1000);
  await page.getByLabel('Email', { exact: true }).fill(email);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByRole('heading', { name: 'Welcome back, Jordan Lee.' })).toBeVisible();
  await pause(2000);

  await nav('Resumes');
  await page.getByLabel('Resume title', { exact: true }).fill('Backend Resume v1');
  await page.getByLabel('Resume content', { exact: true }).fill(resume);
  await pause(1500);
  await page.getByRole('button', { name: 'Save resume', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Backend Resume v1', exact: true })).toBeVisible();
  await pause(1800);

  await nav('Job descriptions');
  await page.getByLabel('Title', { exact: true }).fill('Entry-level Backend Engineer');
  await page.getByLabel('Company (optional)', { exact: true }).fill('Acme Corp');
  await page.getByLabel('Job description content', { exact: true }).fill(jd);
  await pause(1500);
  await page.getByRole('button', { name: 'Save job description', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Entry-level Backend Engineer', exact: true })).toBeVisible();
  await pause(1800);

  await nav('Analyze');
  await page.getByRole('combobox', { name: /^Resume/ }).selectOption({ label: 'Backend Resume v1' });
  await page.getByRole('combobox', { name: /^Job description/ }).selectOption({ label: 'Entry-level Backend Engineer · Acme Corp' });
  await pause(1000);
  const analysisResponse = page.waitForResponse(r => r.url().endsWith('/analyses') && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'Run analysis', exact: true }).click();
  const response = await analysisResponse;
  expect(response.status()).toBe(201);
  const saved = (await response.json()).data;
  expect(Number(saved.keyword_overlap.score_weights.cosine_similarity_score)).toBe(0);
  await expect(page.getByText('Match score', { exact: true })).toBeVisible();
  await pause(4800);
  await showHeading('How this score was calculated');
  await showHeading('Category breakdown', 2800);
  await showHeading('Matched terms');
  await showHeading('Missing hard skills');
  await showHeading('Other missing keywords', 3000);
  await showHeading('Suggestions', 3200);

  await nav('History');
  await expect(page.getByRole('heading', { name: 'Past analyses.', exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: /Backend Resume v1/ })).toHaveCount(1);
  await page.getByRole('button', { name: /Backend Resume v1/ }).click();
  await expect(page.getByText('Match score', { exact: true })).toBeVisible();
  await pause(5500);
  expect(failures, 'Walkthrough must have no runtime, API, or visible errors').toEqual([]);
  complete = true;
} catch (error) {
  // Redact credentials from Playwright diagnostics, which can include fill values.
  console.error('Walkthrough failed. Check the local app and recording; credentials are omitted.');
  console.error(String(error.message).replaceAll(password, '[redacted]'));
  process.exitCode = 1;
} finally {
  await context.close();
  if (complete) await video.saveAs(`${base}.webm`);
  await browser.close();
}
if (complete) {
  const ffmpeg = args => execFileSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', ...args], { stdio: 'inherit' });
  // Skip the initial blank Chromium frame so README previews show the landing page.
  ffmpeg(['-ss', '0.8', '-i', `${base}.webm`, '-c:v', 'libx264', '-preset', 'slow', '-crf', '23', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', `${base}.mp4`]);
  const gif = join(scratch, 'demo.gif');
  for (const fps of [12, 10, 8]) {
    ffmpeg(['-ss', '0.8', '-i', `${base}.webm`, '-filter_complex', `fps=${fps},scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96:stats_mode=diff[p];[b][p]paletteuse=dither=none:diff_mode=rectangle`, '-loop', '0', gif]);
    if ((await stat(gif)).size < 8 * 1024 * 1024) break;
  }
  if ((await stat(gif)).size >= 8 * 1024 * 1024) throw new Error('GIF exceeds 8 MiB; shorten the pauses.');
  await rename(gif, `${base}.gif`);
  await rm(scratch, { recursive: true, force: true });
  console.log('Walkthrough verified: landing, registration, login, resume, job description, analysis, history.');
  console.log('Saved docs/media/hirehub-browser-demo.{webm,mp4,gif}');
}
