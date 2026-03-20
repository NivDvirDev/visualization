const { pool } = require('../config');

const Clip = {
  async findAll(mode = 'all') {
    const baseSelect = `
      SELECT c.*,
        EXISTS(SELECT 1 FROM labels l WHERE l.clip_id = c.id AND l.user_id IS NOT NULL) AS has_human_label,
        EXISTS(SELECT 1 FROM labels l WHERE l.clip_id = c.id AND l.user_id IS NULL) AS has_auto_label,
        (SELECT COUNT(DISTINCT l.user_id) FROM labels l WHERE l.clip_id = c.id AND l.user_id IS NOT NULL) AS rater_count,
        EXISTS(SELECT 1 FROM labels l WHERE l.clip_id = c.id AND l.user_id IS NOT NULL AND l.created_at >= NOW() - INTERVAL '7 days') AS is_hot
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

  // --- Creator attribution ---

  async claim(clipId, userId) {
    // Returns the updated clip row; caller must verify video ID match before calling
    const { rows: [clip] } = await pool.query(
      `UPDATE clips
       SET claimed_by_user_id = $1, claimed_at = NOW(),
           display_credit = COALESCE(display_credit, creator_name)
       WHERE id = $2
       RETURNING *`,
      [userId, clipId]
    );
    return clip || null;
  },

  async unclaim(clipId, userId) {
    // Only clears if this user is the current claimer
    const { rows: [clip] } = await pool.query(
      `UPDATE clips
       SET claimed_by_user_id = NULL, claimed_at = NULL,
           display_credit = NULL, display_link = NULL, credit_visible = TRUE
       WHERE id = $1 AND claimed_by_user_id = $2
       RETURNING *`,
      [clipId, userId]
    );
    return clip || null;
  },

  async updateCreatorDisplay(clipId, userId, { display_credit, display_link, credit_visible }) {
    const { rows: [clip] } = await pool.query(
      `UPDATE clips
       SET display_credit  = COALESCE($1, display_credit),
           display_link    = COALESCE($2, display_link),
           credit_visible  = COALESCE($3, credit_visible)
       WHERE id = $4 AND claimed_by_user_id = $5
       RETURNING *`,
      [display_credit ?? null, display_link ?? null, credit_visible ?? null, clipId, userId]
    );
    return clip || null;
  },

  async getCreatorInfo(clipId) {
    const { rows: [row] } = await pool.query(
      `SELECT c.id, c.creator_name, c.creator_url,
              c.claimed_by_user_id, c.claimed_at,
              c.display_credit, c.display_link, c.credit_visible,
              u.username AS claimed_by_username
       FROM clips c
       LEFT JOIN users u ON c.claimed_by_user_id = u.id
       WHERE c.id = $1`,
      [clipId]
    );
    if (!row) return null;
    return {
      creator_name: row.creator_name,
      creator_url: row.creator_url,
      claimed: row.claimed_by_user_id !== null,
      claimed_by_username: row.claimed_by_username || null,
      display_credit: row.display_credit,
      display_link: row.display_link,
      credit_visible: row.credit_visible,
    };
  },
};

module.exports = Clip;
