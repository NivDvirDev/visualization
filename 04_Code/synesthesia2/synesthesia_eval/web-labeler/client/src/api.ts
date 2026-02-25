import { ClipSummary, ClipDetail, ClipMode, Label, SaveLabelPayload, Stats } from './types';

const API = '/api';

export const getClips = (mode: ClipMode): Promise<ClipSummary[]> =>
  fetch(`${API}/clips?mode=${mode}`).then((r) => r.json());

export const getClip = (id: string): Promise<ClipDetail> =>
  fetch(`${API}/clips/${id}`).then((r) => r.json());

export const getLabels = (clipId: string): Promise<Label[]> =>
  fetch(`${API}/labels/${clipId}`).then((r) => r.json());

export const saveLabel = (clipId: string, data: SaveLabelPayload): Promise<unknown> =>
  fetch(`${API}/labels/${clipId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }).then((r) => r.json());

export const deleteLabel = (clipId: string, labeler: string): Promise<unknown> =>
  fetch(`${API}/labels/${clipId}/${encodeURIComponent(labeler)}`, {
    method: 'DELETE',
  }).then((r) => r.json());

export const getStats = (): Promise<Stats> =>
  fetch(`${API}/stats`).then((r) => r.json());

export const exportLabels = (): Promise<unknown> =>
  fetch(`${API}/labels/export?format=json`).then((r) => r.json());
