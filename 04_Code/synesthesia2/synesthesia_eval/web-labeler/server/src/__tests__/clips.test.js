const request = require('supertest');
const { getApp } = require('./setup');
const Clip = require('../models/clip');

jest.mock('../models/clip');

jest.mock('../middleware/rateLimiter', () => ({
  authLimiter: (_req, _res, next) => next(),
  labelWriteLimiter: (_req, _res, next) => next(),
  globalLimiter: (_req, _res, next) => next(),
}));

const app = getApp();

describe('GET /api/clips', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns clips with id, filename, is_hot fields', async () => {
    Clip.findAll.mockResolvedValue([
      { id: '001', filename: '001_test.mp4', has_human_label: false, has_auto_label: true, rater_count: 0, is_hot: false },
      { id: '002', filename: '002_test.mp4', has_human_label: true, has_auto_label: false, rater_count: 1, is_hot: true },
    ]);

    const res = await request(app).get('/api/clips');

    expect(res.status).toBe(200);
    expect(Array.isArray(res.body)).toBe(true);
    expect(res.body[0]).toHaveProperty('id');
    expect(res.body[0]).toHaveProperty('filename');
    expect(res.body[0]).toHaveProperty('is_hot');
  });

  it('mode=unlabeled returns only clips without human labels', async () => {
    Clip.findAll.mockResolvedValue([
      { id: '003', filename: '003_test.mp4', has_human_label: false, has_auto_label: false, rater_count: 0, is_hot: false },
    ]);

    const res = await request(app).get('/api/clips?mode=unlabeled');

    expect(res.status).toBe(200);
    expect(Clip.findAll).toHaveBeenCalledWith('unlabeled');
    expect(res.body.every(c => !c.has_human_label)).toBe(true);
  });

  it('mode defaults to all when not specified', async () => {
    Clip.findAll.mockResolvedValue([]);

    await request(app).get('/api/clips');

    expect(Clip.findAll).toHaveBeenCalledWith('all');
  });
});

describe('GET /api/clips/rankings', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns ClipRanking objects with avg scores', async () => {
    Clip.rankings.mockResolvedValue([
      {
        id: '001',
        filename: '001_test.mp4',
        rater_count: 3,
        avg_sync: 4.0,
        avg_harmony: 3.5,
        avg_aesthetic: 4.5,
        avg_motion: 3.0,
        avg_overall: 3.75,
      },
    ]);

    const res = await request(app).get('/api/clips/rankings');

    expect(res.status).toBe(200);
    expect(Array.isArray(res.body)).toBe(true);
    expect(res.body[0]).toHaveProperty('avg_sync');
    expect(res.body[0]).toHaveProperty('avg_harmony');
    expect(res.body[0]).toHaveProperty('avg_aesthetic');
    expect(res.body[0]).toHaveProperty('avg_motion');
    expect(res.body[0]).toHaveProperty('avg_overall');
  });

  it('avg_overall reflects overall impression scores', async () => {
    Clip.rankings.mockResolvedValue([
      {
        id: '001',
        filename: '001_test.mp4',
        rater_count: 2,
        avg_sync: 5.0,
        avg_harmony: 5.0,
        avg_aesthetic: 5.0,
        avg_motion: 5.0,
        avg_overall: 5.0,
      },
    ]);

    const res = await request(app).get('/api/clips/rankings');

    expect(res.status).toBe(200);
    expect(res.body[0].avg_overall).toBe(5.0);
  });
});

describe('GET /api/clips/:id', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns clip with labels array', async () => {
    Clip.findById.mockResolvedValue({
      id: '001',
      filename: '001_test.mp4',
      labels: [
        { labeler: 'testuser', sync_quality: 4, harmony: 3, aesthetic_quality: 5, motion_smoothness: 4 },
      ],
    });

    const res = await request(app).get('/api/clips/001');

    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('id', '001');
    expect(res.body).toHaveProperty('labels');
    expect(Array.isArray(res.body.labels)).toBe(true);
  });

  it('returns 404 for unknown clip id', async () => {
    Clip.findById.mockResolvedValue(null);

    const res = await request(app).get('/api/clips/9999');

    expect(res.status).toBe(404);
    expect(res.body).toHaveProperty('error');
  });

  it('returns empty labels array when clip has no labels', async () => {
    Clip.findById.mockResolvedValue({
      id: '002',
      filename: '002_test.mp4',
      labels: [],
    });

    const res = await request(app).get('/api/clips/002');

    expect(res.status).toBe(200);
    expect(res.body.labels).toHaveLength(0);
  });
});
