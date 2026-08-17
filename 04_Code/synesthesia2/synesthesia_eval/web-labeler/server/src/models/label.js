const { pool } = require('../config');

// Anonymous guest ratings are HUMAN ratings, not model output. See ratingSource.js
// for why classifying on user_id alone was wrong.
const {
  isAnonLabeler,
  REGISTERED_SQL,
  ANON_SQL,
  HUMAN_LABEL_SQL,
  AUTO_LABEL_SQL,
} = require('./ratingSource');

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
      // Swipe mode
      overall_impression,
    } = data;

    const cols = 'clip_id, labeler, sync_quality, harmony, aesthetic_quality, motion_smoothness, pitch_accuracy, rhythm_accuracy, dynamics_accuracy, timbre_accuracy, melody_accuracy, notes, overall_impression';
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
           overall_impression = EXCLUDED.overall_impression,
           updated_at = NOW()`;

    let row;
    if (user_id) {
      const result = await pool.query(
        `INSERT INTO labels (${cols}, user_id)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
         ON CONFLICT (clip_id, user_id) WHERE user_id IS NOT NULL DO UPDATE SET ${updates}
         RETURNING *`,
        [clipId, labeler, sync_quality, harmony, aesthetic_quality, motion_smoothness,
         pitch_accuracy || null, rhythm_accuracy || null, dynamics_accuracy || null,
         timbre_accuracy || null, melody_accuracy || null, notes, overall_impression || null, user_id]
      );
      row = result.rows[0];
    } else {
      const result = await pool.query(
        `INSERT INTO labels (${cols})
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
         ON CONFLICT (clip_id, labeler) WHERE user_id IS NULL DO UPDATE SET ${updates}
         RETURNING *`,
        [clipId, labeler, sync_quality, harmony, aesthetic_quality, motion_smoothness,
         pitch_accuracy || null, rhythm_accuracy || null, dynamics_accuracy || null,
         timbre_accuracy || null, melody_accuracy || null, notes, overall_impression || null]
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
        overall_impression: row.overall_impression,
        notes: row.notes,
      };
      // A rating is human if it came from a registered user OR from an anonymous
      // guest session (labeler 'anon_<ms>_<rand>', written by POST /api/labels/anonymous).
      // Only genuine model output (user_id NULL and a non-anon labeler) is an auto-label.
      // Anonymous ratings used to fall into the auto bucket, where — because auto is keyed
      // by clip_id — they silently overwrote the Gemini labels. See HUMAN_LABEL_SQL below.
      if (row.user_id || isAnonLabeler(row.labeler)) {
        if (!humanLabels[row.clip_id]) humanLabels[row.clip_id] = [];
        humanLabels[row.clip_id].push({
          ...entry,
          username: row.user_id ? row.username : null,
          anonymous: !row.user_id,
          session: row.user_id ? null : row.labeler,
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
        (SELECT COUNT(DISTINCT clip_id) FROM labels WHERE ${HUMAN_LABEL_SQL}) AS labeled_human,
        (SELECT COUNT(DISTINCT clip_id) FROM labels WHERE ${AUTO_LABEL_SQL}) AS labeled_auto,
        (SELECT COUNT(*) FROM labels WHERE ${HUMAN_LABEL_SQL}) AS human_ratings,
        (SELECT COUNT(*) FROM labels WHERE ${REGISTERED_SQL}) AS registered_ratings,
        (SELECT COUNT(*) FROM labels WHERE ${ANON_SQL}) AS anonymous_ratings,
        (SELECT COUNT(DISTINCT labeler) FROM labels WHERE ${ANON_SQL}) AS anonymous_sessions,
        (SELECT COUNT(*) FROM clips c WHERE NOT EXISTS (
          SELECT 1 FROM labels l WHERE l.clip_id = c.id
        )) AS unlabeled,
        (SELECT COUNT(*) FROM users) AS total_users,
        (SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '7 days') AS recent_users_7d
    `);

    // Averaged over HUMAN ratings only — mixing model output into a "community score"
    // made avg_scores drift toward the auto-labels. Auto-label averages are reported
    // separately so the two can still be compared.
    const avgCols = `
        ROUND(AVG(sync_quality)::numeric, 2) AS sync_quality,
        ROUND(AVG(harmony)::numeric, 2) AS harmony,
        ROUND(AVG(aesthetic_quality)::numeric, 2) AS aesthetic_quality,
        ROUND(AVG(motion_smoothness)::numeric, 2) AS motion_smoothness`;
    const { rows: [avgs] } = await pool.query(
      `SELECT ${avgCols} FROM labels WHERE ${HUMAN_LABEL_SQL}`
    );
    const { rows: [autoAvgs] } = await pool.query(
      `SELECT ${avgCols} FROM labels WHERE ${AUTO_LABEL_SQL}`
    );
    const toScores = (r) => ({
      sync_quality: r && r.sync_quality ? parseFloat(r.sync_quality) : null,
      harmony: r && r.harmony ? parseFloat(r.harmony) : null,
      aesthetic_quality: r && r.aesthetic_quality ? parseFloat(r.aesthetic_quality) : null,
      motion_smoothness: r && r.motion_smoothness ? parseFloat(r.motion_smoothness) : null,
    });

    return {
      total_clips: parseInt(counts.total_clips, 10),
      labeled_human: parseInt(counts.labeled_human, 10),
      labeled_auto: parseInt(counts.labeled_auto, 10),
      unlabeled: parseInt(counts.unlabeled, 10),
      total_users: parseInt(counts.total_users, 10),
      recent_users_7d: parseInt(counts.recent_users_7d, 10),
      // Rating volume. labeled_* above are DISTINCT-CLIP counts and saturate at
      // total_clips; these are the counts to watch for engagement over time.
      human_ratings: parseInt(counts.human_ratings, 10),
      registered_ratings: parseInt(counts.registered_ratings, 10),
      anonymous_ratings: parseInt(counts.anonymous_ratings, 10),
      anonymous_sessions: parseInt(counts.anonymous_sessions, 10),
      avg_scores: toScores(avgs),
      avg_scores_auto: toScores(autoAvgs),
    };
  },
};

module.exports = Label;
