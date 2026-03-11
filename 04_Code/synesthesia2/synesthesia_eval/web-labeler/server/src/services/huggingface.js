const { pool, HF_TOKEN, HF_DATASET, USE_HUGGINGFACE } = require('../config');

const HF_API_BASE = 'https://huggingface.co/api/datasets';
const HF_RESOLVE_BASE = 'https://huggingface.co/datasets';

function headers() {
  const h = { 'Content-Type': 'application/json' };
  if (HF_TOKEN) h['Authorization'] = `Bearer ${HF_TOKEN}`;
  return h;
}

const HuggingFace = {
  /**
   * Get the direct URL to stream a video file from HuggingFace
   */
  getVideoUrl(filename) {
    return `${HF_RESOLVE_BASE}/${HF_DATASET}/resolve/main/data/clips/${encodeURIComponent(filename)}`;
  },

  /**
   * List clip files from the HuggingFace dataset
   */
  async listClipFiles() {
    const url = `${HF_API_BASE}/${HF_DATASET}/tree/main/data/clips`;
    const res = await fetch(url, { headers: headers() });
    if (!res.ok) {
      throw new Error(`HuggingFace API error: ${res.status} ${res.statusText}`);
    }
    const files = await res.json();
    // Filter to video files only
    return files
      .filter(f => f.type === 'file' && /\.(mp4|webm|mov)$/i.test(f.path))
      .map(f => {
        const filename = f.path.split('/').pop();
        // Extract clip ID from filename (e.g., "01_something.mp4" -> "01")
        const match = filename.match(/^(\d+)/);
        const id = match ? match[1] : filename.replace(/\.[^.]+$/, '');
        return { id, filename };
      });
  },

  /**
   * Sync clips from HuggingFace into the local database
   */
  async syncClips() {
    if (!USE_HUGGINGFACE) return { synced: 0 };

    console.log('[HuggingFace] Syncing clips from dataset...');
    const files = await this.listClipFiles();
    let synced = 0;

    for (const { id, filename } of files) {
      const { rowCount } = await pool.query(
        `INSERT INTO clips (id, filename, source)
         VALUES ($1, $2, 'huggingface')
         ON CONFLICT (id) DO UPDATE SET filename = EXCLUDED.filename`,
        [id, filename]
      );
      if (rowCount > 0) synced++;
    }

    console.log(`[HuggingFace] Synced ${synced} clips from ${files.length} files`);
    return { synced, total: files.length };
  },

  /**
   * Fetch existing community labels from HuggingFace
   */
  async fetchCommunityLabels() {
    const url = `${HF_RESOLVE_BASE}/${HF_DATASET}/resolve/main/data/community_labels.json`;
    const res = await fetch(url, { headers: headers() });
    if (!res.ok) {
      if (res.status === 404) return []; // File doesn't exist yet
      throw new Error(`HuggingFace fetch error: ${res.status}`);
    }
    return res.json();
  },

  /**
   * Push community labels to HuggingFace dataset
   */
  async pushLabels() {
    if (!USE_HUGGINGFACE || !HF_TOKEN) {
      console.log('[HuggingFace] Skipping push (disabled or no token)');
      return false;
    }

    // Gather all labels with user info
    const { rows } = await pool.query(`
      SELECT l.clip_id, u.username, l.sync_quality, l.harmony,
             l.aesthetic_quality, l.motion_smoothness,
             l.pitch_accuracy, l.rhythm_accuracy, l.dynamics_accuracy,
             l.timbre_accuracy, l.melody_accuracy,
             l.notes, l.labeler, l.created_at, l.updated_at
      FROM labels l
      LEFT JOIN users u ON l.user_id = u.id
      ORDER BY l.clip_id, l.created_at
    `);

    const communityLabels = rows.map(r => ({
      clip_id: r.clip_id,
      user: r.username || r.labeler,
      perceptual: {
        sync_quality: r.sync_quality,
        harmony: r.harmony,
        aesthetic_quality: r.aesthetic_quality,
        motion_smoothness: r.motion_smoothness,
      },
      psychoacoustic: {
        pitch_accuracy: r.pitch_accuracy,
        rhythm_accuracy: r.rhythm_accuracy,
        dynamics_accuracy: r.dynamics_accuracy,
        timbre_accuracy: r.timbre_accuracy,
        melody_accuracy: r.melody_accuracy,
      },
      notes: r.notes || '',
      timestamp: r.updated_at || r.created_at,
    }));

    const content = JSON.stringify(communityLabels, null, 2);
    const contentBase64 = Buffer.from(content).toString('base64');

    // Use HuggingFace API to create/update file
    const url = `${HF_API_BASE}/${HF_DATASET}/commit/main`;
    const res = await fetch(url, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({
        commit_message: `Update community labels (${communityLabels.length} entries)`,
        operations: [{
          operation: 'create',
          path: 'data/community_labels.json',
          content: contentBase64,
          encoding: 'base64',
        }],
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      console.error(`[HuggingFace] Push failed: ${res.status} ${text}`);
      return false;
    }

    console.log(`[HuggingFace] Pushed ${communityLabels.length} labels`);
    return true;
  },
};

module.exports = HuggingFace;
