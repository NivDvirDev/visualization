const jwt = require('jsonwebtoken');
const { JWT_SECRET } = require('../config');

function authRequired(req, res, next) {
  const header = req.headers.authorization;
  if (!header || !header.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Authentication required' });
  }

  const token = header.slice(7);
  try {
    const payload = jwt.verify(token, JWT_SECRET);
    req.user = { id: payload.id, username: payload.username, email: payload.email };
    next();
  } catch {
    return res.status(401).json({ error: 'Invalid or expired token' });
  }
}

function authOptional(req, _res, next) {
  const header = req.headers.authorization;
  if (header && header.startsWith('Bearer ')) {
    const token = header.slice(7);
    try {
      const payload = jwt.verify(token, JWT_SECRET);
      req.user = { id: payload.id, username: payload.username, email: payload.email };
    } catch {
      // Ignore invalid tokens for optional auth
    }
  }
  next();
}

module.exports = { authRequired, authOptional };
