const { Router } = require('express');
const Clip = require('../models/clip');

const router = Router();

// GET /api/clips?mode=all|unlabeled|labeled
router.get('/', async (req, res, next) => {
  try {
    const mode = req.query.mode || 'all';
    const clips = await Clip.findAll(mode);
    res.json(clips);
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
    res.json(clip);
  } catch (err) {
    next(err);
  }
});

module.exports = router;
