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
const HuggingFace = require('./services/huggingface');

const app = express();

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

// API routes
app.use('/api/auth', authRouter);
app.use('/api/clips', clipsRouter);
app.use('/api/labels', labelsRouter);
app.use('/api/stats', statsRouter);

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

  // Sync clips from HuggingFace if enabled
  if (USE_HUGGINGFACE) {
    try {
      await HuggingFace.syncClips();
    } catch (err) {
      console.error('[HuggingFace] Sync failed:', err.message);
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
