const { Router } = require('express');
const { pool } = require('../config');

const router = Router();

function computeLevel(total_labels, total_clips) {
  if (total_clips > 0 && total_labels >= total_clips) return { level: 5, level_title: 'Master Synesthetist 👑' };
  if (total_labels >= 30) return { level: 4, level_title: 'Psychoacoustic Analyst' };
  if (total_labels >= 15) return { level: 3, level_title: 'Synesthete' };
  if (total_labels >= 5)  return { level: 2, level_title: 'Rhythm Watcher' };
  if (total_labels >= 1)  return { level: 1, level_title: 'Novice Listener' };
  return { level: 0, level_title: 'Newcomer' };
}

const PERSONALITIES = [
  { key: 'sync_quality',      emoji: '⚡', label: 'Sync Purist',        desc: 'Lives for the beat-lock.' },
  { key: 'harmony',           emoji: '🌊', label: 'Harmony Seeker',      desc: 'Coherence is everything.' },
  { key: 'aesthetic_quality', emoji: '🎨', label: 'Aesthetic Visionary', desc: 'Beauty above all.' },
  { key: 'motion_smoothness', emoji: '🌀', label: 'Motion Master',       desc: 'Flow and fluidity define them.' },
];

// GET /api/users/:username — public profile
router.get('/:username', async (req, res, next) => {
  try {
    const { username } = req.params;

    const { rows: userRows } = await pool.query(
      'SELECT id, username, created_at FROM users WHERE LOWER(username) = LOWER($1)',
      [username]
    );
    if (!userRows.length) return res.status(404).json({ error: 'User not found' });

    const user = userRows[0];
    const userId = user.id;

    const [labelResult, clipResult, rankResult, profileResult] = await Promise.all([
      pool.query('SELECT COUNT(*)::int AS total FROM labels WHERE user_id = $1', [userId]),
      pool.query('SELECT COUNT(*)::int AS total FROM clips'),
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
        `SELECT
          ROUND(AVG(sync_quality)::numeric, 2)      AS avg_sync,
          ROUND(AVG(harmony)::numeric, 2)           AS avg_harmony,
          ROUND(AVG(aesthetic_quality)::numeric, 2) AS avg_aesthetic,
          ROUND(AVG(motion_smoothness)::numeric, 2) AS avg_motion,
          COUNT(*)::int                              AS label_count
         FROM labels
         WHERE user_id = $1 AND sync_quality IS NOT NULL`,
        [userId]
      ),
    ]);

    const total_labels = labelResult.rows[0].total;
    const total_clips  = clipResult.rows[0].total;
    const rank         = rankResult.rows[0].rank + 1;
    const { level, level_title } = computeLevel(total_labels, total_clips);

    const pr = profileResult.rows[0];
    const parse = v => (v ? parseFloat(v) : null);
    const perceptual = {
      sync_quality:      parse(pr.avg_sync),
      harmony:           parse(pr.avg_harmony),
      aesthetic_quality: parse(pr.avg_aesthetic),
      motion_smoothness: parse(pr.avg_motion),
    };

    let personality = null;
    if (pr.label_count > 0) {
      const best = PERSONALITIES.reduce((a, b) =>
        (perceptual[a.key] || 0) >= (perceptual[b.key] || 0) ? a : b
      );
      personality = best;
    }

    // Badges
    const badges = [];
    if (total_labels >= 1)  badges.push('first_label');
    if (total_labels >= 10) badges.push('ten_labels');
    if (total_labels >= total_clips && total_clips > 0) badges.push('completionist');

    res.json({
      username: user.username,
      created_at: user.created_at,
      total_labels,
      rank,
      level,
      level_title,
      badges,
      perceptual,
      personality,
    });
  } catch (err) {
    next(err);
  }
});

module.exports = router;
