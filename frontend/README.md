# LinkedIn AI Agent — Frontend

Next.js 15 + React 19 + TypeScript + Tailwind + TanStack Query.

## Setup

```bash
cd frontend
cp .env.local.example .env.local   # adjust if backend isn't on :8000
pnpm install                       # or: npm install / yarn
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000).

## Pages

| Route | Purpose |
|---|---|
| `/` | Dev login (in production, replaced by Sign in with LinkedIn) |
| `/compose` | Generate a post draft and schedule it |
| `/dashboard` | List of all your scheduled / published / failed posts |
| `/settings` | Connect or disconnect LinkedIn |

## Auth

JWT from `POST /auth/dev-login` is stored in `localStorage` under `linkedin_agent_token` and sent as `Authorization: Bearer <token>` on every API request.

## Backend dependency

The FastAPI backend must be running at the URL set in `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`).
