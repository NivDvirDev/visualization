const fs = require('fs');
const path = require('path');
const { pool } = require('../config');

const DATA_DIR = path.resolve(__dirname, '../../../../data');

async function migrate() {
  const client = await pool.connect();
  try {
    // Run DDL
    const ddl = fs.readFileSync(path.join(__dirname, '001_create_tables.sql'), 'utf8');
    await client.query(ddl);
    console.log('Tables created (or already exist).');

    // Migrate clips from metadata.json
    const metadataPath = path.join(DATA_DIR, 'clips', 'metadata.json');
    let clipCount = 0;
    if (fs.existsSync(metadataPath)) {
      const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
      const clips = metadata.clips || [];
      for (const clip of clips) {
        await client.query(
          `INSERT INTO clips (id, filename, description, source, categories)
           VALUES ($1, $2, $3, $4, $5)
           ON CONFLICT (id) DO UPDATE SET
             filename = EXCLUDED.filename,
             description = EXCLUDED.description,
             source = EXCLUDED.source,
             categories = EXCLUDED.categories`,
          [clip.id, clip.filename, clip.description, clip.source || 'youtube_playlist', JSON.stringify(clip.categories || {})]
        );
        clipCount++;
      }
    } else {
      console.warn(`metadata.json not found at ${metadataPath}`);
    }

    // Migrate auto_labels.json
    const autoLabelsPath = path.join(DATA_DIR, 'auto_labels.json');
    let autoCount = 0;
    if (fs.existsSync(autoLabelsPath)) {
      const autoLabels = JSON.parse(fs.readFileSync(autoLabelsPath, 'utf8'));
      for (const [clipId, entry] of Object.entries(autoLabels)) {
        await client.query(
          `INSERT INTO labels (clip_id, labeler, sync_quality, visual_audio_alignment, aesthetic_quality, motion_smoothness, notes, created_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
           ON CONFLICT (clip_id, labeler) DO UPDATE SET
             sync_quality = EXCLUDED.sync_quality,
             visual_audio_alignment = EXCLUDED.visual_audio_alignment,
             aesthetic_quality = EXCLUDED.aesthetic_quality,
             motion_smoothness = EXCLUDED.motion_smoothness,
             notes = EXCLUDED.notes,
             updated_at = NOW()`,
          [
            clipId,
            entry.model || 'gemini-2.5-flash-lite',
            entry.sync_quality,
            entry.visual_audio_alignment,
            entry.aesthetic_quality,
            entry.motion_smoothness,
            entry.notes || null,
            entry.timestamp || new Date().toISOString(),
          ]
        );
        autoCount++;
      }
    } else {
      console.warn(`auto_labels.json not found at ${autoLabelsPath}`);
    }

    // Migrate labels.json (human labels)
    const labelsPath = path.join(DATA_DIR, 'labels.json');
    let humanCount = 0;
    if (fs.existsSync(labelsPath)) {
      const labels = JSON.parse(fs.readFileSync(labelsPath, 'utf8'));
      for (const [clipId, entry] of Object.entries(labels)) {
        if (!entry.sync_quality) continue; // skip empty entries
        await client.query(
          `INSERT INTO labels (clip_id, labeler, sync_quality, visual_audio_alignment, aesthetic_quality, motion_smoothness, notes)
           VALUES ($1, 'human', $2, $3, $4, $5, $6)
           ON CONFLICT (clip_id, labeler) DO UPDATE SET
             sync_quality = EXCLUDED.sync_quality,
             visual_audio_alignment = EXCLUDED.visual_audio_alignment,
             aesthetic_quality = EXCLUDED.aesthetic_quality,
             motion_smoothness = EXCLUDED.motion_smoothness,
             notes = EXCLUDED.notes,
             updated_at = NOW()`,
          [
            clipId,
            entry.sync_quality,
            entry.visual_audio_alignment,
            entry.aesthetic_quality,
            entry.motion_smoothness,
            entry.notes || null,
          ]
        );
        humanCount++;
      }
    } else {
      console.warn(`labels.json not found at ${labelsPath}`);
    }

    console.log(`Migrated ${clipCount} clips, ${autoCount} auto-labels, ${humanCount} human labels.`);
  } finally {
    client.release();
    await pool.end();
  }
}

migrate().catch((err) => {
  console.error('Migration failed:', err);
  process.exit(1);
});
