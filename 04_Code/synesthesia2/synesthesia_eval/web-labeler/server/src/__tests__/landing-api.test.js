/**
 * Landing Page API Smoke Tests
 *
 * Verifies the 3 API endpoints consumed by the redesigned landing page:
 *   1. GET /api/stats         → Live Pulse section
 *   2. GET /api/clips/rankings → Featured Creations section
 *   3. GET /api/stats/leaderboard → Top Contributors section
 */

const request = require('supertest');
const { getApp } = require('./setup');
const Label = require('../models/label');
const Clip = require('../models/clip');
const { pool } = require('../config');

jest.mock('../models/label');
jest.mock('../models/clip');

jest.mock('../middleware/rateLimiter', () => ({
  authLimiter: (_req, _res, next) => next(),
  labelWriteLimiter: (_req, _res, next) => next(),
  globalLimiter: (_req, _res, next) => next(),
}));

const app = getApp();

// ── GET /api/stats (Live Pulse) ─────────────────────────────────────────────

describe('Landing API — GET /api/stats', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns stats with total_clips and total_users for Live Pulse', async () => {
    Label.stats.mockResolvedValue({
      total_clips: 81,
      labeled_human: 5,
      labeled_auto: 76,
      unlabeled: 0,
      total_users: 12,
      recent_users_7d: 3,
      avg_scores: {
        sync_quality: 3.5,
        harmony: 4.0,
        aesthetic_quality: 3.8,
        motion_smoothness: 4.2,
      },
    });

    const res = await request(app).get('/api/stats');

    expect(res.status).toBe(200);
    // Landing page needs these for "Live Pulse" section:
    expect(res.body).toHaveProperty('total_clips');
    expect(res.body).toHaveProperty('total_users');
    expect(res.body).toHaveProperty('labeled_human');
    expect(res.body).toHaveProperty('labeled_auto');
    expect(typeof res.body.total_clips).toBe('number');
    expect(typeof res.body.total_users).toBe('number');
  });

  it('returns valid stats even when everything is zero', async () => {
    Label.stats.mockResolvedValue({
      total_clips: 0,
      labeled_human: 0,
      labeled_auto: 0,
      unlabeled: 0,
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
    expect(res.body.total_clips).toBe(0);
    expect(res.body.total_users).toBe(0);
  });
});

// ── GET /api/clips/rankings (Featured Creations) ────────────────────────────

describe('Landing API — GET /api/clips/rankings', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns rankings with avg_overall for Featured Creations', async () => {
    Clip.rankings.mockResolvedValue([
      {
        id: '001',
        filename: '001_test_clip.mp4',
        rater_count: 3,
        avg_sync: 4.0,
        avg_harmony: 3.5,
        avg_aesthetic: 4.5,
        avg_motion: 3.0,
        avg_overall: 3.75,
      },
      {
        id: '002',
        filename: '002_another.mp4',
        rater_count: 2,
        avg_sync: 3.0,
        avg_harmony: 4.0,
        avg_aesthetic: 4.0,
        avg_motion: 3.5,
        avg_overall: 3.63,
      },
    ]);

    const res = await request(app).get('/api/clips/rankings');

    expect(res.status).toBe(200);
    expect(Array.isArray(res.body)).toBe(true);
    expect(res.body.length).toBe(2);
    // Landing page needs these fields for each clip card:
    expect(res.body[0]).toHaveProperty('id');
    expect(res.body[0]).toHaveProperty('filename');
    expect(res.body[0]).toHaveProperty('avg_overall');
    expect(res.body[0]).toHaveProperty('rater_count');
  });

  it('returns empty array when no clips rated', async () => {
    Clip.rankings.mockResolvedValue([]);

    const res = await request(app).get('/api/clips/rankings');

    expect(res.status).toBe(200);
    expect(res.body).toEqual([]);
  });

  it('rankings are sorted by avg_overall descending', async () => {
    Clip.rankings.mockResolvedValue([
      { id: '001', filename: 'a.mp4', rater_count: 5, avg_sync: 5, avg_harmony: 5, avg_aesthetic: 5, avg_motion: 5, avg_overall: 5.0 },
      { id: '002', filename: 'b.mp4', rater_count: 3, avg_sync: 3, avg_harmony: 3, avg_aesthetic: 3, avg_motion: 3, avg_overall: 3.0 },
    ]);

    const res = await request(app).get('/api/clips/rankings');

    expect(res.status).toBe(200);
    expect(res.body[0].avg_overall).toBeGreaterThanOrEqual(res.body[1].avg_overall);
  });
});

// ── GET /api/stats/leaderboard (Top Contributors) ───────────────────────────

describe('Landing API — GET /api/stats/leaderboard', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns leaderboard with usernames and total_labels', async () => {
    pool.query
      .mockResolvedValueOnce({
        rows: [
          { username: 'alice', total_labels: 42 },
          { username: 'bob', total_labels: 17 },
          { username: 'charlie', total_labels: 8 },
        ],
      })
      .mockResolvedValueOnce({ rows: [{ total: 81 }] });

    const res = await request(app).get('/api/stats/leaderboard');

    expect(res.status).toBe(200);
    expect(Array.isArray(res.body)).toBe(true);
    expect(res.body.length).toBe(3);
    // Landing page needs these fields:
    expect(res.body[0]).toHaveProperty('username');
    expect(res.body[0]).toHaveProperty('total_labels');
    expect(res.body[0]).toHaveProperty('level');
  });

  it('returns empty leaderboard gracefully', async () => {
    pool.query
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [{ total: 81 }] });

    const res = await request(app).get('/api/stats/leaderboard');

    expect(res.status).toBe(200);
    expect(res.body).toEqual([]);
  });

  it('leaderboard entries are sorted by total_labels descending', async () => {
    pool.query
      .mockResolvedValueOnce({
        rows: [
          { username: 'top', total_labels: 100 },
          { username: 'mid', total_labels: 50 },
          { username: 'low', total_labels: 5 },
        ],
      })
      .mockResolvedValueOnce({ rows: [{ total: 81 }] });

    const res = await request(app).get('/api/stats/leaderboard');

    expect(res.status).toBe(200);
    for (let i = 0; i < res.body.length - 1; i++) {
      expect(res.body[i].total_labels).toBeGreaterThanOrEqual(res.body[i + 1].total_labels);
    }
  });
});
