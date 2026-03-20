import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getClip, getConfig } from '../../../api';
import { ClipDetail, AppConfig } from '../../../types';
import VideoPlayer from '../../labeling/VideoPlayer/VideoPlayer';
import RatingsTable from '../../labeling/RatingsTable/RatingsTable';
import ClaimCreatorPanel from '../../labeling/ClaimCreatorPanel/ClaimCreatorPanel';
import CreatorControls from '../../labeling/CreatorControls/CreatorControls';
import { FlameIcon } from '../../brand/FlameIcon/FlameIcon';
import { Button, ScoreBar } from '../../atoms';
import './ClipDetailPage.css';

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
  const [creatorInfo, setCreatorInfo] = useState<{
    claimed?: boolean;
    claimed_by_username?: string | null;
    display_credit?: string | null;
    display_link?: string | null;
    credit_visible?: boolean;
  }>({});

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
        setCreatorInfo({
          claimed: c.claimed,
          claimed_by_username: c.claimed_by_username,
          display_credit: c.display_credit,
          display_link: c.display_link,
          credit_visible: c.credit_visible,
        });
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
          <Button variant="primary" onClick={() => navigate('/rankings')}>
            Back to Rankings
          </Button>
        </div>
      </div>
    );
  }

  const labels = clip.labels || [];
  const userLabels = labels.filter(l => l.user_id != null);
  const autoLabels = labels.filter(l => l.user_id == null);
  const useHF = config?.useHuggingFace || false;
  const token = localStorage.getItem('token');
  const isLoggedIn = !!token;
  const currentUsername = (() => {
    try {
      const t = token;
      if (!t) return null;
      const payload = JSON.parse(atob(t.split('.')[1]));
      return payload.username || null;
    } catch {
      return null;
    }
  })();

  const claimed = creatorInfo.claimed ?? clip?.claimed;
  const claimedByUsername = creatorInfo.claimed_by_username ?? clip?.claimed_by_username;
  const displayCredit = creatorInfo.display_credit ?? clip?.display_credit;
  const displayLink = creatorInfo.display_link ?? clip?.display_link;
  const creditVisible = creatorInfo.credit_visible ?? clip?.credit_visible;

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
          {creditVisible && (displayCredit || clip.creator_name) && (
            <div className="creator-credit">
              Created by{' '}
              <a href={displayLink || clip.creator_url || undefined}>
                {displayCredit || clip.creator_name}
              </a>
              {claimed ? ' \u2705' : ''}
            </div>
          )}
          {!claimed && (
            <ClaimCreatorPanel
              clipId={clip.id}
              token={token}
              onClaimed={(info) => setCreatorInfo(info as typeof creatorInfo)}
            />
          )}
          {claimed && claimedByUsername === currentUsername && token && (
            <CreatorControls
              clipId={clip.id}
              initialCredit={displayCredit || null}
              initialLink={displayLink || null}
              initialVisible={creditVisible ?? true}
              token={token}
              onUpdate={(data) => setCreatorInfo(prev => ({
                ...prev,
                display_credit: data.display_credit,
                display_link: data.display_link,
                credit_visible: data.credit_visible,
              }))}
              onUnclaim={() => setCreatorInfo(prev => ({
                ...prev,
                claimed: false,
                claimed_by_username: null,
              }))}
            />
          )}
        </div>
        <div className="clip-detail-nav">
          <Button variant="secondary" onClick={() => navigate('/rankings')}>
            Rankings
          </Button>
          {isLoggedIn && (
            <Button variant="primary" onClick={() => navigate('/')}>
              Rate This Clip
            </Button>
          )}
          {!isLoggedIn && (
            <Button variant="primary" onClick={() => navigate('/')}>
              Join &amp; Rate
            </Button>
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
                    {avgs[d] != null
                      ? <ScoreBar value={avgs[d]!} max={5} size="sm" />
                      : <span className="rank-na">&mdash;</span>
                    }
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
