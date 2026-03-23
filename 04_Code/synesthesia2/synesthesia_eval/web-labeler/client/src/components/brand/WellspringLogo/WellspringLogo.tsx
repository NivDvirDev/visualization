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
    <div className="landing-hero-bg" aria-hidden="true">
      <div className="landing-hero-glow" />
    </div>
    <div className="landing-hero-content">
      <WellspringIcon size={100} animate />
      <h1 className="landing-hero-title">The Wellspring</h1>
      <p className="landing-hero-tagline">The Ancient Dance, Renewed</p>
      <p className="landing-hero-sub">
        From the first rhythmic movement to the frontiers of audio-visual harmony — we dance together.
      </p>
      <div className="landing-hero-cta">
        <Link to="/swipe" style={{ textDecoration: 'none' }} onClick={() => trackEvent('landing_cta_clicked', { cta: 'join_the_dance' })}>
          <Button variant="primary" size="lg">Join the Dance</Button>
        </Link>
      </div>
      <div className="landing-hero-secondary">
        <a href="#featured" style={{ textDecoration: 'none' }} onClick={() => trackEvent('landing_cta_clicked', { cta: 'watch_creation' })}>
          <Button variant="ghost" size="sm">Watch a Creation</Button>
        </a>
        <Link to="/rankings" style={{ textDecoration: 'none' }} onClick={() => trackEvent('landing_cta_clicked', { cta: 'rankings' })}>
          <Button variant="ghost" size="sm">Rankings</Button>
        </Link>
      </div>
    </div>
  </section>
);

export default WellspringLogo;
