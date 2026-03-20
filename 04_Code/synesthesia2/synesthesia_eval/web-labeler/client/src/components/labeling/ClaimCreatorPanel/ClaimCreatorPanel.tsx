import React, { useState } from 'react';
import { claimClip } from '../../../api';

interface Props {
  clipId: string;
  token: string | null;
  onClaimed: (info: unknown) => void;
}

export default function ClaimCreatorPanel({ clipId, token, onClaimed }: Props) {
  const [open, setOpen] = useState(false);
  const [url, setUrl] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  if (!token) {
    return (
      <div className="claim-panel claim-panel--nudge">
        <span>🎨 Is this your creation?</span>
        <a href="/app">Sign in to claim it</a>
      </div>
    );
  }

  if (success) {
    return <div className="claim-panel claim-panel--success">✅ Claimed! You can now edit the display credit below.</div>;
  }

  return (
    <div className="claim-panel">
      {!open ? (
        <button className="claim-panel__trigger" onClick={() => setOpen(true)}>
          🎨 Is this your creation? Claim it
        </button>
      ) : (
        <form
          className="claim-panel__form"
          onSubmit={async (e) => {
            e.preventDefault();
            setError(null);
            setLoading(true);
            try {
              const info = await claimClip(clipId, url, token);
              setSuccess(true);
              onClaimed(info);
            } catch (err) {
              setError(err instanceof Error ? err.message : 'Claim failed');
            } finally {
              setLoading(false);
            }
          }}
        >
          <label htmlFor="claim-url">Paste this video's YouTube URL to verify ownership</label>
          <input
            id="claim-url"
            type="url"
            placeholder="https://www.youtube.com/watch?v=..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
          />
          {error && <p className="claim-panel__error">{error}</p>}
          <div className="claim-panel__actions">
            <button type="submit" disabled={loading}>{loading ? 'Verifying…' : 'Claim'}</button>
            <button type="button" onClick={() => setOpen(false)}>Cancel</button>
          </div>
        </form>
      )}
    </div>
  );
}
