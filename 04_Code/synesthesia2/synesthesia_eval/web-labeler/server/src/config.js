const { Pool } = require('pg');
const path = require('path');

require('dotenv').config({ path: path.join(__dirname, '..', '.env') });

const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgres://synesthesia:synesthesia@localhost:5432/synesthesia_eval',
});

const PORT = parseInt(process.env.PORT, 10) || 3001;
const CLIPS_DIR = path.resolve(__dirname, '..', process.env.CLIPS_DIR || '../../data/clips');

module.exports = { pool, PORT, CLIPS_DIR };
