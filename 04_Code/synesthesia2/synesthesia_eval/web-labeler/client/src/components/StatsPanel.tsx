import React from 'react';
import ProgressBar from './ProgressBar';
import { Stats } from '../types';

interface StatsPanelProps {
  stats: Stats;
}

const StatsPanel: React.FC<StatsPanelProps> = ({ stats }) => {
  const { total_clips, labeled_human, labeled_auto, unlabeled, avg_scores } = stats;

  return (
    <div className="stats-panel">
      <div className="stats-cards">
        <div className="stat-card">
          <div className="stat-value">{total_clips}</div>
          <div className="stat-label">Total</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{labeled_human}</div>
          <div className="stat-label">Human</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{labeled_auto}</div>
          <div className="stat-label">Auto</div>
        </div>
      </div>

      <ProgressBar
        total={total_clips}
        labeled={labeled_human}
        remaining={unlabeled}
      />

      {avg_scores && avg_scores.sync_quality != null && (
        <div className="avg-scores">
          <span className="avg-score">
            Sync: <strong>{avg_scores.sync_quality}</strong>
          </span>
          <span className="avg-score">
            Align: <strong>{avg_scores.visual_audio_alignment}</strong>
          </span>
          <span className="avg-score">
            Aesth: <strong>{avg_scores.aesthetic_quality}</strong>
          </span>
          <span className="avg-score">
            Motion: <strong>{avg_scores.motion_smoothness}</strong>
          </span>
        </div>
      )}
    </div>
  );
};

export default StatsPanel;
