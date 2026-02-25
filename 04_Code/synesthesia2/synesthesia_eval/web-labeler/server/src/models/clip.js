const { pool } = require('../config');

const Clip = {
  async findAll(mode = 'all') {
    const baseSelect = `
      SELECT c.*,
        EXISTS(SELECT 1 FROM labels l WHERE l.clip_id = c.id AND l.labeler = 'human') AS has_human_label,
        EXISTS(SELECT 1 FROM labels l WHERE l.clip_id = c.id AND l.labeler != 'human') AS has_auto_label
      FROM clips c`;

    let query;
    if (mode === 'unlabeled') {
      query = `${baseSelect}
        WHERE NOT EXISTS(SELECT 1 FROM labels l WHERE l.clip_id = c.id AND l.labeler = 'human')
        ORDER BY c.id`;
    } else if (mode === 'labeled') {
      query = `${baseSelect}
        WHERE EXISTS(SELECT 1 FROM labels l WHERE l.clip_id = c.id AND l.labeler = 'human')
        ORDER BY c.id`;
    } else {
      query = `${baseSelect} ORDER BY c.id`;
    }
    const { rows } = await pool.query(query);
    return rows;
  },

  async findById(id) {
    const { rows: [clip] } = await pool.query('SELECT * FROM clips WHERE id = $1', [id]);
    if (!clip) return null;

    const { rows: labels } = await pool.query(
      'SELECT * FROM labels WHERE clip_id = $1 ORDER BY labeler',
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
