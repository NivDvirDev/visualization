const request = require('supertest');

const { generateToken, getApp } = require('./setup');
const Label = require('../models/label');

jest.mock('../models/label');

// Disable rate limiting in tests
jest.mock('../middleware/rateLimiter', () => ({
  authLimiter: (_req, _res, next) => next(),
  labelWriteLimiter: (_req, _res, next) => next(),
  globalLimiter: (_req, _res, next) => next(),
}));

const app = getApp();

describe('GET /api/labels', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns all labels', async () => {
    const mockLabels = [
      { id: 1, clip_id: '01', labeler: 'alice', sync_quality: 4 },
      { id: 2, clip_id: '02', labeler: 'bob', sync_quality: 3 },
    ];
    Label.findAll.mockResolvedValue(mockLabels);

    const res = await request(app).get('/api/labels');

    expect(res.status).toBe(200);
    expect(res.body).toHaveLength(2);
  });
});

describe('GET /api/labels/:clip_id', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns labels for a specific clip', async () => {
    const mockLabels = [{ id: 1, clip_id: '01', labeler: 'alice', sync_quality: 5 }];
    Label.findByClipId.mockResolvedValue(mockLabels);

    const res = await request(app).get('/api/labels/01');

    expect(res.status).toBe(200);
    expect(res.body).toHaveLength(1);
    expect(Label.findByClipId).toHaveBeenCalledWith('01');
  });
});

describe('PUT /api/labels/:clip_id', () => {
  beforeEach(() => jest.clearAllMocks());

  it('upserts label when authenticated', async () => {
    const mockLabel = { id: 1, clip_id: '01', labeler: 'testuser', sync_quality: 4, visual_audio_alignment: 3, aesthetic_quality: 5, motion_smoothness: 4 };
    Label.upsert.mockResolvedValue(mockLabel);
    const token = generateToken();

    const res = await request(app)
      .put('/api/labels/01')
      .set('Authorization', `Bearer ${token}`)
      .send({ sync_quality: 4, visual_audio_alignment: 3, aesthetic_quality: 5, motion_smoothness: 4 });

    expect(res.status).toBe(200);
    expect(Label.upsert).toHaveBeenCalledWith('01', expect.objectContaining({
      labeler: 'testuser',
      user_id: 1,
      sync_quality: 4,
    }));
  });

  it('returns 401 without authentication', async () => {
    const res = await request(app)
      .put('/api/labels/01')
      .send({ sync_quality: 4 });

    expect(res.status).toBe(401);
  });
});

describe('DELETE /api/labels/:clip_id/:labeler', () => {
  beforeEach(() => jest.clearAllMocks());

  it('deletes own label', async () => {
    Label.delete.mockResolvedValue(true);
    const token = generateToken({ id: 1, username: 'testuser', email: 'test@example.com' });

    const res = await request(app)
      .delete('/api/labels/01/testuser')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
  });

  it('returns 403 when deleting another user\'s label', async () => {
    const token = generateToken({ id: 1, username: 'testuser', email: 'test@example.com' });

    const res = await request(app)
      .delete('/api/labels/01/otheruser')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(403);
  });
});
