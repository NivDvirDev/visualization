const request = require('supertest');

// Setup mocks before loading app
const { generateToken, getApp } = require('./setup');
const User = require('../models/user');

jest.mock('../models/user');

// Disable rate limiting in tests
jest.mock('../middleware/rateLimiter', () => ({
  authLimiter: (_req, _res, next) => next(),
  labelWriteLimiter: (_req, _res, next) => next(),
  globalLimiter: (_req, _res, next) => next(),
}));

const app = getApp();

describe('POST /api/auth/register', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns 201 with user and token on success', async () => {
    User.create.mockResolvedValue({ id: 1, username: 'alice', email: 'alice@example.com', created_at: new Date() });

    const res = await request(app)
      .post('/api/auth/register')
      .send({ username: 'alice', email: 'alice@example.com', password: 'secret123' });

    expect(res.status).toBe(201);
    expect(res.body.user.username).toBe('alice');
    expect(res.body.token).toBeDefined();
  });

  it('returns 400 when fields are missing', async () => {
    const res = await request(app)
      .post('/api/auth/register')
      .send({ username: 'alice' });

    expect(res.status).toBe(400);
    expect(res.body.error).toMatch(/required/);
  });

  it('returns 400 when password is too short', async () => {
    const res = await request(app)
      .post('/api/auth/register')
      .send({ username: 'alice', email: 'alice@example.com', password: '123' });

    expect(res.status).toBe(400);
    expect(res.body.error).toMatch(/6 characters/);
  });

  it('returns 409 on duplicate email', async () => {
    User.create.mockRejectedValue({ code: '23505', detail: 'Key (email)=(alice@example.com) already exists.' });

    const res = await request(app)
      .post('/api/auth/register')
      .send({ username: 'alice', email: 'alice@example.com', password: 'secret123' });

    expect(res.status).toBe(409);
    expect(res.body.error).toMatch(/email/i);
  });
});

describe('POST /api/auth/login', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns 200 with token on valid credentials', async () => {
    User.findByEmail.mockResolvedValue({ id: 1, username: 'alice', email: 'alice@example.com', password_hash: 'hashed', created_at: new Date() });
    User.verifyPassword.mockResolvedValue(true);

    const res = await request(app)
      .post('/api/auth/login')
      .send({ email: 'alice@example.com', password: 'secret123' });

    expect(res.status).toBe(200);
    expect(res.body.token).toBeDefined();
    expect(res.body.user.username).toBe('alice');
  });

  it('returns 401 on wrong password', async () => {
    User.findByEmail.mockResolvedValue({ id: 1, username: 'alice', email: 'alice@example.com', password_hash: 'hashed' });
    User.verifyPassword.mockResolvedValue(false);

    const res = await request(app)
      .post('/api/auth/login')
      .send({ email: 'alice@example.com', password: 'wrong' });

    expect(res.status).toBe(401);
  });

  it('returns 400 when fields are missing', async () => {
    const res = await request(app)
      .post('/api/auth/login')
      .send({ email: 'alice@example.com' });

    expect(res.status).toBe(400);
  });
});

describe('GET /api/auth/me', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns user profile with valid token', async () => {
    User.findById.mockResolvedValue({ id: 1, username: 'testuser', email: 'test@example.com', created_at: new Date() });
    const token = generateToken();

    const res = await request(app)
      .get('/api/auth/me')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(res.body.username).toBe('testuser');
  });

  it('returns 401 without token', async () => {
    const res = await request(app).get('/api/auth/me');

    expect(res.status).toBe(401);
  });
});
