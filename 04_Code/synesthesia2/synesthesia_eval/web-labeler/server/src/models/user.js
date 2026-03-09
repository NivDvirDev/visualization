const bcrypt = require('bcryptjs');
const { pool } = require('../config');

const SALT_ROUNDS = 10;

const User = {
  async create({ username, email, password }) {
    const password_hash = await bcrypt.hash(password, SALT_ROUNDS);
    const { rows: [user] } = await pool.query(
      `INSERT INTO users (username, email, password_hash)
       VALUES ($1, $2, $3)
       RETURNING id, username, email, created_at`,
      [username, email, password_hash]
    );
    return user;
  },

  async findByEmail(email) {
    const { rows: [user] } = await pool.query(
      'SELECT * FROM users WHERE email = $1',
      [email]
    );
    return user || null;
  },

  async findByUsername(username) {
    const { rows: [user] } = await pool.query(
      'SELECT id, username, email, created_at FROM users WHERE username = $1',
      [username]
    );
    return user || null;
  },

  async findById(id) {
    const { rows: [user] } = await pool.query(
      'SELECT id, username, email, created_at FROM users WHERE id = $1',
      [id]
    );
    return user || null;
  },

  async verifyPassword(plaintext, hash) {
    if (!hash) return false;
    return bcrypt.compare(plaintext, hash);
  },

  async findByGoogleId(googleId) {
    const { rows: [user] } = await pool.query(
      'SELECT * FROM users WHERE google_id = $1',
      [googleId]
    );
    return user || null;
  },

  async createFromGoogle({ username, email, googleId }) {
    const { rows: [user] } = await pool.query(
      `INSERT INTO users (username, email, google_id)
       VALUES ($1, $2, $3)
       RETURNING id, username, email, created_at`,
      [username, email, googleId]
    );
    return user;
  },

  async linkGoogleId(userId, googleId) {
    await pool.query(
      'UPDATE users SET google_id = $1 WHERE id = $2',
      [googleId, userId]
    );
  },
};

module.exports = User;
