-- Migration 005: Two-axis rating framework
-- Axis 1 (Perceptual): rename visual_audio_alignment → harmony
-- Axis 2 (Psychoacoustic): add 5 new dimensions

-- Rename visual_audio_alignment to harmony (Axis 1 change)
-- Only rename if old column exists (idempotent)
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'labels' AND column_name = 'visual_audio_alignment') THEN
    ALTER TABLE labels RENAME COLUMN visual_audio_alignment TO harmony;
  END IF;
END $$;

-- Add Axis 2: Psychoacoustic Accuracy dimensions (all nullable for backward compat)
ALTER TABLE labels ADD COLUMN IF NOT EXISTS pitch_accuracy SMALLINT CHECK (pitch_accuracy BETWEEN 1 AND 5);
ALTER TABLE labels ADD COLUMN IF NOT EXISTS rhythm_accuracy SMALLINT CHECK (rhythm_accuracy BETWEEN 1 AND 5);
ALTER TABLE labels ADD COLUMN IF NOT EXISTS dynamics_accuracy SMALLINT CHECK (dynamics_accuracy BETWEEN 1 AND 5);
ALTER TABLE labels ADD COLUMN IF NOT EXISTS timbre_accuracy SMALLINT CHECK (timbre_accuracy BETWEEN 1 AND 5);
ALTER TABLE labels ADD COLUMN IF NOT EXISTS melody_accuracy SMALLINT CHECK (melody_accuracy BETWEEN 1 AND 5);
