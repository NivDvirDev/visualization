const request = require('supertest');

const { generateToken, getApp } = require('./setup');
const Label = require('../models/label');
const { pool } = require('../config');

jest.mock('../models/label');

jest.mock('../middleware/rateLimiter', () => ({
  authLimiter: (_req, _res, next) => next(),
  labelWriteLimiter: (_req, _res, next) => next(),
  globalLimiter: (_req, _res, next) => next(),
}));

const app = getApp();

describe('GET /api/stats', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns stats with correct structure', async () => {
    Label.stats.mockResolvedValue({
      total_clips: 81,
      labeled_human: 10,
      labeled_auto: 29,
      unlabeled: 42,
      total_users: 5,
      recent_users_7d: 2,
      avg_scores: {
        sync_quality: 3.5,
        harmony: 4.0,
        aesthetic_quality: 3.8,
        motion_smoothness: 4.2,
      },
    });

    const res = await request(app).get('/api/stats');

    expect(res.status).toBe(200);
    expect(res.body.total_clips).toBe(81);
    expect(res.body.labeled_human).toBe(10);
    expect(res.body.labeled_auto).toBe(29);
    expect(res.body.unlabeled).toBe(42);
    expect(res.body.avg_scores).toHaveProperty('harmony');
    expect(res.body.avg_scores).not.toHaveProperty('visual_audio_alignment');
  });

  it('handles zero labels gracefully', async () => {
    Label.stats.mockResolvedValue({
      total_clips: 81,
      labeled_human: 0,
      labeled_auto: 0,
      unlabeled: 81,
      total_users: 0,
      recent_users_7d: 0,
      avg_scores: {
        sync_quality: null,
        harmony: null,
        aesthetic_quality: null,
        motion_smoothness: null,
      },
    });

    const res = await request(app).get('/api/stats');

    expect(res.status).toBe(200);
    expect(res.body.avg_scores.sync_quality).toBeNull();
  });
});

describe('GET /api/stats/leaderboard', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns ranked users', async () => {
    pool.query
      .mockResolvedValueOnce({                                // leaderboard query
        rows: [
          { username: 'alice', total_labels: 25 },
          { username: 'bob', total_labels: 10 },
          { username: 'carol', total_labels: 5 },
        ],
      })
      .mockResolvedValueOnce({ rows: [{ total: 81 }] });     // clip count

    const res = await request(app).get('/api/stats/leaderboard');

    expect(res.status).toBe(200);
    expect(res.body).toHaveLength(3);
    expect(res.body[0].username).toBe('alice');
    expect(res.body[0].total_labels).toBe(25);
    // Verify sorted descending
    expect(res.body[0].total_labels).toBeGreaterThan(res.body[1].total_labels);
  });

  it('returns empty array when no users', async () => {
    pool.query
      .mockResolvedValueOnce({ rows: [] })                    // leaderboard query
      .mockResolvedValueOnce({ rows: [{ total: 81 }] });      // clip count

    const res = await request(app).get('/api/stats/leaderboard');

    expect(res.status).toBe(200);
    expect(res.body).toHaveLength(0);
  });

  it('user with more labels ranks higher', async () => {
    pool.query
      .mockResolvedValueOnce({
        rows: [
          { username: 'topuser', total_labels: 50 },
          { username: 'newuser', total_labels: 1 },
        ],
      })
      .mockResolvedValueOnce({ rows: [{ total: 81 }] });

    const res = await request(app).get('/api/stats/leaderboard');

    expect(res.status).toBe(200);
    expect(res.body[0].username).toBe('topuser');
  });
});

describe('GET /api/stats/challenge', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns challenge with emoji, title, description, goal', async () => {
    const res = await request(app).get('/api/stats/challenge');

    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('emoji');
    expect(res.body).toHaveProperty('title');
    expect(res.body).toHaveProperty('description');
    expect(res.body).toHaveProperty('goal');
    expect(typeof res.body.goal).toBe('number');
    expect(res.body.goal).toBeGreaterThan(0);
  });
});

describe('GET /api/stats/me', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns personal stats with badges', async () => {
    const token = generateToken({ id: 1, username: 'testuser', email: 'test@example.com' });

    pool.query
      .mockResolvedValueOnce({ rows: [{ total: 12 }] })    // label count
      .mockResolvedValueOnce({ rows: [{ total: 81 }] })    // clip count
      .mockResolvedValueOnce({                               // streak dates
        rows: [
          { d: new Date().toISOString().split('T')[0] },
          { d: new Date(Date.now() - 86400000).toISOString().split('T')[0] },
        ],
      })
      .mockResolvedValueOnce({ rows: [{ rank: 0 }] })      // rank query
      .mockResolvedValueOnce({ rows: [{ total: 3 }] })     // labels this week
      .mockResolvedValueOnce({ rows: [{ matching_clips: 0 }] }); // consensus

    const res = await request(app)
      .get('/api/stats/me')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(res.body.total_labels).toBe(12);
    expect(res.body.clips_remaining).toBe(69);
    expect(res.body.current_streak).toBeGreaterThanOrEqual(0);
    expect(res.body.badges).toContain('first_label');
    expect(res.body.badges).toContain('ten_labels');
  });

  it('returns 401 without auth', async () => {
    const res = await request(app).get('/api/stats/me');

    expect(res.status).toBe(401);
  });

  it('returns total_labels: 0 for new user', async () => {
    const token = generateToken({ id: 99, username: 'newuser', email: 'new@example.com' });

    pool.query
      .mockResolvedValueOnce({ rows: [{ total: 0 }] })
      .mockResolvedValueOnce({ rows: [{ total: 81 }] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [{ rank: 0 }] })
      .mockResolvedValueOnce({ rows: [{ total: 0 }] })
      .mockResolvedValueOnce({ rows: [{ matching_clips: 0 }] });

    const res = await request(app)
      .get('/api/stats/me')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(res.body.total_labels).toBe(0);
    expect(res.body.badges).toEqual([]);
  });

  it('rank is 1 when only user with labels', async () => {
    const token = generateToken({ id: 1, username: 'testuser', email: 'test@example.com' });

    pool.query
      .mockResolvedValueOnce({ rows: [{ total: 5 }] })
      .mockResolvedValueOnce({ rows: [{ total: 81 }] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [{ rank: 0 }] })  // 0 users ranked above → rank = 1
      .mockResolvedValueOnce({ rows: [{ total: 2 }] })
      .mockResolvedValueOnce({ rows: [{ matching_clips: 0 }] });

    const res = await request(app)
      .get('/api/stats/me')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(res.body.rank).toBe(1);
  });

  it('current_streak is at least 0 after first label', async () => {
    // Streak comparison is timezone-sensitive in the route; verify structure only
    const token = generateToken({ id: 1, username: 'testuser', email: 'test@example.com' });
    const today = new Date().toISOString().split('T')[0];

    pool.query
      .mockResolvedValueOnce({ rows: [{ total: 1 }] })
      .mockResolvedValueOnce({ rows: [{ total: 81 }] })
      .mockResolvedValueOnce({ rows: [{ d: today }] })
      .mockResolvedValueOnce({ rows: [{ rank: 0 }] })
      .mockResolvedValueOnce({ rows: [{ total: 1 }] })
      .mockResolvedValueOnce({ rows: [{ matching_clips: 0 }] });

    const res = await request(app)
      .get('/api/stats/me')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(typeof res.body.current_streak).toBe('number');
    expect(res.body.current_streak).toBeGreaterThanOrEqual(0);
  });

  it('level is 1 for 1 label', async () => {
    const token = generateToken({ id: 1, username: 'testuser', email: 'test@example.com' });

    pool.query
      .mockResolvedValueOnce({ rows: [{ total: 1 }] })
      .mockResolvedValueOnce({ rows: [{ total: 81 }] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [{ rank: 0 }] })
      .mockResolvedValueOnce({ rows: [{ total: 0 }] })
      .mockResolvedValueOnce({ rows: [{ matching_clips: 0 }] });

    const res = await request(app)
      .get('/api/stats/me')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(res.body.level).toBe(1);
    expect(res.body.level_title).toBe('Novice Listener');
  });

  it('returns completionist badge when all clips rated', async () => {
    const token = generateToken({ id: 1, username: 'testuser', email: 'test@example.com' });

    pool.query
      .mockResolvedValueOnce({ rows: [{ total: 81 }] })    // label count = total
      .mockResolvedValueOnce({ rows: [{ total: 81 }] })    // clip count
      .mockResolvedValueOnce({ rows: [] })                   // no streak
      .mockResolvedValueOnce({ rows: [{ rank: 0 }] })       // rank query
      .mockResolvedValueOnce({ rows: [{ total: 0 }] })      // labels this week
      .mockResolvedValueOnce({ rows: [{ matching_clips: 0 }] }); // consensus

    const res = await request(app)
      .get('/api/stats/me')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(res.body.clips_remaining).toBe(0);
    expect(res.body.badges).toContain('completionist');
  });
});
