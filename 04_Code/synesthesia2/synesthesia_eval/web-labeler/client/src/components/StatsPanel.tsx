import React from 'react';
import { Stats } from '../types';

interface StatsPanelProps {
  stats: Stats;
}

const StatsPanel: React.FC<StatsPanelProps> = ({ stats }) => {
  const { total_clips, labeled_human, labeled_auto } = stats;

  return (
    <div className="stats-panel">
      <div className="stats-cards">
        <div className="stat-card">
          <span className="stat-value">{total_clips}</span>
          <span className="stat-label">Total</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{labeled_human}</span>
          <span className="stat-label">Human</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{labeled_auto}</span>
          <span className="stat-label">Auto</span>
        </div>
      </div>
    </div>
  );
};

export default StatsPanel;
