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

  async count() {
    const { rows: [{ count }] } = await pool.query('SELECT COUNT(*) FROM clips');
    return parseInt(count, 10);
  },
};

module.exports = Clip;
