const { pool } = require('../config');

const Clip = {
  async findAll(mode = 'all') {
    const baseSelect = `
      SELECT c.*,
        EXISTS(SELECT 1 FROM labels l WHERE l.clip_id = c.id AND l.user_id IS NOT NULL) AS has_human_label,
        EXISTS(SELECT 1 FROM labels l WHERE l.clip_id = c.id AND l.user_id IS NULL) AS has_auto_label,
        (SELECT COUNT(DISTINCT l.user_id) FROM labels l WHERE l.clip_id = c.id AND l.user_id IS NOT NULL) AS rater_count
      FROM clips c`;

    let query;
    if (mode === 'unlabeled') {
      query = `${baseSelect}
        WHERE NOT EXISTS(SELECT 1 FROM labels l WHERE l.clip_id = c.id AND l.user_id IS NOT NULL)
        ORDER BY c.id`;
    } else if (mode === 'labeled') {
      query = `${baseSelect}
        WHERE EXISTS(SELECT 1 FROM labels l WHERE l.clip_id = c.id AND l.user_id IS NOT NULL)
        ORDER BY c.id`;
    } else {
      query = `${baseSelect} ORDER BY c.id`;
    }
    const { rows } = await pool.query(query);
    return rows.map(r => ({ ...r, rater_count: parseInt(r.rater_count, 10) }));
  },

  async findById(id) {
    const { rows: [clip] } = await pool.query('SELECT * FROM clips WHERE id = $1', [id]);
    if (!clip) return null;

    const { rows: labels } = await pool.query(
      `SELECT l.*, u.username FROM labels l
       LEFT JOIN users u ON l.user_id = u.id
       WHERE l.clip_id = $1
       ORDER BY l.created_at`,
      [id]
    );
    return { ...clip, labels };
  },

  async rankings() {
    const { rows } = await pool.query(`
      SELECT c.id, c.filename,
        COUNT(DISTINCT l.user_id) FILTER (WHERE l.user_id IS NOT NULL)::int AS rater_count,
        ROUND(AVG(l.sync_quality)::numeric, 2) AS avg_sync,
        ROUND(AVG(l.harmony)::numeric, 2) AS avg_harmony,
        ROUND(AVG(l.aesthetic_quality)::numeric, 2) AS avg_aesthetic,
        ROUND(AVG(l.motion_smoothness)::numeric, 2) AS avg_motion,
        ROUND((
          COALESCE(AVG(l.sync_quality), 0) +
          COALESCE(AVG(l.harmony), 0) +
          COALESCE(AVG(l.aesthetic_quality), 0) +
          COALESCE(AVG(l.motion_smoothness), 0)
        )::numeric / 4, 2) AS avg_overall
      FROM clips c
      JOIN labels l ON l.clip_id = c.id AND l.user_id IS NOT NULL
      GROUP BY c.id, c.filename
      HAVING COUNT(DISTINCT l.user_id) >= 1
      ORDER BY avg_overall DESC, rater_count DESC
    `);
    return rows.map(r => ({
      ...r,
      avg_sync: r.avg_sync ? parseFloat(r.avg_sync) : null,
      avg_harmony: r.avg_harmony ? parseFloat(r.avg_harmony) : null,
      avg_aesthetic: r.avg_aesthetic ? parseFloat(r.avg_aesthetic) : null,
      avg_motion: r.avg_motion ? parseFloat(r.avg_motion) : null,
      avg_overall: r.avg_overall ? parseFloat(r.avg_overall) : null,
    }));
  },

  async count() {
    const { rows: [{ count }] } = await pool.query('SELECT COUNT(*) FROM clips');
    return parseInt(count, 10);
  },
};

module.exports = Clip;
