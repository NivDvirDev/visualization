import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import SwipeCard from '../SwipeCard/SwipeCard';
import SwipeGuestPrompt from '../SwipeGuestPrompt/SwipeGuestPrompt';
import SwipeCategoryTuner, { CategoryScores } from '../SwipeCategoryTuner/SwipeCategoryTuner';
import { WellspringIcon } from '../../brand/WellspringLogo/WellspringIcon/WellspringIcon';
import { Button, useToast, ToastContainer } from '../../atoms';
import { saveSwipeLabel, saveAnonymousLabel, getMe } from '../../../api';
import './SwipeMode.css';

const trackEvent = (name: string, params?: Record<string, unknown>) => {
  if (typeof window !== 'undefined' && (window as any).gtag) {
    (window as any).gtag('event', name, params);
  }
};

interface ClipItem {
  id: string;
  filename: string;
  video_url?: string;
}

interface SwipeUser {
  id: number;
  username: string;
  token: string;
}

const SwipeMode: React.FC = () => {
  const navigate = useNavigate();
  const { toasts, toast, dismiss } = useToast();
  const [clips, setClips] = useState<ClipItem[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [user, setUser] = useState<SwipeUser | null>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [guestSwipeCount, setGuestSwipeCount] = useState(0);
  const [showGuestPrompt, setShowGuestPrompt] = useState(false);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [swipedCount, setSwipedCount] = useState(0);
  const [muted, setMuted] = useState(false);
  const [pendingScore, setPendingScore] = useState<{ clipId: string; score: number } | null>(null);
  const [skipCategories, setSkipCategories] = useState(() =>
    localStorage.getItem('swipe_skip_categories') === 'true'
  );
  const [sessionId] = useState(() => {
    let sid = sessionStorage.getItem('anon_session');
    if (!sid) {
      sid = `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
      sessionStorage.setItem('anon_session', sid);
    }
    return sid;
  });

  // Check auth and load clips on mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    const username = localStorage.getItem('username');
    const userId = localStorage.getItem('userId');

    if (token && username) {
      setUser({ id: Number(userId), username, token });
      setAuthChecked(true);
    } else if (token) {
      // Token exists but username missing — restore from server
      getMe()
        .then((u) => {
          localStorage.setItem('username', u.username);
          localStorage.setItem('userId', String(u.id));
          setUser({ id: u.id, username: u.username, token });
          setAuthChecked(true);
        })
        .catch(() => {
          // Token invalid — clear and continue as guest
          localStorage.removeItem('token');
          setAuthChecked(true);
        });
    } else {
      setAuthChecked(true);
    }

    // Load clips from API
    const apiBase = '/api';
    const url = `${apiBase}/clips?mode=unlabeled&limit=50`;
    fetch(url, token ? { headers: { Authorization: `Bearer ${token}` } } : {})
      .then(r => r.json())
      .then((data: ClipItem[]) => {
        const shuffled = [...data].sort(() => Math.random() - 0.5);
        setClips(shuffled);
        setLoading(false);
        trackEvent('clip_loaded', { clip_count: shuffled.length });
      })
      .catch(() => {
        fetch(`${apiBase}/clips`, token ? { headers: { Authorization: `Bearer ${token}` } } : {})
          .then(r => r.json())
          .then((data: ClipItem[]) => {
            const fallbackShuffled = [...data].sort(() => Math.random() - 0.5);
            setClips(fallbackShuffled);
            setLoading(false);
            trackEvent('clip_loaded', { clip_count: fallbackShuffled.length });
          })
          .catch(() => setLoading(false));
      });
  }, []);

  const advanceCard = useCallback(() => {
    setSwipedCount(c => c + 1);
    setCurrentIndex(i => i + 1);
  }, []);

  const handleCommit = useCallback(async (score: number) => {
    const clip = clips[currentIndex];
    if (!clip) return;

    trackEvent('swipe_attempt', {
      score,
      clip_id: clip.id,
      is_guest: !user,
      swipe_number: swipedCount + 1,
    });

    // Guest mode: save anonymously, prompt sign-up after 3
    if (!user) {
      if (guestSwipeCount >= 3) {
        trackEvent('guest_limit_reached');
        trackEvent('signup_modal_shown');
        setShowGuestPrompt(true);
        return;
      }
      if (guestSwipeCount === 0) {
        toast('Rating saved! Sign in to track your rank', { variant: 'success', duration: 4000 });
      }
      setGuestSwipeCount(c => c + 1);
      // Save anonymously — no auth required
      saveAnonymousLabel(clip.id, score, sessionId).catch(err =>
        console.error('Anonymous save failed:', err)
      );
      advanceCard();
      return;
    }

    // Authenticated path
    if (skipCategories) {
      // Auto-fill categories with overall score, save immediately
      setSaving(true);
      try {
        await saveSwipeLabel(clip.id, score, user.token, {
          sync_quality: score, harmony: score,
          aesthetic_quality: score, motion_smoothness: score,
        });
        trackEvent('swipe_save_success', { clip_id: clip.id });
      } catch (e) {
        console.error('Save failed:', e);
        toast('Rating failed to save — try again', { variant: 'error', duration: 4000 });
        trackEvent('swipe_save_failed', { clip_id: clip.id, error: String(e) });
      }
      setSaving(false);
      advanceCard();
    } else {
      // Show category tuner overlay
      setPendingScore({ clipId: clip.id, score });
    }
  }, [clips, currentIndex, user, guestSwipeCount, swipedCount, skipCategories, toast, advanceCard]);

  const handleCategoryConfirm = useCallback(async (categories: CategoryScores) => {
    if (!pendingScore || !user) return;
    const { clipId, score } = pendingScore;
    setPendingScore(null);

    // Check if any category was adjusted
    const adjusted = Object.values(categories).some(v => v !== score);
    if (adjusted) {
      trackEvent('swipe_categories_tuned', {
        clip_id: clipId,
        changed: Object.entries(categories)
          .filter(([, v]) => v !== score)
          .map(([k]) => k),
      });
    }

    setSaving(true);
    try {
      await saveSwipeLabel(clipId, score, user.token, categories);
      trackEvent('swipe_save_success', { clip_id: clipId });
    } catch (e) {
      console.error('Save failed:', e);
      toast('Rating failed to save — try again', { variant: 'error', duration: 4000 });
      trackEvent('swipe_save_failed', { clip_id: clipId, error: String(e) });
    }
    setSaving(false);
    advanceCard();
  }, [pendingScore, user, toast, advanceCard]);

  const handleSkipToggle = useCallback((skip: boolean) => {
    setSkipCategories(skip);
    if (skip) {
      localStorage.setItem('swipe_skip_categories', 'true');
      trackEvent('swipe_categories_skipped');
    } else {
      localStorage.removeItem('swipe_skip_categories');
    }
  }, []);

  const currentClip = clips[currentIndex];

  const getVideoUrl = (clip: ClipItem): string => {
    if (clip.video_url) return clip.video_url;
    return `/videos/${clip.filename}`;
  };

  if (loading) {
    return (
      <div className="swipe-mode swipe-mode--loading">
        <WellspringIcon size={88} animate />
        <p>Loading clips…</p>
      </div>
    );
  }

  if (!currentClip || currentIndex >= clips.length) {
    return (
      <div className="swipe-mode swipe-mode--done">
        <WellspringIcon size={80} animate />
        <h2>All caught up!</h2>
        <p>You've swiped through {swipedCount} clips{user ? ' — scores saved to your profile.' : '.'}</p>
        {!user && (
          <Button variant="primary" size="md" onClick={() => navigate('/app')}>
            Sign up to see your rank
          </Button>
        )}
        <Button variant="secondary" size="sm" onClick={() => setCurrentIndex(0)}>
          Start over
        </Button>
      </div>
    );
  }

  return (
    <div className="swipe-mode">
      <header className="swipe-header">
        <div className="swipe-header-brand">
          <WellspringIcon size={34} animate />
          <div className="swipe-header-titles">
            <span className="swipe-header-brand-name">The Wellspring</span>
            <span className="swipe-header-title">Quick Rate</span>
          </div>
        </div>
        <div className="swipe-header-actions">
          {user ? (
            <span className="swipe-header-user">@{user.username}</span>
          ) : (
            <Button variant="ghost" size="sm" onClick={() => navigate('/app')}>
              Sign in to save
            </Button>
          )}
          <Button variant="secondary" size="sm" onClick={() => navigate('/app')}>
            Detail Mode →
          </Button>
        </div>
      </header>

      <div className="swipe-arena">
        <div className="swipe-hint swipe-hint--left">👎</div>
        <SwipeCard
          key={currentClip.id}
          clip={{ id: currentClip.id, videoUrl: getVideoUrl(currentClip) }}
          onCommit={handleCommit}
          disabled={saving}
          muted={muted}
          onMuteToggle={() => setMuted(m => !m)}
        />
        <div className="swipe-hint swipe-hint--right">👍</div>
      </div>

      <div className="swipe-footer">
        <div className="swipe-footer-instructions">
          ← drag to score 1–5 →
        </div>
        {skipCategories && (
          <span
            className="swipe-footer-categories"
            onClick={() => handleSkipToggle(false)}
            title="Click to re-enable category tuning"
          >
            Categories: auto
          </span>
        )}
        <div className="swipe-footer-count">
          {swipedCount} rated · {clips.length - currentIndex} left
        </div>
      </div>

      {showGuestPrompt && (
        <SwipeGuestPrompt onContinue={() => setShowGuestPrompt(false)} />
      )}

      {pendingScore && (
        <SwipeCategoryTuner
          overallScore={pendingScore.score}
          skipCategories={skipCategories}
          onConfirm={handleCategoryConfirm}
          onSkipToggle={handleSkipToggle}
        />
      )}

      <ToastContainer toasts={toasts} onDismiss={dismiss} />
    </div>
  );
};

export default SwipeMode;
