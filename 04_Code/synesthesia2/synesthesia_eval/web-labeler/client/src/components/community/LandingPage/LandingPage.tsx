import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import WellspringLogo from '../../brand/WellspringLogo/WellspringLogo';
import { getStats, getClipRankings, getLeaderboard } from '../../../api';
import { Stats, ClipRanking, LeaderboardEntry } from '../../../types';
import { Button, Card, CardContent, Badge } from '../../atoms';
import './LandingPage.css';

const trackEvent = (name: string, params?: Record<string, unknown>) => {
  if (typeof window !== 'undefined' && (window as any).gtag) {
    (window as any).gtag('event', name, params);
  }
};

const LandingPage: React.FC = () => {
  const [stats, setStats] = useState<Stats | null>(null);
  const [topClips, setTopClips] = useState<ClipRanking[]>([]);
  const [topRaters, setTopRaters] = useState<LeaderboardEntry[]>([]);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Auto-redirect ad traffic straight to swipe mode
  useEffect(() => {
    if (searchParams.get('utm_source') || searchParams.get('gclid')) {
      trackEvent('ad_redirect_to_swipe', {
        utm_source: searchParams.get('utm_source'),
        utm_medium: searchParams.get('utm_medium'),
        utm_campaign: searchParams.get('utm_campaign'),
      });
      navigate('/swipe', { replace: true });
      return;
    }
  }, [searchParams, navigate]);

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
      <WellspringLogo />

      {/* How it works */}
      <section className="landing-section">
        <h2 className="landing-section-title">How It Works</h2>
        <div className="landing-steps">
          <div className="landing-step">
            <Badge variant="accent">1</Badge>
            <h3>Watch</h3>
            <p>Watch short audio visualization clips — sound transformed into visual art</p>
          </div>
          <div className="landing-step">
            <Badge variant="accent">2</Badge>
            <h3>Rate</h3>
            <p>Score each clip on sync quality, aesthetics, harmony, and motion smoothness</p>
          </div>
          <div className="landing-step">
            <Badge variant="accent">3</Badge>
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
            <Card variant="glass" padding="md" className="landing-stat-card-wrap">
              <CardContent>
                <span className="landing-stat-value">{stats.total_clips}</span>
                <span className="landing-stat-label">Clips</span>
              </CardContent>
            </Card>
            <Card variant="glass" padding="md" className="landing-stat-card-wrap">
              <CardContent>
                <span className="landing-stat-value">{stats.labeled_auto}</span>
                <span className="landing-stat-label">AI Ratings</span>
              </CardContent>
            </Card>
            <Card variant="glass" padding="md" className="landing-stat-card-wrap">
              <CardContent>
                <span className="landing-stat-value">{stats.labeled_human}</span>
                <span className="landing-stat-label">Human Ratings</span>
              </CardContent>
            </Card>
            <Card variant="glass" padding="md" className="landing-stat-card-wrap accent">
              <CardContent>
                <span className="landing-stat-value">{stats.total_users}</span>
                <span className="landing-stat-label">Human Raters</span>
              </CardContent>
            </Card>
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
            <Link to="/rankings" onClick={() => trackEvent('landing_cta_clicked', { cta: 'view_rankings' })}><Button variant="secondary">View All Rankings</Button></Link>
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
                <Badge variant="neutral">Lv.{entry.level}</Badge>
                <span className="landing-rater-labels">{entry.total_labels} ratings</span>
              </div>
            ))}
          </div>
          <div className="landing-section-cta">
            <Link to="/swipe" onClick={() => trackEvent('landing_cta_clicked', { cta: 'join_leaderboard' })}><Button variant="primary">Join the Leaderboard</Button></Link>
          </div>
        </section>
      )}

      {/* Footer */}
      <footer className="landing-footer">
        <p>
          Part of the <strong>Synesthesia</strong> research project — building an open dataset
          for AI-powered audio visualization evaluation.
        </p>
        <nav className="landing-footer-legal">
          <Link to="/privacy" className="landing-footer-legal-link">Privacy Policy</Link>
          <span className="landing-footer-legal-sep">·</span>
          <Link to="/terms" className="landing-footer-legal-link">Terms of Service</Link>
        </nav>
      </footer>
    </div>
  );
};

export default LandingPage;
