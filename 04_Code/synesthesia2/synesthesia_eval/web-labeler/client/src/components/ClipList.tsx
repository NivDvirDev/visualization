import React from 'react';
import { ClipSummary, ClipMode } from '../types';

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

const ClipList: React.FC<ClipListProps> = ({
  clips,
  selectedClipId,
  onSelect,
  mode,
  onModeChange,
  onRandom,
}) => {
  return (
    <aside className="clip-list">
      <div className="clip-list-controls">
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
          Random Clip
        </button>
      </div>
      <div className="clip-items">
        {clips.length === 0 && (
          <div style={{ padding: '16px 12px', color: '#666', fontSize: 13 }}>
            No clips in this mode.
          </div>
        )}
        {clips.map((clip) => (
          <div
            key={clip.id}
            className={'clip-item' + (clip.id === selectedClipId ? ' selected' : '')}
            onClick={() => onSelect(clip.id)}
          >
            <span className={'status-dot ' + getStatusClass(clip)} />
            <span className="clip-item-id">{clip.id}</span>
            <span className="clip-item-desc">{clip.description || clip.filename}</span>
          </div>
        ))}
      </div>
    </aside>
  );
};

export default ClipList;
