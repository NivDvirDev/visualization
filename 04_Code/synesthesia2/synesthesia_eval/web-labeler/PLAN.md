# Web Labeler — Architecture Reference

Crowd-sourcing platform for evaluating synesthesia visualization clips.
Rate clips on 4 quality dimensions, compare human vs. AI labels.

- **Live:** https://synesthesia-labeler.onrender.com
- **Backend:** Node.js + Express
- **Frontend:** React 18 (TypeScript)
- **Database:** PostgreSQL (Render.com free tier)
- **Dataset:** HuggingFace Hub (`NivDvir/synesthesia-eval`)
- **Auth:** JWT + bcrypt + Google OAuth

---

## 1. Directory Structure

```
synesthesia_eval/web-labeler/
├── PLAN.md
├── README.md
├── package.json                     # Root workspace config
│
├── server/
│   ├── package.json
│   ├── .env.example
│   └── src/
│       ├── index.js                 # Express entry point + migration runner
│       ├── config.js                # DB pool, env vars
│       ├── routes/
│       │   ├── auth.js              # Register, login, Google OAuth
│       │   ├── clips.js             # GET /api/clips
│       │   ├── labels.js            # PUT/DELETE /api/labels
│       │   └── stats.js             # GET /api/stats
│       ├── models/
│       │   ├── clip.js              # Clip queries
│       │   ├── label.js             # Label queries (upsert, export, stats)
│       │   └── user.js              # User queries (password, Google OAuth)
│       ├── middleware/
│       │   ├── auth.js              # JWT verification (authRequired, authOptional)
│       │   └── errorHandler.js
│       ├── services/
│       │   └── huggingface.js       # HF API: video URLs, clip sync, label push
│       └── migrate/
│           ├── 001_create_tables.sql
│           ├── 002_seed_from_json.js
│           ├── 003_add_users.sql
│           └── 004_add_google_oauth.sql
│
├── client/
│   ├── package.json
│   ├── tsconfig.json
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── index.tsx
│       ├── App.tsx                   # Root component + state management
│       ├── api.ts                    # Fetch wrapper with JWT auth headers
│       ├── types.ts                  # TypeScript interfaces
│       ├── components/
│       │   ├── LoginPage.tsx         # Login/Register + Google Sign-In
│       │   ├── ClipList.tsx          # Sidebar clip navigator
│       │   ├── VideoPlayer.tsx       # HTML5 video player
│       │   ├── LabelForm.tsx         # 4-dimension rating form
│       │   ├── RatingsTable.tsx      # Human vs. auto label comparison
│       │   ├── ProgressBar.tsx       # Completion progress
│       │   └── StatsPanel.tsx        # Dashboard stats
│       └── styles/
│           └── App.css               # Dark theme
│
└── scripts/
    └── migrate-json.js               # Standalone JSON → DB import
```

---

## 2. Architecture

### Data Flow

```
HuggingFace Hub (source of truth)
    │
    ▼
Backend (secure proxy)
    ├── Streams video from HF (no local storage needed)
    ├── Syncs clip metadata → PostgreSQL
    └── Pushes community_labels.json → HF
    │
    ▼
PostgreSQL (local cache)
    ├── users (auth, profiles)
    ├── clips (synced from HF)
    └── labels (user ratings)
    │
    ▼
React Frontend
    ├── Authenticated via JWT
    └── Fetches clips/labels from backend API
```

### Key Principles

- **HuggingFace = source of truth** for video files and dataset metadata
- **Backend = secure proxy** — HF write token stays server-side, append-only label writes
- **PostgreSQL = cache** — stores users, sessions, and label indexes locally
- **No local video storage** — clips stream directly from HuggingFace when `USE_HUGGINGFACE=true`

---

## 3. Database Schema

```sql
-- 001_create_tables.sql
CREATE TABLE clips (
    id          VARCHAR(8) PRIMARY KEY,
    filename    TEXT NOT NULL,
    description TEXT,
    source      VARCHAR(64) DEFAULT 'youtube_playlist',
    categories  JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE labels (
    id                      SERIAL PRIMARY KEY,
    clip_id                 VARCHAR(8) NOT NULL REFERENCES clips(id),
    labeler                 VARCHAR(64) NOT NULL,
    user_id                 INTEGER REFERENCES users(id),
    sync_quality            SMALLINT CHECK (sync_quality BETWEEN 1 AND 5),
    visual_audio_alignment  SMALLINT CHECK (visual_audio_alignment BETWEEN 1 AND 5),
    aesthetic_quality       SMALLINT CHECK (aesthetic_quality BETWEEN 1 AND 5),
    motion_smoothness       SMALLINT CHECK (motion_smoothness BETWEEN 1 AND 5),
    notes                   TEXT,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

-- Partial unique indexes (user vs auto labels)
CREATE UNIQUE INDEX idx_labels_clip_user ON labels(clip_id, user_id) WHERE user_id IS NOT NULL;
CREATE UNIQUE INDEX idx_labels_clip_labeler ON labels(clip_id, labeler) WHERE user_id IS NULL;

-- 003_add_users.sql
CREATE TABLE users (
    id             SERIAL PRIMARY KEY,
    username       VARCHAR(64) UNIQUE NOT NULL,
    email          VARCHAR(255) UNIQUE NOT NULL,
    password_hash  TEXT,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

-- 004_add_google_oauth.sql
ALTER TABLE users ADD COLUMN google_id VARCHAR(255) UNIQUE;
```

---

## 4. API Endpoints

### Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/register` | No | Create account (username, email, password) |
| POST | `/api/auth/login` | No | Email/password → JWT (7-day expiry) |
| POST | `/api/auth/google` | No | Google ID token → JWT |
| GET | `/api/auth/me` | Required | Current user profile |

### Clips

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/clips?mode=unlabeled\|all\|labeled` | No | List clips |
| GET | `/api/clips/:id` | No | Single clip with labels |

### Labels

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/labels` | No | All labels (filterable by labeler, clip_id) |
| GET | `/api/labels/:clip_id` | No | Labels for a clip |
| PUT | `/api/labels/:clip_id` | Required | Create/update label (upsert) |
| DELETE | `/api/labels/:clip_id/:labeler` | Required | Delete a label |

### Other

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/stats` | No | Totals, averages, completion counts |
| GET | `/api/config` | No | App config flags (useHuggingFace, googleClientId) |
| GET | `/api/video-url/:filename` | No | Resolve video URL (HF or local) |

---

## 5. Authentication Flow

1. **Register:** POST `/api/auth/register` → bcrypt hash → store user → return JWT
2. **Login:** POST `/api/auth/login` → verify password → return JWT
3. **Google OAuth:** Frontend gets ID token via `@react-oauth/google` → POST to backend → verify with `google-auth-library` → create/link user → return JWT
4. **Protected routes:** `Authorization: Bearer <token>` header → `authRequired` middleware verifies JWT

---

## 6. Rating Dimensions

Each clip is rated 1–5 on four dimensions:

| Dimension | 1 | 3 | 5 |
|-----------|---|---|---|
| Sync Quality | No sync | Moderate | Perfect sync |
| Visual-Audio Alignment | Mismatched | Somewhat matched | Perfect match |
| Aesthetic Quality | Unappealing | Average | Stunning |
| Motion Smoothness | Very choppy | Acceptable | Perfectly fluid |

---

## 7. HuggingFace Integration

**Dataset:** `NivDvir/synesthesia-eval` (29 MP4 clips)

When `USE_HUGGINGFACE=true`:
- `getVideoUrl(filename)` — resolves HF CDN URL for streaming
- `listClipFiles()` — fetches file list from dataset
- `syncClips()` — syncs clip metadata to PostgreSQL
- `pushLabels()` — exports `community_labels.json` back to dataset

---

## 8. Deployment (Render.com)

- **Build:** `cd server && npm install && cd ../client && npm install --legacy-peer-deps && npm run build`
- **Start:** `cd server && node src/index.js`
- Server serves the built React app as static files from `../client/build/`
- Migrations run automatically on startup

### Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (auto-linked on Render) |
| `JWT_SECRET` | JWT signing secret |
| `HF_TOKEN` | HuggingFace API token (write access) |
| `HF_DATASET` | Dataset ID (default: `NivDvir/synesthesia-eval`) |
| `USE_HUGGINGFACE` | Enable HF integration (`true` / `false`) |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID |
| `PORT` | Server port (default: 3001) |

---

## 9. Local Development

```bash
# Install dependencies
cd server && npm install
cd ../client && npm install

# Configure environment
cp server/.env.example server/.env
# Edit server/.env with your credentials

# Need a PostgreSQL instance (local or cloud)
# Update DATABASE_URL in server/.env

# Start backend (port 3001)
cd server && npm run dev

# Start frontend (port 3000, proxied to 3001)
cd client && npm start
```
