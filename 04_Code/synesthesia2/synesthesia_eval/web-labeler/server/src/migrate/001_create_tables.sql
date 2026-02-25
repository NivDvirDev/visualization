CREATE TABLE IF NOT EXISTS clips (
    id          VARCHAR(8) PRIMARY KEY,
    filename    TEXT NOT NULL,
    description TEXT,
    source      VARCHAR(64) DEFAULT 'youtube_playlist',
    categories  JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS labels (
    id                      SERIAL PRIMARY KEY,
    clip_id                 VARCHAR(8) NOT NULL REFERENCES clips(id),
    labeler                 VARCHAR(64) NOT NULL,
    sync_quality            SMALLINT CHECK (sync_quality BETWEEN 1 AND 5),
    visual_audio_alignment  SMALLINT CHECK (visual_audio_alignment BETWEEN 1 AND 5),
    aesthetic_quality        SMALLINT CHECK (aesthetic_quality BETWEEN 1 AND 5),
    motion_smoothness       SMALLINT CHECK (motion_smoothness BETWEEN 1 AND 5),
    notes                   TEXT,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(clip_id, labeler)
);

CREATE INDEX IF NOT EXISTS idx_labels_clip_id ON labels(clip_id);
CREATE INDEX IF NOT EXISTS idx_labels_labeler ON labels(labeler);
