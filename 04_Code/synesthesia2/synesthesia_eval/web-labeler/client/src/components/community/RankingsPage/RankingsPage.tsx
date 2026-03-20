import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getLeaderboard, getClipRankings, getStats } from '../../../api';
import { LeaderboardEntry, ClipRanking, Stats } from '../../../types';
import { FlameIcon } from '../../brand/FlameIcon/FlameIcon';
import { Button, ScoreBar, Tabs, TabPanel } from '../../atoms';
import './RankingsPage.css';

const MEDALS = ['\u{1F3C6}', '\u{1F948}', '\u{1F949}'];

const RANKINGS_TABS = [
  { id: 'clips', label: 'Top Clips' },
  { id: 'raters', label: 'Top Raters' },
];

function clipDisplayName(filename: string): string {
  return filename.replace(/^\d+_/, '').replace(/\.[^.]+$/, '').replace(/_/g, ' ');
}

function scoreBar(score: number | null): React.ReactNode {
  if (score == null) return <span className="rank-na">&mdash;</span>;
  return <ScoreBar value={score} max={5} size="sm" />;
}

const RankingsPage: React.FC = () => {
  const [leaders, setLeaders] = useState<LeaderboardEntry[]>([]);
  const [clips, setClips] = useState<ClipRanking[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [tab, setTab] = useState<'clips' | 'raters'>('clips');
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([
      getLeaderboard().catch(() => []),
      getClipRankings().catch(() => []),
      getStats().catch(() => null),
    ]).then(([lb, cr, st]) => {
      setLeaders(lb);
      setClips(cr);
      setStats(st);
      setLoading(false);
    });
  }, []);

  const isLoggedIn = !!localStorage.getItem('token');

  return (
    <div className="rankings-page">
      <header className="rankings-header">
        <div className="rankings-header-inner">
          <FlameIcon size={44} className="rankings-logo" onClick={() => navigate('/')} />
          <p className="rankings-subtitle">Sound Visualization Rankings</p>
        </div>
        {!isLoggedIn && (
          <Button variant="primary" onClick={() => navigate('/')}>
            Join &amp; Rate
          </Button>
        )}
        {isLoggedIn && (
          <Button variant="primary" onClick={() => navigate('/')}>
            Go to Labeler
          </Button>
        )}
      </header>

      {stats && (
        <div className="rankings-stats-bar">
          <div className="rankings-stat">
            <span className="rankings-stat-value">{stats.total_clips}</span>
            <span className="rankings-stat-label">Clips</span>
          </div>
          <div className="rankings-stat">
            <span className="rankings-stat-value">{stats.labeled_human}</span>
            <span className="rankings-stat-label">Rated</span>
          </div>
          <div className="rankings-stat">
            <span className="rankings-stat-value">{leaders.length}</span>
            <span className="rankings-stat-label">Raters</span>
          </div>
          {stats.avg_scores?.harmony != null && (
            <div className="rankings-stat">
              <span className="rankings-stat-value">
                {((
                  (stats.avg_scores.sync_quality || 0) +
                  (stats.avg_scores.harmony || 0) +
                  (stats.avg_scores.aesthetic_quality || 0) +
                  (stats.avg_scores.motion_smoothness || 0)
                ) / 4).toFixed(1)}
              </span>
              <span className="rankings-stat-label">Avg Score</span>
            </div>
          )}
        </div>
      )}

      <div className="rankings-tabs">
        <Tabs
          tabs={RANKINGS_TABS}
          activeTab={tab}
          onChange={(id) => setTab(id as 'clips' | 'raters')}
          variant="underline"
        />
      </div>

      {loading ? (
        <div className="rankings-loading">Loading rankings...</div>
      ) : (
        <>
          <TabPanel id="clips" activeTab={tab}>
            <div className="rankings-content">
              {clips.length === 0 ? (
                <div className="rankings-empty">
                  No rated clips yet. Be the first to rate!
                </div>
              ) : (
                <div className="clip-rankings-list">
                  {clips.map((clip, i) => (
                    <div
                      key={clip.id}
                      className="clip-rank-card"
                      onClick={() => navigate(`/clip/${clip.id}`)}
                    >
                      <div className="clip-rank-position">
                        {MEDALS[i] || `#${i + 1}`}
                      </div>
                      <div className="clip-rank-info">
                        <div className="clip-rank-name">{clipDisplayName(clip.filename)}</div>
                        <div className="clip-rank-meta">
                          {clip.rater_count} rater{clip.rater_count !== 1 ? 's' : ''}
                        </div>
                      </div>
                      <div className="clip-rank-scores">
                        <div className="clip-rank-score-row">
                          <span className="clip-rank-dim">Sync</span>
                          {scoreBar(clip.avg_sync)}
                        </div>
                        <div className="clip-rank-score-row">
                          <span className="clip-rank-dim">Harm</span>
                          {scoreBar(clip.avg_harmony)}
                        </div>
                        <div className="clip-rank-score-row">
                          <span className="clip-rank-dim">Aesth</span>
                          {scoreBar(clip.avg_aesthetic)}
                        </div>
                        <div className="clip-rank-score-row">
                          <span className="clip-rank-dim">Motion</span>
                          {scoreBar(clip.avg_motion)}
                        </div>
                      </div>
                      <div className="clip-rank-overall">
                        <span className="clip-rank-overall-value">
                          {clip.avg_overall?.toFixed(1) ?? '\u2014'}
                        </span>
                        <span className="clip-rank-overall-label">overall</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </TabPanel>
          <TabPanel id="raters" activeTab={tab}>
            <div className="rankings-content">
              {leaders.length === 0 ? (
                <div className="rankings-empty">
                  No raters yet. Be the first!
                </div>
              ) : (
                <table className="rankings-raters-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Rater</th>
                      <th>Labels</th>
                    </tr>
                  </thead>
                  <tbody>
                    {leaders.map((entry, i) => (
                      <tr key={entry.username}>
                        <td className="rater-rank-pos">{MEDALS[i] || i + 1}</td>
                        <td className="rater-rank-name">{entry.username}</td>
                        <td className="rater-rank-count">{entry.total_labels}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </TabPanel>
        </>
      )}

      <footer className="rankings-footer">
        <p>
          Synesthesia — Psychoacoustic Visualization Rankings
        </p>
        {!isLoggedIn && (
          <Button variant="primary" onClick={() => navigate('/')}>
            Join the Community
          </Button>
        )}
      </footer>
    </div>
  );
};

export default RankingsPage;
