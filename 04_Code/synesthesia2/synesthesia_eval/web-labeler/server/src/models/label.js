const { pool } = require('../config');

const Label = {
  async findAll({ labeler, clip_id } = {}) {
    const conditions = [];
    const params = [];
    if (labeler) {
      params.push(labeler);
      conditions.push(`l.labeler = $${params.length}`);
    }
    if (clip_id) {
      params.push(clip_id);
      conditions.push(`l.clip_id = $${params.length}`);
    }
    const where = conditions.length ? `WHERE ${conditions.join(' AND ')}` : '';
    const { rows } = await pool.query(
      `SELECT l.*, u.username FROM labels l
       LEFT JOIN users u ON l.user_id = u.id
       ${where} ORDER BY l.clip_id, l.created_at`,
      params
    );
    return rows;
  },

  async findByClipId(clipId) {
    const { rows } = await pool.query(
      `SELECT l.*, u.username FROM labels l
       LEFT JOIN users u ON l.user_id = u.id
       WHERE l.clip_id = $1
       ORDER BY l.created_at`,
      [clipId]
    );
    return rows;
  },

  async upsert(clipId, data) {
    const {
      labeler, user_id, notes,
      // Axis 1: Perceptual
      sync_quality, harmony, aesthetic_quality, motion_smoothness,
      // Axis 2: Psychoacoustic
      pitch_accuracy, rhythm_accuracy, dynamics_accuracy, timbre_accuracy, melody_accuracy,
    } = data;

    const cols = 'clip_id, labeler, sync_quality, harmony, aesthetic_quality, motion_smoothness, pitch_accuracy, rhythm_accuracy, dynamics_accuracy, timbre_accuracy, melody_accuracy, notes';
    const updates = `
           labeler = EXCLUDED.labeler,
           sync_quality = EXCLUDED.sync_quality,
           harmony = EXCLUDED.harmony,
           aesthetic_quality = EXCLUDED.aesthetic_quality,
           motion_smoothness = EXCLUDED.motion_smoothness,
           pitch_accuracy = EXCLUDED.pitch_accuracy,
           rhythm_accuracy = EXCLUDED.rhythm_accuracy,
           dynamics_accuracy = EXCLUDED.dynamics_accuracy,
           timbre_accuracy = EXCLUDED.timbre_accuracy,
           melody_accuracy = EXCLUDED.melody_accuracy,
           notes = EXCLUDED.notes,
           updated_at = NOW()`;

    let row;
    if (user_id) {
      const result = await pool.query(
        `INSERT INTO labels (${cols}, user_id)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
         ON CONFLICT (clip_id, user_id) WHERE user_id IS NOT NULL DO UPDATE SET ${updates}
         RETURNING *`,
        [clipId, labeler, sync_quality, harmony, aesthetic_quality, motion_smoothness,
         pitch_accuracy || null, rhythm_accuracy || null, dynamics_accuracy || null,
         timbre_accuracy || null, melody_accuracy || null, notes, user_id]
      );
      row = result.rows[0];
    } else {
      const result = await pool.query(
        `INSERT INTO labels (${cols})
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
         ON CONFLICT (clip_id, labeler) WHERE user_id IS NULL DO UPDATE SET ${updates}
         RETURNING *`,
        [clipId, labeler, sync_quality, harmony, aesthetic_quality, motion_smoothness,
         pitch_accuracy || null, rhythm_accuracy || null, dynamics_accuracy || null,
         timbre_accuracy || null, melody_accuracy || null, notes]
      );
      row = result.rows[0];
    }
    return row;
  },

  async delete(clipId, labeler) {
    const { rowCount } = await pool.query(
      'DELETE FROM labels WHERE clip_id = $1 AND labeler = $2',
      [clipId, labeler]
    );
    return rowCount > 0;
  },

  async exportJson() {
    const { rows } = await pool.query(
      `SELECT l.*, u.username FROM labels l
       LEFT JOIN users u ON l.user_id = u.id
       ORDER BY l.clip_id, l.created_at`
    );
    const humanLabels = {};
    const autoLabels = {};
    for (const row of rows) {
      const entry = {
        sync_quality: row.sync_quality,
        harmony: row.harmony,
        aesthetic_quality: row.aesthetic_quality,
        motion_smoothness: row.motion_smoothness,
        pitch_accuracy: row.pitch_accuracy,
        rhythm_accuracy: row.rhythm_accuracy,
        dynamics_accuracy: row.dynamics_accuracy,
        timbre_accuracy: row.timbre_accuracy,
        melody_accuracy: row.melody_accuracy,
        notes: row.notes,
      };
      if (row.user_id) {
        if (!humanLabels[row.clip_id]) humanLabels[row.clip_id] = [];
        humanLabels[row.clip_id].push({
          ...entry,
          username: row.username,
          timestamp: row.updated_at || row.created_at,
        });
      } else {
        autoLabels[row.clip_id] = {
          ...entry,
          model: row.labeler,
          timestamp: row.created_at,
        };
      }
    }
    return { human: humanLabels, auto: autoLabels };
  },

  async stats() {
    const { rows: [counts] } = await pool.query(`
      SELECT
        (SELECT COUNT(*) FROM clips) AS total_clips,
        (SELECT COUNT(DISTINCT clip_id) FROM labels WHERE user_id IS NOT NULL) AS labeled_human,
        (SELECT COUNT(DISTINCT clip_id) FROM labels WHERE user_id IS NULL) AS labeled_auto,
        (SELECT COUNT(*) FROM clips c WHERE NOT EXISTS (
          SELECT 1 FROM labels l WHERE l.clip_id = c.id
        )) AS unlabeled,
        (SELECT COUNT(*) FROM users) AS total_users,
        (SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '7 days') AS recent_users_7d
    `);

    const { rows: [avgs] } = await pool.query(`
      SELECT
        ROUND(AVG(sync_quality)::numeric, 2) AS sync_quality,
        ROUND(AVG(harmony)::numeric, 2) AS harmony,
        ROUND(AVG(aesthetic_quality)::numeric, 2) AS aesthetic_quality,
        ROUND(AVG(motion_smoothness)::numeric, 2) AS motion_smoothness
      FROM labels
    `);

    return {
      total_clips: parseInt(counts.total_clips, 10),
      labeled_human: parseInt(counts.labeled_human, 10),
      labeled_auto: parseInt(counts.labeled_auto, 10),
      unlabeled: parseInt(counts.unlabeled, 10),
      total_users: parseInt(counts.total_users, 10),
      recent_users_7d: parseInt(counts.recent_users_7d, 10),
      avg_scores: {
        sync_quality: avgs.sync_quality ? parseFloat(avgs.sync_quality) : null,
        harmony: avgs.harmony ? parseFloat(avgs.harmony) : null,
        aesthetic_quality: avgs.aesthetic_quality ? parseFloat(avgs.aesthetic_quality) : null,
        motion_smoothness: avgs.motion_smoothness ? parseFloat(avgs.motion_smoothness) : null,
      },
    };
  },
};

module.exports = Label;
