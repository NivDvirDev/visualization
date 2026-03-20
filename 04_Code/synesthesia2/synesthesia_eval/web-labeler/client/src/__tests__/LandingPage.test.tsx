import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import * as api from '../api';

jest.mock('../api');

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => jest.fn(),
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
    filename: '001_test.mp4',
    rater_count: 3,
    avg_sync: 4,
    avg_harmony: 3,
    avg_aesthetic: 5,
    avg_motion: 3,
    avg_overall: 4,
  },
];

const mockLeaderboard = [
  { username: 'user1', total_labels: 10, level: 2, level_title: 'Rhythm Watcher', rank: 1, badges: [] },
];

describe('LandingPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.getStats as jest.Mock).mockResolvedValue(mockStats);
    (api.getClipRankings as jest.Mock).mockResolvedValue(mockRankings);
    (api.getLeaderboard as jest.Mock).mockResolvedValue(mockLeaderboard);
  });

  it('renders hero heading "The Wellspring"', async () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByText('The Wellspring')).toBeInTheDocument());
  });

  it('calls getStats on mount', async () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>
    );
    await waitFor(() => expect(api.getStats).toHaveBeenCalled());
  });

  it('calls getClipRankings on mount', async () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>
    );
    await waitFor(() => expect(api.getClipRankings).toHaveBeenCalled());
  });

  it('calls getLeaderboard on mount', async () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>
    );
    await waitFor(() => expect(api.getLeaderboard).toHaveBeenCalled());
  });

  it('renders total_clips count from stats', async () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByText('81')).toBeInTheDocument());
  });

  it('renders top clip filename (sanitized)', async () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>
    );
    // filename: '001_test.mp4' → displayed as '001 test' (underscores → spaces, .mp4 removed)
    await waitFor(() => expect(screen.getByText('001 test')).toBeInTheDocument());
  });

  it('renders top rater username', async () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByText('user1')).toBeInTheDocument());
  });

  it('has link to /swipe for quick mode', async () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>
    );
    await waitFor(() => {
      const link = screen.getByText(/Try Quick Mode/i).closest('a');
      expect(link).toHaveAttribute('href', '/swipe');
    });
  });

  it('renders "How It Works" section', async () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByText('How It Works')).toBeInTheDocument());
  });

  it('renders "Top Raters" section when leaderboard has entries', async () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByText('Top Raters')).toBeInTheDocument());
  });

  it('renders labeled_human count as Human Ratings', async () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByText('5')).toBeInTheDocument());
  });
});
