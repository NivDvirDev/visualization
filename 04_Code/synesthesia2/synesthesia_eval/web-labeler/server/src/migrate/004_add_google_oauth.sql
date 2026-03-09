-- Add Google OAuth support
-- Add google_id column to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id VARCHAR(255) UNIQUE;

-- Make password_hash nullable (for Google-only users)
ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;
