import React, { useEffect, useState, useRef, useCallback } from 'react';
import { DotLottieReact } from '@lottiefiles/dotlottie-react';
import './SwipeOnboarding.css';

const LOTTIE_SRC = 'https://assets-v2.lottiefiles.com/a/94fb52cc-1163-11ee-8a6e-7f03993d3bcc/xXjG9MW2sj.lottie';

const trackEvent = (name: string, params?: Record<string, unknown>) => {
  if (typeof window !== 'undefined' && (window as any).gtag) {
    (window as any).gtag('event', name, params);
  }
};

const SCORE_META = [
  { score: 1, label: 'Awful',    bg: 'rgba(183,28,28,0.4)' },
  { score: 2, label: 'Bad',      bg: 'rgba(183,28,28,0.25)' },
  { score: 3, label: 'OK',       bg: 'transparent' },
  { score: 4, label: 'Good',     bg: 'rgba(46,125,50,0.25)' },
  { score: 5, label: 'Love it!', bg: 'rgba(46,125,50,0.4)' },
];

const SEGMENTS = [
  { score: 1, color: '#D84315', icon: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
      <line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/>
    </svg>
  )},
  { score: 2, color: '#E65100', icon: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M7 13 L12 18 L17 13"/><line x1="12" y1="6" x2="12" y2="18"/>
    </svg>
  )},
  { score: 3, color: '#8B7355', icon: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
      <line x1="6" y1="12" x2="18" y2="12"/>
    </svg>
  )},
  { score: 4, color: '#43A047', icon: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M7 11 L12 6 L17 11"/><line x1="12" y1="6" x2="12" y2="18"/>
    </svg>
  )},
  { score: 5, color: '#2E7D32', icon: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26"/>
    </svg>
  )},
];

function getState(t: number): { idx: number; opacity: number } {
  if (t < 0.05) return { idx: 2, opacity: 0 };
  if (t < 0.10) return { idx: 2, opacity: 0.15 };
  if (t < 0.15) return { idx: 1, opacity: 0.3 };
  if (t < 0.20) return { idx: 0, opacity: 0.5 };
  if (t < 0.27) return { idx: 0, opacity: 0.5 };
  if (t < 0.32) return { idx: 1, opacity: 0.3 };
  if (t < 0.38) return { idx: 2, opacity: 0.1 };
  if (t < 0.52) return { idx: 2, opacity: 0 };
  if (t < 0.57) return { idx: 2, opacity: 0.1 };
  if (t < 0.62) return { idx: 3, opacity: 0.3 };
  if (t < 0.70) return { idx: 4, opacity: 0.5 };
  if (t < 0.77) return { idx: 4, opacity: 0.5 };
  if (t < 0.82) return { idx: 3, opacity: 0.3 };
  if (t < 0.88) return { idx: 2, opacity: 0.1 };
  return { idx: 2, opacity: 0 };
}

const SwipeOnboarding: React.FC = () => {
  const [visible, setVisible] = useState(false);
  const [fading, setFading] = useState(false);
  const [activeIdx, setActiveIdx] = useState(2);
  const [overlayStyle, setOverlayStyle] = useState({ bg: 'transparent', opacity: 0 });
  const rafRef = useRef<number>(0);
  const startRef = useRef(0);
  const dismissedRef = useRef(false);

  const dismiss = useCallback(() => {
    if (dismissedRef.current) return;
    dismissedRef.current = true;
    setFading(true);
    localStorage.setItem('wellspring_onboarded', '1');
    trackEvent('onboarding_dismissed');
    setTimeout(() => setVisible(false), 300);
  }, []);

  useEffect(() => {
    if (localStorage.getItem('wellspring_onboarded') === '1') return;
    setVisible(true);
    startRef.current = performance.now();

    const animate = () => {
      const elapsed = (performance.now() - startRef.current) / 1000;
      const t = (elapsed % 5) / 5;
      const { idx, opacity } = getState(t);
      setActiveIdx(idx);

      if (opacity > 0.02) {
        const meta = SCORE_META[idx];
        const bg = idx <= 1 ? meta.bg
                 : idx >= 3 ? meta.bg
                 : 'transparent';
        setOverlayStyle({ bg, opacity: Math.min(opacity * 1.5, 1) });
      } else {
        setOverlayStyle({ bg: 'transparent', opacity: 0 });
      }

      rafRef.current = requestAnimationFrame(animate);
    };
    rafRef.current = requestAnimationFrame(animate);

    const timer = setTimeout(dismiss, 8000);

    // Use 'click' (not pointerdown) to avoid false triggers from video autoplay/page load.
    // Delay 1s to skip any initial browser-generated events.
    const handleInteraction = () => dismiss();
    const listenerDelay = setTimeout(() => {
      window.addEventListener('click', handleInteraction, { capture: true, once: true });
      window.addEventListener('touchstart', handleInteraction, { capture: true, once: true });
    }, 1000);

    return () => {
      cancelAnimationFrame(rafRef.current);
      clearTimeout(timer);
      clearTimeout(listenerDelay);
      window.removeEventListener('click', handleInteraction, { capture: true });
      window.removeEventListener('touchstart', handleInteraction, { capture: true });
    };
  }, [dismiss]);

  if (!visible) return null;

  const meta = SCORE_META[activeIdx];

  return (
    <div className={`onboarding-overlay${fading ? ' onboarding-fadeout' : ''}`}>
      <div className="onboarding-unit">

        {/* Mini card + Lottie hand */}
        <div className="demo-drag-area">
          <div className="demo-card">
            <div
              className="demo-overlay"
              style={{ background: overlayStyle.bg, opacity: overlayStyle.opacity }}
            >
              <div className="demo-overlay-score">{meta.score}</div>
              <div className="demo-overlay-label">{meta.label}</div>
            </div>
          </div>
          <div className="demo-hand">
            <DotLottieReact
              src={LOTTIE_SRC}
              loop
              autoplay
              style={{ width: '100%', height: '100%' }}
            />
          </div>
        </div>

        {/* Score track */}
        <div className="onboarding-track">
          <div className="onboarding-rail" />
          {SEGMENTS.map((seg, i) => (
            <div
              key={seg.score}
              className={`onboarding-segment${i === activeIdx ? ' active' : ''}`}
              style={{ '--seg-color': seg.color } as React.CSSProperties}
            >
              {seg.icon}
              <span className="onboarding-score-num">{seg.score}</span>
            </div>
          ))}
        </div>

      </div>
    </div>
  );
};

export default SwipeOnboarding;
