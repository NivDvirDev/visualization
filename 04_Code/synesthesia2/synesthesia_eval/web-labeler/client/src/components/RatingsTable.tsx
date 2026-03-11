import React from 'react';
import { Label, DimensionKey } from '../types';

interface RatingsTableProps {
  labels: Label[];
  currentUsername?: string;
}

const PERCEPTUAL_DIMS: { key: DimensionKey; short: string }[] = [
  { key: 'sync_quality', short: 'Sync' },
  { key: 'harmony', short: 'Harm' },
  { key: 'aesthetic_quality', short: 'Aesth' },
  { key: 'motion_smoothness', short: 'Motion' },
];

const PSYCHOACOUSTIC_DIMS: { key: DimensionKey; short: string }[] = [
  { key: 'pitch_accuracy', short: 'Pitch' },
  { key: 'rhythm_accuracy', short: 'Rhythm' },
  { key: 'dynamics_accuracy', short: 'Dyn' },
  { key: 'timbre_accuracy', short: 'Timbre' },
  { key: 'melody_accuracy', short: 'Melody' },
];

const ALL_DIMS = [...PERCEPTUAL_DIMS, ...PSYCHOACOUSTIC_DIMS];

function averageScore(labels: Label[], key: DimensionKey): string {
  const vals = labels.map((l) => l[key]).filter((v) => v != null) as number[];
  if (vals.length === 0) return '\u2014';
  return (vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1);
}

function formatDate(dateStr?: string): string {
  if (!dateStr) return '\u2014';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

const RatingsTable: React.FC<RatingsTableProps> = ({ labels, currentUsername }) => {
  const userLabels = labels.filter((l) => l.user_id != null);
  const autoLabels = labels.filter((l) => l.user_id == null);

  if (userLabels.length === 0 && autoLabels.length === 0) {
    return null;
  }

  // Check if any label has psychoacoustic data
  const hasPsychoacoustic = labels.some((l) =>
    PSYCHOACOUSTIC_DIMS.some((d) => l[d.key] != null)
  );
  const displayDims = hasPsychoacoustic ? ALL_DIMS : PERCEPTUAL_DIMS;

  return (
    <div className="ratings-table-container">
      <h4 className="ratings-table-title">
        All Ratings ({userLabels.length} user{userLabels.length !== 1 ? 's' : ''}
        {autoLabels.length > 0 ? ` + ${autoLabels.length} auto` : ''})
      </h4>

      <div className="ratings-table-scroll">
        <table className="ratings-table">
          <thead>
            <tr>
              <th>Rater</th>
              {PERCEPTUAL_DIMS.map((d) => (
                <th key={d.key} className="ratings-th-perceptual">{d.short}</th>
              ))}
              {hasPsychoacoustic && (
                <>
                  <th className="ratings-th-separator"></th>
                  {PSYCHOACOUSTIC_DIMS.map((d) => (
                    <th key={d.key} className="ratings-th-psychoacoustic">{d.short}</th>
                  ))}
                </>
              )}
              <th>Notes</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            {/* Average row */}
            {userLabels.length > 1 && (
              <tr className="ratings-row-avg">
                <td className="ratings-rater">Average</td>
                {PERCEPTUAL_DIMS.map((d) => (
                  <td key={d.key} className="ratings-score ratings-score-avg">
                    {averageScore(userLabels, d.key)}
                  </td>
                ))}
                {hasPsychoacoustic && (
                  <>
                    <td className="ratings-separator"></td>
                    {PSYCHOACOUSTIC_DIMS.map((d) => (
                      <td key={d.key} className="ratings-score ratings-score-avg">
                        {averageScore(userLabels, d.key)}
                      </td>
                    ))}
                  </>
                )}
                <td></td>
                <td></td>
              </tr>
            )}
            {/* User labels */}
            {userLabels.map((label, i) => {
              const isMe = label.username === currentUsername;
              return (
                <tr key={`user-${i}`} className={isMe ? 'ratings-row-me' : ''}>
                  <td className="ratings-rater">
                    {label.username || label.labeler}
                    {isMe && <span className="ratings-you-badge">you</span>}
                  </td>
                  {PERCEPTUAL_DIMS.map((d) => (
                    <td key={d.key} className="ratings-score">
                      {label[d.key] ?? '\u2014'}
                    </td>
                  ))}
                  {hasPsychoacoustic && (
                    <>
                      <td className="ratings-separator"></td>
                      {PSYCHOACOUSTIC_DIMS.map((d) => (
                        <td key={d.key} className="ratings-score">
                          {label[d.key] ?? '\u2014'}
                        </td>
                      ))}
                    </>
                  )}
                  <td className="ratings-notes">{label.notes || '\u2014'}</td>
                  <td className="ratings-date">{formatDate(label.updated_at || label.created_at)}</td>
                </tr>
              );
            })}
            {/* Auto labels */}
            {autoLabels.map((label, i) => (
              <tr key={`auto-${i}`} className="ratings-row-auto">
                <td className="ratings-rater">
                  {label.labeler}
                  <span className="ratings-auto-badge">AI</span>
                </td>
                {PERCEPTUAL_DIMS.map((d) => (
                  <td key={d.key} className="ratings-score ratings-score-auto">
                    {label[d.key] ?? '\u2014'}
                  </td>
                ))}
                {hasPsychoacoustic && (
                  <>
                    <td className="ratings-separator"></td>
                    {PSYCHOACOUSTIC_DIMS.map((d) => (
                      <td key={d.key} className="ratings-score ratings-score-auto">
                        {label[d.key] ?? '\u2014'}
                      </td>
                    ))}
                  </>
                )}
                <td className="ratings-notes">{label.notes || '\u2014'}</td>
                <td className="ratings-date">{formatDate(label.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default RatingsTable;
