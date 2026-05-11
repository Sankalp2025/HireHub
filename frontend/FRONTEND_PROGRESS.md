# HireHub Frontend Progress

This file tracks what has been built on the `frontend` branch, what commands help run the project, and what we plan to build next.

## Project Goal

Build the full user-facing frontend for HireHub using React + TypeScript + Vite.

The frontend will:
- let users register and log in
- save resumes
- save job descriptions
- run resume-to-job-description analyses
- display analysis results and history

The backend already exists in FastAPI. The frontend talks to it through HTTP requests.

## Frontend Stack

- React
- TypeScript
- Vite
- React Router
- Axios
- CSS with custom variables and component-level styling

## Design Direction

- clean and user-friendly
- neutral base colors
- restrained red accent
- olive green as a secondary accent
- no emoji-based styling
- functional before overly decorative

## Progress Log

### Step 1: Frontend branch created

Completed:
- created a dedicated git branch named `frontend`
- kept frontend work isolated from backend development

Why this matters:
- prevents accidental conflicts with backend work
- gives you a clean place to commit UI progress

### Step 2: React app scaffolded

Completed:
- created a new Vite React TypeScript app inside `frontend/`
- installed core dependencies

Important files created by setup:
- `frontend/package.json`
- `frontend/src/main.tsx`
- `frontend/src/App.tsx`
- `frontend/src/index.css`

Why this matters:
- this is the foundation of the entire frontend

### Step 3: Initial app shell and routing

Completed:
- replaced the Vite starter screen
- created a HireHub landing page
- added routes for:
  - `/`
  - `/login`
  - `/register`
  - `/dashboard`
- created a clean visual system with neutral colors and red/olive accents

Key files:
- `frontend/src/App.tsx`
- `frontend/src/App.css`
- `frontend/src/index.css`

Why this matters:
- this establishes the layout, navigation, and design language

### Step 4: Register page connected to backend

Completed:
- created a real register form
- added frontend validation
- connected the form to `POST /auth/register`
- added loading, success, and error states
- added reusable API helper logic

Key files:
- `frontend/src/pages/RegisterPage.tsx`
- `frontend/src/lib/api.ts`

What this taught:
- controlled inputs
- React state for forms
- submit handlers
- API calls with Axios
- showing feedback to the user

### Step 5: Login page and token storage

Completed:
- created a real login form
- connected it to `POST /auth/login`
- stored `access_token` and `refresh_token` in browser local storage
- redirected the user to the dashboard after successful login

Key files:
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/lib/auth.ts`

Why this matters:
- this is the start of real session handling in the frontend

## Current File Structure

```text
frontend/
  .env.example
  FRONTEND_PROGRESS.md
  package.json
  src/
    lib/
      api.ts
      auth.ts
    pages/
      LoginPage.tsx
      RegisterPage.tsx
    App.tsx
    App.css
    index.css
    main.tsx
```

## Commands You’ll Use Often

### Start the frontend

Run this from the `frontend/` folder:

```bash
npm run dev
```

What it does:
- starts the Vite development server
- gives you a local browser URL, usually `http://localhost:5173`

### Build the frontend

```bash
npm run build
```

What it does:
- checks TypeScript
- creates a production build
- helps catch compile errors early

### Preview the production build

```bash
npm run preview
```

### Install dependencies

```bash
npm install
```

Use this if:
- you clone the repo fresh
- `node_modules` does not exist

### Run the backend

From the repo root:

```bash
docker compose up --build -d
```

Why:
- the frontend needs the backend running to register, log in, and later save data

### Check backend health

```bash
curl http://localhost:8000/api/v1/health
```

### Stop backend containers

```bash
docker compose down
```

## Git Commands You’ll Use Often

From the repo root:

```bash
git status
git add frontend
git commit -m "Your message here"
git push
```

From inside the `frontend/` folder:

```bash
git status
git add .
git commit -m "Your message here"
git push
```

## Environment Variables

Frontend environment file:

```bash
frontend/.env.example
```

Current variable:

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

If needed later, copy it like this:

```bash
cp .env.example .env
```

Run that from inside the `frontend/` folder.

## What To Build Next

Planned next steps:
- show the logged-in state on the dashboard
- add `GET /auth/me` support
- create shared auth state across the app
- protect dashboard routes
- build resume CRUD pages
- build job description CRUD pages
- build analysis creation and results pages

## Notes and Lessons

- Frontend and backend are separate layers.
- As long as you work inside `frontend/`, you are not changing backend logic.
- The frontend can still break if the backend API contract changes, so always keep request and response shapes in sync.
- Small commits are good. Commit after meaningful checkpoints.
