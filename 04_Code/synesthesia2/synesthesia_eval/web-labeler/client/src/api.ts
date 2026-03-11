import { ClipSummary, ClipDetail, ClipMode, Label, LabelData, Stats, AuthResponse, User, AppConfig, LeaderboardEntry, MyStats, ClipRanking } from './types';

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
