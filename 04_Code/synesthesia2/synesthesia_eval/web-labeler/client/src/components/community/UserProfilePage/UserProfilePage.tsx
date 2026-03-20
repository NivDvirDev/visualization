import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getUserProfile } from '../../../api';
import { UserProfile } from '../../../types';
import TasteProfile from '../TasteProfile/TasteProfile';
import './UserProfilePage.css';

const BADGE_MAP: Record<string, { emoji: string; label: string }> = {
  first_label:    { emoji: '⭐', label: 'First Label' },
  five_streak:    { emoji: '🔥', label: '5-Day Streak' },
  ten_labels:     { emoji: '🎯', label: '10 Labels' },
  completionist:  { emoji: '👑', label: 'Completionist' },
  consensus_rater:{ emoji: '👂', label: 'Sharp Ear' },
};

const UserProfilePage: React.FC = () => {
  const { username } = useParams<{ username: string }>();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!username) return;
    setLoading(true);
    getUserProfile(username)
      .then(setProfile)
      .catch(() => setError('User not found'))
      .finally(() => setLoading(false));
  }, [username]);

  if (loading) return (
    <div className="user-profile-page">
      <div className="user-profile-loading">Loading profile…</div>
    </div>
  );

  if (error || !profile) return (
    <div className="user-profile-page">
      <div className="user-profile-error">
        <p>👤 User not found</p>
        <Link to="/" className="user-profile-back">← Back to The Wellspring</Link>
      </div>
    </div>
  );

  const joinedYear = new Date(profile.created_at).getFullYear();

  return (
    <div className="user-profile-page">
      <div className="user-profile-card">
        <Link to="/" className="user-profile-back">← The Wellspring</Link>

        <div className="user-profile-header">
          <div className="user-profile-avatar">{profile.username[0].toUpperCase()}</div>
          <div className="user-profile-identity">
            <h1 className="user-profile-username">@{profile.username}</h1>
            <span className="user-profile-level">{profile.level_title}</span>
            <span className="user-profile-joined">Member since {joinedYear}</span>
          </div>
          <div className="user-profile-rank">
            <span className="user-profile-rank-value">#{profile.rank}</span>
            <span className="user-profile-rank-label">Global Rank</span>
          </div>
        </div>

        <div className="user-profile-stats">
          <div className="user-profile-stat">
            <span className="user-profile-stat-value">{profile.total_labels}</span>
            <span className="user-profile-stat-label">Ratings</span>
          </div>
          <div className="user-profile-stat">
            <span className="user-profile-stat-value">Lv.{profile.level}</span>
            <span className="user-profile-stat-label">Level</span>
          </div>
        </div>

        {profile.badges.length > 0 && (
          <div className="user-profile-badges">
            {profile.badges.map(b => {
              const badge = BADGE_MAP[b];
              if (!badge) return null;
              return (
                <span key={b} className="user-profile-badge" title={badge.label}>
                  {badge.emoji} {badge.label}
                </span>
              );
            })}
          </div>
        )}

        {profile.claimed_clips && profile.claimed_clips.length > 0 && (
          <section className="user-profile__creations">
            <h3>Their Creations</h3>
            <ul>
              {profile.claimed_clips.map(c => (
                <li key={c.id}>
                  <a href={`/clip/${c.id}`}>{c.display_credit || c.filename}</a>
                </li>
              ))}
            </ul>
          </section>
        )}

        {profile.personality && (
          <div className="user-profile-taste-section">
            <h2 className="user-profile-section-title">Taste Profile</h2>
            <TasteProfile
              data={{
                perceptual: profile.perceptual,
                personality: profile.personality,
                label_count: profile.total_labels,
              }}
            />
          </div>
        )}

        <div className="user-profile-cta">
          <p>Think you can beat <strong>@{profile.username}</strong>?</p>
          <Link to="/" className="user-profile-cta-btn">Rate clips on The Wellspring →</Link>
        </div>
      </div>
    </div>
  );
};

export default UserProfilePage;
