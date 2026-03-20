import React from 'react';
import { ScoreBar } from '../../atoms';
import './ProgressBar.css';

interface ProgressBarProps {
  total: number;
  labeled: number;
  remaining: number;
}

const ProgressBar: React.FC<ProgressBarProps> = ({ total, labeled }) => {
  const pct = total > 0 ? Math.round((labeled / total) * 100) : 0;

  return (
    <div className="global-progress">
      <ScoreBar value={labeled} max={total} showLabel={false} size="sm" className="global-progress-bar-atom" />
      <span className="global-progress-text">
        {labeled}/{total} labeled ({pct}%)
      </span>
    </div>
  );
};

export default ProgressBar;
