import React from 'react';
import './ShareCard.css';

interface ShareCardProps {
  username: string;
  totalLabels: number;
  rank: number;
  onClose: () => void;
}

const ShareCard: React.FC<ShareCardProps> = ({ username, totalLabels, rank, onClose }) => {
  const siteUrl = 'https://synesthesia-labeler.onrender.com';
  const tweetText = `I rated ${totalLabels} audio visualizations on The Wellspring — I'm rank #${rank} on the leaderboard! 🎧\n\nRate & compete: ${siteUrl}`;
  const tweetUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(tweetText)}`;

  return (
    <div className="share-card-overlay" onClick={onClose}>
      <div className="share-card" onClick={(e) => e.stopPropagation()}>
        <button className="share-card-close" onClick={onClose}>✕</button>
        <div className="share-card-content">
          <div className="share-card-emoji">🎧</div>
          <h3 className="share-card-title">Label saved!</h3>
          <p className="share-card-username">@{username}</p>
          <div className="share-card-stats">
            <div className="share-stat">
              <span className="share-stat-value">{totalLabels}</span>
              <span className="share-stat-label">Labels</span>
            </div>
            <div className="share-stat">
              <span className="share-stat-value">#{rank}</span>
              <span className="share-stat-label">Rank</span>
            </div>
          </div>
          <a
            className="share-card-tweet-btn"
            href={tweetUrl}
            target="_blank"
            rel="noopener noreferrer"
          >
            Share on X / Twitter
          </a>
          <button className="share-card-continue" onClick={onClose}>
            Continue Rating →
          </button>
        </div>
      </div>
    </div>
  );
};

export default ShareCard;
