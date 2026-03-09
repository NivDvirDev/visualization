const { Pool } = require('pg');
const path = require('path');

require('dotenv').config({ path: path.join(__dirname, '..', '.env') });

const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgres://synesthesia:synesthesia@localhost:5432/synesthesia_eval',
});

const PORT = parseInt(process.env.PORT, 10) || 3001;
const CLIPS_DIR = path.resolve(__dirname, '..', process.env.CLIPS_DIR || '../../data/clips');
const JWT_SECRET = process.env.JWT_SECRET || 'synesthesia-dev-secret-change-in-production';
const HF_TOKEN = process.env.HF_TOKEN || '';
const HF_DATASET = process.env.HF_DATASET || 'NivDvir/synesthesia-eval';
const USE_HUGGINGFACE = process.env.USE_HUGGINGFACE === 'true';
const GOOGLE_CLIENT_ID = process.env.GOOGLE_CLIENT_ID || '';

module.exports = { pool, PORT, CLIPS_DIR, JWT_SECRET, HF_TOKEN, HF_DATASET, USE_HUGGINGFACE, GOOGLE_CLIENT_ID };
