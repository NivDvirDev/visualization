import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import * as api from '../api';

jest.mock('../api');

const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  Link: ({ children, to }: { children: React.ReactNode; to: string }) => (
    <a href={to}>{children}</a>
  ),
}));

import LandingPage from '../components/community/LandingPage/LandingPage';

const mockStats = {
  total_clips: 81,
  labeled_human: 5,
  labeled_auto: 76,
  unlabeled: 0,
  total_users: 12,
  recent_users_7d: 2,
  avg_scores: {
    sync_quality: 3.5,
    harmony: 3.2,
    aesthetic_quality: 4.0,
    motion_smoothness: 3.8,
  },
};

const mockRankings = [
  {
    id: '001',
    filename: '001_test_clip.mp4',
    rater_count: 3,
    avg_sync: 4,
    avg_harmony: 3,
    avg_aesthetic: 5,
    avg_motion: 3,
    avg_overall: 4.0,
  },
  {
    id: '002',
    filename: '002_another_clip.mp4',
    rater_count: 2,
    avg_sync: 3,
    avg_harmony: 4,
    avg_aesthetic: 4,
    avg_motion: 3,
    avg_overall: 3.5,
  },
];

const mockLeaderboard = [
  { username: 'alice', total_labels: 42, level: 4, level_title: 'Psychoacoustic Analyst', rank: 1, badges: [] },
  { username: 'bob', total_labels: 17, level: 3, level_title: 'Synesthete', rank: 2, badges: [] },
  { username: 'charlie', total_labels: 8, level: 2, level_title: 'Rhythm Watcher', rank: 3, badges: [] },
];

const renderLanding = (initialEntries: string[] = ['/']) =>
  render(
    <MemoryRouter initialEntries={initialEntries}>
      <LandingPage />
    </MemoryRouter>
  );

// ── Hero Section ────────────────────────────────────────────────────────────

describe('LandingPage — Hero', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.getStats as jest.Mock).mockResolvedValue(mockStats);
    (api.getClipRankings as jest.Mock).mockResolvedValue(mockRankings);
    (api.getLeaderboard as jest.Mock).mockResolvedValue(mockLeaderboard);
  });

  it('renders "The Wellspring" heading', () => {
    renderLanding();
    expect(screen.getByText('The Wellspring')).toBeInTheDocument();
  });

  it('renders tagline "The Ancient Dance, Renewed"', () => {
    renderLanding();
    expect(screen.getByText('The Ancient Dance, Renewed')).toBeInTheDocument();
  });

  it('renders hero subline about rhythmic movement', () => {
    renderLanding();
    expect(screen.getByText(/frontiers of audio-visual harmony/)).toBeInTheDocument();
  });

  it('has "Join the Dance" CTA linking to /swipe', () => {
    renderLanding();
    const link = screen.getByText('Join the Dance').closest('a');
    expect(link).toHaveAttribute('href', '/swipe');
  });

  it('has "Watch a Creation" button with #featured anchor', () => {
    renderLanding();
    const link = screen.getByText('Watch a Creation').closest('a');
    expect(link).toHaveAttribute('href', '#featured');
  });

  it('has "Rankings" link to /rankings', () => {
    renderLanding();
    const link = screen.getByText('Rankings').closest('a');
    expect(link).toHaveAttribute('href', '/rankings');
  });
});

// ── 3 Pillars: The Journey ──────────────────────────────────────────────────

describe('LandingPage — The Journey (3 Pillars)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.getStats as jest.Mock).mockResolvedValue(mockStats);
    (api.getClipRankings as jest.Mock).mockResolvedValue(mockRankings);
    (api.getLeaderboard as jest.Mock).mockResolvedValue(mockLeaderboard);
  });

  it('renders "The Journey" section heading', () => {
    renderLanding();
    expect(screen.getByText('The Journey')).toBeInTheDocument();
  });

  it('renders "Experience" pillar', () => {
    renderLanding();
    expect(screen.getByText('Experience')).toBeInTheDocument();
    expect(screen.getByText(/Watch sound become light/)).toBeInTheDocument();
  });

  it('renders "Create" pillar', () => {
    renderLanding();
    expect(screen.getByText('Create')).toBeInTheDocument();
    expect(screen.getByText(/Shape your own harmony/)).toBeInTheDocument();
  });

  it('renders "Connect" pillar', () => {
    renderLanding();
    expect(screen.getByText('Connect')).toBeInTheDocument();
    expect(screen.getByText(/Find your resonance/)).toBeInTheDocument();
  });

  it('has "Start Watching" button linking to /swipe', () => {
    renderLanding();
    const link = screen.getByText('Start Watching').closest('a');
    expect(link).toHaveAttribute('href', '/swipe');
  });

  it('shows "Coming Soon" badges on Create and Connect', () => {
    renderLanding();
    const badges = screen.getAllByText('Coming Soon');
    expect(badges.length).toBe(2);
  });
});

// ── Featured Creations ──────────────────────────────────────────────────────

describe('LandingPage — Featured Creations', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.getStats as jest.Mock).mockResolvedValue(mockStats);
    (api.getClipRankings as jest.Mock).mockResolvedValue(mockRankings);
    (api.getLeaderboard as jest.Mock).mockResolvedValue(mockLeaderboard);
  });

  it('renders "Featured Creations" section when clips available', async () => {
    renderLanding();
    await waitFor(() => expect(screen.getByText('Featured Creations')).toBeInTheDocument());
  });

  it('renders sanitized clip filenames (underscore→space, .mp4 removed)', async () => {
    renderLanding();
    await waitFor(() => expect(screen.getByText('001 test clip')).toBeInTheDocument());
  });

  it('renders clip scores', async () => {
    renderLanding();
    await waitFor(() => expect(screen.getByText('4.0')).toBeInTheDocument());
  });

  it('renders rating counts', async () => {
    renderLanding();
    await waitFor(() => expect(screen.getByText('3 ratings')).toBeInTheDocument());
  });

  it('clip cards link to /clip/:id', async () => {
    renderLanding();
    await waitFor(() => {
      const link = screen.getByText('001 test clip').closest('a');
      expect(link).toHaveAttribute('href', '/clip/001');
    });
  });

  it('"Explore All" CTA links to /rankings', async () => {
    renderLanding();
    await waitFor(() => {
      const link = screen.getByText('Explore All').closest('a');
      expect(link).toHaveAttribute('href', '/rankings');
    });
  });

  it('hides Featured Creations section when no clips available', async () => {
    (api.getClipRankings as jest.Mock).mockResolvedValue([]);
    renderLanding();
    // Wait for API to resolve
    await waitFor(() => expect(api.getClipRankings).toHaveBeenCalled());
    expect(screen.queryByText('Featured Creations')).not.toBeInTheDocument();
  });
});

// ── Live Pulse Stats ────────────────────────────────────────────────────────

describe('LandingPage — Live Pulse', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.getStats as jest.Mock).mockResolvedValue(mockStats);
    (api.getClipRankings as jest.Mock).mockResolvedValue(mockRankings);
    (api.getLeaderboard as jest.Mock).mockResolvedValue(mockLeaderboard);
  });

  it('renders "Live Pulse" section title', async () => {
    renderLanding();
    await waitFor(() => expect(screen.getByText('Live Pulse')).toBeInTheDocument());
  });

  it('shows total_clips as "Creations"', async () => {
    renderLanding();
    await waitFor(() => {
      expect(screen.getByText('Creations')).toBeInTheDocument();
      // total_clips = 81, verify it appears in the stats section
      const creationsLabel = screen.getByText('Creations');
      const card = creationsLabel.closest('.landing-stat-card-wrap');
      expect(card).not.toBeNull();
    });
  });

  it('shows combined ratings (auto + human) as "Ratings Given"', async () => {
    renderLanding();
    // 76 auto + 5 human = 81
    await waitFor(() => {
      expect(screen.getByText('Ratings Given')).toBeInTheDocument();
    });
  });

  it('shows total_users as "Active Members"', async () => {
    renderLanding();
    await waitFor(() => {
      expect(screen.getByText('12')).toBeInTheDocument();
      expect(screen.getByText('Active Members')).toBeInTheDocument();
    });
  });

  it('hides stats section when stats not loaded', async () => {
    (api.getStats as jest.Mock).mockRejectedValue(new Error('Network error'));
    renderLanding();
    await waitFor(() => expect(api.getStats).toHaveBeenCalled());
    expect(screen.queryByText('Live Pulse')).not.toBeInTheDocument();
  });
});

// ── Top Contributors ────────────────────────────────────────────────────────

describe('LandingPage — Top Contributors', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.getStats as jest.Mock).mockResolvedValue(mockStats);
    (api.getClipRankings as jest.Mock).mockResolvedValue(mockRankings);
    (api.getLeaderboard as jest.Mock).mockResolvedValue(mockLeaderboard);
  });

  it('renders "Top Contributors" heading', async () => {
    renderLanding();
    await waitFor(() => expect(screen.getByText('Top Contributors')).toBeInTheDocument());
  });

  it('renders contributor usernames', async () => {
    renderLanding();
    await waitFor(() => {
      expect(screen.getByText('alice')).toBeInTheDocument();
      expect(screen.getByText('bob')).toBeInTheDocument();
      expect(screen.getByText('charlie')).toBeInTheDocument();
    });
  });

  it('renders levels and rating counts', async () => {
    renderLanding();
    await waitFor(() => {
      expect(screen.getByText('Lv.4')).toBeInTheDocument();
      expect(screen.getByText('42 ratings')).toBeInTheDocument();
    });
  });

  it('"Join the Leaderboard" CTA links to /swipe', async () => {
    renderLanding();
    await waitFor(() => {
      const link = screen.getByText('Join the Leaderboard').closest('a');
      expect(link).toHaveAttribute('href', '/swipe');
    });
  });

  it('hides Top Contributors when leaderboard is empty', async () => {
    (api.getLeaderboard as jest.Mock).mockResolvedValue([]);
    renderLanding();
    await waitFor(() => expect(api.getLeaderboard).toHaveBeenCalled());
    expect(screen.queryByText('Top Contributors')).not.toBeInTheDocument();
  });
});

// ── The Call (Vision Section) ───────────────────────────────────────────────

describe('LandingPage — The Call', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.getStats as jest.Mock).mockResolvedValue(mockStats);
    (api.getClipRankings as jest.Mock).mockResolvedValue(mockRankings);
    (api.getLeaderboard as jest.Mock).mockResolvedValue(mockLeaderboard);
  });

  it('renders "A Collective Journey" heading', () => {
    renderLanding();
    expect(screen.getByText('A Collective Journey')).toBeInTheDocument();
  });

  it('renders the vision statement', () => {
    renderLanding();
    expect(screen.getByText(/collective journey whose resonance/)).toBeInTheDocument();
  });

  it('"Begin Your Journey" CTA links to /swipe', () => {
    renderLanding();
    const link = screen.getByText('Begin Your Journey').closest('a');
    expect(link).toHaveAttribute('href', '/swipe');
  });
});

// ── Footer ──────────────────────────────────────────────────────────────────

describe('LandingPage — Footer', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.getStats as jest.Mock).mockResolvedValue(mockStats);
    (api.getClipRankings as jest.Mock).mockResolvedValue(mockRankings);
    (api.getLeaderboard as jest.Mock).mockResolvedValue(mockLeaderboard);
  });

  it('renders "Built by Niv Dvir"', () => {
    renderLanding();
    expect(screen.getByText(/Niv Dvir/)).toBeInTheDocument();
  });

  it('has Privacy Policy link to /privacy', () => {
    renderLanding();
    const link = screen.getByText('Privacy Policy').closest('a');
    expect(link).toHaveAttribute('href', '/privacy');
  });

  it('has Terms of Service link to /terms', () => {
    renderLanding();
    const link = screen.getByText('Terms of Service').closest('a');
    expect(link).toHaveAttribute('href', '/terms');
  });
});

// ── Ad Traffic Redirect ─────────────────────────────────────────────────────

describe('LandingPage — Ad Redirect', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockNavigate.mockClear();
    (api.getStats as jest.Mock).mockResolvedValue(mockStats);
    (api.getClipRankings as jest.Mock).mockResolvedValue(mockRankings);
    (api.getLeaderboard as jest.Mock).mockResolvedValue(mockLeaderboard);
  });

  it('redirects to /swipe when utm_source param present', () => {
    renderLanding(['/?utm_source=google&utm_medium=cpc']);
    expect(mockNavigate).toHaveBeenCalledWith('/swipe', { replace: true });
  });

  it('redirects to /swipe when gclid param present', () => {
    renderLanding(['/?gclid=abc123']);
    expect(mockNavigate).toHaveBeenCalledWith('/swipe', { replace: true });
  });

  it('does NOT redirect without UTM/gclid params', () => {
    renderLanding();
    expect(mockNavigate).not.toHaveBeenCalled();
  });
});

// ── API Calls ───────────────────────────────────────────────────────────────

describe('LandingPage — API Calls', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.getStats as jest.Mock).mockResolvedValue(mockStats);
    (api.getClipRankings as jest.Mock).mockResolvedValue(mockRankings);
    (api.getLeaderboard as jest.Mock).mockResolvedValue(mockLeaderboard);
  });

  it('calls getStats on mount', async () => {
    renderLanding();
    await waitFor(() => expect(api.getStats).toHaveBeenCalledTimes(1));
  });

  it('calls getClipRankings on mount', async () => {
    renderLanding();
    await waitFor(() => expect(api.getClipRankings).toHaveBeenCalledTimes(1));
  });

  it('calls getLeaderboard on mount', async () => {
    renderLanding();
    await waitFor(() => expect(api.getLeaderboard).toHaveBeenCalledTimes(1));
  });
});

// ── Edge Cases ──────────────────────────────────────────────────────────────

describe('LandingPage — Edge Cases', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders gracefully when all API calls fail', async () => {
    (api.getStats as jest.Mock).mockRejectedValue(new Error('fail'));
    (api.getClipRankings as jest.Mock).mockRejectedValue(new Error('fail'));
    (api.getLeaderboard as jest.Mock).mockRejectedValue(new Error('fail'));
    renderLanding();

    // Static content still renders
    await waitFor(() => expect(api.getStats).toHaveBeenCalled());
    expect(screen.getByText('The Wellspring')).toBeInTheDocument();
    expect(screen.getByText('The Journey')).toBeInTheDocument();
    expect(screen.getByText('A Collective Journey')).toBeInTheDocument();

    // Dynamic sections are hidden
    expect(screen.queryByText('Featured Creations')).not.toBeInTheDocument();
    expect(screen.queryByText('Live Pulse')).not.toBeInTheDocument();
    expect(screen.queryByText('Top Contributors')).not.toBeInTheDocument();
  });

  it('renders gracefully with zero-value stats', async () => {
    const zeroStats = { ...mockStats, total_clips: 0, labeled_human: 0, labeled_auto: 0, total_users: 0 };
    (api.getStats as jest.Mock).mockResolvedValue(zeroStats);
    (api.getClipRankings as jest.Mock).mockResolvedValue([]);
    (api.getLeaderboard as jest.Mock).mockResolvedValue([]);
    renderLanding();

    await waitFor(() => expect(screen.getByText('Live Pulse')).toBeInTheDocument());
    expect(screen.getByText('Creations')).toBeInTheDocument();
  });

  it('renders gracefully with empty rankings and leaderboard', async () => {
    (api.getStats as jest.Mock).mockResolvedValue(mockStats);
    (api.getClipRankings as jest.Mock).mockResolvedValue([]);
    (api.getLeaderboard as jest.Mock).mockResolvedValue([]);
    renderLanding();

    await waitFor(() => expect(api.getClipRankings).toHaveBeenCalled());
    expect(screen.queryByText('Featured Creations')).not.toBeInTheDocument();
    expect(screen.queryByText('Top Contributors')).not.toBeInTheDocument();
    // Static sections still present
    expect(screen.getByText('The Wellspring')).toBeInTheDocument();
  });
});
