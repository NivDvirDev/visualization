import { ClipSummary, ClipDetail, ClipMode, Label, LabelData, Stats, AuthResponse, User, AppConfig, LeaderboardEntry, MyStats, ClipRanking, Challenge, TasteProfile, UserProfile } from './types';

const API = '/api';

function getToken(): string | null {
  return localStorage.getItem('token');
}

function authHeaders(): Record<string, string> {
  const token = getToken();
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return headers;
}

// Auth API
export const register = (username: string, email: string, password: string): Promise<AuthResponse> =>
  fetch(`${API}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password }),
  }).then(async (r) => {
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || 'Registration failed');
    return data;
  });

export const login = (email: string, password: string): Promise<AuthResponse> =>
  fetch(`${API}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  }).then(async (r) => {
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || 'Login failed');
    return data;
  });

export const googleLogin = (credential: string): Promise<AuthResponse> =>
  fetch(`${API}/auth/google`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ credential }),
  }).then(async (r) => {
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || 'Google sign-in failed');
    return data;
  });

export const getMe = (): Promise<User> =>
  fetch(`${API}/auth/me`, {
    headers: authHeaders(),
  }).then(async (r) => {
    if (!r.ok) throw new Error('Not authenticated');
    return r.json();
  });

// Config API
export const getConfig = (): Promise<AppConfig> =>
  fetch(`${API}/config`).then((r) => r.json());

// Video URL API
export const getVideoUrl = (filename: string): Promise<string> =>
  fetch(`${API}/video-url/${encodeURIComponent(filename)}`).then((r) => r.json()).then((d) => d.url);

// Clips API
export const getClips = (mode: ClipMode): Promise<ClipSummary[]> =>
  fetch(`${API}/clips?mode=${mode}`).then((r) => r.json());

export const getClip = (id: string): Promise<ClipDetail> =>
  fetch(`${API}/clips/${id}`).then((r) => r.json());

// Labels API
export const getLabels = (clipId: string): Promise<Label[]> =>
  fetch(`${API}/labels/${clipId}`).then((r) => r.json());

export const saveLabel = (clipId: string, data: LabelData): Promise<unknown> =>
  fetch(`${API}/labels/${clipId}`, {
    method: 'PUT',
    headers: authHeaders(),
    body: JSON.stringify(data),
  }).then(async (r) => {
    const json = await r.json();
    if (!r.ok) throw new Error(json.error || 'Save failed');
    return json;
  });

export const saveSwipeLabel = async (
  clipId: string,
  score: number,
  token: string | null,
  categories?: { sync_quality: number; harmony: number; aesthetic_quality: number; motion_smoothness: number }
): Promise<unknown> => {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const body: Record<string, unknown> = { overall_impression: score, notes: '' };
  if (categories) Object.assign(body, categories);
  const r = await fetch(`${API}/labels/${clipId}`, {
    method: 'PUT',
    headers,
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const json = await r.json().catch(() => ({ error: 'Unknown error' }));
    const err = new Error(json.error || `Save failed (${r.status})`);
    (err as any).status = r.status;
    throw err;
  }
  return r.json();
};

// Save anonymous guest rating — no auth required
export const saveAnonymousLabel = async (
  clipId: string,
  score: number,
  sessionId: string,
): Promise<unknown> => {
  const r = await fetch(`${API}/labels/anonymous`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      clip_id: clipId,
      overall_score: score,
      sync_quality: score,
      harmony: score,
      aesthetic_quality: score,
      motion_smoothness: score,
      session_id: sessionId,
    }),
  });
  if (!r.ok) {
    const json = await r.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(json.error || `Anonymous save failed (${r.status})`);
  }
  return r.json();
};

export const deleteLabel = (clipId: string, labeler: string): Promise<unknown> =>
  fetch(`${API}/labels/${clipId}/${encodeURIComponent(labeler)}`, {
    method: 'DELETE',
    headers: authHeaders(),
  }).then((r) => r.json());

// Stats API
export const getStats = (): Promise<Stats> =>
  fetch(`${API}/stats`).then((r) => r.json());

export const exportLabels = (): Promise<unknown> =>
  fetch(`${API}/labels/export?format=json`).then((r) => r.json());

// Leaderboard API
export const getLeaderboard = (): Promise<LeaderboardEntry[]> =>
  fetch(`${API}/stats/leaderboard`).then((r) => r.json());

export const getMyStats = (): Promise<MyStats> =>
  fetch(`${API}/stats/me`, {
    headers: authHeaders(),
  }).then(async (r) => {
    if (!r.ok) throw new Error('Failed to fetch stats');
    return r.json();
  });

// Clip Rankings API
export const getClipRankings = (): Promise<ClipRanking[]> =>
  fetch(`${API}/clips/rankings`).then((r) => r.json());

// Weekly Challenge API
export const getChallenge = (): Promise<Challenge> =>
  fetch(`${API}/stats/challenge`).then((r) => r.json());

// Taste Profile API
export const getMyTasteProfile = (): Promise<TasteProfile> =>
  fetch(`${API}/stats/me/profile`, {
    headers: authHeaders(),
  }).then(async (r) => {
    if (!r.ok) throw new Error('Failed to fetch taste profile');
    return r.json();
  });

// Public User Profile API
export const getUserProfile = (username: string): Promise<UserProfile> =>
  fetch(`${API}/users/${encodeURIComponent(username)}`).then(async (r) => {
    if (!r.ok) throw new Error('User not found');
    return r.json();
  });

// Creator Attribution API
export const claimClip = async (clipId: string, youtubeUrl: string, token: string): Promise<unknown> => {
  const r = await fetch(`${API}/clips/${clipId}/claim`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ youtube_url: youtubeUrl }),
  });
  const json = await r.json();
  if (!r.ok) throw new Error(json.error || 'Claim failed');
  return json;
};

export const unclaimClip = async (clipId: string, token: string): Promise<void> => {
  const r = await fetch(`${API}/clips/${clipId}/claim`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!r.ok) { const json = await r.json(); throw new Error(json.error || 'Unclaim failed'); }
};

export const updateCreatorDisplay = async (
  clipId: string,
  data: { display_credit?: string; display_link?: string; credit_visible?: boolean },
  token: string
): Promise<unknown> => {
  const r = await fetch(`${API}/clips/${clipId}/creator`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify(data),
  });
  const json = await r.json();
  if (!r.ok) throw new Error(json.error || 'Update failed');
  return json;
};
