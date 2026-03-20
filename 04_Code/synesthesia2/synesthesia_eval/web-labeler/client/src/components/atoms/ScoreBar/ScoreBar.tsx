import React from 'react';
import './ScoreBar.css';

export type ScoreBarSize = 'sm' | 'md' | 'lg';

export interface ScoreBarProps {
  /** Value to display, in range [0, max] */
  value: number;
  max?: number;
  showLabel?: boolean;
  size?: ScoreBarSize;
  className?: string;
}

/**
 * ScoreBar — horizontal score visualization atom.
 * Replaces .score-bar-container / .score-bar-fill usages in RankingsPage + ClipDetailPage.
 */
export const ScoreBar: React.FC<ScoreBarProps> = ({
  value,
  max = 5,
  showLabel = true,
  size = 'md',
  className = '',
}) => {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  const label = value.toFixed(1);
  return (
    <div className={['atom-score-bar', `atom-score-bar--${size}`, className].filter(Boolean).join(' ')}>
      <div className="atom-score-bar__track">
        <div className="atom-score-bar__fill" style={{ width: `${pct}%` }} />
      </div>
      {showLabel && <span className="atom-score-bar__label">{label}</span>}
    </div>
  );
};
