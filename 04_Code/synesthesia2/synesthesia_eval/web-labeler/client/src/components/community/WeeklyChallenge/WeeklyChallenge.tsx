import React, { useState, useEffect } from 'react';
import { getChallenge } from '../../../api';
import { Challenge } from '../../../types';
import './WeeklyChallenge.css';

interface WeeklyChallengeProps {
  labelsThisWeek: number;
}

const WeeklyChallenge: React.FC<WeeklyChallengeProps> = ({ labelsThisWeek }) => {
  const [challenge, setChallenge] = useState<Challenge | null>(null);

  useEffect(() => {
    getChallenge().catch(() => null).then((c) => { if (c) setChallenge(c); });
  }, []);

  if (!challenge) return null;

  const progress = Math.min(labelsThisWeek / challenge.goal, 1);
  const pct = Math.round(progress * 100);
  const done = labelsThisWeek >= challenge.goal;

  return (
    <div className={`weekly-challenge ${done ? 'weekly-challenge--done' : ''}`}>
      <div className="weekly-challenge-header">
        <span className="weekly-challenge-emoji">{challenge.emoji}</span>
        <div className="weekly-challenge-info">
          <span className="weekly-challenge-label">Weekly Challenge</span>
          <span className="weekly-challenge-title">{challenge.title}</span>
        </div>
        {done && <span className="weekly-challenge-check">✓</span>}
      </div>
      <p className="weekly-challenge-desc">{challenge.description}</p>
      <div className="weekly-challenge-bar-track">
        <div className="weekly-challenge-bar-fill" style={{ width: `${pct}%` }} />
      </div>
      <span className="weekly-challenge-count">
        {labelsThisWeek} / {challenge.goal}
      </span>
    </div>
  );
};

export default WeeklyChallenge;
