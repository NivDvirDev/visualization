const { Router } = require('express');
const Label = require('../models/label');
const { authRequired } = require('../middleware/auth');
const HuggingFace = require('../services/huggingface');
const { USE_HUGGINGFACE } = require('../config');

const router = Router();

// GET /api/labels?labeler=human&clip_id=001
router.get('/', async (req, res, next) => {
  try {
    const labels = await Label.findAll(req.query);
    res.json(labels);
  } catch (err) {
    next(err);
  }
});

// GET /api/labels/export?format=json
router.get('/export', async (req, res, next) => {
  try {
    const data = await Label.exportJson();
    res.json(data);
  } catch (err) {
    next(err);
  }
});

// GET /api/labels/:clip_id
router.get('/:clip_id', async (req, res, next) => {
  try {
    const labels = await Label.findByClipId(req.params.clip_id);
    res.json(labels);
  } catch (err) {
    next(err);
  }
});

// PUT /api/labels/:clip_id — requires authentication
router.put('/:clip_id', authRequired, async (req, res, next) => {
  try {
    const { sync_quality, visual_audio_alignment, aesthetic_quality, motion_smoothness, notes } = req.body;
    const label = await Label.upsert(req.params.clip_id, {
      labeler: req.user.username,
      user_id: req.user.id,
      sync_quality,
      visual_audio_alignment,
      aesthetic_quality,
      motion_smoothness,
      notes,
    });
    // Push to HuggingFace in background if enabled
    if (USE_HUGGINGFACE) {
      HuggingFace.pushLabels().catch(err => console.error('[HF push error]', err.message));
    }
    res.json(label);
  } catch (err) {
    next(err);
  }
});

// DELETE /api/labels/:clip_id/:labeler — users can only delete their own labels
router.delete('/:clip_id/:labeler', authRequired, async (req, res, next) => {
  try {
    if (req.params.labeler !== req.user.username) {
      return res.status(403).json({ error: 'You can only delete your own labels' });
    }
    const deleted = await Label.delete(req.params.clip_id, req.params.labeler);
    if (!deleted) return res.status(404).json({ error: 'Label not found' });
    res.json({ success: true });
  } catch (err) {
    next(err);
  }
});

module.exports = router;
