#!/usr/bin/env node

/**
 * Standalone CLI migration script.
 * Imports clip metadata and labels from JSON files into PostgreSQL.
 *
 * Usage:
 *   node scripts/migrate-json.js [--data-dir ../data] [--database-url postgres://...]
 */

const fs = require('fs');
const path = require('path');
const { Pool } = require('pg');

// Parse CLI args
const args = process.argv.slice(2);
function getArg(name, fallback) {
  const idx = args.indexOf(name);
  return idx !== -1 && args[idx + 1] ? args[idx + 1] : fallback;
}

const DATA_DIR = path.resolve(getArg('--data-dir', path.join(__dirname, '../../data')));
const DATABASE_URL = getArg('--database-url', process.env.DATABASE_URL || 'postgres://synesthesia:synesthesia@localhost:5432/synesthesia_eval');

const pool = new Pool({ connectionString: DATABASE_URL });

async function migrate() {
  const client = await pool.connect();
  console.log(`Data directory: ${DATA_DIR}`);
  console.log(`Database: ${DATABASE_URL.replace(/:[^:@]+@/, ':***@')}`);

  try {
    // Create tables
    const ddlPath = path.join(__dirname, '../server/src/migrate/001_create_tables.sql');
    const ddl = fs.readFileSync(ddlPath, 'utf8');
    await client.query(ddl);
    console.log('Schema created.');

    // Import clips
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
      console.log(`Imported ${clipCount} clips.`);
    } else {
      console.warn(`WARN: ${metadataPath} not found, skipping clips.`);
    }

    // Import auto labels
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
      console.log(`Imported ${autoCount} auto-labels.`);
    } else {
      console.warn(`WARN: ${autoLabelsPath} not found, skipping auto-labels.`);
    }

    // Import human labels
    const labelsPath = path.join(DATA_DIR, 'labels.json');
    let humanCount = 0;
    if (fs.existsSync(labelsPath)) {
      const labels = JSON.parse(fs.readFileSync(labelsPath, 'utf8'));
      for (const [clipId, entry] of Object.entries(labels)) {
        if (!entry.sync_quality) continue;
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
      console.log(`Imported ${humanCount} human labels.`);
    } else {
      console.warn(`WARN: ${labelsPath} not found, skipping human labels.`);
    }

    console.log(`\nMigrated ${clipCount} clips, ${autoCount} auto-labels, ${humanCount} human labels.`);
  } finally {
    client.release();
    await pool.end();
  }
}

migrate().catch((err) => {
  console.error('Migration failed:', err.message);
  process.exit(1);
});
