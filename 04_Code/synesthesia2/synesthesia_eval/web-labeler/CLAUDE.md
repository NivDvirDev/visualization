# Web Labeler — CLAUDE.md

Crowd-sourcing platform for rating synesthesia visualization clips on 4 quality dimensions.

**Live:** https://synesthesia-labeler.onrender.com
**Stack:** Node.js + Express | React 18 (TypeScript) | PostgreSQL | HuggingFace Hub

See `PLAN.md` for full architecture reference. See parent `../../CLAUDE.md` for broader project context.
Detailed rules also in `/Project/.claude/rules/web-labeler.md`.

---

## Quick Commands

```bash
# Development
cd server && npm run dev      # Backend on port 3001
cd client && npm start        # Frontend on port 3000 (proxied to 3001)

# Tests
cd server && npm test         # Jest (auth.test.js, labels.test.js)

# Production build
cd server && npm install && cd ../client && npm install --legacy-peer-deps && npm run build

# Start production
cd server && node src/index.js
```

## Key Directories

```
server/src/
├── routes/     auth.js, clips.js, labels.js, stats.js
├── models/     user.js, clip.js, label.js
├── middleware/  auth.js, rateLimiter.js, errorHandler.js
├── services/   huggingface.js
└── migrate/    001-004 SQL migrations (run on startup)

client/src/
├── App.tsx, api.ts, types.ts
└── components/  LoginPage, ClipList, VideoPlayer, LabelForm,
                 RatingsTable, Leaderboard, ProgressBar, StatsPanel
```

## Features

- JWT + Google OAuth authentication
- 4-dimension rating (sync, alignment, aesthetics, motion)
- Human vs AI label comparison (RatingsTable)
- Leaderboard, badges, streak tracking
- HuggingFace video streaming (no local storage in prod)
- Rate limiting (global, auth, label writes)
- Auto-migrations on startup

## Environment

Requires: `DATABASE_URL`, `JWT_SECRET`, `HF_TOKEN`
Optional: `USE_HUGGINGFACE`, `GOOGLE_CLIENT_ID`, `CLIPS_DIR`, `PORT`

---

*Last updated: 2026-03-09*
