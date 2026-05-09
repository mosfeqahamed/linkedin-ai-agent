# LinkedIn AI Agent

AI-powered LinkedIn post scheduler. User picks a date/time and a topic; DeepSeek generates the post; APScheduler auto-publishes via the LinkedIn API at the scheduled time.

## Screenshots

### Compose

Enter a topic (and optional context), then generate a draft with DeepSeek before scheduling.

![Compose page](image/image1.png)

### Dashboard

Track every post — published, scheduled, failed, or cancelled — with its status, scheduled time, and (once live) the LinkedIn share URN.

![Dashboard with a published post](image/image2.png)

### Settings

Connect or disconnect your LinkedIn account. Once connected, scheduled posts publish automatically.

![Settings page after LinkedIn connected](image/image3.png)

## Stack

- **FastAPI** + **Uvicorn** — async backend
- **MongoDB** + **Motor** + **Beanie** — database & ODM
- **DeepSeek** (`deepseek-chat`) via OpenAI SDK — text generation
- **APScheduler** with `MongoDBJobStore` — persistent scheduling
- **LinkedIn UGC Posts API** — auto-posting (requires `w_member_social` scope)
- **Fernet** — encrypts OAuth tokens at rest

## Quick start

### 1. Start MongoDB

```bash
docker compose up -d
```

### 2. Set up environment

```bash
cp .env.example .env
# Generate a Fernet key:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Paste it into FERNET_KEY in .env
# Add your DEEPSEEK_API_KEY
# Set JWT_SECRET to any long random string
```

### 3. Install dependencies

```bash
# With uv (recommended)
uv sync

# Or with pip
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

### 4. Run the server

```bash
uvicorn app.main:app --reload
```

Open [http://localhost:8000/docs](http://localhost:8000/docs) for the Swagger UI.

## Test the generation flow (no LinkedIn needed)

```bash
# 1. Get a dev session token
curl -X POST http://localhost:8000/auth/dev-login \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "name": "You"}'
# → {"access_token": "...", "token_type": "bearer"}

# 2. Generate a post
curl -X POST http://localhost:8000/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"topic": "Lessons from a year of remote work", "description": "Focus on async communication"}'

# 3. Schedule it
curl -X POST http://localhost:8000/posts \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "...",
    "generated_text": "...",
    "scheduled_at": "2026-05-10T09:00:00Z"
  }'
```

## LinkedIn setup (for auto-posting)

1. Create an app at [developer.linkedin.com](https://developer.linkedin.com).
2. Add the **Sign In with LinkedIn using OpenID Connect** product.
3. Apply for the **Share on LinkedIn** product (gives you `w_member_social`).
   This requires LinkedIn review — can take days to weeks.
4. Set the redirect URL to `http://localhost:8000/auth/linkedin/callback` (and your prod URL later).
5. Copy the Client ID and Client Secret into `.env`.

Once approved, hit `GET /auth/linkedin/login` (with a session token) to start the OAuth flow.

## Project layout

```
linkedin-ai-agent/
├── app/                          ← FastAPI backend (Python)
│   ├── main.py                   FastAPI entry + lifespan
│   ├── config.py                 Settings (env-driven)
│   ├── db.py                     PyMongo AsyncMongoClient + Beanie init
│   ├── security.py               Fernet + JWT
│   ├── deps.py                   FastAPI dependencies (current_user)
│   ├── schemas.py                Pydantic request/response models
│   ├── models/
│   │   ├── user.py
│   │   └── post.py
│   ├── routers/
│   │   ├── auth.py               dev-login + LinkedIn OAuth
│   │   ├── generate.py           POST /generate
│   │   └── posts.py              CRUD + schedule + regenerate
│   └── services/
│       ├── deepseek.py           Post generation
│       ├── linkedin.py           OAuth + UGC Posts API
│       └── scheduler.py          APScheduler + publish job + token refresh cron
├── frontend/                     ← Next.js 15 frontend (TypeScript)
│   ├── src/
│   │   ├── app/                  App Router pages (login, compose, dashboard, settings)
│   │   ├── components/           Nav, PostCard, StatusBadge, Providers
│   │   └── lib/                  API client, auth, types, formatters
│   └── package.json
├── docker-compose.yml            Local Mongo
├── pyproject.toml
└── .env.example
```

## Running both backend and frontend

In two terminals:

```bash
# Terminal 1: backend
uv run uvicorn app.main:app --reload    # http://localhost:8000

# Terminal 2: frontend
cd frontend
cp .env.local.example .env.local
pnpm install   # or npm install
pnpm dev                                  # http://localhost:3000
```

Then open [http://localhost:3000](http://localhost:3000), log in with any email, compose a post, schedule it.

## What's not built yet

- Image generation (deferred — easy to add as a `/generate-image` endpoint)
- Sign in with LinkedIn as the only auth (currently dev-login is the entry point; LinkedIn is connected separately on /settings)
- Production deployment configs (Dockerfile for backend, Vercel for frontend)
- Tests (pytest for backend, Playwright for frontend)
