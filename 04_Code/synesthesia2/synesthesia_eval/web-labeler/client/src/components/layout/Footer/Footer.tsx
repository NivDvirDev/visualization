import React from 'react';
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
      <p className="footer-copy">Synesthesia Eval</p>
    </footer>
  );
};

export default Footer;
