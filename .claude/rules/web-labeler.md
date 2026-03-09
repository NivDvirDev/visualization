---
paths:
  - "04_Code/synesthesia2/synesthesia_eval/web-labeler/**"
---

# Web Labeler — Crowd-Sourcing Platform

Evaluate synesthesia visualization clips on 4 quality dimensions. Compare human vs AI labels.

- **Live:** https://synesthesia-labeler.onrender.com
- **GitHub:** https://github.com/NivDvirDev/synesthesia-labeler
- **Host:** Render.com (free tier, auto-deploy from main branch)
- **Service ID:** srv-d6houvvgi27c73fv3820

## Stack

Node.js + Express | React 18 (TypeScript) | PostgreSQL | HuggingFace Hub (`NivDvir/synesthesia-eval`)

## Architecture

- **HuggingFace** = source of truth (video clips + labels)
- **PostgreSQL** = local cache (users, sessions, label indexes)
- **Backend** = secure proxy (HF write token server-side only, append-only label writes)
- Videos stream directly from HuggingFace when `USE_HUGGINGFACE=true`

## Environment Variables (Render)

| Variable | Description |
|----------|-------------|
| DATABASE_URL | PostgreSQL internal URL (auto-linked) |
| HF_TOKEN | HuggingFace API token (write access) |
| JWT_SECRET | JWT signing secret |
| USE_HUGGINGFACE | Enable HF integration (true) |
| GOOGLE_CLIENT_ID | Google OAuth Client ID |

## Google OAuth

- **GCP Project:** sound-APR2020 (sound-272617)
- **Client ID:** 214450922102-3sbthhu9ijks0k117o03negn5ood50id.apps.googleusercontent.com
- **Status:** External, Testing mode
- **Test users:** dvirniv@gmail.com, nivdvirtadirantele@gmail.com, nivtsubery@gmail.com

## Key Files

| File | Description |
|------|-------------|
| server/src/index.js | Express entry + migration runner + startup sync |
| server/src/routes/auth.js | JWT + Google OAuth routes |
| server/src/routes/labels.js | Label CRUD (upsert, export) |
| server/src/routes/stats.js | Stats, leaderboard, personal stats |
| server/src/services/huggingface.js | HF API: video URLs, clip sync, label push |
| server/src/middleware/auth.js | JWT auth (authRequired, authOptional) |
| server/src/middleware/rateLimiter.js | Rate limiting (global, auth, label writes) |
| server/src/models/user.js | User queries (password, Google OAuth) |
| client/src/App.tsx | Root component + state management |
| client/src/components/LoginPage.tsx | Auth UI + Google Sign-In |
| client/src/components/LabelForm.tsx | 4-dimension rating form |
| client/src/components/Leaderboard.tsx | User rankings |
| client/src/components/RatingsTable.tsx | Human vs auto label comparison |

## Development

```bash
cd server && npm run dev     # Backend (port 3001)
cd client && npm start       # Frontend (port 3000, proxied)
cd server && npm test        # Jest tests (auth, labels)
```

## Deployment

- **Build:** `cd server && npm install && cd ../client && npm install --legacy-peer-deps && npm run build`
- **Start:** `cd server && node src/index.js`
- Migrations run automatically on startup
