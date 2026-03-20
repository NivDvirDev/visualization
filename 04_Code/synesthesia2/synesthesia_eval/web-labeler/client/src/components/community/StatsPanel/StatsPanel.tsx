import React from 'react';
import { Stats } from '../../../types';
import { Card, CardContent } from '../../atoms';
import './StatsPanel.css';

interface StatsPanelProps {
  stats: Stats;
}

const StatsPanel: React.FC<StatsPanelProps> = ({ stats }) => {
  const { total_clips, labeled_human, labeled_auto } = stats;

  return (
    <div className="stats-panel">
      <div className="stats-cards">
        <Card variant="glass" padding="sm" className="stat-card">
          <CardContent>
            <span className="stat-value">{total_clips}</span>
            <span className="stat-label">Total</span>
          </CardContent>
        </Card>
        <Card variant="glass" padding="sm" className="stat-card">
          <CardContent>
            <span className="stat-value">{labeled_human}</span>
            <span className="stat-label">Human</span>
          </CardContent>
        </Card>
        <Card variant="glass" padding="sm" className="stat-card">
          <CardContent>
            <span className="stat-value">{labeled_auto}</span>
            <span className="stat-label">Auto</span>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default StatsPanel;
