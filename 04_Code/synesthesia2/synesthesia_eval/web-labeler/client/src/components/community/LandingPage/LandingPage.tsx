import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { WellspringLogo } from '../../brand/WellspringLogo/WellspringLogo';
import { getStats, getClipRankings, getLeaderboard } from '../../../api';
import { Stats, ClipRanking, LeaderboardEntry } from '../../../types';
import './LandingPage.css';

const LandingPage: React.FC = () => {
  const [stats, setStats] = useState<Stats | null>(null);
  const [topClips, setTopClips] = useState<ClipRanking[]>([]);
  const [topRaters, setTopRaters] = useState<LeaderboardEntry[]>([]);

  useEffect(() => {
    getStats().then(setStats).catch(() => {});
    getClipRankings()
      .then((clips) => setTopClips(clips.slice(0, 4)))
      .catch(() => {});
    getLeaderboard()
      .then((entries) => setTopRaters(entries.slice(0, 3)))
      .catch(() => {});
  }, []);

  return (
    <div className="landing-page">
      {/* Hero */}
      <section className="landing-hero">
        <WellspringLogo size={120} animate />
        <h1 className="landing-hero-title">The Wellspring</h1>
        <p className="landing-hero-tagline">
          Rate how well visuals capture sound
        </p>
        <p className="landing-hero-sub">
          Watch audio visualizations. Rate them on sync, aesthetics, and motion.
          Compare your perception with AI. Climb the leaderboard.
        </p>
        <div className="landing-hero-cta">
          <Link to="/app" className="btn btn-join">Start Rating</Link>
          <Link to="/rankings" className="btn btn-outline">Explore Rankings</Link>
        </div>
      </section>

      {/* How it works */}
      <section className="landing-section">
        <h2 className="landing-section-title">How It Works</h2>
        <div className="landing-steps">
          <div className="landing-step">
            <span className="landing-step-num">1</span>
            <h3>Watch</h3>
            <p>Watch short audio visualization clips — sound transformed into visual art</p>
          </div>
          <div className="landing-step">
            <span className="landing-step-num">2</span>
            <h3>Rate</h3>
            <p>Score each clip on sync quality, aesthetics, harmony, and motion smoothness</p>
          </div>
          <div className="landing-step">
            <span className="landing-step-num">3</span>
            <h3>Compare</h3>
            <p>See how your ratings stack up against AI predictions and other raters</p>
          </div>
        </div>
      </section>

      {/* Live stats */}
      {stats && (
        <section className="landing-section">
          <h2 className="landing-section-title">The Dataset So Far</h2>
          <div className="landing-stats">
            <div className="landing-stat-card">
              <span className="landing-stat-value">{stats.total_clips}</span>
              <span className="landing-stat-label">Clips</span>
            </div>
            <div className="landing-stat-card">
              <span className="landing-stat-value">{stats.labeled_auto}</span>
              <span className="landing-stat-label">AI Ratings</span>
            </div>
            <div className="landing-stat-card">
              <span className="landing-stat-value">{stats.labeled_human}</span>
              <span className="landing-stat-label">Human Ratings</span>
            </div>
            <div className="landing-stat-card accent">
              <span className="landing-stat-value">{stats.unlabeled}</span>
              <span className="landing-stat-label">Waiting for You</span>
            </div>
          </div>
        </section>
      )}

      {/* Top rated clips */}
      {topClips.length > 0 && (
        <section className="landing-section">
          <h2 className="landing-section-title">Top Rated Clips</h2>
          <div className="landing-clips">
            {topClips.map((clip) => (
              <Link
                key={clip.id}
                to={`/clip/${clip.id}`}
                className="landing-clip-card"
              >
                <div className="landing-clip-score">
                  <span className="landing-clip-score-value">
                    {clip.avg_overall?.toFixed(1) || '—'}
                  </span>
                  <span className="landing-clip-score-label">overall</span>
                </div>
                <div className="landing-clip-info">
                  <span className="landing-clip-name">
                    {clip.filename?.replace(/\.mp4$/i, '').replace(/_/g, ' ')}
                  </span>
                  <span className="landing-clip-raters">
                    {clip.rater_count || 0} rating{(clip.rater_count || 0) !== 1 ? 's' : ''}
                  </span>
                </div>
              </Link>
            ))}
          </div>
          <div className="landing-section-cta">
            <Link to="/rankings" className="btn btn-outline">View All Rankings</Link>
          </div>
        </section>
      )}

      {/* Leaderboard teaser */}
      {topRaters.length > 0 && (
        <section className="landing-section">
          <h2 className="landing-section-title">Top Raters</h2>
          <div className="landing-leaderboard">
            {topRaters.map((entry, i) => (
              <div key={entry.username} className="landing-rater">
                <span className="landing-rater-medal">
                  {i === 0 ? '🏆' : i === 1 ? '🥈' : '🥉'}
                </span>
                <span className="landing-rater-name">{entry.username}</span>
                <span className="landing-rater-level">Lv.{entry.level}</span>
                <span className="landing-rater-labels">{entry.total_labels} ratings</span>
              </div>
            ))}
          </div>
          <div className="landing-section-cta">
            <Link to="/app" className="btn btn-join">Join the Leaderboard</Link>
          </div>
        </section>
      )}

      {/* Footer */}
      <footer className="landing-footer">
        <p>
          Part of the <strong>Synesthesia</strong> research project — building an open dataset
          for AI-powered audio visualization evaluation.
        </p>
      </footer>
    </div>
  );
};

export default LandingPage;
