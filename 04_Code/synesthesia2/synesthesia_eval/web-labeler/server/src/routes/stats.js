const { Router } = require('express');
const Label = require('../models/label');
const { pool } = require('../config');
const { authRequired } = require('../middleware/auth');

const router = Router();

function computeLevel(total_labels, total_clips) {
  if (total_clips > 0 && total_labels >= total_clips) return { level: 5, level_title: 'Master Synesthetist 👑' };
  if (total_labels >= 30) return { level: 4, level_title: 'Psychoacoustic Analyst' };
  if (total_labels >= 15) return { level: 3, level_title: 'Synesthete' };
  if (total_labels >= 5) return { level: 2, level_title: 'Rhythm Watcher' };
  if (total_labels >= 1) return { level: 1, level_title: 'Novice Listener' };
  return { level: 0, level_title: 'Newcomer' };
}

function getWeekStart() {
  const now = new Date();
  const monday = new Date(now);
  const day = monday.getDay();
  monday.setDate(monday.getDate() - (day === 0 ? 6 : day - 1));
  monday.setHours(0, 0, 0, 0);
  return monday;
}

const WEEKLY_CHALLENGES = [
  { emoji: '⚡', title: 'Speed Rater', description: 'Rate 10 clips this week', goal: 10 },
  { emoji: '🎵', title: 'First Steps', description: 'Rate 5 clips this week', goal: 5 },
  { emoji: '🔬', title: 'Deep Listen', description: 'Rate 8 clips this week', goal: 8 },
  { emoji: '🏆', title: 'Champion Week', description: 'Rate 15 clips this week', goal: 15 },
  { emoji: '🎸', title: 'Harmony Hunter', description: 'Rate 6 clips this week', goal: 6 },
];

function getCurrentWeekChallenge() {
  const startOfYear = new Date(new Date().getFullYear(), 0, 1);
  const week = Math.floor((Date.now() - startOfYear.getTime()) / (7 * 24 * 60 * 60 * 1000));
  return WEEKLY_CHALLENGES[week % WEEKLY_CHALLENGES.length];
}

// GET /api/stats
router.get('/', async (req, res, next) => {
  try {
    const stats = await Label.stats();
    res.json(stats);
  } catch (err) {
    next(err);
  }
});

// GET /api/stats/leaderboard
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

    const total_clips_result = await pool.query('SELECT COUNT(*)::int AS total FROM clips');
    const total_clips = total_clips_result.rows[0].total;

    const enriched = rows.map(row => {
      const { level, level_title } = computeLevel(row.total_labels, total_clips);
      return { ...row, level, level_title };
    });

    res.json(enriched);
  } catch (err) {
    next(err);
  }
});

// GET /api/stats/me
router.get('/me', authRequired, async (req, res, next) => {
  try {
    const userId = req.user.id;
    const weekStart = getWeekStart();

    const [labelResult, clipResult, streakResult, rankResult, weekResult, consensusResult] = await Promise.all([
      pool.query('SELECT COUNT(*)::int AS total FROM labels WHERE user_id = $1', [userId]),
      pool.query('SELECT COUNT(*)::int AS total FROM clips'),
      pool.query(
        `SELECT DISTINCT DATE(created_at) AS d FROM labels WHERE user_id = $1 ORDER BY d DESC`,
        [userId]
      ),
      pool.query(
        `SELECT COUNT(DISTINCT user_id)::int AS rank
         FROM labels
         WHERE user_id IS NOT NULL
           AND user_id != $1
           AND user_id IN (
             SELECT user_id FROM labels WHERE user_id IS NOT NULL
             GROUP BY user_id
             HAVING COUNT(*) > (SELECT COUNT(*) FROM labels WHERE user_id = $1)
           )`,
        [userId]
      ),
      pool.query(
        `SELECT COUNT(*)::int AS total FROM labels WHERE user_id = $1 AND created_at >= $2`,
        [userId, weekStart]
      ),
      // Consensus badge: avg absolute deviation < 0.75 across >=3 clips with community ratings
      pool.query(
        `SELECT COUNT(*) AS matching_clips
         FROM (
           SELECT
             l.clip_id,
             ABS(l.sync_quality - avg_c.avg_sync) AS d1,
             ABS(l.harmony - avg_c.avg_harmony) AS d2,
             ABS(l.aesthetic_quality - avg_c.avg_aesthetic) AS d3,
             ABS(l.motion_smoothness - avg_c.avg_motion) AS d4
           FROM labels l
           JOIN (
             SELECT clip_id,
               AVG(sync_quality) AS avg_sync,
               AVG(harmony) AS avg_harmony,
               AVG(aesthetic_quality) AS avg_aesthetic,
               AVG(motion_smoothness) AS avg_motion,
               COUNT(*) AS rater_count
             FROM labels
             WHERE user_id IS NOT NULL
               AND sync_quality IS NOT NULL
             GROUP BY clip_id
             HAVING COUNT(*) >= 2
           ) avg_c ON avg_c.clip_id = l.clip_id
           WHERE l.user_id = $1
             AND l.sync_quality IS NOT NULL
         ) deviations
         WHERE (d1 + d2 + d3 + d4) / 4.0 < 0.75`,
        [userId]
      ),
    ]);

    const total_labels = labelResult.rows[0].total;
    const total_clips = clipResult.rows[0].total;
    const clips_remaining = Math.max(0, total_clips - total_labels);
    const rank = rankResult.rows[0].rank + 1;
    const labels_this_week = weekResult.rows[0].total;
    const consensus_matching = parseInt(consensusResult.rows[0].matching_clips, 10);

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
    if (consensus_matching >= 3) badges.push('consensus_rater');

    const { level, level_title } = computeLevel(total_labels, total_clips);

    res.json({ total_labels, clips_remaining, current_streak, badges, level, level_title, rank, labels_this_week });
  } catch (err) {
    next(err);
  }
});

// GET /api/stats/challenge
router.get('/challenge', async (req, res, next) => {
  try {
    res.json(getCurrentWeekChallenge());
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
