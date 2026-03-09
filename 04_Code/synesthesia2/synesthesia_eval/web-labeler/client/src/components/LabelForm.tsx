import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Dimension, DimensionKey, Label, LabelData, RatingValue } from '../types';

const DOT_COLORS = ['#ff4444', '#ff8844', '#ffcc44', '#88cc44', '#44cc88'];

const DIMENSIONS: (Dimension & { icon: React.ReactNode })[] = [
  {
    key: 'sync_quality',
    label: 'Sync',
    icon: <svg width="20" height="20" viewBox="0 0 20 20" stroke="currentColor" strokeWidth={2} fill="none"><circle cx={8} cy={10} r={5}/><circle cx={12} cy={10} r={5}/></svg>,
    descriptions: {
      1: 'No sync at all',
      2: 'Occasional sync',
      3: 'Moderate sync',
      4: 'Good sync',
      5: 'Perfect sync',
    },
  },
  {
    key: 'aesthetic_quality',
    label: 'Aesthetic',
    icon: <svg width="20" height="20" viewBox="0 0 20 20" stroke="currentColor" strokeWidth={2} fill="none"><path d="M10 2L18 10L10 18L2 10Z"/></svg>,
    descriptions: {
      1: 'Unappealing',
      2: 'Below average',
      3: 'Average',
      4: 'Visually appealing',
      5: 'Stunning',
    },
  },
  {
    key: 'visual_audio_alignment',
    label: 'Alignment',
    icon: <svg width="20" height="20" viewBox="0 0 20 20" stroke="currentColor" strokeWidth={2} fill="none"><line x1={3} y1={7} x2={17} y2={7}/><line x1={3} y1={13} x2={17} y2={13}/><circle cx={7} cy={7} r={2} fill="currentColor"/><circle cx={13} cy={13} r={2} fill="currentColor"/></svg>,
    descriptions: {
      1: 'Completely mismatched',
      2: 'Poorly aligned',
      3: 'Somewhat aligned',
      4: 'Well aligned',
      5: 'Perfect alignment',
    },
  },
  {
    key: 'motion_smoothness',
    label: 'Motion',
    icon: <svg width="20" height="20" viewBox="0 0 20 20" stroke="currentColor" strokeWidth={2} fill="none"><path d="M2 10C5 4 9 16 12 10S16 4 18 10"/><path d="M15 7L18 10L15 13"/></svg>,
    descriptions: {
      1: 'Very choppy',
      2: 'Somewhat choppy',
      3: 'Acceptable',
      4: 'Smooth',
      5: 'Perfectly fluid',
    },
  },
];

interface LabelFormProps {
  clipId: string;
  existingLabel?: Label;
  autoLabel?: Label;
  onSave: (clipId: string, data: LabelData) => void;
  onSkip: () => void;
  onPrev: () => void;
  onNext: () => void;
  saving: boolean;
}

type Ratings = Record<DimensionKey, number | null>;

function getInitialRatings(label?: Label): Ratings {
  if (label) {
    return {
      sync_quality: label.sync_quality ?? null,
      visual_audio_alignment: label.visual_audio_alignment ?? null,
      aesthetic_quality: label.aesthetic_quality ?? null,
      motion_smoothness: label.motion_smoothness ?? null,
    };
  }
  return {
    sync_quality: null,
    visual_audio_alignment: null,
    aesthetic_quality: null,
    motion_smoothness: null,
  };
}

function LabelForm({ clipId, existingLabel, autoLabel, onSave, onSkip, onPrev, onNext, saving }: LabelFormProps) {
  const [ratings, setRatings] = useState<Ratings>(() => getInitialRatings(existingLabel));
  const [notes, setNotes] = useState(() => existingLabel?.notes || '');
  const [showNotes, setShowNotes] = useState(() => !!existingLabel?.notes);
  const [activeDimension, setActiveDimension] = useState(0);
  const [justRated, setJustRated] = useState<string | null>(null);
  const [hoveredDot, setHoveredDot] = useState<{ dim: string; val: number } | null>(null);

  const animTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const autoSaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const isComplete = DIMENSIONS.every((d) => ratings[d.key] != null);
  const rated = DIMENSIONS.filter((d) => ratings[d.key] != null).length;

  const handleSave = useCallback(() => {
    onSave(clipId, { ...ratings, notes });
  }, [clipId, onSave, ratings, notes]);

  // Reset state when clipId changes
  useEffect(() => {
    if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current);
    setRatings(getInitialRatings(existingLabel));
    setNotes(existingLabel?.notes || '');
    setShowNotes(!!existingLabel?.notes);
    setActiveDimension(0);
    setJustRated(null);
    setHoveredDot(null);
  }, [clipId]); // Only reset on clipId change, existingLabel read at call time

  // Auto-save when all dimensions are rated for the first time
  const prevCompleteRef = useRef(false);
  useEffect(() => {
    const wasComplete = prevCompleteRef.current;
    prevCompleteRef.current = isComplete;

    if (!wasComplete && isComplete && !existingLabel && !saving) {
      if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current);
      autoSaveTimer.current = setTimeout(() => handleSave(), 800);
    }

    return () => {
      if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current);
    };
  }, [isComplete, existingLabel, saving, handleSave]);

  // Reset prevCompleteRef when clipId changes
  useEffect(() => {
    prevCompleteRef.current = false;
  }, [clipId]);

  const handleRatingChange = useCallback((dimKey: DimensionKey, value: RatingValue) => {
    if (animTimer.current) clearTimeout(animTimer.current);

    setRatings((prev) => ({ ...prev, [dimKey]: value }));
    setJustRated(dimKey);

    animTimer.current = setTimeout(() => {
      setJustRated(null);
    }, 500);

    const idx = DIMENSIONS.findIndex((d) => d.key === dimKey);
    setRatings((prev) => {
      const updated = { ...prev, [dimKey]: value };
      for (let i = 1; i <= DIMENSIONS.length; i++) {
        const nextIdx = (idx + i) % DIMENSIONS.length;
        const nextDim = DIMENSIONS[nextIdx];
        if (updated[nextDim.key] == null) {
          setActiveDimension(nextIdx);
          return updated;
        }
      }
      setActiveDimension(idx);
      return updated;
    });
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target.tagName === 'TEXTAREA' || target.tagName === 'INPUT') return;

      const key = e.key;

      if (key >= '1' && key <= '5') {
        e.preventDefault();
        setActiveDimension((current) => {
          const dim = DIMENSIONS[current];
          handleRatingChange(dim.key, parseInt(key, 10) as RatingValue);
          return current;
        });
      } else if (key === 'Tab') {
        e.preventDefault();
        setActiveDimension((s) => (s + 1) % DIMENSIONS.length);
      } else if (key === 'Enter') {
        e.preventDefault();
        // handleSave is called via ref to get latest state
        handleSaveRef.current();
      } else if (key === 'n') {
        e.preventDefault();
        onNext();
      } else if (key === 'p') {
        e.preventDefault();
        onPrev();
      } else if (key === 's' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        handleSaveRef.current();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onNext, onPrev, handleRatingChange]);

  // Ref to always have latest handleSave + isComplete for keyboard handler
  const handleSaveRef = useRef(() => {});
  handleSaveRef.current = () => {
    if (isComplete) handleSave();
  };

  // Cleanup timers on unmount
  useEffect(() => {
    return () => {
      if (animTimer.current) clearTimeout(animTimer.current);
      if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current);
    };
  }, []);

  return (
    <div className={'label-form glass-panel' + (isComplete ? ' label-form-complete' : '')}>
      <div className="label-form-header">
        <span className="label-form-title">Rate This Clip</span>
        <span className="label-form-progress">
          {isComplete ? (
            <span className="label-form-check">{'\u2713'}</span>
          ) : (
            <span className="label-form-counter">{rated}/4</span>
          )}
        </span>
      </div>

      <div className="rating-dimensions">
        {DIMENSIONS.map((dim, i) => {
          const currentValue = ratings[dim.key];
          const isActive = activeDimension === i;
          const wasJustRated = justRated === dim.key;

          return (
            <div
              key={dim.key}
              className={
                'rating-dim' +
                (isActive ? ' active' : '') +
                (wasJustRated ? ' just-rated' : '')
              }
              onClick={() => setActiveDimension(i)}
            >
              <span className="rating-dim-icon">{dim.icon}</span>
              <span className="rating-dim-label">{dim.label}</span>
              <div className="rating-dots">
                {([1, 2, 3, 4, 5] as RatingValue[]).map((val) => {
                  const isSelected = currentValue === val;
                  const isHovered = hoveredDot?.dim === dim.key && hoveredDot?.val === val;

                  return (
                    <div key={val} className="rating-dot-wrapper">
                      <button
                        className={
                          'rating-dot' +
                          (isSelected ? ' selected' : '') +
                          (isHovered ? ' hovered' : '') +
                          (isSelected && wasJustRated ? ' pulse' : '')
                        }
                        style={{ '--dot-color': DOT_COLORS[val - 1] } as React.CSSProperties}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRatingChange(dim.key, val);
                        }}
                        onMouseEnter={() => setHoveredDot({ dim: dim.key, val })}
                        onMouseLeave={() => setHoveredDot(null)}
                      >
                        {val}
                      </button>
                      {isHovered && (
                        <span className="rating-tooltip">
                          {val} &mdash; {dim.descriptions[val]}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      <div className="label-form-actions">
        <button
          className={'btn btn-save' + (isComplete ? ' ready' : '')}
          onClick={handleSave}
          disabled={!isComplete || saving}
          title="Save (Enter)"
        >
          {saving ? '...' : '\uD83D\uDCBE'}
        </button>
        <button className="btn btn-nav" onClick={onPrev} title="Previous (p)">
          {'\u25C0'}
        </button>
        <button className="btn btn-nav" onClick={onNext} title="Next (n)">
          {'\u25B6'}
        </button>
        <button className="btn btn-skip" onClick={onSkip} title="Skip">
          {'\u23ED'}
        </button>
      </div>

      <div className="label-form-extras">
        <button
          className="notes-toggle"
          onClick={() => setShowNotes((s) => !s)}
        >
          {showNotes ? '\u25BE Notes' : '\u25B8 Notes'}
        </button>
        {showNotes && (
          <textarea
            className="notes-input"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Optional notes..."
            rows={2}
          />
        )}
      </div>

      <div className="keyboard-hint">
        1-5 rate &middot; Tab cycle &middot; Enter save &middot; n/p nav &middot; {'\u2318'}S save
      </div>
    </div>
  );
}

export default LabelForm;
