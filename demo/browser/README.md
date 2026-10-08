# Browser walkthrough

Start the backend and PostgreSQL with `docker compose up --build -d`, using an
existing root `.env` configured from `.env.example`. Wait for
`http://localhost:8000/api/v1/health` to report `db: connected`. In another terminal,
run `cd frontend && npm ci && npm run dev -- --port 5173 --strictPort`.
The frontend must use port 5173 for backend CORS.

Install the isolated recorder dependencies once:

```bash
cd demo/browser
npm ci
npx playwright install chromium
cd ../..
make demo-browser
```

Requires Node.js and ffmpeg (with libx264). The target assumes both the backend
and frontend are already running. It uses the real UI and fictional fixtures,
creates a fresh Jordan Lee account on every run, and generates a throwaway
password without printing it. Accounts and saved records remain in the local
database. Record twice to check repeatability; rapid retries may hit the backend's
10-per-minute auth limit.

The approximately one-minute recording uses a 1280×800 desktop viewport and
shows registration, login, saved resume and job description, category-weighted
analysis, gaps, suggestions, and saved history. TF-IDF cosine contributes 0% to
the score, even though the current UI labels it “Semantic similarity.”

Output: `docs/media/hirehub-browser-demo.webm`, H.264 MP4, and a looping 960px GIF
(12 fps, reduced if needed to keep it below 8 MiB). Only the GIF and MP4 are
committed. The recorder rejects failed API responses, runtime errors, and error
alerts/toasts; failures leave a temporary recording for inspection and never
print Playwright call logs containing credentials.

Known frontend limitations: no automatic token refresh, lists limited to the
first 20 records, mobile Analyze overflow, and client-only logout. Fresh accounts,
one short session, and the desktop viewport avoid these in the demo.
