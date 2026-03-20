const { Router } = require('express');
const Clip = require('../models/clip');
const { authRequired } = require('../middleware/auth');
const { USE_HUGGINGFACE } = require('../config');
const HuggingFace = require('../services/huggingface');

function resolveVideoUrl(filename) {
  if (USE_HUGGINGFACE) return HuggingFace.getVideoUrl(filename);
  return `/videos/${encodeURIComponent(filename)}`;
}

const router = Router();

// Extract YouTube video ID from any standard YouTube URL
function extractYouTubeId(url) {
  if (!url) return null;
  const patterns = [
    /[?&]v=([A-Za-z0-9_-]{11})/,
    /youtu\.be\/([A-Za-z0-9_-]{11})/,
    /embed\/([A-Za-z0-9_-]{11})/,
  ];
  for (const re of patterns) {
    const m = url.match(re);
    if (m) return m[1];
  }
  return null;
}

// GET /api/clips?mode=all|unlabeled|labeled
router.get('/', async (req, res, next) => {
  try {
    const mode = req.query.mode || 'all';
    const clips = await Clip.findAll(mode);
    res.json(clips.map(c => ({ ...c, video_url: resolveVideoUrl(c.filename) })));
  } catch (err) {
    next(err);
  }
});

// GET /api/clips/rankings — public clip rankings by average score
router.get('/rankings', async (req, res, next) => {
  try {
    const clips = await Clip.rankings();
    res.json(clips);
  } catch (err) {
    next(err);
  }
});

// GET /api/clips/:id
router.get('/:id', async (req, res, next) => {
  try {
    const clip = await Clip.findById(req.params.id);
    if (!clip) return res.status(404).json({ error: 'Clip not found' });
    const creator = await Clip.getCreatorInfo(req.params.id);
    res.json({ ...clip, video_url: resolveVideoUrl(clip.filename), ...(creator || {}) });
  } catch (err) {
    next(err);
  }
});

// POST /api/clips/:id/claim — claim this clip as your creation
router.post('/:id/claim', authRequired, async (req, res, next) => {
  try {
    const { youtube_url } = req.body;
    if (!youtube_url) {
      return res.status(400).json({ error: 'youtube_url is required' });
    }

    const clip = await Clip.findById(req.params.id);
    if (!clip) return res.status(404).json({ error: 'Clip not found' });

    // Verify the YouTube video ID matches
    const submittedId = extractYouTubeId(youtube_url);
    if (!submittedId || submittedId !== clip.youtube_video_id) {
      return res.status(400).json({ error: "URL doesn't match this clip's video" });
    }

    // Check if already claimed by a different user
    const creator = await Clip.getCreatorInfo(req.params.id);
    if (creator && creator.claimed && creator.claimed_by_username !== req.user.username) {
      return res.status(409).json({ error: 'This clip has already been claimed by another user' });
    }

    const updated = await Clip.claim(req.params.id, req.user.id);
    const updatedCreator = await Clip.getCreatorInfo(req.params.id);
    res.json({ ...updated, ...(updatedCreator || {}) });
  } catch (err) {
    next(err);
  }
});

// DELETE /api/clips/:id/claim — remove your claim
router.delete('/:id/claim', authRequired, async (req, res, next) => {
  try {
    const creator = await Clip.getCreatorInfo(req.params.id);
    if (!creator) return res.status(404).json({ error: 'Clip not found' });
    if (!creator.claimed) return res.status(400).json({ error: 'Clip is not claimed' });
    if (creator.claimed_by_username !== req.user.username) {
      return res.status(403).json({ error: 'You are not the claimer of this clip' });
    }

    await Clip.unclaim(req.params.id, req.user.id);
    res.json({ success: true });
  } catch (err) {
    next(err);
  }
});

// PUT /api/clips/:id/creator — update display credit/link/visibility
router.put('/:id/creator', authRequired, async (req, res, next) => {
  try {
    const creator = await Clip.getCreatorInfo(req.params.id);
    if (!creator) return res.status(404).json({ error: 'Clip not found' });
    if (!creator.claimed) return res.status(400).json({ error: 'Clip is not claimed' });
    if (creator.claimed_by_username !== req.user.username) {
      return res.status(403).json({ error: 'You are not the claimer of this clip' });
    }

    const { display_credit, display_link, credit_visible } = req.body;
    const updated = await Clip.updateCreatorDisplay(req.params.id, req.user.id, {
      display_credit,
      display_link,
      credit_visible,
    });
    const updatedCreator = await Clip.getCreatorInfo(req.params.id);
    res.json({ ...updated, ...(updatedCreator || {}) });
  } catch (err) {
    next(err);
  }
});

module.exports = router;
