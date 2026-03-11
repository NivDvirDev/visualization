import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getClip, getConfig } from '../api';
import { ClipDetail, AppConfig } from '../types';
import VideoPlayer from './VideoPlayer';
import RatingsTable from './RatingsTable';
import { FlameIcon } from './FlameIcon';

function clipDisplayName(filename: string): string {
  return filename.replace(/^\d+_/, '').replace(/\.[^.]+$/, '').replace(/_/g, ' ');
}

const ClipDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [clip, setClip] = useState<ClipDetail | null>(null);
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    Promise.all([
      getClip(id),
      getConfig().catch(() => null),
    ]).then(([c, cfg]) => {
      if (!c || !c.id) {
        setError('Clip not found');
      } else {
        setClip(c);
        setConfig(cfg);
      }
      setLoading(false);
    }).catch(() => {
      setError('Failed to load clip');
      setLoading(false);
    });
  }, [id]);

  if (loading) {
    return (
      <div className="clip-detail-page">
        <div className="rankings-loading">Loading clip...</div>
      </div>
    );
  }

  if (error || !clip) {
    return (
      <div className="clip-detail-page">
        <div className="clip-detail-error">
          <h2>{error || 'Clip not found'}</h2>
          <button className="btn-join" onClick={() => navigate('/rankings')}>
            Back to Rankings
          </button>
        </div>
      </div>
    );
  }

  const labels = clip.labels || [];
  const userLabels = labels.filter(l => l.user_id != null);
  const autoLabels = labels.filter(l => l.user_id == null);
  const useHF = config?.useHuggingFace || false;
  const isLoggedIn = !!localStorage.getItem('token');

  // Compute averages
  const dims = ['sync_quality', 'harmony', 'aesthetic_quality', 'motion_smoothness'] as const;
  const avgs: Record<string, number | null> = {};
  for (const d of dims) {
    const vals = userLabels.map(l => l[d]).filter(v => v != null) as number[];
    avgs[d] = vals.length > 0 ? vals.reduce((a, b) => a + b, 0) / vals.length : null;
  }
  const validAvgs = Object.values(avgs).filter(v => v != null) as number[];
  const overallAvg = validAvgs.length > 0
    ? validAvgs.reduce((a, b) => a + b, 0) / validAvgs.length
    : null;

  return (
    <div className="clip-detail-page">
      <header className="rankings-header">
        <div className="rankings-header-inner">
          <FlameIcon size={44} className="rankings-logo" onClick={() => navigate('/')} />
          <p className="rankings-subtitle">{clipDisplayName(clip.filename)}</p>
        </div>
        <div className="clip-detail-nav">
          <button className="btn-join" onClick={() => navigate('/rankings')}>
            Rankings
          </button>
          {isLoggedIn && (
            <button className="btn-join" onClick={() => navigate('/')}>
              Rate This Clip
            </button>
          )}
          {!isLoggedIn && (
            <button className="btn-join" onClick={() => navigate('/')}>
              Join &amp; Rate
            </button>
          )}
        </div>
      </header>

      <div className="clip-detail-content">
        <div className="clip-detail-video">
          <VideoPlayer
            clipId={clip.id}
            filename={clip.filename}
            metadata={clip}
            useHuggingFace={useHF}
          />
        </div>

        <div className="clip-detail-sidebar">
          <div className="clip-detail-score-card">
            <div className="clip-detail-overall">
              <span className="clip-detail-overall-value">
                {overallAvg != null ? overallAvg.toFixed(1) : '\u2014'}
              </span>
              <span className="clip-detail-overall-label">Overall Score</span>
            </div>

            <div className="clip-detail-dims">
              {dims.map(d => {
                const label = d === 'sync_quality' ? 'Sync' :
                  d === 'harmony' ? 'Harmony' :
                  d === 'aesthetic_quality' ? 'Aesthetics' : 'Motion';
                return (
                  <div key={d} className="clip-detail-dim-row">
                    <span className="clip-detail-dim-name">{label}</span>
                    <div className="score-bar-container">
                      <div
                        className="score-bar-fill"
                        style={{ width: avgs[d] != null ? `${(avgs[d]! / 5) * 100}%` : '0%' }}
                      />
                      <span className="score-bar-label">
                        {avgs[d] != null ? avgs[d]!.toFixed(1) : '\u2014'}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="clip-detail-meta">
              {userLabels.length} human rating{userLabels.length !== 1 ? 's' : ''}
              {autoLabels.length > 0 && ` + ${autoLabels.length} AI`}
            </div>
          </div>
        </div>
      </div>

      <div className="clip-detail-ratings">
        <RatingsTable labels={labels} />
      </div>

      <footer className="rankings-footer">
        <p>Synesthesia — Psychoacoustic Visualization Rankings</p>
      </footer>
    </div>
  );
};

export default ClipDetailPage;
