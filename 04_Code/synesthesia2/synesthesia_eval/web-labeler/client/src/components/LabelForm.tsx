import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Dimension, DimensionKey, PerceptualDimensionKey, PsychoacousticDimensionKey, Label, LabelData, RatingValue } from '../types';

const DOT_COLORS = ['#ff4444', '#ff8844', '#ffcc44', '#88cc44', '#44cc88'];

const PERCEPTUAL_DIMENSIONS: (Dimension & { icon: React.ReactNode })[] = [
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
    key: 'harmony',
    label: 'Harmony',
    icon: <svg width="20" height="20" viewBox="0 0 20 20" stroke="currentColor" strokeWidth={2} fill="none"><path d="M10 2C14 6 14 14 10 18"/><path d="M10 2C6 6 6 14 10 18"/><line x1={4} y1={10} x2={16} y2={10}/></svg>,
    descriptions: {
      1: 'Feels disconnected',
      2: 'Slightly unified',
      3: 'Moderately harmonious',
      4: 'Feels well unified',
      5: 'Perfectly harmonious',
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

const PSYCHOACOUSTIC_DIMENSIONS: (Dimension & { icon: React.ReactNode })[] = [
  {
    key: 'pitch_accuracy',
    label: 'Pitch',
    icon: <svg width="20" height="20" viewBox="0 0 20 20" stroke="currentColor" strokeWidth={2} fill="none"><path d="M4 16L8 4L12 12L16 2"/></svg>,
    descriptions: {
      1: 'Pitches indistinguishable',
      2: 'Barely distinguishable',
      3: 'Somewhat distinguishable',
      4: 'Clearly distinguishable',
      5: 'Perfectly mapped',
    },
  },
  {
    key: 'rhythm_accuracy',
    label: 'Rhythm',
    icon: <svg width="20" height="20" viewBox="0 0 20 20" stroke="currentColor" strokeWidth={2} fill="none"><rect x={3} y={8} width={3} height={8}/><rect x={8.5} y={4} width={3} height={12}/><rect x={14} y={6} width={3} height={10}/></svg>,
    descriptions: {
      1: 'No rhythmic patterns visible',
      2: 'Faint rhythmic hints',
      3: 'Some beats visible',
      4: 'Rhythmic patterns clear',
      5: 'Beat-perfect visualization',
    },
  },
  {
    key: 'dynamics_accuracy',
    label: 'Dynamics',
    icon: <svg width="20" height="20" viewBox="0 0 20 20" stroke="currentColor" strokeWidth={2} fill="none"><path d="M4 10h2l2-4 2 8 2-6 2 4h2"/></svg>,
    descriptions: {
      1: 'Loudness changes invisible',
      2: 'Barely shows dynamics',
      3: 'Some dynamic range visible',
      4: 'Dynamics well represented',
      5: 'Perfect dynamic mapping',
    },
  },
  {
    key: 'timbre_accuracy',
    label: 'Timbre',
    icon: <svg width="20" height="20" viewBox="0 0 20 20" stroke="currentColor" strokeWidth={2} fill="none"><circle cx={10} cy={10} r={7}/><circle cx={10} cy={10} r={4} strokeDasharray="2 2"/><circle cx={10} cy={10} r={1} fill="currentColor"/></svg>,
    descriptions: {
      1: 'Instruments indistinguishable',
      2: 'Barely distinguishable',
      3: 'Some timbral differences',
      4: 'Instruments distinguishable',
      5: 'Timbres perfectly separated',
    },
  },
  {
    key: 'melody_accuracy',
    label: 'Melody',
    icon: <svg width="20" height="20" viewBox="0 0 20 20" stroke="currentColor" strokeWidth={2} fill="none"><path d="M2 14C5 14 6 6 8 6S10 10 12 10S14 4 16 4L18 6"/><circle cx={16} cy={4} r={2} fill="currentColor"/></svg>,
    descriptions: {
      1: 'Melodic line invisible',
      2: 'Faint melodic hints',
      3: 'Melody partially visible',
      4: 'Melody clearly followable',
      5: 'Melody perfectly traced',
    },
  },
];

const ALL_DIMENSIONS = [...PERCEPTUAL_DIMENSIONS, ...PSYCHOACOUSTIC_DIMENSIONS];

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
      harmony: label.harmony ?? null,
      aesthetic_quality: label.aesthetic_quality ?? null,
      motion_smoothness: label.motion_smoothness ?? null,
      pitch_accuracy: label.pitch_accuracy ?? null,
      rhythm_accuracy: label.rhythm_accuracy ?? null,
      dynamics_accuracy: label.dynamics_accuracy ?? null,
      timbre_accuracy: label.timbre_accuracy ?? null,
      melody_accuracy: label.melody_accuracy ?? null,
    };
  }
  return {
    sync_quality: null,
    harmony: null,
    aesthetic_quality: null,
    motion_smoothness: null,
    pitch_accuracy: null,
    rhythm_accuracy: null,
    dynamics_accuracy: null,
    timbre_accuracy: null,
    melody_accuracy: null,
  };
}

const PERCEPTUAL_KEYS = PERCEPTUAL_DIMENSIONS.map(d => d.key) as PerceptualDimensionKey[];
const PSYCHOACOUSTIC_KEYS = PSYCHOACOUSTIC_DIMENSIONS.map(d => d.key) as PsychoacousticDimensionKey[];

function LabelForm({ clipId, existingLabel, autoLabel, onSave, onSkip, onPrev, onNext, saving }: LabelFormProps) {
  const [ratings, setRatings] = useState<Ratings>(() => getInitialRatings(existingLabel));
  const [notes, setNotes] = useState(() => existingLabel?.notes || '');
  const [showNotes, setShowNotes] = useState(() => !!existingLabel?.notes);
  const [activeDimension, setActiveDimension] = useState(0);
  const [justRated, setJustRated] = useState<string | null>(null);
  const [hoveredDot, setHoveredDot] = useState<{ dim: string; val: number } | null>(null);
  const [activeAxis, setActiveAxis] = useState<'perceptual' | 'psychoacoustic'>('perceptual');

  const animTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const autoSaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const perceptualComplete = PERCEPTUAL_KEYS.every((k) => ratings[k] != null);
  const psychoacousticComplete = PSYCHOACOUSTIC_KEYS.every((k) => ratings[k] != null);
  const perceptualRated = PERCEPTUAL_KEYS.filter((k) => ratings[k] != null).length;
  const psychoacousticRated = PSYCHOACOUSTIC_KEYS.filter((k) => ratings[k] != null).length;
  const isComplete = perceptualComplete; // Only Axis 1 required

  const currentDimensions = activeAxis === 'perceptual' ? PERCEPTUAL_DIMENSIONS : PSYCHOACOUSTIC_DIMENSIONS;

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
    setActiveAxis('perceptual');
    setJustRated(null);
    setHoveredDot(null);
  }, [clipId]); // Only reset on clipId change

  // Auto-save when Axis 1 is complete for the first time
  const prevCompleteRef = useRef(false);
  useEffect(() => {
    const wasComplete = prevCompleteRef.current;
    prevCompleteRef.current = isComplete;

    if (!wasComplete && isComplete && !existingLabel && !saving) {
      // Don't auto-save — wait for user to optionally rate Axis 2
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

    // Auto-advance to next unrated dimension within current axis
    const dims = PERCEPTUAL_KEYS.includes(dimKey as PerceptualDimensionKey)
      ? PERCEPTUAL_DIMENSIONS
      : PSYCHOACOUSTIC_DIMENSIONS;
    const idx = dims.findIndex((d) => d.key === dimKey);
    setRatings((prev) => {
      const updated = { ...prev, [dimKey]: value };
      for (let i = 1; i <= dims.length; i++) {
        const nextIdx = (idx + i) % dims.length;
        const nextDim = dims[nextIdx];
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
          const dim = currentDimensions[current];
          if (dim) handleRatingChange(dim.key, parseInt(key, 10) as RatingValue);
          return current;
        });
      } else if (key === 'Tab') {
        e.preventDefault();
        setActiveDimension((s) => (s + 1) % currentDimensions.length);
      } else if (key === 'Enter') {
        e.preventDefault();
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
  }, [onNext, onPrev, handleRatingChange, currentDimensions]);

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

  const renderDimensionGroup = (dimensions: (Dimension & { icon: React.ReactNode })[]) => (
    <div className="rating-dimensions">
      {dimensions.map((dim, i) => {
        const currentValue = ratings[dim.key];
        const isActive = activeAxis === (PERCEPTUAL_KEYS.includes(dim.key as PerceptualDimensionKey) ? 'perceptual' : 'psychoacoustic')
          && activeDimension === i;
        const wasJustRated = justRated === dim.key;

        return (
          <div
            key={dim.key}
            className={
              'rating-dim' +
              (isActive ? ' active' : '') +
              (wasJustRated ? ' just-rated' : '')
            }
            onClick={() => {
              const axis = PERCEPTUAL_KEYS.includes(dim.key as PerceptualDimensionKey) ? 'perceptual' : 'psychoacoustic';
              setActiveAxis(axis);
              setActiveDimension(i);
            }}
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
  );

  return (
    <div className={'label-form glass-panel' + (isComplete ? ' label-form-complete' : '')}>
      <div className="label-form-header">
        <span className="label-form-title">Rate This Clip</span>
        <span className="label-form-progress">
          {perceptualComplete && psychoacousticComplete ? (
            <span className="label-form-check">{'\u2713\u2713'}</span>
          ) : perceptualComplete ? (
            <span className="label-form-check">{'\u2713'}</span>
          ) : (
            <span className="label-form-counter">{perceptualRated}/4</span>
          )}
        </span>
      </div>

      {/* Axis Tabs */}
      <div className="axis-tabs">
        <button
          className={`axis-tab${activeAxis === 'perceptual' ? ' active' : ''}${perceptualComplete ? ' complete' : ''}`}
          onClick={() => { setActiveAxis('perceptual'); setActiveDimension(0); }}
        >
          How Does It Feel?
          <span className="axis-tab-count">{perceptualRated}/4</span>
        </button>
        <button
          className={`axis-tab${activeAxis === 'psychoacoustic' ? ' active' : ''}${psychoacousticComplete ? ' complete' : ''}`}
          onClick={() => { setActiveAxis('psychoacoustic'); setActiveDimension(0); }}
        >
          How Accurately Does It Represent?
          <span className="axis-tab-count">{psychoacousticRated}/5</span>
        </button>
      </div>

      {/* Active Axis Dimensions */}
      {activeAxis === 'perceptual'
        ? renderDimensionGroup(PERCEPTUAL_DIMENSIONS)
        : renderDimensionGroup(PSYCHOACOUSTIC_DIMENSIONS)
      }

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
