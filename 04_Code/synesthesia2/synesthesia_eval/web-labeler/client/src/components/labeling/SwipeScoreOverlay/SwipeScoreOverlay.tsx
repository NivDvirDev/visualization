import React from 'react';
import './SwipeScoreOverlay.css';

const SCORE_META = [
  { label: 'Awful', emoji: '❌' },
  { label: 'Bad', emoji: '🟠' },
  { label: 'OK', emoji: '⭐' },
  { label: 'Good', emoji: '💚' },
  { label: 'Love it!', emoji: '✨' },
];

interface Props {
  score: number | null;  // 1-5 or null
  ratio: number;         // -1 to +1
}

const SwipeScoreOverlay: React.FC<Props> = ({ score, ratio }) => {
  if (score === null) return null;
  const meta = SCORE_META[score - 1];
  const opacity = Math.min(Math.abs(ratio) * 0.85, 0.85);
  const isPositive = ratio >= 0;
  return (
    <div
      className="swipe-overlay"
      style={{
        background: isPositive
          ? `rgba(46,125,50,${opacity * 0.5})`
          : `rgba(183,28,28,${opacity * 0.5})`,
        opacity: Math.abs(ratio) > 0.05 ? 1 : 0,
      }}
    >
      <div className="swipe-overlay-score">{score}</div>
      <div className="swipe-overlay-emoji">{meta.emoji}</div>
      <div className="swipe-overlay-label">{meta.label}</div>
    </div>
  );
};

export default SwipeScoreOverlay;
