const { Router } = require('express');
const Label = require('../models/label');
const { pool } = require('../config');
const { authRequired } = require('../middleware/auth');

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

// GET /api/leaderboard
router.get('/leaderboard', async (req, res, next) => {
  try {
    const { rows } = await pool.query(`
      SELECT u.username, COUNT(l.id)::int AS total_labels
      FROM labels l
      JOIN users u ON u.id = l.user_id
      WHERE l.user_id IS NOT NULL
      GROUP BY l.user_id, u.username
      ORDER BY total_labels DESC
    `);
    res.json(rows);
  } catch (err) {
    next(err);
  }
});

// GET /api/stats/me
router.get('/me', authRequired, async (req, res, next) => {
  try {
    const userId = req.user.id;

    const [labelResult, clipResult, streakResult] = await Promise.all([
      pool.query('SELECT COUNT(*)::int AS total FROM labels WHERE user_id = $1', [userId]),
      pool.query('SELECT COUNT(*)::int AS total FROM clips'),
      pool.query(
        `SELECT DISTINCT DATE(created_at) AS d FROM labels WHERE user_id = $1 ORDER BY d DESC`,
        [userId]
      ),
    ]);

    const total_labels = labelResult.rows[0].total;
    const total_clips = clipResult.rows[0].total;
    const clips_remaining = total_clips - total_labels;

    // Calculate consecutive-day streak ending today
    let current_streak = 0;
    const dates = streakResult.rows.map(r => r.d);
    if (dates.length > 0) {
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      let expected = today;
      for (const d of dates) {
        const day = new Date(d);
        day.setHours(0, 0, 0, 0);
        if (day.getTime() === expected.getTime()) {
          current_streak++;
          expected = new Date(expected);
          expected.setDate(expected.getDate() - 1);
        } else {
          break;
        }
      }
    }

    const badges = [];
    if (total_labels >= 1) badges.push('first_label');
    if (current_streak >= 5) badges.push('five_streak');
    if (total_labels >= 10) badges.push('ten_labels');
    if (clips_remaining === 0) badges.push('completionist');

    res.json({ total_labels, clips_remaining, current_streak, badges });
  } catch (err) {
    next(err);
  }
});

// GET /api/stats/users
router.get('/users', async (req, res, next) => {
  try {
    const { rows } = await pool.query(
      'SELECT id, username, email, created_at FROM users ORDER BY created_at DESC'
    );
    res.json(rows);
  } catch (err) {
    next(err);
  }
});

module.exports = router;
