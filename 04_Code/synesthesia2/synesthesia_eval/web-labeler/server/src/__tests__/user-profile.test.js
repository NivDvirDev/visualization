const request = require('supertest');
const { getApp } = require('./setup');

jest.mock('../middleware/rateLimiter', () => ({
  authLimiter: (_req, _res, next) => next(),
  labelWriteLimiter: (_req, _res, next) => next(),
  globalLimiter: (_req, _res, next) => next(),
}));

const { pool } = require('../config');

const app = getApp();

// Helper: make pool.query return values for the multi-query pattern in /api/users/:username
// The route calls pool.query 4 times (user lookup, label count, clip count, rank, profile)
// Actually it runs: 1 user lookup + 4 parallel queries via Promise.all
function mockUserNotFound() {
  pool.query.mockResolvedValueOnce({ rows: [] });
}

function mockUserFound({
  id = 42,
  username = 'testuser',
  created_at = '2026-01-01T00:00:00Z',
  total_labels = 5,
  total_clips = 10,
  rank = 0,
  avg_sync = '4.00',
  avg_harmony = '3.00',
  avg_aesthetic = '5.00',
  avg_motion = '2.00',
  label_count = 5,
} = {}) {
  // 1. User lookup
  pool.query.mockResolvedValueOnce({ rows: [{ id, username, created_at }] });
  // 2-6. Promise.all([labelResult, clipResult, rankResult, profileResult, claimedResult])
  pool.query
    .mockResolvedValueOnce({ rows: [{ total: total_labels }] })
    .mockResolvedValueOnce({ rows: [{ total: total_clips }] })
    .mockResolvedValueOnce({ rows: [{ rank }] })
    .mockResolvedValueOnce({
      rows: [{
        avg_sync,
        avg_harmony,
        avg_aesthetic,
        avg_motion,
        label_count,
      }],
    })
    .mockResolvedValueOnce({ rows: [] }); // claimed_clips (empty by default)
}

describe('GET /api/users/:username', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns 404 for unknown username', async () => {
    mockUserNotFound();
    const res = await request(app).get('/api/users/nobody');
    expect(res.status).toBe(404);
    expect(res.body.error).toMatch(/not found/i);
  });

  it('returns public profile for existing user', async () => {
    mockUserFound();
    const res = await request(app).get('/api/users/testuser');
    expect(res.status).toBe(200);
    expect(res.body.username).toBe('testuser');
    expect(res.body).toHaveProperty('total_labels');
    expect(res.body).toHaveProperty('rank');
    expect(res.body).toHaveProperty('level');
    expect(res.body).toHaveProperty('level_title');
    expect(res.body).toHaveProperty('badges');
    expect(res.body).toHaveProperty('perceptual');
  });

  it('case-insensitive lookup — query uses LOWER()', async () => {
    // The route does LOWER(username) = LOWER($1) so any casing works at DB level.
    // Test that the route passes the raw username param to pool.query.
    mockUserFound({ username: 'TestUser' });
    const res = await request(app).get('/api/users/TESTUSER');
    expect(res.status).toBe(200);
    // pool.query should have been called with the raw param — actual case-insensitivity is DB-level
    expect(pool.query).toHaveBeenCalledWith(
      expect.stringContaining('LOWER'),
      expect.arrayContaining(['TESTUSER'])
    );
  });

  it('returns first_label badge after first label', async () => {
    mockUserFound({ total_labels: 1, total_clips: 10 });
    const res = await request(app).get('/api/users/testuser');
    expect(res.status).toBe(200);
    expect(res.body.badges).toContain('first_label');
  });

  it('returns personality from labels', async () => {
    mockUserFound({ avg_sync: '5.00', avg_harmony: '1.00', avg_aesthetic: '1.00', avg_motion: '1.00', label_count: 1 });
    const res = await request(app).get('/api/users/testuser');
    expect(res.status).toBe(200);
    expect(res.body.personality).not.toBeNull();
    expect(res.body.personality.label).toBe('Sync Purist');
  });

  it('does not include email or password_hash', async () => {
    mockUserFound();
    const res = await request(app).get('/api/users/testuser');
    expect(res.status).toBe(200);
    expect(res.body).not.toHaveProperty('email');
    expect(res.body).not.toHaveProperty('password_hash');
  });

  it('level 1 for 1 label', async () => {
    mockUserFound({ total_labels: 1, total_clips: 10 });
    const res = await request(app).get('/api/users/testuser');
    expect(res.status).toBe(200);
    expect(res.body.level).toBe(1);
    expect(res.body.level_title).toBe('Novice Listener');
  });

  it('perceptual averages match label data', async () => {
    mockUserFound({
      avg_sync: '4.50',
      avg_harmony: '3.50',
      avg_aesthetic: '5.00',
      avg_motion: '2.50',
      label_count: 2,
    });
    const res = await request(app).get('/api/users/testuser');
    expect(res.status).toBe(200);
    expect(res.body.perceptual.sync_quality).toBe(4.5);
    expect(res.body.perceptual.harmony).toBe(3.5);
    expect(res.body.perceptual.aesthetic_quality).toBe(5);
    expect(res.body.perceptual.motion_smoothness).toBe(2.5);
  });
});
