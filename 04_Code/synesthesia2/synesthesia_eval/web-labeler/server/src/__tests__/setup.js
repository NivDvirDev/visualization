const jwt = require('jsonwebtoken');

const JWT_SECRET = 'test-secret';

// Mock config before any app code loads
jest.mock('../config', () => ({
  pool: { query: jest.fn() },
  PORT: 3001,
  CLIPS_DIR: '/tmp/clips',
  JWT_SECRET,
  HF_TOKEN: '',
  HF_DATASET: 'test/dataset',
  USE_HUGGINGFACE: false,
  GOOGLE_CLIENT_ID: '',
}));

// Mock HuggingFace service
jest.mock('../services/huggingface', () => ({
  syncClips: jest.fn(),
  getVideoUrl: jest.fn((f) => `https://example.com/${f}`),
  pushLabels: jest.fn(),
}));

function generateToken(user = { id: 1, username: 'testuser', email: 'test@example.com' }) {
  return jwt.sign(user, JWT_SECRET, { expiresIn: '1h' });
}

function getApp() {
  // Clear module cache to get fresh app per test file
  const { app } = require('../index');
  return app;
}

module.exports = { generateToken, getApp, JWT_SECRET };
