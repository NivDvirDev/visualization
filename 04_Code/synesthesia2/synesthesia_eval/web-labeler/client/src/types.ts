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
  sync_quality?: number | null;
  visual_audio_alignment?: number | null;
  aesthetic_quality?: number | null;
  motion_smoothness?: number | null;
  notes?: string;
}

export interface ClipSummary {
  id: string;
  filename: string;
  description?: string;
  has_human_label: boolean;
  has_auto_label: boolean;
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
