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

      {/* The Journey — 3 Pillars */}
      <section className="landing-section">
        <h2 className="landing-section-title">The Journey</h2>
        <div className="landing-pillars">
          <div className="landing-pillar">
            <div className="landing-pillar-icon">
              <svg width="48" height="48" viewBox="0 0 48 48" fill="none" aria-hidden="true">
                <circle cx="24" cy="24" r="20" stroke="currentColor" strokeWidth="1.5" opacity="0.3"/>
                <path d="M19 16v16l14-8z" fill="var(--color-accent)" opacity="0.9"/>
              </svg>
            </div>
            <h3 className="landing-pillar-title">Experience</h3>
            <p className="landing-pillar-desc">Watch sound become light. Rate audio-visual creations and discover how your perception compares to AI.</p>
            <Link to="/swipe" className="landing-pillar-link" onClick={() => trackEvent('landing_pillar_clicked', { pillar: 'experience' })}>
              <Button variant="secondary" size="sm">Start Watching</Button>
            </Link>
          </div>

          <div className="landing-pillar landing-pillar--coming">
            <Badge variant="accent" className="landing-pillar-badge">Coming Soon</Badge>
            <div className="landing-pillar-icon">
              <svg width="48" height="48" viewBox="0 0 48 48" fill="none" aria-hidden="true">
                <circle cx="24" cy="24" r="20" stroke="currentColor" strokeWidth="1.5" opacity="0.3"/>
                <path d="M24 12v12l8 4" stroke="var(--color-accent)" strokeWidth="2.5" strokeLinecap="round" opacity="0.9"/>
                <circle cx="24" cy="24" r="3" fill="var(--color-accent)" opacity="0.7"/>
              </svg>
            </div>
            <h3 className="landing-pillar-title">Create</h3>
            <p className="landing-pillar-desc">Shape your own harmony. Browser-based tools to transform sound into moving visual art — no installation needed.</p>
          </div>

          <div className="landing-pillar landing-pillar--coming">
            <Badge variant="accent" className="landing-pillar-badge">Coming Soon</Badge>
            <div className="landing-pillar-icon">
              <svg width="48" height="48" viewBox="0 0 48 48" fill="none" aria-hidden="true">
                <circle cx="24" cy="24" r="20" stroke="currentColor" strokeWidth="1.5" opacity="0.3"/>
                <circle cx="18" cy="22" r="4" stroke="var(--color-accent)" strokeWidth="2" opacity="0.8"/>
                <circle cx="30" cy="22" r="4" stroke="var(--color-accent)" strokeWidth="2" opacity="0.8"/>
                <path d="M14 32c2-3 6-5 10-5s8 2 10 5" stroke="var(--color-accent)" strokeWidth="2" strokeLinecap="round" opacity="0.6"/>
              </svg>
            </div>
            <h3 className="landing-pillar-title">Connect</h3>
            <p className="landing-pillar-desc">Find your resonance. Share techniques, learn from others, and join a global community of audio-visual creators.</p>
          </div>
        </div>
      </section>

      {/* Featured Creations */}
      {topClips.length > 0 && (
        <section className="landing-section" id="featured">
          <h2 className="landing-section-title">Featured Creations</h2>
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
            <Link to="/rankings" onClick={() => trackEvent('landing_cta_clicked', { cta: 'explore_all' })}>
              <Button variant="secondary">Explore All</Button>
            </Link>
          </div>
        </section>
      )}

      {/* Live Pulse */}
      {stats && (
        <section className="landing-section">
          <h2 className="landing-section-title">Live Pulse</h2>
          <div className="landing-stats">
            <Card variant="glass" padding="md" className="landing-stat-card-wrap">
              <CardContent>
                <span className="landing-stat-value">{stats.total_clips}</span>
                <span className="landing-stat-label">Creations</span>
              </CardContent>
            </Card>
            <Card variant="glass" padding="md" className="landing-stat-card-wrap">
              <CardContent>
                <span className="landing-stat-value">{(stats.labeled_auto || 0) + (stats.labeled_human || 0)}</span>
                <span className="landing-stat-label">Ratings Given</span>
              </CardContent>
            </Card>
            <Card variant="glass" padding="md" className="landing-stat-card-wrap accent">
              <CardContent>
                <span className="landing-stat-value">{stats.total_users}</span>
                <span className="landing-stat-label">Active Members</span>
              </CardContent>
            </Card>
          </div>
        </section>
      )}

      {/* Top Raters */}
      {topRaters.length > 0 && (
        <section className="landing-section">
          <h2 className="landing-section-title">Top Contributors</h2>
          <div className="landing-leaderboard">
            {topRaters.map((entry, i) => (
              <div key={entry.username} className="landing-rater">
                <span className="landing-rater-medal">
                  {i === 0 ? '\u{1F3C6}' : i === 1 ? '\u{1F948}' : '\u{1F949}'}
                </span>
                <span className="landing-rater-name">{entry.username}</span>
                <Badge variant="neutral">Lv.{entry.level}</Badge>
                <span className="landing-rater-labels">{entry.total_labels} ratings</span>
              </div>
            ))}
          </div>
          <div className="landing-section-cta">
            <Link to="/swipe" onClick={() => trackEvent('landing_cta_clicked', { cta: 'join_leaderboard' })}>
              <Button variant="primary">Join the Leaderboard</Button>
            </Link>
          </div>
        </section>
      )}

      {/* The Call — Vision statement */}
      <section className="landing-call">
        <div className="landing-call-content">
          <h2 className="landing-call-title">A Collective Journey</h2>
          <p className="landing-call-text">
            This is a collective journey whose resonance goes back to the first ancient dance
            humans ever made. Once again we raise a global call — come together to see what
            beautiful harmony we could reach through proper coordination between sound and
            moving image. Now as we stand on new ground of capabilities.
          </p>
          <Link to="/swipe" onClick={() => trackEvent('landing_cta_clicked', { cta: 'begin_journey' })}>
            <Button variant="primary" size="lg">Begin Your Journey</Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <p>
          Built by <strong>Niv Dvir</strong> — part of the <strong>Synesthesia</strong> research project.
        </p>
        <nav className="landing-footer-legal">
          <Link to="/privacy" className="landing-footer-legal-link">Privacy Policy</Link>
          <span className="landing-footer-legal-sep">&middot;</span>
          <Link to="/terms" className="landing-footer-legal-link">Terms of Service</Link>
        </nav>
      </footer>
    </div>
  );
};

export default LandingPage;
