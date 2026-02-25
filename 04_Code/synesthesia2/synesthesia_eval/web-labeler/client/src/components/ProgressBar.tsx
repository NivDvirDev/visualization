import React from 'react';

interface ProgressBarProps {
  total: number;
  labeled: number;
  remaining: number;
}

const ProgressBar: React.FC<ProgressBarProps> = ({ total, labeled, remaining }) => {
  const pct = total > 0 ? Math.round((labeled / total) * 100) : 0;

  return (
    <div className="progress-bar-container">
      <div className="progress-bar">
        <div className="progress-bar-fill" style={{ width: pct + '%' }} />
      </div>
      <div className="progress-text">
        {labeled} / {total} labeled ({remaining} remaining)
      </div>
    </div>
  );
};

export default ProgressBar;
