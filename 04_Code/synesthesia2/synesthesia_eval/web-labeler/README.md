# Synesthesia Web Labeler

Crowd-sourcing platform for evaluating synesthesia audio visualization clips. Users rate clips on 4 quality dimensions (sync, alignment, aesthetics, motion) and results are compared against AI auto-labels.

**Live:** https://synesthesia-labeler.onrender.com

## Tech Stack

- **Frontend:** React 18 (TypeScript)
- **Backend:** Node.js + Express
- **Database:** PostgreSQL (Render.com free tier)
- **Dataset:** HuggingFace Hub ([NivDvir/synesthesia-eval](https://huggingface.co/datasets/NivDvir/synesthesia-eval))
- **Auth:** JWT + bcrypt + Google OAuth

## Architecture

```
HuggingFace Hub ──► Backend (secure proxy) ──► PostgreSQL (cache)
                         │                          │
                         └──── React Frontend ◄─────┘
```

- **HuggingFace** is the source of truth for video clips and dataset metadata
- **Backend** acts as a secure proxy — the HF write token stays server-side, label writes are append-only
- **PostgreSQL** caches users, clip metadata, and labels locally
- Videos stream directly from HuggingFace (no local storage needed in production)

## Local Development

```bash
# Install dependencies
cd server && npm install
cd ../client && npm install

# Configure environment
cp server/.env.example server/.env
# Edit server/.env with your database URL and secrets

# Start backend (port 3001)
cd server && npm run dev

# Start frontend (port 3000, proxied to 3001)
cd client && npm start
```

You need a PostgreSQL instance running locally or remotely. Update `DATABASE_URL` in `server/.env` accordingly. Migrations run automatically on server startup.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `JWT_SECRET` | Yes | Secret for signing JWT tokens |
| `HF_TOKEN` | Yes | HuggingFace API token (write access) |
| `USE_HUGGINGFACE` | No | Enable HF integration (`true`/`false`, default `false`) |
| `GOOGLE_CLIENT_ID` | No | Google OAuth Client ID for sign-in |
| `HF_DATASET` | No | HuggingFace dataset ID (default: `NivDvir/synesthesia-eval`) |
| `PORT` | No | Server port (default: `3001`) |
| `CLIPS_DIR` | No | Local clips directory for development |

## Deployment

Deployed on Render.com with auto-deploy from the `main` branch.

- **Build:** `cd server && npm install && cd ../client && npm install --legacy-peer-deps && npm run build`
- **Start:** `cd server && node src/index.js`

The server serves the built React app as static files and runs database migrations on startup.

## Rating Dimensions

Each clip is rated 1–5 on:

| Dimension | Description |
|-----------|-------------|
| Sync Quality | How well visuals sync with beat/rhythm |
| Visual-Audio Alignment | How well visuals match audio characteristics |
| Aesthetic Quality | Overall visual appeal |
| Motion Smoothness | Fluidity of motion and animation |
