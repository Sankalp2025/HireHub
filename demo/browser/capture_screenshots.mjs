import { chromium, expect } from '@playwright/test';
import { randomBytes } from 'node:crypto';
import { mkdir, readFile } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

// README screenshots from the real local stack. Data is created through the API so
// the shots are deterministic; the pages themselves are the real frontend.
const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const out = join(root, 'docs/media/screenshots');
const api = 'http://localhost:8000/api/v1';
const app = 'http://localhost:5173';
const resume = (await readFile(join(root, 'demo/fixtures/resume.txt'), 'utf8')).trim();
const jd = (await readFile(join(root, 'demo/fixtures/job_description.txt'), 'utf8')).trim();
const email = `demo+${Date.now()}@example.com`;
const password = `Demo!${randomBytes(24).toString('hex')}`;

async function call(path, body, token) {
  const response = await fetch(`${api}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(token && { Authorization: `Bearer ${token}` }) },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(`API failure: ${response.status} ${path}`);
  return (await response.json()).data;
}

await call('/auth/register', { email, password, full_name: 'Jordan Lee' });
const tokens = await call('/auth/login', { email, password });
const token = tokens.access_token;
await call('/resumes', { title: 'Backend Resume v1', content: resume }, token);
await call('/job-descriptions', { title: 'Entry-level Backend Engineer', company: 'Acme Corp', content: jd }, token);

await mkdir(out, { recursive: true });
const browser = await chromium.launch();
const context = await browser.newContext({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 2 });
await context.addInitScript(([access, refresh]) => {
  localStorage.setItem('hirehub_access_token', access);
  localStorage.setItem('hirehub_refresh_token', refresh);
}, [token, tokens.refresh_token]);
const page = await context.newPage();
page.setDefaultTimeout(15000);
const settle = () => page.evaluate(() => document.fonts.ready).then(() => page.waitForTimeout(300));

try {
  await page.goto(`${app}/resumes`);
  await expect(page.getByRole('heading', { name: 'Backend Resume v1', exact: true })).toBeVisible();
  await settle();
  await page.screenshot({ path: join(out, 'resumes.png') });

  await page.goto(`${app}/analyze`);
  await page.getByRole('button', { name: 'Run analysis', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Suggestions', exact: true })).toBeVisible();
  await settle();
  // Full page keeps the sticky header from overlapping the result card.
  await page.screenshot({ path: join(out, 'analysis.png'), fullPage: true });

  await page.goto(`${app}/history`);
  await expect(page.getByRole('heading', { name: 'Past analyses.', exact: true })).toBeVisible();
  await expect(page.getByText('Match score', { exact: true })).toBeVisible();
  await settle();
  await page.screenshot({ path: join(out, 'history.png') });
  console.log('Saved docs/media/screenshots/{resumes,analysis,history}.png');
} finally {
  await browser.close();
}
