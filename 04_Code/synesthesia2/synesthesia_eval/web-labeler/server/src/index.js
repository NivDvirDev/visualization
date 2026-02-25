const express = require('express');
const cors = require('cors');
const path = require('path');
const { PORT, CLIPS_DIR } = require('./config');
const errorHandler = require('./middleware/errorHandler');
const clipsRouter = require('./routes/clips');
const labelsRouter = require('./routes/labels');
const statsRouter = require('./routes/stats');

const app = express();

app.use(cors());
app.use(express.json());

// Serve video files with Range header support
app.use('/videos', express.static(CLIPS_DIR, {
  acceptRanges: true,
  setHeaders(res, filePath) {
    const ext = path.extname(filePath).toLowerCase();
    if (ext === '.mp4') res.setHeader('Content-Type', 'video/mp4');
    else if (ext === '.webm') res.setHeader('Content-Type', 'video/webm');
  },
}));

// API routes
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

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
  console.log(`Serving clips from: ${CLIPS_DIR}`);
});
