import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../../atoms';
import './TermsOfService.css';

const TermsOfService: React.FC = () => (
  <div className="legal-page">
    <div className="legal-container">
      <div className="legal-nav">
        <Link to="/" style={{ textDecoration: 'none' }}>
          <Button variant="ghost" size="sm">← Back to The Wellspring</Button>
        </Link>
      </div>

      <h1 className="legal-title">Terms of Service</h1>
      <p className="legal-updated">Last updated: March 2026</p>

      <section className="legal-section">
        <h2>1. What This Platform Is</h2>
        <p>
          The Wellspring is a non-commercial academic research tool. It collects crowd-sourced
          ratings of audio-visual content to train AI models for psychoacoustic visualization
          research. Use of this platform is free and open to the public.
        </p>
      </section>

      <section className="legal-section">
        <h2>2. Eligibility</h2>
        <p>
          By creating an account, you confirm that you are at least 13 years old (or the minimum
          age required in your country) and that you are participating voluntarily as a research
          contributor.
        </p>
      </section>

      <section className="legal-section">
        <h2>3. Your Contributions</h2>
        <p>
          By submitting ratings on this platform, you grant the Synesthesia research project a
          perpetual, worldwide, royalty-free licence to use, reproduce, and publish your ratings
          as part of the{' '}
          <a href="https://huggingface.co/datasets/NivDvir/synesthesia-eval" target="_blank" rel="noreferrer">
            NivDvir/synesthesia-eval
          </a>{' '}
          open dataset under the{' '}
          <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/" target="_blank" rel="noreferrer">
            CC-BY-NC-SA 4.0
          </a>{' '}
          licence. Your ratings are attributed to your username, not your email address.
        </p>
        <p>
          You retain no ownership claim over the aggregated dataset. The dataset is provided
          freely for non-commercial academic use.
        </p>
      </section>

      <section className="legal-section">
        <h2>4. Acceptable Use</h2>
        <p>You agree not to:</p>
        <ul>
          <li>Submit deliberate spam ratings designed to skew the dataset</li>
          <li>Create multiple accounts to manipulate the leaderboard</li>
          <li>Attempt to access, modify, or delete other users' data</li>
          <li>Use automated bots or scripts to submit ratings</li>
          <li>Attempt to reverse-engineer or overload the platform's servers</li>
        </ul>
      </section>

      <section className="legal-section">
        <h2>5. Account Termination</h2>
        <p>
          We reserve the right to suspend or delete accounts that violate these terms, particularly
          accounts that submit fraudulent ratings. You can delete your own account at any time by
          contacting us.
        </p>
      </section>

      <section className="legal-section">
        <h2>6. Availability</h2>
        <p>
          The platform is hosted on Render.com free tier and may experience downtime or rate
          limits. We make no guarantees of uptime or data persistence, though we make reasonable
          efforts to maintain continuity. This is a research project, not a commercial service.
        </p>
      </section>

      <section className="legal-section">
        <h2>7. Limitation of Liability</h2>
        <p>
          The platform is provided "as is" without warranty of any kind. The research project and
          its operators are not liable for any damages arising from use of the platform. Since the
          platform is free and non-commercial, your sole remedy for dissatisfaction is to stop
          using it.
        </p>
      </section>

      <section className="legal-section">
        <h2>8. Governing Law</h2>
        <p>
          These terms are governed by the laws of Israel, where the project operator is based.
          Any disputes shall be resolved in the courts of Tel Aviv, Israel.
        </p>
      </section>

      <section className="legal-section">
        <h2>9. Changes to These Terms</h2>
        <p>
          We may update these terms from time to time. The "Last updated" date above reflects the
          current version. Continued use of the platform after an update constitutes acceptance.
        </p>
      </section>
    </div>
  </div>
);

export default TermsOfService;
