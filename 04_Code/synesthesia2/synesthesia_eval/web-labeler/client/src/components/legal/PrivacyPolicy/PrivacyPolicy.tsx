import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../../atoms';
import './PrivacyPolicy.css';

const PrivacyPolicy: React.FC = () => (
  <div className="legal-page">
    <div className="legal-container">
      <div className="legal-nav">
        <Link to="/" style={{ textDecoration: 'none' }}>
          <Button variant="ghost" size="sm">← Back to The Wellspring</Button>
        </Link>
      </div>

      <h1 className="legal-title">Privacy Policy</h1>
      <p className="legal-updated">Last updated: March 2026</p>

      <section className="legal-section">
        <h2>1. Who We Are</h2>
        <p>
          The Wellspring is a crowd-sourcing research platform operated by Niv Dvir as part of the
          Synesthesia psychoacoustic visualization research project. The platform collects human
          ratings of audio-visual content to build an open dataset for AI research.
        </p>
        <p>
          Contact: The project is publicly hosted at{' '}
          <a href="https://synesthesia-labeler.onrender.com" target="_blank" rel="noreferrer">
            synesthesia-labeler.onrender.com
          </a>
          .
        </p>
      </section>

      <section className="legal-section">
        <h2>2. What Data We Collect</h2>
        <p>When you create an account, we collect:</p>
        <ul>
          <li>Your username (chosen by you)</li>
          <li>Your email address (for login only)</li>
          <li>A hashed version of your password (we never store raw passwords)</li>
          <li>If you sign in with Google: your Google account name and email</li>
        </ul>
        <p>When you rate clips, we collect:</p>
        <ul>
          <li>Your numeric ratings (1–5) on four dimensions: sync, harmony, aesthetics, motion</li>
          <li>Optional free-text notes you write</li>
          <li>Timestamps of your activity</li>
        </ul>
        <p>We do <strong>not</strong> collect:</p>
        <ul>
          <li>Your IP address or location</li>
          <li>Browser fingerprint or device identifiers</li>
          <li>Browsing history outside this site</li>
          <li>Payment information (the platform is free)</li>
        </ul>
      </section>

      <section className="legal-section">
        <h2>3. How We Use Your Data</h2>
        <p>Your ratings are used to:</p>
        <ul>
          <li>Build a publicly available open dataset (CC-BY-NC-SA 4.0) for AI research</li>
          <li>Display your score on the leaderboard (using your username, not your email)</li>
          <li>Show your personal statistics in your profile</li>
          <li>Compare human vs. AI labeling accuracy</li>
        </ul>
        <p>
          Rating data is published to HuggingFace Hub (
          <a href="https://huggingface.co/datasets/NivDvir/synesthesia-eval" target="_blank" rel="noreferrer">
            NivDvir/synesthesia-eval
          </a>
          ) using only your username — never your email address.
        </p>
        <p>We do <strong>not</strong>: sell your data, use it for advertising, or share it with any third party for commercial purposes.</p>
      </section>

      <section className="legal-section">
        <h2>4. Data Storage</h2>
        <p>
          Account data is stored in a PostgreSQL database hosted on Render.com (US region).
          We use industry-standard encryption in transit (HTTPS/TLS) and at rest.
        </p>
      </section>

      <section className="legal-section">
        <h2>5. Your Rights</h2>
        <p>You can request at any time:</p>
        <ul>
          <li><strong>Access</strong> — a copy of all data we hold about you</li>
          <li><strong>Correction</strong> — fix any incorrect information</li>
          <li><strong>Deletion</strong> — removal of your account and personal data</li>
        </ul>
        <p>
          Note: if you request deletion, your anonymised ratings (stored only as username + scores,
          no email) may remain in the published open dataset as they are part of the research corpus.
        </p>
      </section>

      <section className="legal-section">
        <h2>6. Cookies &amp; Tracking</h2>
        <p>
          We use a single session cookie (JWT token) to keep you logged in. We do not use
          advertising cookies or cross-site tracking cookies. If Google Analytics is enabled,
          it may set its own cookies — you can disable it via your browser's cookie settings or a
          browser ad-blocker.
        </p>
      </section>

      <section className="legal-section">
        <h2>7. Third-Party Services</h2>
        <ul>
          <li><strong>Google OAuth</strong> — optional sign-in. Governed by Google's Privacy Policy.</li>
          <li><strong>HuggingFace</strong> — dataset hosting. Governed by HuggingFace's Privacy Policy.</li>
          <li><strong>Render.com</strong> — hosting provider. Governed by Render's Privacy Policy.</li>
          <li><strong>Google Analytics</strong> (if enabled) — anonymous page-view analytics.</li>
        </ul>
      </section>

      <section className="legal-section">
        <h2>8. Changes to This Policy</h2>
        <p>
          We may update this policy occasionally. The "Last updated" date at the top will always
          reflect the most recent version. Continued use of the platform after a policy update
          constitutes acceptance of the changes.
        </p>
      </section>
    </div>
  </div>
);

export default PrivacyPolicy;
