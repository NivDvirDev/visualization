// Shared types for the Web Labeler application

// Axis 1: Perceptual/Emotional
export type PerceptualDimensionKey =
  | 'sync_quality'
  | 'harmony'
  | 'aesthetic_quality'
  | 'motion_smoothness';

// Axis 2: Psychoacoustic Accuracy
export type PsychoacousticDimensionKey =
  | 'pitch_accuracy'
  | 'rhythm_accuracy'
  | 'dynamics_accuracy'
  | 'timbre_accuracy'
  | 'melody_accuracy';

export type DimensionKey = PerceptualDimensionKey | PsychoacousticDimensionKey;

export type RatingValue = 1 | 2 | 3 | 4 | 5;

export type ClipMode = 'unlabeled' | 'all' | 'labeled';

export interface Dimension {
  key: DimensionKey;
  label: string;
  descriptions: Record<RatingValue, string>;
}

export interface Label {
  labeler: string;
  username?: string;
  user_id?: number | null;
  // Axis 1: Perceptual
  sync_quality?: number | null;
  harmony?: number | null;
  aesthetic_quality?: number | null;
  motion_smoothness?: number | null;
  // Axis 2: Psychoacoustic
  pitch_accuracy?: number | null;
  rhythm_accuracy?: number | null;
  dynamics_accuracy?: number | null;
  timbre_accuracy?: number | null;
  melody_accuracy?: number | null;
  // Swipe mode
  overall_impression?: number | null;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ClipSummary {
  id: string;
  filename: string;
  description?: string;
  youtube_video_id?: string;
  has_human_label: boolean;
  has_auto_label: boolean;
  rater_count: number;
  is_hot?: boolean;
  video_url?: string;
  creator_name?: string | null;
  creator_url?: string | null;
  claimed?: boolean;
  claimed_by_username?: string | null;
  display_credit?: string | null;
  display_link?: string | null;
  credit_visible?: boolean;
}

export interface ClaimedClip {
  id: string;
  filename: string;
  display_credit: string | null;
}

export interface TastePersonality {
  key: string;
  emoji: string;
  label: string;
  desc: string;
}

export interface TasteProfile {
  perceptual: {
    sync_quality: number | null;
    harmony: number | null;
    aesthetic_quality: number | null;
    motion_smoothness: number | null;
  };
  psychoacoustic: {
    pitch_accuracy: number | null;
    rhythm_accuracy: number | null;
    dynamics_accuracy: number | null;
    timbre_accuracy: number | null;
    melody_accuracy: number | null;
  };
  personality: TastePersonality | null;
  label_count: number;
}

export interface UserProfile {
  username: string;
  created_at: string;
  total_labels: number;
  rank: number;
  level: number;
  level_title: string;
  badges: BadgeKey[];
  perceptual: TasteProfile['perceptual'];
  personality: TastePersonality | null;
  claimed_clips?: ClaimedClip[];
}

export interface ClipDetail {
  id: string;
  filename: string;
  description?: string;
  labels?: Label[];
  creator_name?: string | null;
  creator_url?: string | null;
  claimed?: boolean;
  claimed_by_username?: string | null;
  display_credit?: string | null;
  display_link?: string | null;
  credit_visible?: boolean;
  [key: string]: unknown;
}

export interface AvgScores {
  sync_quality: number | null;
  harmony: number | null;
  aesthetic_quality: number | null;
  motion_smoothness: number | null;
}

export interface Stats {
  total_clips: number;
  labeled_human: number;
  labeled_auto: number;
  unlabeled: number;
  total_users: number;
  recent_users_7d: number;
  avg_scores?: AvgScores | null;
}

export interface LabelData {
  // Axis 1: Perceptual
  sync_quality: number | null;
  harmony: number | null;
  aesthetic_quality: number | null;
  motion_smoothness: number | null;
  // Axis 2: Psychoacoustic (optional)
  pitch_accuracy?: number | null;
  rhythm_accuracy?: number | null;
  dynamics_accuracy?: number | null;
  timbre_accuracy?: number | null;
  melody_accuracy?: number | null;
  // Swipe mode
  overall_impression?: number | null;
  notes: string;
}

export interface SaveLabelPayload extends LabelData {
  labeler: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  created_at?: string;
}

export interface AuthResponse {
  user: User;
  token: string;
}

export interface AppConfig {
  useHuggingFace: boolean;
  googleClientId: string | null;
}

export interface LeaderboardEntry {
  username: string;
  total_labels: number;
  level: number;
  level_title: string;
}

export type BadgeKey = 'first_label' | 'five_streak' | 'ten_labels' | 'completionist' | 'consensus_rater';

export interface MyStats {
  total_labels: number;
  clips_remaining: number;
  current_streak: number;
  badges: BadgeKey[];
  level: number;
  level_title: string;
  rank: number;
  labels_this_week: number;
}

export interface Challenge {
  emoji: string;
  title: string;
  description: string;
  goal: number;
}

export interface ClipRanking {
  id: string;
  filename: string;
  rater_count: number;
  avg_sync: number | null;
  avg_harmony: number | null;
  avg_aesthetic: number | null;
  avg_motion: number | null;
  avg_overall: number | null;
}
