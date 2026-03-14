const express = require('express');
const cors = require('cors');
const path = require('path');
const { pool, PORT, CLIPS_DIR, USE_HUGGINGFACE, GOOGLE_CLIENT_ID } = require('./config');
const errorHandler = require('./middleware/errorHandler');
const { globalLimiter, authLimiter, labelWriteLimiter } = require('./middleware/rateLimiter');
const clipsRouter = require('./routes/clips');
const labelsRouter = require('./routes/labels');
const statsRouter = require('./routes/stats');
const authRouter = require('./routes/auth');
const usersRouter = require('./routes/users');
const HuggingFace = require('./services/huggingface');

const app = express();

app.set('trust proxy', 1);
app.use(cors());
app.use(express.json());

// Rate limiting
app.use('/api/', globalLimiter);
app.use('/api/auth', authLimiter);
app.use('/api/labels', labelWriteLimiter);

// Serve video files with Range header support (local mode)
if (!USE_HUGGINGFACE) {
  app.use('/videos', express.static(CLIPS_DIR, {
    acceptRanges: true,
    setHeaders(res, filePath) {
      const ext = path.extname(filePath).toLowerCase();
      if (ext === '.mp4') res.setHeader('Content-Type', 'video/mp4');
      else if (ext === '.webm') res.setHeader('Content-Type', 'video/webm');
    },
  }));
}

// API to get video URL (supports both local and HuggingFace)
app.get('/api/video-url/:filename', (req, res) => {
  if (USE_HUGGINGFACE) {
    res.json({ url: HuggingFace.getVideoUrl(req.params.filename) });
  } else {
    res.json({ url: `/videos/${encodeURIComponent(req.params.filename)}` });
  }
});

// API to get config flags for frontend
app.get('/api/config', (_req, res) => {
  res.json({
    useHuggingFace: USE_HUGGINGFACE,
    googleClientId: GOOGLE_CLIENT_ID || null,
  });
});

// Admin: force re-sync auto-labels from HuggingFace (protected by HF_TOKEN)
app.post('/api/admin/sync', async (req, res) => {
  const { HF_TOKEN } = require('./config');
  const token = req.headers.authorization?.replace('Bearer ', '');
  if (!token || token !== HF_TOKEN) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  try {
    const clips = await HuggingFace.syncClips();
    const labels = await HuggingFace.fetchAutoLabels();
    res.json({ clips, labels });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// API routes
app.use('/api/auth', authRouter);
app.use('/api/clips', clipsRouter);
app.use('/api/labels', labelsRouter);
app.use('/api/stats', statsRouter);
app.use('/api/users', usersRouter);

// Serve React build in production
const clientBuild = path.join(__dirname, '../../client/build');
app.use(express.static(clientBuild));
app.get('*', (req, res, next) => {
  if (req.path.startsWith('/api/') || req.path.startsWith('/videos/')) return next();
  res.sendFile(path.join(clientBuild, 'index.html'));
});

app.use(errorHandler);

async function startServer() {
  // Run all migrations in order
  const fs = require('fs');

  // Migration 001: Create base tables
  try {
    const sql = fs.readFileSync(path.join(__dirname, 'migrate/001_create_tables.sql'), 'utf-8');
    await pool.query(sql);
    console.log('[DB] Migration 001_create_tables applied');
  } catch (err) {
    if (!err.message.includes('already exists')) {
      console.error('[DB] Migration warning:', err.message);
    }
  }

  // Run migration for users table
  try {

    const migrationSql = fs.readFileSync(path.join(__dirname, 'migrate/003_add_users.sql'), 'utf-8');
    await pool.query(migrationSql);
    console.log('[DB] Migration 003_add_users applied');
  } catch (err) {
    if (!err.message.includes('already exists')) {
      console.error('[DB] Migration warning:', err.message);
    }
  }

  // Run migration for Google OAuth
  try {

    const migrationSql = fs.readFileSync(path.join(__dirname, 'migrate/004_add_google_oauth.sql'), 'utf-8');
    await pool.query(migrationSql);
    console.log('[DB] Migration 004_add_google_oauth applied');
  } catch (err) {
    if (!err.message.includes('already exists')) {
      console.error('[DB] Migration warning:', err.message);
    }
  }

  // Migration 005: Two-axis rating framework
  try {
    const migrationSql = fs.readFileSync(path.join(__dirname, 'migrate/005_two_axis_ratings.sql'), 'utf-8');
    await pool.query(migrationSql);
    console.log('[DB] Migration 005_two_axis_ratings applied');
  } catch (err) {
    if (!err.message.includes('already exists') && !err.message.includes('does not exist')) {
      console.error('[DB] Migration warning:', err.message);
    }
  }

  // Migration 006: Add youtube_video_id column
  try {
    const migrationSql = fs.readFileSync(path.join(__dirname, 'migrate/006_add_youtube_video_id.sql'), 'utf-8');
    await pool.query(migrationSql);
    console.log('[DB] Migration 006_add_youtube_video_id applied');
  } catch (err) {
    if (!err.message.includes('already exists')) {
      console.error('[DB] Migration warning:', err.message);
    }
  }

  // Populate youtube_video_id from local metadata.json (local mode)
  if (!USE_HUGGINGFACE) {
    try {
      const metadataPath = path.join(CLIPS_DIR, 'metadata.json');
      if (fs.existsSync(metadataPath)) {
        const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf-8'));
        const clips = metadata.clips || [];
        let updated = 0;
        for (const clip of clips) {
          const videoId = clip.youtube_source?.video_id;
          if (!videoId) continue;
          const { rowCount } = await pool.query(
            `UPDATE clips SET youtube_video_id = $1 WHERE id = $2 AND (youtube_video_id IS NULL OR youtube_video_id != $1)`,
            [videoId, clip.id]
          );
          if (rowCount > 0) updated++;
        }
        if (updated > 0) console.log(`[DB] Updated youtube_video_id for ${updated} clips`);
      }
    } catch (err) {
      console.error('[DB] youtube_video_id populate warning:', err.message);
    }
  }

  // Sync clips and auto-labels from HuggingFace if enabled
  // Only sync what's missing — skip if already populated to avoid slow cold starts
  if (USE_HUGGINGFACE) {
    try {
      const { rows: [{ clips, auto_labels }] } = await pool.query(
        `SELECT
           (SELECT COUNT(*)::int FROM clips) AS clips,
           (SELECT COUNT(*)::int FROM labels WHERE user_id IS NULL) AS auto_labels`
      );
      if (clips === 0) {
        console.log('[HuggingFace] No clips — running initial sync...');
        await HuggingFace.syncClips();
      }
      if (auto_labels === 0) {
        console.log('[HuggingFace] No auto-labels — fetching from HuggingFace...');
        await HuggingFace.fetchAutoLabels();
      }
      if (clips > 0 && auto_labels > 0) {
        console.log(`[HuggingFace] DB ready (${clips} clips, ${auto_labels} auto-labels) — skipping sync`);
      }
    } catch (err) {
      console.error('[HuggingFace] Sync check failed:', err.message);
    }
  }

  app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
    console.log(`Serving clips from: ${USE_HUGGINGFACE ? 'HuggingFace' : CLIPS_DIR}`);
  });
}

module.exports = { app, startServer };

if (require.main === module) {
  startServer();
}
