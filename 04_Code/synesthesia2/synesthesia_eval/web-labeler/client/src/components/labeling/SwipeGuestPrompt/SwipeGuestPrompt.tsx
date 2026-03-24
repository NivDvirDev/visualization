import React from 'react';
import { useNavigate } from 'react-router-dom';
import './SwipeGuestPrompt.css';

const trackEvent = (name: string, params?: Record<string, unknown>) => {
  if (typeof window !== 'undefined' && (window as any).gtag) {
    (window as any).gtag('event', name, params);
  }
};

interface Props {
  onContinue: () => void;
}

const SwipeGuestPrompt: React.FC<Props> = ({ onContinue }) => {
  const navigate = useNavigate();
  return (
    <div className="guest-prompt-backdrop">
      <div className="guest-prompt-card">
        <div className="guest-prompt-icon">🎧</div>
        <h2>You've rated 3 clips!</h2>
        <p>Sign up to save your ratings, earn badges, and compete on the global leaderboard.</p>
        <button className="guest-prompt-cta" onClick={() => { trackEvent('signup_cta_clicked'); navigate('/app'); }}>
          Sign Up to Save Scores
        </button>
        <button className="guest-prompt-skip" onClick={() => { trackEvent('guest_continue_clicked'); onContinue(); }}>
          Keep rating anonymously
        </button>
      </div>
    </div>
  );
};

export default SwipeGuestPrompt;
