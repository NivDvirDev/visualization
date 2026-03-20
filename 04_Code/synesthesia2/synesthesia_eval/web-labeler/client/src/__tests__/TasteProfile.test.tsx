import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import TasteProfile from '../components/community/TasteProfile/TasteProfile';
import * as api from '../api';

jest.mock('../api');

const mockProfile = {
  label_count: 5,
  perceptual: {
    sync_quality: 4,
    harmony: 3,
    aesthetic_quality: 5,
    motion_smoothness: 2,
  },
  psychoacoustic: {
    pitch_accuracy: 3,
    rhythm_accuracy: 3,
    dynamics_accuracy: 3,
    timbre_accuracy: 3,
    melody_accuracy: 3,
  },
  personality: {
    key: 'aesthetic_quality',
    emoji: '🎨',
    label: 'Aesthetic Visionary',
    desc: 'Beauty above all.',
  },
};

describe('TasteProfile', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders nothing when label_count is 0', () => {
    const { container } = render(
      <TasteProfile data={{ ...mockProfile, label_count: 0 }} />
    );
    expect(container).toBeEmptyDOMElement();
  });

  it('renders personality label when data has labels', () => {
    render(<TasteProfile data={mockProfile} />);
    expect(screen.getByText('Aesthetic Visionary')).toBeInTheDocument();
  });

  it('renders personality emoji', () => {
    render(<TasteProfile data={mockProfile} />);
    expect(screen.getByText('🎨')).toBeInTheDocument();
  });

  it('renders personality description', () => {
    render(<TasteProfile data={mockProfile} />);
    expect(screen.getByText('Beauty above all.')).toBeInTheDocument();
  });

  it('renders Sync dimension label', () => {
    render(<TasteProfile data={mockProfile} />);
    expect(screen.getByText('Sync')).toBeInTheDocument();
  });

  it('renders Harmony dimension label', () => {
    render(<TasteProfile data={mockProfile} />);
    expect(screen.getByText('Harmony')).toBeInTheDocument();
  });

  it('renders Aesthetics dimension label', () => {
    render(<TasteProfile data={mockProfile} />);
    expect(screen.getByText('Aesthetics')).toBeInTheDocument();
  });

  it('renders Motion dimension label', () => {
    render(<TasteProfile data={mockProfile} />);
    expect(screen.getByText('Motion')).toBeInTheDocument();
  });

  it('calls getMyTasteProfile when no data prop is provided', async () => {
    (api.getMyTasteProfile as jest.Mock).mockResolvedValue(mockProfile);
    render(<TasteProfile />);
    await waitFor(() => expect(api.getMyTasteProfile).toHaveBeenCalled());
  });

  it('renders profile data returned by getMyTasteProfile', async () => {
    (api.getMyTasteProfile as jest.Mock).mockResolvedValue(mockProfile);
    render(<TasteProfile />);
    await waitFor(() => expect(screen.getByText('Aesthetic Visionary')).toBeInTheDocument());
  });

  it('renders nothing when getMyTasteProfile returns label_count 0', async () => {
    (api.getMyTasteProfile as jest.Mock).mockResolvedValue({
      ...mockProfile,
      label_count: 0,
    });
    const { container } = render(<TasteProfile />);
    await waitFor(() => expect(api.getMyTasteProfile).toHaveBeenCalled());
    expect(container).toBeEmptyDOMElement();
  });

  it('renders numeric bar values for each dimension', () => {
    render(<TasteProfile data={mockProfile} />);
    // aesthetic_quality = 5.0
    expect(screen.getByText('5.0')).toBeInTheDocument();
    // sync_quality = 4.0
    expect(screen.getByText('4.0')).toBeInTheDocument();
  });
});
