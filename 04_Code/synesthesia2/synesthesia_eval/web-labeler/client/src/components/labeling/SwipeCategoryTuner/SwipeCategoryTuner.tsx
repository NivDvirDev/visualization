import React, { useState } from 'react';
import { Slider, Button, Checkbox } from '../../atoms';
import './SwipeCategoryTuner.css';

export interface CategoryScores {
  sync_quality: number;
  harmony: number;
  aesthetic_quality: number;
  motion_smoothness: number;
}

interface Props {
  overallScore: number;
  skipCategories: boolean;
  onConfirm: (categories: CategoryScores) => void;
  onSkipToggle: (skip: boolean) => void;
}

const CATEGORIES: { key: keyof CategoryScores; label: string }[] = [
  { key: 'sync_quality', label: 'Sync' },
  { key: 'harmony', label: 'Harmony' },
  { key: 'aesthetic_quality', label: 'Aesthetic' },
  { key: 'motion_smoothness', label: 'Motion' },
];

const STAR_MARKS = [1, 2, 3, 4, 5].map((v) => ({ value: v }));

const SwipeCategoryTuner: React.FC<Props> = ({
  overallScore,
  skipCategories,
  onConfirm,
  onSkipToggle,
}) => {
  const [scores, setScores] = useState<CategoryScores>({
    sync_quality: overallScore,
    harmony: overallScore,
    aesthetic_quality: overallScore,
    motion_smoothness: overallScore,
  });

  const handleChange = (key: keyof CategoryScores, value: number) => {
    setScores((prev) => ({ ...prev, [key]: value }));
  };

  const stars = Array.from({ length: 5 }, (_, i) => (i < overallScore ? '\u2605' : '\u2606')).join('');

  return (
    <div className="swipe-tuner-overlay">
      <div className="swipe-tuner-panel">
        <div className="swipe-tuner-header">
          Score: {stars} ({overallScore})
        </div>

        <div className="swipe-tuner-sliders">
          {CATEGORIES.map(({ key, label }) => (
            <div key={key} className="swipe-tuner-row">
              <Slider
                label={label}
                value={scores[key]}
                min={1}
                max={5}
                step={1}
                marks={STAR_MARKS}
                showValue
                size="sm"
                onChange={(v) => handleChange(key, v)}
              />
            </div>
          ))}
        </div>

        <div className="swipe-tuner-skip">
          <Checkbox
            checked={skipCategories}
            onChange={(checked) => onSkipToggle(checked)}
            label="Skip categories"
          />
        </div>

        <Button variant="primary" size="md" onClick={() => onConfirm(scores)}>
          Next &rarr;
        </Button>
      </div>
    </div>
  );
};

export default SwipeCategoryTuner;
