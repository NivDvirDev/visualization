import React from 'react';
import { Link } from 'react-router-dom';
import { WellspringIcon } from './WellspringIcon/WellspringIcon';
import { Button } from '../../atoms';
import './WellspringLogo.css';

const trackEvent = (name: string, params?: Record<string, unknown>) => {
  if (typeof window !== 'undefined' && (window as any).gtag) {
    (window as any).gtag('event', name, params);
  }
};

const WellspringLogo: React.FC = () => (
  <section className="landing-hero">
    <WellspringIcon size={120} animate />
    <h1 className="landing-hero-title">The Wellspring</h1>
    <p className="landing-hero-tagline">
      Rate how well visuals capture sound
    </p>
    <p className="landing-hero-sub">
      Watch a clip. Swipe to rate it. See how you compare to AI.
    </p>
    <div className="landing-hero-cta">
      <Link to="/swipe" style={{ textDecoration: 'none' }} onClick={() => trackEvent('landing_cta_clicked', { cta: 'quick_rate_hero' })}>
        <Button variant="primary" size="lg">Start Rating</Button>
      </Link>
    </div>
    <div className="landing-hero-secondary">
      <Link to="/app" style={{ textDecoration: 'none' }} onClick={() => trackEvent('landing_cta_clicked', { cta: 'detailed_mode' })}>
        <Button variant="ghost" size="sm">Detailed Mode</Button>
      </Link>
      <Link to="/rankings" style={{ textDecoration: 'none' }} onClick={() => trackEvent('landing_cta_clicked', { cta: 'rankings' })}>
        <Button variant="ghost" size="sm">Rankings</Button>
      </Link>
    </div>
  </section>
);

export default WellspringLogo;
