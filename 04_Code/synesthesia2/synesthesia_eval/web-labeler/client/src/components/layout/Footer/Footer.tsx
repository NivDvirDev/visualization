import React from 'react';
import { Link } from 'react-router-dom';
import { FlameIcon } from '../../brand/FlameIcon/FlameIcon';
import './Footer.css';

const Footer: React.FC = () => {
  return (
    <footer className="app-footer">
      <div className="footer-logo">
        <FlameIcon size={36} animate={false} />
      </div>
      <p className="footer-title">The Wellspring</p>
      <p className="footer-tagline">Where sound becomes visible flame</p>
      <nav className="footer-legal">
        <Link to="/privacy" className="footer-legal-link">Privacy Policy</Link>
        <span className="footer-legal-sep">·</span>
        <Link to="/terms" className="footer-legal-link">Terms of Service</Link>
      </nav>
      <p className="footer-copy">Synesthesia Eval</p>
    </footer>
  );
};

export default Footer;
