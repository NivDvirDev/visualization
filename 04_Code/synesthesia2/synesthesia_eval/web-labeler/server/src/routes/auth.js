const { Router } = require('express');
const jwt = require('jsonwebtoken');
const { OAuth2Client } = require('google-auth-library');
const User = require('../models/user');
const { JWT_SECRET, GOOGLE_CLIENT_ID } = require('../config');
const { authRequired } = require('../middleware/auth');

const router = Router();

function signToken(user) {
  return jwt.sign(
    { id: user.id, username: user.username, email: user.email },
    JWT_SECRET,
    { expiresIn: '7d' }
  );
}

// POST /api/auth/register
router.post('/register', async (req, res, next) => {
  try {
    const { username, email, password } = req.body;
    if (!username || !email || !password) {
      return res.status(400).json({ error: 'username, email, and password are required' });
    }
    if (password.length < 6) {
      return res.status(400).json({ error: 'Password must be at least 6 characters' });
    }
    const user = await User.create({ username, email, password });
    const token = signToken(user);
    res.status(201).json({ user, token });
  } catch (err) {
    if (err.code === '23505') {
      const detail = err.detail || '';
      if (detail.includes('email')) {
        return res.status(409).json({ error: 'Email already registered' });
      }
      if (detail.includes('username')) {
        return res.status(409).json({ error: 'Username already taken' });
      }
      return res.status(409).json({ error: 'User already exists' });
    }
    next(err);
  }
});

// POST /api/auth/login
router.post('/login', async (req, res, next) => {
  try {
    const { email, password } = req.body;
    if (!email || !password) {
      return res.status(400).json({ error: 'email and password are required' });
    }
    const user = await User.findByEmail(email);
    if (!user) {
      return res.status(401).json({ error: 'Invalid email or password' });
    }
    const valid = await User.verifyPassword(password, user.password_hash);
    if (!valid) {
      return res.status(401).json({ error: 'Invalid email or password' });
    }
    const token = signToken({ id: user.id, username: user.username, email: user.email });
    res.json({
      user: { id: user.id, username: user.username, email: user.email, created_at: user.created_at },
      token,
    });
  } catch (err) {
    next(err);
  }
});

// POST /api/auth/google
router.post('/google', async (req, res, next) => {
  try {
    if (!GOOGLE_CLIENT_ID) {
      return res.status(501).json({ error: 'Google Sign-In is not configured' });
    }

    const { credential } = req.body;
    if (!credential) {
      return res.status(400).json({ error: 'credential is required' });
    }

    // Verify the Google ID token
    const client = new OAuth2Client(GOOGLE_CLIENT_ID);
    let ticket;
    try {
      ticket = await client.verifyIdToken({
        idToken: credential,
        audience: GOOGLE_CLIENT_ID,
      });
    } catch {
      return res.status(401).json({ error: 'Invalid Google token' });
    }

    const payload = ticket.getPayload();
    const googleId = payload.sub;
    const email = payload.email;
    const name = payload.name || email.split('@')[0];

    // Check if user exists with this Google ID
    let user = await User.findByGoogleId(googleId);
    if (user) {
      const token = signToken({ id: user.id, username: user.username, email: user.email });
      return res.json({
        user: { id: user.id, username: user.username, email: user.email, created_at: user.created_at },
        token,
      });
    }

    // Check if user exists with this email (link Google account)
    user = await User.findByEmail(email);
    if (user) {
      await User.linkGoogleId(user.id, googleId);
      const token = signToken({ id: user.id, username: user.username, email: user.email });
      return res.json({
        user: { id: user.id, username: user.username, email: user.email, created_at: user.created_at },
        token,
      });
    }

    // Create new user from Google profile
    // Generate a unique username from the Google name
    let username = name.toLowerCase().replace(/[^a-z0-9]/g, '');
    if (!username) username = 'user';
    // Check if username is taken, append random digits if so
    const existingUser = await User.findByUsername(username);
    if (existingUser) {
      username = username + Math.floor(Math.random() * 10000);
    }

    user = await User.createFromGoogle({ username, email, googleId });
    const token = signToken(user);
    res.status(201).json({ user, token });
  } catch (err) {
    next(err);
  }
});

// GET /api/auth/me
router.get('/me', authRequired, async (req, res, next) => {
  try {
    const user = await User.findById(req.user.id);
    if (!user) return res.status(404).json({ error: 'User not found' });
    res.json(user);
  } catch (err) {
    next(err);
  }
});

module.exports = router;
