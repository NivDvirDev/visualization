const { Router } = require('express');
const Label = require('../models/label');

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

// PUT /api/labels/:clip_id
router.put('/:clip_id', async (req, res, next) => {
  try {
    const { labeler, sync_quality, visual_audio_alignment, aesthetic_quality, motion_smoothness, notes } = req.body;
    if (!labeler) {
      return res.status(400).json({ error: 'labeler is required' });
    }
    const label = await Label.upsert(req.params.clip_id, {
      labeler,
      sync_quality,
      visual_audio_alignment,
      aesthetic_quality,
      motion_smoothness,
      notes,
    });
    res.json(label);
  } catch (err) {
    next(err);
  }
});

// DELETE /api/labels/:clip_id/:labeler
router.delete('/:clip_id/:labeler', async (req, res, next) => {
  try {
    const deleted = await Label.delete(req.params.clip_id, req.params.labeler);
    if (!deleted) return res.status(404).json({ error: 'Label not found' });
    res.json({ success: true });
  } catch (err) {
    next(err);
  }
});

module.exports = router;
