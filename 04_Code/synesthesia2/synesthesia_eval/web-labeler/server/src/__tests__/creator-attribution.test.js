const request = require('supertest');
const { generateToken, getApp } = require('./setup');

jest.mock('../middleware/rateLimiter', () => ({
  authLimiter: (_req, _res, next) => next(),
  labelWriteLimiter: (_req, _res, next) => next(),
  globalLimiter: (_req, _res, next) => next(),
}));

jest.mock('../models/clip');
const Clip = require('../models/clip');

const app = getApp();

// ── Fixtures ─────────────────────────────────────────────────────────────────

const clip = {
  id: '001',
  filename: '001_test.mp4',
  youtube_video_id: 'abc123def45',
  creator_name: 'Polyfjord',
  creator_url: 'https://www.youtube.com/watch?v=abc123def45',
  claimed_by_user_id: null,
  display_credit: null,
  display_link: null,
  credit_visible: true,
  labels: [],
};

const claimedByOther = {
  creator_name: 'Polyfjord',
  creator_url: 'https://www.youtube.com/watch?v=abc123def45',
  claimed: true,
  claimed_by_username: 'otheruser',
  display_credit: 'Polyfjord',
  display_link: null,
  credit_visible: true,
};

const unclaimedCreatorInfo = {
  creator_name: 'Polyfjord',
  creator_url: 'https://www.youtube.com/watch?v=abc123def45',
  claimed: false,
  claimed_by_username: null,
  display_credit: null,
  display_link: null,
  credit_visible: true,
};

const claimedCreatorInfo = {
  creator_name: 'Polyfjord',
  creator_url: 'https://www.youtube.com/watch?v=abc123def45',
  claimed: true,
  claimed_by_username: 'testuser',
  display_credit: 'Polyfjord',
  display_link: null,
  credit_visible: true,
};

// ── POST /api/clips/:id/claim ─────────────────────────────────────────────────

describe('POST /api/clips/:id/claim', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns 401 without token', async () => {
    const res = await request(app).post('/api/clips/001/claim').send({ youtube_url: 'https://youtu.be/abc123def45' });
    expect(res.status).toBe(401);
  });

  it('returns 400 when youtube_url is missing', async () => {
    Clip.findById.mockResolvedValue(clip);
    Clip.getCreatorInfo.mockResolvedValue(unclaimedCreatorInfo);
    const token = generateToken();
    const res = await request(app)
      .post('/api/clips/001/claim')
      .set('Authorization', `Bearer ${token}`)
      .send({});
    expect(res.status).toBe(400);
    expect(res.body.error).toMatch(/youtube_url/i);
  });

  it('returns 400 when video ID does not match clip', async () => {
    Clip.findById.mockResolvedValue(clip);
    Clip.getCreatorInfo.mockResolvedValue(unclaimedCreatorInfo);
    const token = generateToken();
    const res = await request(app)
      .post('/api/clips/001/claim')
      .set('Authorization', `Bearer ${token}`)
      .send({ youtube_url: 'https://www.youtube.com/watch?v=WRONGVIDEOID' });
    expect(res.status).toBe(400);
    expect(res.body.error).toMatch(/doesn't match/i);
  });

  it('returns 200 and claimed: true when video ID matches', async () => {
    Clip.findById.mockResolvedValue(clip);
    Clip.getCreatorInfo
      .mockResolvedValueOnce(unclaimedCreatorInfo)
      .mockResolvedValueOnce(claimedCreatorInfo);
    Clip.claim.mockResolvedValue({ ...clip, claimed_by_user_id: 1, display_credit: 'Polyfjord' });
    const token = generateToken();
    const res = await request(app)
      .post('/api/clips/001/claim')
      .set('Authorization', `Bearer ${token}`)
      .send({ youtube_url: 'https://www.youtube.com/watch?v=abc123def45' });
    expect(res.status).toBe(200);
    expect(res.body.claimed).toBe(true);
    expect(res.body.claimed_by_username).toBe('testuser');
  });

  it('returns 409 when clip already claimed by a different user', async () => {
    Clip.findById.mockResolvedValue(clip);
    Clip.getCreatorInfo.mockResolvedValue(claimedByOther);
    const token = generateToken();
    const res = await request(app)
      .post('/api/clips/001/claim')
      .set('Authorization', `Bearer ${token}`)
      .send({ youtube_url: 'https://www.youtube.com/watch?v=abc123def45' });
    expect(res.status).toBe(409);
    expect(res.body.error).toMatch(/already been claimed/i);
  });

  it('returns 200 (idempotent) when same user re-claims', async () => {
    Clip.findById.mockResolvedValue(clip);
    Clip.getCreatorInfo
      .mockResolvedValueOnce(claimedCreatorInfo)
      .mockResolvedValueOnce(claimedCreatorInfo);
    Clip.claim.mockResolvedValue({ ...clip, claimed_by_user_id: 1 });
    const token = generateToken();
    const res = await request(app)
      .post('/api/clips/001/claim')
      .set('Authorization', `Bearer ${token}`)
      .send({ youtube_url: 'https://www.youtube.com/watch?v=abc123def45' });
    expect(res.status).toBe(200);
  });

  it('accepts youtu.be short URL format', async () => {
    Clip.findById.mockResolvedValue(clip);
    Clip.getCreatorInfo
      .mockResolvedValueOnce(unclaimedCreatorInfo)
      .mockResolvedValueOnce(claimedCreatorInfo);
    Clip.claim.mockResolvedValue({ ...clip, claimed_by_user_id: 1 });
    const token = generateToken();
    const res = await request(app)
      .post('/api/clips/001/claim')
      .set('Authorization', `Bearer ${token}`)
      .send({ youtube_url: 'https://youtu.be/abc123def45' });
    expect(res.status).toBe(200);
  });
});

// ── DELETE /api/clips/:id/claim ───────────────────────────────────────────────

describe('DELETE /api/clips/:id/claim', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns 401 without token', async () => {
    const res = await request(app).delete('/api/clips/001/claim');
    expect(res.status).toBe(401);
  });

  it('returns 403 when not the claimer', async () => {
    Clip.getCreatorInfo.mockResolvedValue(claimedByOther);
    const token = generateToken();
    const res = await request(app)
      .delete('/api/clips/001/claim')
      .set('Authorization', `Bearer ${token}`);
    expect(res.status).toBe(403);
    expect(res.body.error).toMatch(/not the claimer/i);
  });

  it('returns 200 and clears claim for the claimer', async () => {
    Clip.getCreatorInfo.mockResolvedValue(claimedCreatorInfo);
    Clip.unclaim.mockResolvedValue({ ...clip, claimed_by_user_id: null });
    const token = generateToken();
    const res = await request(app)
      .delete('/api/clips/001/claim')
      .set('Authorization', `Bearer ${token}`);
    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
    expect(Clip.unclaim).toHaveBeenCalledWith('001', 1);
  });
});

// ── PUT /api/clips/:id/creator ────────────────────────────────────────────────

describe('PUT /api/clips/:id/creator', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns 401 without token', async () => {
    const res = await request(app).put('/api/clips/001/creator').send({ display_credit: 'My Channel' });
    expect(res.status).toBe(401);
  });

  it('returns 403 when not the claimer', async () => {
    Clip.getCreatorInfo.mockResolvedValue(claimedByOther);
    const token = generateToken();
    const res = await request(app)
      .put('/api/clips/001/creator')
      .set('Authorization', `Bearer ${token}`)
      .send({ display_credit: 'My Channel' });
    expect(res.status).toBe(403);
  });

  it('updates display_credit', async () => {
    const updated = { ...claimedCreatorInfo, display_credit: 'My Channel' };
    Clip.getCreatorInfo
      .mockResolvedValueOnce(claimedCreatorInfo)
      .mockResolvedValueOnce(updated);
    Clip.updateCreatorDisplay.mockResolvedValue({ ...clip, display_credit: 'My Channel' });
    const token = generateToken();
    const res = await request(app)
      .put('/api/clips/001/creator')
      .set('Authorization', `Bearer ${token}`)
      .send({ display_credit: 'My Channel' });
    expect(res.status).toBe(200);
    expect(res.body.display_credit).toBe('My Channel');
    expect(Clip.updateCreatorDisplay).toHaveBeenCalledWith('001', 1, expect.objectContaining({
      display_credit: 'My Channel',
    }));
  });

  it('updates display_link', async () => {
    const updated = { ...claimedCreatorInfo, display_link: 'https://example.com' };
    Clip.getCreatorInfo
      .mockResolvedValueOnce(claimedCreatorInfo)
      .mockResolvedValueOnce(updated);
    Clip.updateCreatorDisplay.mockResolvedValue({ ...clip, display_link: 'https://example.com' });
    const token = generateToken();
    const res = await request(app)
      .put('/api/clips/001/creator')
      .set('Authorization', `Bearer ${token}`)
      .send({ display_link: 'https://example.com' });
    expect(res.status).toBe(200);
    expect(res.body.display_link).toBe('https://example.com');
  });

  it('sets credit_visible to false', async () => {
    const updated = { ...claimedCreatorInfo, credit_visible: false };
    Clip.getCreatorInfo
      .mockResolvedValueOnce(claimedCreatorInfo)
      .mockResolvedValueOnce(updated);
    Clip.updateCreatorDisplay.mockResolvedValue({ ...clip, credit_visible: false });
    const token = generateToken();
    const res = await request(app)
      .put('/api/clips/001/creator')
      .set('Authorization', `Bearer ${token}`)
      .send({ credit_visible: false });
    expect(res.status).toBe(200);
    expect(res.body.credit_visible).toBe(false);
  });
});

// ── GET /api/clips/:id (extended) ─────────────────────────────────────────────

describe('GET /api/clips/:id — creator fields', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns claimed: false for unclaimed clip', async () => {
    Clip.findById.mockResolvedValue(clip);
    Clip.getCreatorInfo.mockResolvedValue(unclaimedCreatorInfo);
    const res = await request(app).get('/api/clips/001');
    expect(res.status).toBe(200);
    expect(res.body.claimed).toBe(false);
    expect(res.body.claimed_by_username).toBeNull();
  });

  it('returns claimed: true + claimed_by_username after claim', async () => {
    Clip.findById.mockResolvedValue({ ...clip, claimed_by_user_id: 1 });
    Clip.getCreatorInfo.mockResolvedValue(claimedCreatorInfo);
    const res = await request(app).get('/api/clips/001');
    expect(res.status).toBe(200);
    expect(res.body.claimed).toBe(true);
    expect(res.body.claimed_by_username).toBe('testuser');
  });

  it('returns creator_name populated from metadata', async () => {
    Clip.findById.mockResolvedValue({ ...clip, creator_name: 'Polyfjord' });
    Clip.getCreatorInfo.mockResolvedValue(unclaimedCreatorInfo);
    const res = await request(app).get('/api/clips/001');
    expect(res.status).toBe(200);
    expect(res.body.creator_name).toBe('Polyfjord');
  });
});

// ── GET /api/users/:username — claimed_clips ─────────────────────────────────

describe('GET /api/users/:username — claimed_clips', () => {
  const { pool } = require('../config');

  beforeEach(() => jest.clearAllMocks());

  it('returns claimed_clips array', async () => {
    // User lookup
    pool.query.mockResolvedValueOnce({ rows: [{ id: 1, username: 'testuser', created_at: '2026-01-01' }] });
    // label count
    pool.query.mockResolvedValueOnce({ rows: [{ total: 5 }] });
    // clip count
    pool.query.mockResolvedValueOnce({ rows: [{ total: 81 }] });
    // rank
    pool.query.mockResolvedValueOnce({ rows: [{ rank: 0 }] });
    // profile
    pool.query.mockResolvedValueOnce({ rows: [{ avg_sync: '4.00', avg_harmony: '3.00', avg_aesthetic: '5.00', avg_motion: '2.00', label_count: 5 }] });
    // claimed clips
    pool.query.mockResolvedValueOnce({ rows: [{ id: '001', filename: '001_test.mp4', display_credit: 'Polyfjord', creator_name: 'Polyfjord' }] });

    const res = await request(app).get('/api/users/testuser');
    expect(res.status).toBe(200);
    expect(Array.isArray(res.body.claimed_clips)).toBe(true);
    expect(res.body.claimed_clips[0]).toHaveProperty('id', '001');
    expect(res.body.claimed_clips[0]).toHaveProperty('display_credit', 'Polyfjord');
  });
});
