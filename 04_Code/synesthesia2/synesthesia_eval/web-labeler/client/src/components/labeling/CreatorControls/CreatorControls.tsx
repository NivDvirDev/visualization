import React, { useState } from 'react';
import { updateCreatorDisplay, unclaimClip } from '../../../api';

interface Props {
  clipId: string;
  initialCredit: string | null;
  initialLink: string | null;
  initialVisible: boolean;
  token: string;
  onUpdate: (data: { display_credit: string; display_link: string; credit_visible: boolean }) => void;
  onUnclaim: () => void;
}

export default function CreatorControls({ clipId, initialCredit, initialLink, initialVisible, token, onUpdate, onUnclaim }: Props) {
  const [credit, setCredit] = useState(initialCredit || '');
  const [link, setLink] = useState(initialLink || '');
  const [visible, setVisible] = useState(initialVisible);
  const [saving, setSaving] = useState(false);
  const [confirming, setConfirming] = useState(false);

  return (
    <div className="creator-controls">
      <h4 className="creator-controls__title">Your Creator Settings</h4>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          setSaving(true);
          try {
            await updateCreatorDisplay(clipId, { display_credit: credit, display_link: link, credit_visible: visible }, token);
            onUpdate({ display_credit: credit, display_link: link, credit_visible: visible });
          } finally {
            setSaving(false);
          }
        }}
      >
        <label htmlFor="creator-credit">Display name</label>
        <input id="creator-credit" type="text" value={credit} onChange={(e) => setCredit(e.target.value)} placeholder="Your channel name" />

        <label htmlFor="creator-link">Link (optional)</label>
        <input id="creator-link" type="url" value={link} onChange={(e) => setLink(e.target.value)} placeholder="https://..." />

        <label className="creator-controls__toggle">
          <input type="checkbox" checked={visible} onChange={(e) => setVisible(e.target.checked)} />
          Show credit publicly
        </label>

        <button type="submit" disabled={saving}>{saving ? 'Saving…' : 'Save'}</button>
      </form>

      {!confirming ? (
        <button className="creator-controls__remove" onClick={() => setConfirming(true)}>Remove Claim</button>
      ) : (
        <div className="creator-controls__confirm">
          <span>Are you sure?</span>
          <button onClick={async () => {
            await unclaimClip(clipId, token);
            onUnclaim();
          }}>Yes, remove</button>
          <button onClick={() => setConfirming(false)}>Cancel</button>
        </div>
      )}
    </div>
  );
}
