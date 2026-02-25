# Web Labeler — Rewrite Plan

Replace the Streamlit labeler (`synesthesia_eval/tools/labeler.py`) with a full-stack web application.

- **Backend:** Node.js + Express
- **Frontend:** React 16
- **Database:** PostgreSQL

---

## 1. Directory Structure

```
synesthesia_eval/web-labeler/
├── PLAN.md                  # This file
├── docker-compose.yml       # PostgreSQL + app services
├── package.json             # Root workspace config
│
├── server/
│   ├── package.json
│   ├── src/
│   │   ├── index.js             # Express entry point
│   │   ├── config.js            # DB connection, env vars
│   │   ├── routes/
│   │   │   ├── clips.js         # /api/clips
│   │   │   ├── labels.js        # /api/labels
│   │   │   └── stats.js         # /api/stats
│   │   ├── models/
│   │   │   ├── clip.js          # Clip queries
│   │   │   └── label.js         # Label queries
│   │   ├── middleware/
│   │   │   └── errorHandler.js
│   │   └── migrate/
│   │       ├── 001_create_tables.sql
│   │       └── 002_seed_from_json.js   # JSON → PostgreSQL migration
│   └── .env.example
│
├── client/
│   ├── package.json
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── index.js             # React DOM render
│       ├── App.js               # Root component + routing
│       ├── api.js               # Fetch wrapper for /api/*
│       ├── components/
│       │   ├── ClipList.js      # Sidebar clip selector
│       │   ├── VideoPlayer.js   # HTML5 video element
│       │   ├── LabelForm.js     # Rating radios + notes
│       │   ├── ProgressBar.js   # Labeled / total
│       │   └── StatsPanel.js    # Dashboard metrics
│       └── styles/
│           └── App.css
│
└── scripts/
    └── migrate-json.js          # Standalone JSON import script
```

---

## 2. All Files to Create

### Root
| File | Purpose |
|------|---------|
| `package.json` | Workspace scripts (`npm run dev`, `npm run migrate`) |
| `docker-compose.yml` | PostgreSQL 16 container + volume |

### Server (14 files)
| File | Purpose |
|------|---------|
| `server/package.json` | express, pg, cors, dotenv, multer |
| `server/.env.example` | Template for `DATABASE_URL`, `PORT`, `CLIPS_DIR` |
| `server/src/index.js` | Express app bootstrap, static file serving for videos |
| `server/src/config.js` | pg Pool from `DATABASE_URL`, constants |
| `server/src/routes/clips.js` | CRUD for clips |
| `server/src/routes/labels.js` | CRUD for labels |
| `server/src/routes/stats.js` | Aggregated stats endpoint |
| `server/src/models/clip.js` | SQL queries for clips table |
| `server/src/models/label.js` | SQL queries for labels table |
| `server/src/middleware/errorHandler.js` | Centralized error handling |
| `server/src/migrate/001_create_tables.sql` | DDL for schema |
| `server/src/migrate/002_seed_from_json.js` | Read JSON files → INSERT |

### Client (11 files)
| File | Purpose |
|------|---------|
| `client/package.json` | react@16, react-dom@16, react-scripts |
| `client/public/index.html` | HTML shell |
| `client/src/index.js` | ReactDOM.render entry |
| `client/src/App.js` | Layout, routing, state |
| `client/src/api.js` | Fetch helpers for all endpoints |
| `client/src/components/ClipList.js` | Sidebar with filter modes |
| `client/src/components/VideoPlayer.js` | Video playback |
| `client/src/components/LabelForm.js` | 4 rating dimensions + notes |
| `client/src/components/ProgressBar.js` | Completion progress |
| `client/src/components/StatsPanel.js` | Dashboard metrics |
| `client/src/styles/App.css` | Styling |

### Scripts (1 file)
| File | Purpose |
|------|---------|
| `scripts/migrate-json.js` | CLI tool to import JSON data |

**Total: 28 files**

---

## 3. Database Schema

```sql
-- 001_create_tables.sql

CREATE TABLE clips (
    id          VARCHAR(8) PRIMARY KEY,      -- e.g. "001", "029"
    filename    TEXT NOT NULL,
    description TEXT,
    source      VARCHAR(64) DEFAULT 'youtube_playlist',
    categories  JSONB DEFAULT '{}',          -- {sync_quality, visual_style, music_genre, energy}
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE labels (
    id                      SERIAL PRIMARY KEY,
    clip_id                 VARCHAR(8) NOT NULL REFERENCES clips(id),
    labeler                 VARCHAR(64) NOT NULL,   -- "human" or "gemini-2.5-flash-lite"
    sync_quality            SMALLINT CHECK (sync_quality BETWEEN 1 AND 5),
    visual_audio_alignment  SMALLINT CHECK (visual_audio_alignment BETWEEN 1 AND 5),
    aesthetic_quality        SMALLINT CHECK (aesthetic_quality BETWEEN 1 AND 5),
    motion_smoothness       SMALLINT CHECK (motion_smoothness BETWEEN 1 AND 5),
    notes                   TEXT,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(clip_id, labeler)    -- One label set per labeler per clip
);

CREATE INDEX idx_labels_clip_id ON labels(clip_id);
CREATE INDEX idx_labels_labeler ON labels(labeler);
```

### Design Decisions

- **`labeler` column** — Distinguishes human labels from auto-labels (Gemini). Supports future multi-annotator workflows (inter-rater reliability).
- **`UNIQUE(clip_id, labeler)`** — One label set per labeler per clip. `ON CONFLICT ... DO UPDATE` for upsert on re-labeling.
- **`categories` as JSONB** — Preserves the flexible metadata structure from `metadata.json` without needing extra columns.
- **No separate `auto_labels` table** — Both human and AI labels live in `labels` with the `labeler` field as discriminator. Simplifies queries and comparisons.

---

## 4. API Endpoints

### Clips

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/clips` | List all clips. Query params: `?mode=unlabeled\|labeled\|all` (default `all`) |
| `GET` | `/api/clips/:id` | Single clip with its labels |
| `GET` | `/api/clips/:id/video` | Stream video file (proxied from `CLIPS_DIR`) |

### Labels

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/labels` | All labels. Query params: `?labeler=human`, `?clip_id=001` |
| `GET` | `/api/labels/:clip_id` | Labels for a specific clip (all labelers) |
| `PUT` | `/api/labels/:clip_id` | Create or update label (upsert). Body: `{labeler, sync_quality, visual_audio_alignment, aesthetic_quality, motion_smoothness, notes}` |
| `DELETE` | `/api/labels/:clip_id/:labeler` | Delete a label |

### Stats

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/stats` | `{total_clips, labeled_human, labeled_auto, unlabeled, avg_scores}` |

### Video Serving

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/videos/:filename` | Static file serving from `CLIPS_DIR` with Range header support for seeking |

### Request/Response Examples

**PUT /api/labels/002**
```json
// Request
{
  "labeler": "human",
  "sync_quality": 4,
  "visual_audio_alignment": 3,
  "aesthetic_quality": 5,
  "motion_smoothness": 4,
  "notes": "Great visual appeal, slight audio mismatch"
}

// Response 200
{
  "id": 1,
  "clip_id": "002",
  "labeler": "human",
  "sync_quality": 4,
  "visual_audio_alignment": 3,
  "aesthetic_quality": 5,
  "motion_smoothness": 4,
  "notes": "Great visual appeal, slight audio mismatch",
  "created_at": "2026-02-24T12:00:00Z",
  "updated_at": "2026-02-24T12:00:00Z"
}
```

**GET /api/stats**
```json
{
  "total_clips": 29,
  "labeled_human": 0,
  "labeled_auto": 1,
  "unlabeled": 28,
  "avg_scores": {
    "sync_quality": 4.0,
    "visual_audio_alignment": 4.0,
    "aesthetic_quality": 4.0,
    "motion_smoothness": 4.0
  }
}
```

---

## 5. React Components

### Component Tree

```
<App>
  ├── <StatsPanel />              # Top bar: total / labeled / remaining + progress bar
  ├── <main>
  │   ├── <ClipList />            # Left sidebar
  │   │   ├── Mode selector (Unlabeled / All / Review)
  │   │   ├── Random button
  │   │   └── Scrollable clip list with label status indicators
  │   └── <content>
  │       ├── <VideoPlayer />     # Center-left: HTML5 <video>
  │       │   └── Clip metadata expander
  │       └── <LabelForm />       # Center-right: rating form
  │           ├── 4x RadioGroup (sync, alignment, aesthetic, motion)
  │           ├── Notes textarea
  │           ├── Save button
  │           └── Skip / Next / Previous buttons
  └── <footer />
```

### Component Details

#### `App.js`
- State: `selectedClipId`, `mode` (unlabeled/all/review), `clips[]`, `stats`
- Fetches `/api/clips?mode=...` on mount and mode change
- Passes `selectedClipId` down, receives save callbacks up

#### `ClipList.js`
- Props: `clips[]`, `selectedClipId`, `onSelect(id)`, `mode`, `onModeChange`
- Renders a scrollable list of clip IDs with visual indicators:
  - Green dot = labeled (human)
  - Yellow dot = labeled (auto only)
  - Gray dot = unlabeled
- "Random" button picks a random clip from the filtered list

#### `VideoPlayer.js`
- Props: `clipId`, `filename`, `metadata`
- Renders `<video>` element with `src="/videos/{filename}"`
- Expandable metadata section showing clip info as JSON

#### `LabelForm.js`
- Props: `clipId`, `existingLabel`, `onSave(clipId, labelData)`, `onSkip()`
- Local state for each of the 4 dimensions (radio groups, values 1-5) + notes textarea
- Populates from `existingLabel` when editing
- Keyboard shortcuts: `1-5` to set current focused dimension
- Submit via Save button → calls `PUT /api/labels/:clipId`
- Displays description text for each rating level (matches Streamlit version)

#### `ProgressBar.js`
- Props: `total`, `labeled`, `remaining`
- Simple CSS progress bar + numeric counts

#### `StatsPanel.js`
- Props: `stats` object from `/api/stats`
- Renders 3 metric cards (Total, Labeled, Remaining) + progress bar
- Average score breakdown per dimension

#### `api.js`
```js
const API = '/api';

export const getClips = (mode) => fetch(`${API}/clips?mode=${mode}`).then(r => r.json());
export const getClip = (id) => fetch(`${API}/clips/${id}`).then(r => r.json());
export const getLabels = (clipId) => fetch(`${API}/labels/${clipId}`).then(r => r.json());
export const saveLabel = (clipId, data) => fetch(`${API}/labels/${clipId}`, {
  method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)
}).then(r => r.json());
export const getStats = () => fetch(`${API}/stats`).then(r => r.json());
```

---

## 6. Migration Strategy (JSON → PostgreSQL)

### Source Files

| File | Target |
|------|--------|
| `data/clips/metadata.json` | `clips` table (29 rows) |
| `data/auto_labels.json` | `labels` table with `labeler = 'gemini-2.5-flash-lite'` |
| `data/labels.json` | `labels` table with `labeler = 'human'` (currently empty) |

### Migration Script: `scripts/migrate-json.js`

```
Usage: node scripts/migrate-json.js [--data-dir ../data] [--database-url postgres://...]
```

Steps:
1. Connect to PostgreSQL
2. Run `001_create_tables.sql` (idempotent with `IF NOT EXISTS`)
3. Read `metadata.json` → INSERT each clip into `clips` table
4. Read `auto_labels.json` → INSERT each entry into `labels` with `labeler` = value of the `model` field (e.g. `"gemini-2.5-flash-lite"`)
5. Read `labels.json` → INSERT each entry into `labels` with `labeler = 'human'`
6. Print summary: `Migrated X clips, Y auto-labels, Z human labels`

### Field Mapping

**metadata.json → clips:**
```
clip.id          → clips.id
clip.filename    → clips.filename
clip.description → clips.description
clip.source      → clips.source
clip.categories  → clips.categories (as JSONB)
```

**auto_labels.json → labels:**
```
key (e.g. "002")              → labels.clip_id
entry.sync_quality            → labels.sync_quality
entry.visual_audio_alignment  → labels.visual_audio_alignment
entry.aesthetic_quality        → labels.aesthetic_quality
entry.motion_smoothness       → labels.motion_smoothness
entry.notes                   → labels.notes
entry.model                   → labels.labeler
entry.timestamp               → labels.created_at
```

**labels.json → labels:**
```
key (e.g. "001")              → labels.clip_id
entry.sync_quality            → labels.sync_quality
entry.visual_audio_alignment  → labels.visual_audio_alignment
entry.aesthetic_quality        → labels.aesthetic_quality
entry.motion_smoothness       → labels.motion_smoothness
entry.notes                   → labels.notes
"human"                       → labels.labeler
```

### Export Back to JSON

The API should support exporting labels back to JSON format for backward compatibility with the Python evaluation pipeline:

`GET /api/labels/export?format=json` → returns data in the same shape as `labels.json` / `auto_labels.json`.

---

## 7. Development Workflow

```bash
# Start PostgreSQL
docker-compose up -d postgres

# Run migration
cd server && node src/migrate/002_seed_from_json.js

# Start backend (port 3001)
cd server && npm run dev

# Start frontend (port 3000, proxied to 3001)
cd client && npm start
```

### Environment Variables (`server/.env`)
```
DATABASE_URL=postgres://synesthesia:synesthesia@localhost:5432/synesthesia_eval
PORT=3001
CLIPS_DIR=../../data/clips
```

### docker-compose.yml
```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: synesthesia_eval
      POSTGRES_USER: synesthesia
      POSTGRES_PASSWORD: synesthesia
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

---

## 8. Feature Parity Checklist

Features from the Streamlit labeler that must be preserved:

| Streamlit Feature | Web Labeler Equivalent |
|-------------------|----------------------|
| Video playback | HTML5 `<video>` with controls |
| 4 rating dimensions (1-5 radio) | Radio button groups in LabelForm |
| Notes field | Textarea in LabelForm |
| Progress bar (labeled/total) | StatsPanel + ProgressBar |
| Mode filter (Unlabeled/All/Review) | ClipList mode selector |
| Random clip button | ClipList random button |
| Save + skip buttons | LabelForm save/skip |
| Clip metadata display | Expandable JSON in VideoPlayer |
| Export labels JSON | GET /api/labels/export endpoint |

### New Features (not in Streamlit)

| Feature | Justification |
|---------|--------------|
| Side-by-side human vs. auto labels | Enabled by `labeler` column; aids inter-rater comparison |
| Keyboard shortcuts (1-5, n/p for next/prev) | Faster labeling workflow |
| Persistent state (PostgreSQL) | No more JSON file corruption risk |
| Multi-user support | `labeler` field supports multiple annotators |
