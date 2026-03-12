import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getClips, getClip, getStats, saveLabel, getMe, getConfig, getMyStats } from '../../../api';
import ClipList from '../../labeling/ClipList/ClipList';
import VideoPlayer from '../../labeling/VideoPlayer/VideoPlayer';
import LabelForm from '../../labeling/LabelForm/LabelForm';
import RatingsTable from '../../labeling/RatingsTable/RatingsTable';
import ProgressBar from '../ProgressBar/ProgressBar';
import LoginPage from '../../auth/LoginPage/LoginPage';
import Leaderboard from '../../community/Leaderboard/Leaderboard';
import ShareCard from '../../community/ShareCard/ShareCard';
import Header from '../Header/Header';
import Footer from '../Footer/Footer';
import { ClipSummary, ClipDetail, ClipMode, Label, LabelData, Stats, User, AppConfig, MyStats } from '../../../types';
import './LabelerApp.css';

const LabelerApp: React.FC = () => {
  const [clips, setClips] = useState<ClipSummary[]>([]);
  const [selectedClipId, setSelectedClipId] = useState<string | null>(null);
  const [selectedClip, setSelectedClip] = useState<ClipDetail | null>(null);
  const [mode, setMode] = useState<ClipMode>('unlabeled');
  const [stats, setStats] = useState<Stats | null>(null);
  const [saving, setSaving] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [appConfig, setAppConfig] = useState<AppConfig | null>(null);
  const [showRatings, setShowRatings] = useState(false);
  const [showLeaderboard, setShowLeaderboard] = useState(false);
  const [shareStats, setShareStats] = useState<MyStats | null>(null);
  const navigate = useNavigate();

  const loadClips = useCallback((m: ClipMode) => {
    getClips(m).then((c) => setClips(c));
  }, []);

  const loadStats = useCallback(() => {
    getStats().then((s) => setStats(s));
  }, []);

  const loadClip = useCallback((id: string) => {
    getClip(id).then((clip) => {
      setSelectedClipId(id);
      setSelectedClip(clip);
    });
  }, []);

  // Auth check on mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      setAuthChecked(true);
      return;
    }
    getMe()
      .then((u) => {
        setUser(u);
        setAuthChecked(true);
      })
      .catch(() => {
        localStorage.removeItem('token');
        setAuthChecked(true);
      });
  }, []);

  // Load config on mount
  useEffect(() => {
    getConfig().then((c) => setAppConfig(c)).catch(() => {});
  }, []);

  // Load clips and stats when user becomes available or mode changes
  useEffect(() => {
    if (user) {
      loadClips(mode);
      loadStats();
    }
  }, [user, mode, loadClips, loadStats]);

  const handleLogin = useCallback((u: User, token: string) => {
    localStorage.setItem('token', token);
    setUser(u);
  }, []);

  const handleLogout = useCallback(() => {
    localStorage.removeItem('token');
    setUser(null);
    setClips([]);
    setSelectedClipId(null);
    setSelectedClip(null);
    setStats(null);
  }, []);

  const handleModeChange = useCallback((m: ClipMode) => {
    setMode(m);
  }, []);

  const handleSelect = useCallback((id: string) => {
    loadClip(id);
  }, [loadClip]);

  const handleSave = useCallback((clipId: string, labelData: LabelData) => {
    setSaving(true);
    saveLabel(clipId, labelData)
      .then(() => {
        setSaving(false);
        loadClips(mode);
        loadStats();
        loadClip(clipId);
        // Show share card with updated stats (every 5 labels)
        getMyStats().then((ms) => {
          if (ms.total_labels % 5 === 0 || ms.total_labels === 1) {
            setShareStats(ms);
          }
        }).catch(() => {});
        setClips((prevClips) => {
          setSelectedClipId((prevId) => {
            const idx = prevClips.findIndex((c) => c.id === prevId);
            if (idx >= 0 && idx < prevClips.length - 1) {
              const nextId = prevClips[idx + 1].id;
              getClip(nextId).then((clip) => {
                setSelectedClipId(nextId);
                setSelectedClip(clip);
              });
            }
            return prevId;
          });
          return prevClips;
        });
      })
      .catch((err) => {
        setSaving(false);
        alert(err.message || 'Save failed');
      });
  }, [mode, loadClips, loadStats, loadClip]);

  const handleSkip = useCallback(() => {
    setClips((prevClips) => {
      setSelectedClipId((prevId) => {
        const idx = prevClips.findIndex((c) => c.id === prevId);
        if (idx >= 0 && idx < prevClips.length - 1) {
          const nextId = prevClips[idx + 1].id;
          loadClip(nextId);
        }
        return prevId;
      });
      return prevClips;
    });
  }, [loadClip]);

  const goToPrev = useCallback(() => {
    setClips((prevClips) => {
      setSelectedClipId((prevId) => {
        const idx = prevClips.findIndex((c) => c.id === prevId);
        if (idx > 0) {
          loadClip(prevClips[idx - 1].id);
        }
        return prevId;
      });
      return prevClips;
    });
  }, [loadClip]);

  const goToNext = useCallback(() => {
    setClips((prevClips) => {
      setSelectedClipId((prevId) => {
        const idx = prevClips.findIndex((c) => c.id === prevId);
        if (idx >= 0 && idx < prevClips.length - 1) {
          loadClip(prevClips[idx + 1].id);
        }
        return prevId;
      });
      return prevClips;
    });
  }, [loadClip]);

  const handleRandom = useCallback(() => {
    setClips((prevClips) => {
      if (prevClips.length === 0) return prevClips;
      const clip = prevClips[Math.floor(Math.random() * prevClips.length)];
      loadClip(clip.id);
      return prevClips;
    });
  }, [loadClip]);

  if (!authChecked) {
    return (
      <div className="app">
        <div className="empty-state"><p>Loading...</p></div>
      </div>
    );
  }

  if (!user) {
    return <LoginPage onLogin={handleLogin} googleClientId={appConfig?.googleClientId || null} />;
  }

  const myLabel: Label | undefined = selectedClip
    ? (selectedClip.labels || []).find((l) => l.username === user.username)
    : undefined;
  const autoLabel: Label | undefined = selectedClip
    ? (selectedClip.labels || []).find((l) => l.user_id == null)
    : undefined;
  const useHF = appConfig?.useHuggingFace || false;

  return (
    <div className="app">
      {shareStats && user && (
        <ShareCard
          username={user.username}
          totalLabels={shareStats.total_labels}
          rank={shareStats.rank}
          onClose={() => setShareStats(null)}
        />
      )}

      {stats && (
        <ProgressBar
          total={stats.total_clips}
          labeled={stats.labeled_human}
          remaining={stats.unlabeled}
        />
      )}

      <Header
        stats={stats}
        user={user}
        showLeaderboard={showLeaderboard}
        onToggleLeaderboard={() => setShowLeaderboard(!showLeaderboard)}
        onLogout={handleLogout}
        onNavigateRankings={() => navigate('/rankings')}
      />

      <main className="app-main">
        {showLeaderboard ? (
          <Leaderboard user={user} />
        ) : (
          <>
            <ClipList
              clips={clips}
              selectedClipId={selectedClipId}
              onSelect={handleSelect}
              mode={mode}
              onModeChange={handleModeChange}
              onRandom={handleRandom}
            />

            {selectedClip ? (
              <div className="labeling-layout">
                <div className="workspace-video">
                  <VideoPlayer
                    clipId={selectedClip.id}
                    filename={selectedClip.filename}
                    metadata={selectedClip}
                    useHuggingFace={useHF}
                  />
                  <button
                    className="ratings-toggle"
                    onClick={() => setShowRatings(!showRatings)}
                  >
                    {showRatings ? '\u25BE All Ratings' : '\u25B8 All Ratings'}
                    {selectedClip.labels && selectedClip.labels.length > 0 && (
                      <span className="ratings-toggle-count">
                        {selectedClip.labels.filter((l) => l.user_id != null).length}
                      </span>
                    )}
                  </button>
                  {showRatings && (
                    <RatingsTable
                      labels={selectedClip.labels || []}
                      currentUsername={user.username}
                    />
                  )}
                </div>
                <div className="rating-panel">
                  <LabelForm
                    clipId={selectedClip.id}
                    existingLabel={myLabel}
                    autoLabel={autoLabel}
                    onSave={handleSave}
                    onSkip={handleSkip}
                    onPrev={goToPrev}
                    onNext={goToNext}
                    saving={saving}
                  />
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <p>Select a clip to begin labeling.</p>
              </div>
            )}
          </>
        )}
      </main>
      <Footer />
    </div>
  );
};

export default LabelerApp;
