-- Migration 007: Add overall_impression for swipe mode ratings
ALTER TABLE labels
  ADD COLUMN IF NOT EXISTS overall_impression SMALLINT
    CHECK (overall_impression BETWEEN 1 AND 5);
