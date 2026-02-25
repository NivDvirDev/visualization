const { Router } = require('express');
const Label = require('../models/label');

const router = Router();

// GET /api/stats
router.get('/', async (req, res, next) => {
  try {
    const stats = await Label.stats();
    res.json(stats);
  } catch (err) {
    next(err);
  }
});

module.exports = router;
