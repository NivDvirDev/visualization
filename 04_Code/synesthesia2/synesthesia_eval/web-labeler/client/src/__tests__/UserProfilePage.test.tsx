import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import * as api from '../api';

jest.mock('../api');

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({ username: 'testuser' }),
  useNavigate: () => jest.fn(),
}));

import UserProfilePage from '../components/community/UserProfilePage/UserProfilePage';

const mockProfile = {
  username: 'testuser',
  created_at: '2026-01-01T00:00:00Z',
  total_labels: 5,
  rank: 1,
  level: 1,
  level_title: 'Novice Listener',
  badges: ['first_label'] as const,
  perceptual: {
    sync_quality: 4,
    harmony: 3,
    aesthetic_quality: 5,
    motion_smoothness: 2,
  },
  personality: {
    key: 'aesthetic_quality',
    emoji: '🎨',
    label: 'Aesthetic Visionary',
    desc: 'Beauty above all.',
  },
};

describe('UserProfilePage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('calls getUserProfile with username from params', async () => {
    (api.getUserProfile as jest.Mock).mockResolvedValue(mockProfile);
    render(
      <MemoryRouter>
        <UserProfilePage />
      </MemoryRouter>
    );
    await waitFor(() => expect(api.getUserProfile).toHaveBeenCalledWith('testuser'));
  });

  it('renders username with @ prefix', async () => {
    (api.getUserProfile as jest.Mock).mockResolvedValue(mockProfile);
    render(
      <MemoryRouter>
        <UserProfilePage />
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getAllByText('@testuser').length).toBeGreaterThan(0));
  });

  it('renders level_title', async () => {
    (api.getUserProfile as jest.Mock).mockResolvedValue(mockProfile);
    render(
      <MemoryRouter>
        <UserProfilePage />
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByText('Novice Listener')).toBeInTheDocument());
  });

  it('renders total_labels', async () => {
    (api.getUserProfile as jest.Mock).mockResolvedValue(mockProfile);
    render(
      <MemoryRouter>
        <UserProfilePage />
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByText('5')).toBeInTheDocument());
  });

  it('renders first_label badge pill', async () => {
    (api.getUserProfile as jest.Mock).mockResolvedValue(mockProfile);
    render(
      <MemoryRouter>
        <UserProfilePage />
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByText(/First Label/i)).toBeInTheDocument());
  });

  it('renders global rank', async () => {
    (api.getUserProfile as jest.Mock).mockResolvedValue(mockProfile);
    render(
      <MemoryRouter>
        <UserProfilePage />
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByText('#1')).toBeInTheDocument());
  });

  it('shows error message for 404', async () => {
    (api.getUserProfile as jest.Mock).mockRejectedValue(new Error('Not found'));
    render(
      <MemoryRouter>
        <UserProfilePage />
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByText(/not found/i)).toBeInTheDocument());
  });

  it('renders personality label from profile', async () => {
    (api.getUserProfile as jest.Mock).mockResolvedValue(mockProfile);
    render(
      <MemoryRouter>
        <UserProfilePage />
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByText('Aesthetic Visionary')).toBeInTheDocument());
  });

  it('renders Taste Profile section heading', async () => {
    (api.getUserProfile as jest.Mock).mockResolvedValue(mockProfile);
    render(
      <MemoryRouter>
        <UserProfilePage />
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByText('Taste Profile')).toBeInTheDocument());
  });
});
