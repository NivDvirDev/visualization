-- Add users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    username    VARCHAR(64) NOT NULL UNIQUE,
    email       VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Add user_id column to labels (nullable for auto labels)
ALTER TABLE labels ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id);

-- Create index on user_id
CREATE INDEX IF NOT EXISTS idx_labels_user_id ON labels(user_id);

-- Drop old unique constraint and recreate with user_id
-- The old constraint is UNIQUE(clip_id, labeler).
-- We keep it for auto-labels and add a new one for user labels.
-- Since we can't have partial unique indexes easily with the old constraint,
-- we'll use a unique index with a WHERE clause.
-- First, drop the old constraint if it exists:
ALTER TABLE labels DROP CONSTRAINT IF EXISTS labels_clip_id_labeler_key;

-- Unique constraint for auto-labels (no user_id)
CREATE UNIQUE INDEX IF NOT EXISTS idx_labels_clip_labeler_auto
  ON labels(clip_id, labeler) WHERE user_id IS NULL;

-- Unique constraint for user labels (one per user per clip)
CREATE UNIQUE INDEX IF NOT EXISTS idx_labels_clip_user
  ON labels(clip_id, user_id) WHERE user_id IS NOT NULL;
