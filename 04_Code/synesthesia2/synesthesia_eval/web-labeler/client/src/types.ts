// Shared types for the Web Labeler application

export type DimensionKey =
  | 'sync_quality'
  | 'visual_audio_alignment'
  | 'aesthetic_quality'
  | 'motion_smoothness';

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
  sync_quality?: number | null;
  visual_audio_alignment?: number | null;
  aesthetic_quality?: number | null;
  motion_smoothness?: number | null;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ClipSummary {
  id: string;
  filename: string;
  description?: string;
  has_human_label: boolean;
  has_auto_label: boolean;
  rater_count: number;
}

export interface ClipDetail {
  id: string;
  filename: string;
  description?: string;
  labels?: Label[];
  [key: string]: unknown;
}

export interface AvgScores {
  sync_quality: number | null;
  visual_audio_alignment: number | null;
  aesthetic_quality: number | null;
  motion_smoothness: number | null;
}

export interface Stats {
  total_clips: number;
  labeled_human: number;
  labeled_auto: number;
  unlabeled: number;
  avg_scores?: AvgScores | null;
}

export interface LabelData {
  sync_quality: number | null;
  visual_audio_alignment: number | null;
  aesthetic_quality: number | null;
  motion_smoothness: number | null;
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
}

export type BadgeKey = 'first_label' | 'five_streak' | 'ten_labels' | 'completionist';

export interface MyStats {
  total_labels: number;
  clips_remaining: number;
  current_streak: number;
  badges: BadgeKey[];
}
