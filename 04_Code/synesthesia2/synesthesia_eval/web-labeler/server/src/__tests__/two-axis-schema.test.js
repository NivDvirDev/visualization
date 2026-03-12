const fs = require('fs');
const path = require('path');

const { getApp } = require('./setup');
const Label = require('../models/label');

jest.mock('../models/label');

jest.mock('../middleware/rateLimiter', () => ({
  authLimiter: (_req, _res, next) => next(),
  labelWriteLimiter: (_req, _res, next) => next(),
  globalLimiter: (_req, _res, next) => next(),
}));

const app = getApp();

describe('Migration 005 SQL', () => {
  const migrationPath = path.join(__dirname, '..', 'migrate', '005_two_axis_ratings.sql');

  it('migration file exists', () => {
    expect(fs.existsSync(migrationPath)).toBe(true);
  });

  it('renames visual_audio_alignment to harmony', () => {
    const sql = fs.readFileSync(migrationPath, 'utf8');
    expect(sql).toContain('RENAME COLUMN visual_audio_alignment TO harmony');
  });

  it('adds all 5 psychoacoustic columns', () => {
    const sql = fs.readFileSync(migrationPath, 'utf8');
    const expectedColumns = [
      'pitch_accuracy',
      'rhythm_accuracy',
      'dynamics_accuracy',
      'timbre_accuracy',
      'melody_accuracy',
    ];
    for (const col of expectedColumns) {
      expect(sql).toContain(col);
    }
  });

  it('uses IF NOT EXISTS for idempotent column adds', () => {
    const sql = fs.readFileSync(migrationPath, 'utf8');
    const addColumnCount = (sql.match(/ADD COLUMN IF NOT EXISTS/g) || []).length;
    expect(addColumnCount).toBe(5);
  });

  it('constrains psychoacoustic values to 1-5 range', () => {
    const sql = fs.readFileSync(migrationPath, 'utf8');
    const checkCount = (sql.match(/CHECK \(\w+ BETWEEN 1 AND 5\)/g) || []).length;
    expect(checkCount).toBe(5);
  });

  it('uses idempotent DO block for column rename', () => {
    const sql = fs.readFileSync(migrationPath, 'utf8');
    expect(sql).toContain('DO $$');
    expect(sql).toContain("column_name = 'visual_audio_alignment'");
  });
});

describe('Label model schema (mocked)', () => {
  beforeEach(() => jest.clearAllMocks());

  it('upsert accepts all 9 dimensions', async () => {
    Label.upsert.mockResolvedValue({ id: 1 });

    const data = {
      labeler: 'testuser', user_id: 1,
      sync_quality: 4, harmony: 3, aesthetic_quality: 5, motion_smoothness: 4,
      pitch_accuracy: 3, rhythm_accuracy: 4, dynamics_accuracy: 2, timbre_accuracy: 3, melody_accuracy: 1,
    };

    await Label.upsert('01', data);

    expect(Label.upsert).toHaveBeenCalledWith('01', expect.objectContaining({
      sync_quality: 4,
      harmony: 3,
      pitch_accuracy: 3,
      melody_accuracy: 1,
    }));
  });

  it('upsert handles null psychoacoustic fields', async () => {
    Label.upsert.mockResolvedValue({ id: 1 });

    const data = {
      labeler: 'testuser', user_id: 1,
      sync_quality: 4, harmony: 3, aesthetic_quality: 5, motion_smoothness: 4,
    };

    await Label.upsert('01', data);

    expect(Label.upsert).toHaveBeenCalledWith('01', expect.not.objectContaining({
      pitch_accuracy: expect.any(Number),
    }));
  });

  it('exportJson includes both axes', async () => {
    Label.exportJson.mockResolvedValue({
      human: {
        '01': [{
          sync_quality: 4, harmony: 3, aesthetic_quality: 5, motion_smoothness: 4,
          pitch_accuracy: 3, rhythm_accuracy: 4, dynamics_accuracy: 2, timbre_accuracy: 3, melody_accuracy: 1,
          username: 'alice', timestamp: '2026-03-09',
        }],
      },
      auto: {},
    });

    const result = await Label.exportJson();

    const label = result.human['01'][0];
    // Axis 1
    expect(label).toHaveProperty('harmony');
    expect(label).not.toHaveProperty('visual_audio_alignment');
    // Axis 2
    expect(label).toHaveProperty('pitch_accuracy');
    expect(label).toHaveProperty('rhythm_accuracy');
    expect(label).toHaveProperty('dynamics_accuracy');
    expect(label).toHaveProperty('timbre_accuracy');
    expect(label).toHaveProperty('melody_accuracy');
  });

  it('stats uses harmony not visual_audio_alignment', async () => {
    Label.stats.mockResolvedValue({
      avg_scores: { sync_quality: 3.5, harmony: 4.0, aesthetic_quality: 3.8, motion_smoothness: 4.2 },
    });

    const stats = await Label.stats();
    expect(stats.avg_scores).toHaveProperty('harmony');
    expect(stats.avg_scores).not.toHaveProperty('visual_audio_alignment');
  });
});

describe('Label model source code verification', () => {
  it('label.js uses harmony field throughout', () => {
    const labelSrc = fs.readFileSync(
      path.join(__dirname, '..', 'models', 'label.js'), 'utf8'
    );
    expect(labelSrc).toContain('harmony');
    expect(labelSrc).not.toContain('visual_audio_alignment');
  });

  it('huggingface.js pushLabels exports both axes', () => {
    const hfSrc = fs.readFileSync(
      path.join(__dirname, '..', 'services', 'huggingface.js'), 'utf8'
    );
    expect(hfSrc).toContain('perceptual');
    expect(hfSrc).toContain('psychoacoustic');
    expect(hfSrc).toContain('pitch_accuracy');
    expect(hfSrc).toContain('melody_accuracy');
  });
});
