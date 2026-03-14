import React, { useRef, useCallback } from 'react';
import { ClipSummary, ClipMode } from '../../../types';
import './ClipList.css';

interface ClipListProps {
  clips: ClipSummary[];
  selectedClipId: string | null;
  onSelect: (id: string) => void;
  mode: ClipMode;
  onModeChange: (mode: ClipMode) => void;
  onRandom: () => void;
}

const MODES: { key: ClipMode; label: string }[] = [
  { key: 'unlabeled', label: 'Unlabeled' },
  { key: 'all', label: 'All' },
  { key: 'labeled', label: 'Review' },
];

const getStatusClass = (clip: ClipSummary): string => {
  if (clip.has_human_label) return 'labeled-human';
  if (clip.has_auto_label) return 'labeled-auto';
  return 'unlabeled';
};

const getStatusLabel = (clip: ClipSummary): string => {
  if (clip.has_human_label && clip.rater_count > 0) return `${clip.rater_count} rater${clip.rater_count !== 1 ? 's' : ''}`;
  if (clip.has_human_label) return 'Labeled';
  if (clip.has_auto_label) return 'Auto';
  return 'New';
};

/** Deterministic hue from clip id for the synesthesia color ring */
const idToHue = (id: string): number => {
  let hash = 0;
  for (let i = 0; i < id.length; i++) {
    hash = id.charCodeAt(i) + ((hash << 5) - hash);
  }
  return Math.abs(hash) % 360;
};

const SCROLL_AMOUNT = 320; // px to scroll per arrow click

const ClipList: React.FC<ClipListProps> = ({
  clips,
  selectedClipId,
  onSelect,
  mode,
  onModeChange,
  onRandom,
}) => {
  const trackRef = useRef<HTMLDivElement>(null);

  const scroll = useCallback((direction: 'left' | 'right') => {
    if (!trackRef.current) return;
    const amount = direction === 'left' ? -SCROLL_AMOUNT : SCROLL_AMOUNT;
    trackRef.current.scrollBy({ left: amount, behavior: 'smooth' });
  }, []);

  return (
    <section className="clip-strip">
      {/* Top bar: mode buttons + random */}
      <div className="clip-strip-controls">
        <div className="mode-selector">
          {MODES.map((m) => (
            <button
              key={m.key}
              className={'mode-btn' + (mode === m.key ? ' active' : '')}
              onClick={() => onModeChange(m.key)}
            >
              {m.label}
            </button>
          ))}
        </div>
        <button className="random-btn" onClick={onRandom}>
          ↻ Random
        </button>
      </div>

      {/* Horizontal carousel */}
      <div className="clip-carousel">
        <button
          className="clip-arrow clip-arrow-left"
          onClick={() => scroll('left')}
          aria-label="Scroll left"
        >
          ‹
        </button>

        <div className="clip-track" ref={trackRef}>
          {clips.length === 0 && (
            <div className="clip-empty">No clips in this mode.</div>
          )}
          {clips.map((clip) => {
            const hue = idToHue(clip.id);
            const isSelected = clip.id === selectedClipId;
            return (
              <div
                key={clip.id}
                className={'clip-thumb' + (isSelected ? ' selected' : '')}
                onClick={() => onSelect(clip.id)}
                style={{
                  '--clip-hue': `${hue}`,
                } as React.CSSProperties}
              >
                {/* Dark thumbnail area with YouTube preview or synesthesia ring fallback */}
                <div className="clip-thumb-visual">
                  {clip.youtube_video_id ? (
                    <img
                      className="clip-thumb-img"
                      src={`https://img.youtube.com/vi/${clip.youtube_video_id}/mqdefault.jpg`}
                      alt={clip.description || clip.filename}
                      loading="lazy"
                    />
                  ) : (
                    <svg viewBox="0 0 80 80" className="clip-thumb-svg">
                      <circle cx="40" cy="40" r="30" fill="none"
                        stroke={`hsl(${hue}, 90%, 55%)`} strokeWidth="2" opacity="0.7" />
                      <circle cx="40" cy="40" r="23" fill="none"
                        stroke={`hsl(${(hue + 50) % 360}, 85%, 60%)`} strokeWidth="1.5" opacity="0.5" />
                      <circle cx="40" cy="40" r="16" fill="none"
                        stroke={`hsl(${(hue + 100) % 360}, 80%, 65%)`} strokeWidth="1" opacity="0.35" />
                      <circle cx="40" cy="40" r="9" fill="none"
                        stroke={`hsl(${(hue + 150) % 360}, 75%, 70%)`} strokeWidth="0.8" opacity="0.25" />
                    </svg>
                  )}
                  {/* Status badge overlay */}
                  <span className={'clip-thumb-badge ' + getStatusClass(clip)}>
                    {getStatusLabel(clip)}
                  </span>
                  {/* Hot badge — recently rated */}
                  {clip.is_hot && (
                    <span className="clip-thumb-hot" title="Recently rated">🔥</span>
                  )}
                </div>
                {/* Label below thumbnail */}
                <div className="clip-thumb-label">
                  <span className="clip-thumb-id">#{clip.id}</span>
                  <span className="clip-thumb-name">
                    {clip.description || clip.filename}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        <button
          className="clip-arrow clip-arrow-right"
          onClick={() => scroll('right')}
          aria-label="Scroll right"
        >
          ›
        </button>
      </div>
    </section>
  );
};

export default ClipList;
