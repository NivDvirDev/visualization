import React, { useEffect, useState } from 'react';
import { getMyTasteProfile } from '../../../api';
import { TasteProfile as TasteProfileType } from '../../../types';
import './TasteProfile.css';

const DIM_LABELS: Record<string, string> = {
  sync_quality:      'Sync',
  harmony:           'Harmony',
  aesthetic_quality: 'Aesthetics',
  motion_smoothness: 'Motion',
};

interface Props {
  /** If provided, use this data instead of fetching (e.g. from UserProfilePage) */
  data?: Pick<TasteProfileType, 'perceptual' | 'personality' | 'label_count'>;
}

const TasteProfile: React.FC<Props> = ({ data: externalData }) => {
  const [profile, setProfile] = useState<TasteProfileType | null>(null);
  const [loading, setLoading] = useState(!externalData);

  useEffect(() => {
    if (externalData) return;
    getMyTasteProfile()
      .then(setProfile)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [externalData]);

  const activeData = externalData ?? profile;

  if (loading) return <div className="taste-profile-loading">Loading taste profile…</div>;
  if (!activeData || activeData.label_count === 0) return null;

  const { perceptual, personality } = activeData;

  const dims = Object.entries(DIM_LABELS) as [keyof typeof perceptual, string][];
  const maxVal = Math.max(...dims.map(([k]) => perceptual[k] ?? 0));

  return (
    <div className="taste-profile">
      {personality && (
        <div className="taste-personality">
          <span className="taste-personality-emoji">{personality.emoji}</span>
          <div className="taste-personality-text">
            <span className="taste-personality-label">{personality.label}</span>
            <span className="taste-personality-desc">{personality.desc}</span>
          </div>
        </div>
      )}
      <div className="taste-bars">
        {dims.map(([key, label]) => {
          const val = perceptual[key];
          if (val === null) return null;
          const pct = (val / 5) * 100;
          const isTop = val === maxVal && maxVal > 0;
          return (
            <div key={key} className={`taste-bar-row${isTop ? ' taste-bar-top' : ''}`}>
              <span className="taste-bar-label">{label}</span>
              <div className="taste-bar-track">
                <div className="taste-bar-fill" style={{ width: `${pct}%` }} />
              </div>
              <span className="taste-bar-val">{val.toFixed(1)}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TasteProfile;
