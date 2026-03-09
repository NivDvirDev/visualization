const rateLimit = require('express-rate-limit');

// Strict limiter for auth endpoints (login, register, Google OAuth)
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 15,
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many requests, please try again later' },
});

// Limiter for label write operations (PUT/DELETE only)
const labelWriteLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 30,
  standardHeaders: true,
  legacyHeaders: false,
  skip: (req) => req.method === 'GET',
  message: { error: 'Too many requests, please try again later' },
});

// General limiter for all API routes
const globalLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 100,
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many requests, please try again later' },
});

module.exports = { authLimiter, labelWriteLimiter, globalLimiter };
