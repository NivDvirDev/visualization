import React, { Component } from 'react';
import { Dimension, DimensionKey, Label, LabelData, RatingValue } from '../types';

const DIMENSIONS: Dimension[] = [
  {
    key: 'sync_quality',
    label: 'Sync Quality',
    descriptions: {
      1: 'No sync at all',
      2: 'Occasional sync',
      3: 'Moderate sync',
      4: 'Good sync',
      5: 'Perfect sync',
    },
  },
  {
    key: 'visual_audio_alignment',
    label: 'Visual-Audio Alignment',
    descriptions: {
      1: 'Completely mismatched',
      2: 'Poorly aligned',
      3: 'Somewhat aligned',
      4: 'Well aligned',
      5: 'Perfect alignment',
    },
  },
  {
    key: 'aesthetic_quality',
    label: 'Aesthetic Quality',
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
    label: 'Motion Smoothness',
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

interface LabelFormState {
  sync_quality: number | null;
  visual_audio_alignment: number | null;
  aesthetic_quality: number | null;
  motion_smoothness: number | null;
  notes: string;
}

class LabelForm extends Component<LabelFormProps, LabelFormState> {
  private focusedDimension: number;

  constructor(props: LabelFormProps) {
    super(props);
    this.focusedDimension = 0;
    this.state = this.getInitialState(props);
  }

  getInitialState(props: LabelFormProps): LabelFormState {
    const label = props.existingLabel;
    if (label) {
      return {
        sync_quality: label.sync_quality ?? null,
        visual_audio_alignment: label.visual_audio_alignment ?? null,
        aesthetic_quality: label.aesthetic_quality ?? null,
        motion_smoothness: label.motion_smoothness ?? null,
        notes: label.notes || '',
      };
    }
    return {
      sync_quality: null,
      visual_audio_alignment: null,
      aesthetic_quality: null,
      motion_smoothness: null,
      notes: '',
    };
  }

  componentDidUpdate(prevProps: LabelFormProps) {
    if (prevProps.clipId !== this.props.clipId) {
      this.setState(this.getInitialState(this.props));
      this.focusedDimension = 0;
    }
  }

  componentDidMount() {
    document.addEventListener('keydown', this.handleKeyDown);
  }

  componentWillUnmount() {
    document.removeEventListener('keydown', this.handleKeyDown);
  }

  handleKeyDown = (e: KeyboardEvent) => {
    const target = e.target as HTMLElement;
    if (target.tagName === 'TEXTAREA' || target.tagName === 'INPUT') return;

    const key = e.key;

    if (key >= '1' && key <= '5') {
      e.preventDefault();
      const dim = DIMENSIONS[this.focusedDimension];
      this.setState({ [dim.key]: parseInt(key, 10) } as Pick<LabelFormState, DimensionKey>);
      if (this.focusedDimension < DIMENSIONS.length - 1) {
        this.focusedDimension++;
      }
    } else if (key === 'n') {
      e.preventDefault();
      this.props.onNext();
    } else if (key === 'p') {
      e.preventDefault();
      this.props.onPrev();
    } else if (key === 's' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      this.handleSave();
    }
  };

  handleRatingChange = (dimKey: DimensionKey, value: RatingValue) => {
    this.setState({ [dimKey]: value } as Pick<LabelFormState, DimensionKey>);
    const idx = DIMENSIONS.findIndex((d) => d.key === dimKey);
    this.focusedDimension = Math.min(idx + 1, DIMENSIONS.length - 1);
  };

  handleSave = () => {
    const { clipId, onSave } = this.props;
    const { sync_quality, visual_audio_alignment, aesthetic_quality, motion_smoothness, notes } = this.state;
    onSave(clipId, { sync_quality, visual_audio_alignment, aesthetic_quality, motion_smoothness, notes });
  };

  isComplete(): boolean {
    return DIMENSIONS.every((d) => this.state[d.key] != null);
  }

  render() {
    const { autoLabel, onSkip, saving } = this.props;

    return (
      <div className="label-form">
        <h3>Label This Clip</h3>

        {autoLabel && (
          <div className="auto-label-compare">
            <h4>Auto Label ({autoLabel.labeler})</h4>
            <div className="auto-label-scores">
              {DIMENSIONS.map((dim) => (
                <div key={dim.key} className="auto-label-score">
                  <span className="dim-label">{dim.label}:</span>
                  <span className="dim-value">{autoLabel[dim.key] ?? '\u2014'}</span>
                </div>
              ))}
            </div>
            {autoLabel.notes && (
              <div style={{ marginTop: 8, fontSize: 12, color: '#aaa', fontStyle: 'italic' }}>
                {autoLabel.notes}
              </div>
            )}
          </div>
        )}

        <div className="rating-dimensions">
          {DIMENSIONS.map((dim) => (
            <div key={dim.key} className="rating-group">
              <label>
                {dim.label}
                {this.state[dim.key] && (
                  <span style={{ fontWeight: 400, color: '#888', marginLeft: 8 }}>
                    — {dim.descriptions[this.state[dim.key] as RatingValue]}
                  </span>
                )}
              </label>
              <div className="rating-options">
                {([1, 2, 3, 4, 5] as RatingValue[]).map((val) => (
                  <label key={val} className="rating-option">
                    <input
                      type="radio"
                      name={dim.key}
                      value={val}
                      checked={this.state[dim.key] === val}
                      onChange={() => this.handleRatingChange(dim.key, val)}
                    />
                    <span>{val}</span>
                  </label>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="notes-field">
          <label>Notes</label>
          <textarea
            value={this.state.notes}
            onChange={(e) => this.setState({ notes: e.target.value })}
            placeholder="Optional notes about this clip..."
          />
        </div>

        <div className="form-actions">
          <button
            className="btn btn-save"
            onClick={this.handleSave}
            disabled={!this.isComplete() || saving}
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
          <button className="btn btn-skip" onClick={onSkip}>
            Skip
          </button>
          <button className="btn btn-nav" onClick={this.props.onPrev}>
            Prev
          </button>
          <button className="btn btn-nav" onClick={this.props.onNext}>
            Next
          </button>
        </div>

        <div className="keyboard-hint">
          Keys: 1-5 rate &middot; n/p next/prev &middot; Cmd+S save
        </div>
      </div>
    );
  }
}

export default LabelForm;
