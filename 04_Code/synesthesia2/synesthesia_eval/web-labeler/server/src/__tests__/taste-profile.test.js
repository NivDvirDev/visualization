const request = require('supertest');
const { generateToken, getApp } = require('./setup');

// All DB interaction goes through pool.query which is mocked in setup.js
jest.mock('../middleware/rateLimiter', () => ({
  authLimiter: (_req, _res, next) => next(),
  labelWriteLimiter: (_req, _res, next) => next(),
  globalLimiter: (_req, _res, next) => next(),
}));

const { pool } = require('../config');

const app = getApp();

describe('GET /api/stats/me/profile', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns 401 without token', async () => {
    const res = await request(app).get('/api/stats/me/profile');
    expect(res.status).toBe(401);
  });

  it('returns label_count: 0 and personality: null with no labels', async () => {
    pool.query.mockResolvedValueOnce({
      rows: [{
        avg_sync: null,
        avg_harmony: null,
        avg_aesthetic: null,
        avg_motion: null,
        avg_pitch: null,
        avg_rhythm: null,
        avg_dynamics: null,
        avg_timbre: null,
        avg_melody: null,
        label_count: 0,
      }],
    });

    const token = generateToken();
    const res = await request(app)
      .get('/api/stats/me/profile')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(res.body.label_count).toBe(0);
    expect(res.body.personality).toBeNull();
  });

  it('returns correct averages after saving labels', async () => {
    pool.query.mockResolvedValueOnce({
      rows: [{
        avg_sync: '4.00',
        avg_harmony: '3.00',
        avg_aesthetic: '5.00',
        avg_motion: '2.00',
        avg_pitch: '3.00',
        avg_rhythm: null,
        avg_dynamics: null,
        avg_timbre: null,
        avg_melody: null,
        label_count: 1,
      }],
    });

    const token = generateToken();
    const res = await request(app)
      .get('/api/stats/me/profile')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(res.body.perceptual.sync_quality).toBe(4);
    expect(res.body.perceptual.harmony).toBe(3);
    expect(res.body.perceptual.aesthetic_quality).toBe(5);
    expect(res.body.perceptual.motion_smoothness).toBe(2);
  });

  it('returns Sync Purist personality when sync_quality is highest', async () => {
    pool.query.mockResolvedValueOnce({
      rows: [{
        avg_sync: '5.00',
        avg_harmony: '1.00',
        avg_aesthetic: '1.00',
        avg_motion: '1.00',
        avg_pitch: null,
        avg_rhythm: null,
        avg_dynamics: null,
        avg_timbre: null,
        avg_melody: null,
        label_count: 1,
      }],
    });

    const token = generateToken();
    const res = await request(app)
      .get('/api/stats/me/profile')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(res.body.personality.label).toBe('Sync Purist');
  });

  it('returns Harmony Seeker when harmony is highest', async () => {
    pool.query.mockResolvedValueOnce({
      rows: [{
        avg_sync: '1.00',
        avg_harmony: '5.00',
        avg_aesthetic: '1.00',
        avg_motion: '1.00',
        avg_pitch: null,
        avg_rhythm: null,
        avg_dynamics: null,
        avg_timbre: null,
        avg_melody: null,
        label_count: 1,
      }],
    });

    const token = generateToken();
    const res = await request(app)
      .get('/api/stats/me/profile')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(res.body.personality.label).toBe('Harmony Seeker');
  });

  it('returns Aesthetic Visionary when aesthetic_quality is highest', async () => {
    pool.query.mockResolvedValueOnce({
      rows: [{
        avg_sync: '2.00',
        avg_harmony: '2.00',
        avg_aesthetic: '5.00',
        avg_motion: '1.00',
        avg_pitch: null,
        avg_rhythm: null,
        avg_dynamics: null,
        avg_timbre: null,
        avg_melody: null,
        label_count: 1,
      }],
    });

    const token = generateToken();
    const res = await request(app)
      .get('/api/stats/me/profile')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(res.body.personality.label).toBe('Aesthetic Visionary');
  });

  it('returns Motion Master when motion_smoothness is highest', async () => {
    pool.query.mockResolvedValueOnce({
      rows: [{
        avg_sync: '1.00',
        avg_harmony: '1.00',
        avg_aesthetic: '1.00',
        avg_motion: '5.00',
        avg_pitch: null,
        avg_rhythm: null,
        avg_dynamics: null,
        avg_timbre: null,
        avg_melody: null,
        label_count: 1,
      }],
    });

    const token = generateToken();
    const res = await request(app)
      .get('/api/stats/me/profile')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(res.body.personality.label).toBe('Motion Master');
  });

  it('returns psychoacoustic averages', async () => {
    pool.query.mockResolvedValueOnce({
      rows: [{
        avg_sync: '3.00',
        avg_harmony: '3.00',
        avg_aesthetic: '3.00',
        avg_motion: '3.00',
        avg_pitch: '4.00',
        avg_rhythm: '3.00',
        avg_dynamics: '2.00',
        avg_timbre: '5.00',
        avg_melody: '1.00',
        label_count: 2,
      }],
    });

    const token = generateToken();
    const res = await request(app)
      .get('/api/stats/me/profile')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(res.body.psychoacoustic.pitch_accuracy).toBe(4);
    expect(res.body.psychoacoustic.timbre_accuracy).toBe(5);
    expect(res.body.psychoacoustic.melody_accuracy).toBe(1);
  });

  it('personality has correct emoji field', async () => {
    pool.query.mockResolvedValueOnce({
      rows: [{
        avg_sync: '5.00',
        avg_harmony: '1.00',
        avg_aesthetic: '1.00',
        avg_motion: '1.00',
        avg_pitch: null,
        avg_rhythm: null,
        avg_dynamics: null,
        avg_timbre: null,
        avg_melody: null,
        label_count: 1,
      }],
    });

    const token = generateToken();
    const res = await request(app)
      .get('/api/stats/me/profile')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(res.body.personality).toHaveProperty('emoji');
    expect(typeof res.body.personality.emoji).toBe('string');
    expect(res.body.personality.emoji.length).toBeGreaterThan(0);
  });
});
