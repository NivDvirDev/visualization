import type {
  ClipSummary,
  ClipDetail,
  Stats,
  User,
  Label,
  LeaderboardEntry,
  MyStats,
  ClipRanking,
  LabelData,
} from '../types';

// ── Mock Clips ──────────────────────────────────────────────────────────────

export const mockClips: ClipSummary[] = [
  {
    id: '001',
    filename: '001_Audio Visualization in Blender #1.mp4',
    description: 'Audio Visualization in Blender #1',
    has_human_label: true,
    has_auto_label: true,
    rater_count: 3,
  },
  {
    id: '002',
    filename: '002_Severance Main Theme Melody Visualization.mp4',
    description: 'Severance Main Theme Melody Visualization',
    has_human_label: true,
    has_auto_label: false,
    rater_count: 1,
  },
  {
    id: '003',
    filename: '003_Sound visualization Whales singing.mp4',
    description: 'Sound visualization - Whales singing',
    has_human_label: false,
    has_auto_label: true,
    rater_count: 0,
  },
  {
    id: '004',
    filename: '004_Ferrofluid art meets sound visualization.mp4',
    description: 'Ferrofluid art meets sound visualization',
    has_human_label: false,
    has_auto_label: false,
    rater_count: 0,
  },
  {
    id: '005',
    filename: '005_Processing Sound Visualization #4.mp4',
    description: 'Processing Sound Visualization #4',
    has_human_label: true,
    has_auto_label: true,
    rater_count: 2,
  },
];

// ── Mock Labels ─────────────────────────────────────────────────────────────

export const mockLabels: Label[] = [
  {
    labeler: 'testuser',
    username: 'testuser',
    user_id: 1,
    sync_quality: 4,
    harmony: 5,
    aesthetic_quality: 3,
    motion_smoothness: 4,
    pitch_accuracy: 3,
    rhythm_accuracy: 4,
    dynamics_accuracy: null,
    timbre_accuracy: null,
    melody_accuracy: null,
    notes: 'Great sync with the beat, colors are vivid.',
    created_at: '2026-03-01T14:30:00Z',
    updated_at: '2026-03-01T14:35:00Z',
  },
  {
    labeler: 'alice',
    username: 'alice',
    user_id: 2,
    sync_quality: 3,
    harmony: 4,
    aesthetic_quality: 4,
    motion_smoothness: 5,
    pitch_accuracy: null,
    rhythm_accuracy: null,
    dynamics_accuracy: null,
    timbre_accuracy: null,
    melody_accuracy: null,
    notes: '',
    created_at: '2026-03-02T10:15:00Z',
    updated_at: '2026-03-02T10:15:00Z',
  },
  {
    labeler: 'gemini-2.0-flash',
    username: undefined,
    user_id: null,
    sync_quality: 4,
    harmony: 4,
    aesthetic_quality: 3,
    motion_smoothness: 4,
    pitch_accuracy: 3,
    rhythm_accuracy: 4,
    dynamics_accuracy: 3,
    timbre_accuracy: 2,
    melody_accuracy: 3,
    notes: 'Auto-labeled by Gemini AI.',
    created_at: '2026-02-17T08:00:00Z',
  },
];

// ── Mock Clip Detail ────────────────────────────────────────────────────────

export const mockClipDetail: ClipDetail = {
  id: '001',
  filename: '001_Audio Visualization in Blender #1.mp4',
  description: 'Audio Visualization in Blender #1',
  labels: mockLabels,
};

// ── Mock Stats ──────────────────────────────────────────────────────────────

export const mockStats: Stats = {
  total_clips: 83,
  labeled_human: 29,
  labeled_auto: 29,
  unlabeled: 54,
  avg_scores: {
    sync_quality: 3.8,
    harmony: 3.5,
    aesthetic_quality: 3.9,
    motion_smoothness: 4.1,
  },
};

// ── Mock User ───────────────────────────────────────────────────────────────

export const mockUser: User = {
  id: 1,
  username: 'testuser',
  email: 'testuser@example.com',
  created_at: '2026-02-15T09:00:00Z',
};

// ── Mock Leaderboard ────────────────────────────────────────────────────────

export const mockLeaderboard: LeaderboardEntry[] = [
  { username: 'alice', total_labels: 42, level: 4, level_title: 'Psychoacoustic Analyst' },
  { username: 'testuser', total_labels: 29, level: 3, level_title: 'Synesthete' },
  { username: 'bob', total_labels: 17, level: 3, level_title: 'Synesthete' },
  { username: 'charlie', total_labels: 8, level: 2, level_title: 'Rhythm Watcher' },
  { username: 'diana', total_labels: 3, level: 1, level_title: 'Novice Listener' },
];

// ── Mock My Stats ───────────────────────────────────────────────────────────

export const mockMyStats: MyStats = {
  total_labels: 29,
  clips_remaining: 54,
  current_streak: 5,
  badges: ['first_label', 'ten_labels', 'five_streak'],
  level: 3,
  level_title: 'Synesthete',
  rank: 2,
  labels_this_week: 4,
};

export const mockMyStatsWithAllBadges: MyStats = {
  total_labels: 83,
  clips_remaining: 0,
  current_streak: 12,
  badges: ['first_label', 'five_streak', 'ten_labels', 'completionist'],
  level: 5,
  level_title: 'Master Synesthetist 👑',
  rank: 1,
  labels_this_week: 15,
};

// ── Mock Clip Rankings ──────────────────────────────────────────────────────

export const mockClipRankings: ClipRanking[] = [
  {
    id: '001',
    filename: '001_Audio Visualization in Blender #1.mp4',
    rater_count: 3,
    avg_sync: 4.2,
    avg_harmony: 4.5,
    avg_aesthetic: 4.0,
    avg_motion: 4.3,
    avg_overall: 4.25,
  },
  {
    id: '005',
    filename: '005_Processing Sound Visualization #4.mp4',
    rater_count: 2,
    avg_sync: 3.8,
    avg_harmony: 4.0,
    avg_aesthetic: 4.5,
    avg_motion: 3.5,
    avg_overall: 3.95,
  },
  {
    id: '002',
    filename: '002_Severance Main Theme Melody Visualization.mp4',
    rater_count: 1,
    avg_sync: 3.0,
    avg_harmony: 4.0,
    avg_aesthetic: 5.0,
    avg_motion: 4.0,
    avg_overall: 4.0,
  },
  {
    id: '008',
    filename: '008_Synth party blender audio visualization.mp4',
    rater_count: 2,
    avg_sync: 3.5,
    avg_harmony: 3.0,
    avg_aesthetic: 3.5,
    avg_motion: 4.0,
    avg_overall: 3.5,
  },
  {
    id: '012',
    filename: '012_Sound Visualization Emotional Bass.mp4',
    rater_count: 1,
    avg_sync: 2.0,
    avg_harmony: 3.0,
    avg_aesthetic: 4.0,
    avg_motion: 3.0,
    avg_overall: 3.0,
  },
];

// ── Mock Label Data (for form stories) ──────────────────────────────────────

export const mockExistingLabelPartial: Label = {
  labeler: 'testuser',
  username: 'testuser',
  user_id: 1,
  sync_quality: 4,
  harmony: null,
  aesthetic_quality: 3,
  motion_smoothness: null,
  pitch_accuracy: null,
  rhythm_accuracy: null,
  dynamics_accuracy: null,
  timbre_accuracy: null,
  melody_accuracy: null,
  notes: '',
};

export const mockExistingLabelFull: Label = {
  labeler: 'testuser',
  username: 'testuser',
  user_id: 1,
  sync_quality: 4,
  harmony: 5,
  aesthetic_quality: 3,
  motion_smoothness: 4,
  pitch_accuracy: 3,
  rhythm_accuracy: 4,
  dynamics_accuracy: 3,
  timbre_accuracy: 4,
  melody_accuracy: 5,
  notes: 'Excellent visualization with strong beat sync.',
};

export const mockAutoLabel: Label = {
  labeler: 'gemini-2.0-flash',
  user_id: null,
  sync_quality: 4,
  harmony: 4,
  aesthetic_quality: 3,
  motion_smoothness: 4,
  pitch_accuracy: 3,
  rhythm_accuracy: 4,
  dynamics_accuracy: 3,
  timbre_accuracy: 2,
  melody_accuracy: 3,
  notes: 'Auto-labeled by Gemini AI.',
};
