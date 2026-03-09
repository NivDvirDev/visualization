import React from 'react';

interface ProgressBarProps {
  total: number;
  labeled: number;
  remaining: number;
}

const ProgressBar: React.FC<ProgressBarProps> = ({ total, labeled }) => {
  const pct = total > 0 ? Math.round((labeled / total) * 100) : 0;

  return (
    <div className="global-progress">
      <div className="global-progress-bar">
        <div
          className="global-progress-fill"
          style={{ width: pct + '%' }}
        />
      </div>
      <span className="global-progress-text">
        {labeled}/{total} labeled ({pct}%)
      </span>
    </div>
  );
};

export default ProgressBar;
