import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import SwipeCard from '../SwipeCard/SwipeCard';
import SwipeGuestPrompt from '../SwipeGuestPrompt/SwipeGuestPrompt';
import { WellspringIcon } from '../../brand/WellspringLogo/WellspringIcon/WellspringIcon';
import { Button } from '../../atoms';
import { saveSwipeLabel } from '../../../api';
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

  // Check auth and load clips on mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    const username = localStorage.getItem('username');
    const userId = localStorage.getItem('userId');
    if (token && username) {
      setUser({ id: Number(userId), username, token });
    }
    setAuthChecked(true);

    // Load clips from API
    const apiBase = '/api';
    const url = `${apiBase}/clips?mode=unlabeled&limit=50`;
    fetch(url, token ? { headers: { Authorization: `Bearer ${token}` } } : {})
      .then(r => r.json())
      .then((data: ClipItem[]) => {
        // Shuffle for variety
        const shuffled = [...data].sort(() => Math.random() - 0.5);
        setClips(shuffled);
        setLoading(false);
        trackEvent('clip_loaded', { clip_count: shuffled.length });
      })
      .catch(() => {
        // Fall back to all clips
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

  const handleCommit = useCallback(async (score: number) => {
    const clip = clips[currentIndex];
    if (!clip) return;

    trackEvent('swipe_attempt', {
      score,
      clip_id: clip.id,
      is_guest: !user,
      swipe_number: swipedCount + 1,
    });

    // Guest mode: only allow 3 free swipes
    if (!user) {
      if (guestSwipeCount >= 3) {
        trackEvent('guest_limit_reached');
        trackEvent('signup_modal_shown');
        setShowGuestPrompt(true);
        return;
      }
      setGuestSwipeCount(c => c + 1);
      // Try to save (will likely 401), ignore error
      saveSwipeLabel(clip.id, score, null).catch(() => {});
    } else {
      setSaving(true);
      try {
        await saveSwipeLabel(clip.id, score, user.token);
      } catch (e) {
        console.error('Save failed:', e);
      }
      setSaving(false);
    }

    setSwipedCount(c => c + 1);
    setCurrentIndex(i => i + 1);
  }, [clips, currentIndex, user, guestSwipeCount, swipedCount]);

  const currentClip = clips[currentIndex];

  // Build video URL — match pattern from VideoPlayer component
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
        <div className="swipe-footer-count">
          {swipedCount} rated · {clips.length - currentIndex} left
        </div>
      </div>

      {showGuestPrompt && (
        <SwipeGuestPrompt onContinue={() => setShowGuestPrompt(false)} />
      )}
    </div>
  );
};

export default SwipeMode;
