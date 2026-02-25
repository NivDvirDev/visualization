const { pool } = require('../config');

const Label = {
  async findAll({ labeler, clip_id } = {}) {
    const conditions = [];
    const params = [];
    if (labeler) {
      params.push(labeler);
      conditions.push(`labeler = $${params.length}`);
    }
    if (clip_id) {
      params.push(clip_id);
      conditions.push(`clip_id = $${params.length}`);
    }
    const where = conditions.length ? `WHERE ${conditions.join(' AND ')}` : '';
    const { rows } = await pool.query(
      `SELECT * FROM labels ${where} ORDER BY clip_id, labeler`,
      params
    );
    return rows;
  },

  async findByClipId(clipId) {
    const { rows } = await pool.query(
      'SELECT * FROM labels WHERE clip_id = $1 ORDER BY labeler',
      [clipId]
    );
    return rows;
  },

  async upsert(clipId, data) {
    const { labeler, sync_quality, visual_audio_alignment, aesthetic_quality, motion_smoothness, notes } = data;
    const { rows: [row] } = await pool.query(
      `INSERT INTO labels (clip_id, labeler, sync_quality, visual_audio_alignment, aesthetic_quality, motion_smoothness, notes)
       VALUES ($1, $2, $3, $4, $5, $6, $7)
       ON CONFLICT (clip_id, labeler) DO UPDATE SET
         sync_quality = EXCLUDED.sync_quality,
         visual_audio_alignment = EXCLUDED.visual_audio_alignment,
         aesthetic_quality = EXCLUDED.aesthetic_quality,
         motion_smoothness = EXCLUDED.motion_smoothness,
         notes = EXCLUDED.notes,
         updated_at = NOW()
       RETURNING *`,
      [clipId, labeler, sync_quality, visual_audio_alignment, aesthetic_quality, motion_smoothness, notes]
    );
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
    const { rows } = await pool.query('SELECT * FROM labels ORDER BY clip_id, labeler');
    const humanLabels = {};
    const autoLabels = {};
    for (const row of rows) {
      const entry = {
        sync_quality: row.sync_quality,
        visual_audio_alignment: row.visual_audio_alignment,
        aesthetic_quality: row.aesthetic_quality,
        motion_smoothness: row.motion_smoothness,
        notes: row.notes,
      };
      if (row.labeler === 'human') {
        humanLabels[row.clip_id] = entry;
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
        (SELECT COUNT(DISTINCT clip_id) FROM labels WHERE labeler = 'human') AS labeled_human,
        (SELECT COUNT(DISTINCT clip_id) FROM labels WHERE labeler != 'human') AS labeled_auto,
        (SELECT COUNT(*) FROM clips c WHERE NOT EXISTS (
          SELECT 1 FROM labels l WHERE l.clip_id = c.id
        )) AS unlabeled
    `);

    const { rows: [avgs] } = await pool.query(`
      SELECT
        ROUND(AVG(sync_quality)::numeric, 2) AS sync_quality,
        ROUND(AVG(visual_audio_alignment)::numeric, 2) AS visual_audio_alignment,
        ROUND(AVG(aesthetic_quality)::numeric, 2) AS aesthetic_quality,
        ROUND(AVG(motion_smoothness)::numeric, 2) AS motion_smoothness
      FROM labels
    `);

    return {
      total_clips: parseInt(counts.total_clips, 10),
      labeled_human: parseInt(counts.labeled_human, 10),
      labeled_auto: parseInt(counts.labeled_auto, 10),
      unlabeled: parseInt(counts.unlabeled, 10),
      avg_scores: {
        sync_quality: avgs.sync_quality ? parseFloat(avgs.sync_quality) : null,
        visual_audio_alignment: avgs.visual_audio_alignment ? parseFloat(avgs.visual_audio_alignment) : null,
        aesthetic_quality: avgs.aesthetic_quality ? parseFloat(avgs.aesthetic_quality) : null,
        motion_smoothness: avgs.motion_smoothness ? parseFloat(avgs.motion_smoothness) : null,
      },
    };
  },
};

module.exports = Label;
