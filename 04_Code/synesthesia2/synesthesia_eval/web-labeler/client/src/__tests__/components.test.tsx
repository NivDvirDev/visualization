/**
 * Component rendering tests — verify each component renders without errors
 * using the existing mock data from stories/mockData.ts.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

import {
  mockClips,
  mockStats,
  mockUser,
  mockLabels,
  mockClipDetail,
  mockLeaderboard,
  mockMyStats,
  mockClipRankings,
  mockExistingLabelFull,
  mockAutoLabel,
} from '../stories/mockData';

// ── Brand Components ────────────────────────────────────────────────────────

import { FlameIcon } from '../components/brand/FlameIcon/FlameIcon';
import { WellspringIcon } from '../components/brand/WellspringLogo/WellspringIcon/WellspringIcon';

describe('FlameIcon', () => {
  test('renders SVG', () => {
    const { container } = render(<FlameIcon size={40} />);
    expect(container.querySelector('svg')).toBeInTheDocument();
  });

  test('respects size prop', () => {
    const { container } = render(<FlameIcon size={80} />);
    const svg = container.querySelector('svg');
    expect(svg).toHaveAttribute('width', '80');
    expect(svg).toHaveAttribute('height', '80');
  });

  test('renders without animation when animate=false', () => {
    const { container } = render(<FlameIcon size={40} animate={false} />);
    expect(container.querySelector('svg')).toBeInTheDocument();
  });
});

describe('WellspringIcon', () => {
  test('renders SVG', () => {
    const { container } = render(<WellspringIcon size={200} />);
    expect(container.querySelector('svg')).toBeInTheDocument();
  });

  test('respects size prop', () => {
    const { container } = render(<WellspringIcon size={120} />);
    const svg = container.querySelector('svg');
    expect(svg).toHaveAttribute('width', '120');
    expect(svg).toHaveAttribute('height', '120');
  });
});

// ── Layout Components ───────────────────────────────────────────────────────

import Footer from '../components/layout/Footer/Footer';
import ProgressBar from '../components/layout/ProgressBar/ProgressBar';
import Header from '../components/layout/Header/Header';

describe('Footer', () => {
  test('renders branding text', () => {
    render(<MemoryRouter><Footer /></MemoryRouter>);
    expect(screen.getByText(/The Wellspring/i)).toBeInTheDocument();
  });
});

describe('ProgressBar', () => {
  test('renders with stats', () => {
    const { container } = render(
      <ProgressBar total={83} labeled={29} remaining={54} />
    );
    expect(container.querySelector('.global-progress')).toBeInTheDocument();
    expect(container.querySelector('.atom-score-bar')).toBeInTheDocument();
  });
});

describe('Header', () => {
  test('renders user info and controls', () => {
    render(
      <MemoryRouter>
        <Header
          stats={mockStats}
          user={mockUser}
          showLeaderboard={false}
          onToggleLeaderboard={jest.fn()}
          onLogout={jest.fn()}
          onNavigateRankings={jest.fn()}
        />
      </MemoryRouter>
    );
    expect(screen.getByText(mockUser.username)).toBeInTheDocument();
    expect(screen.getByText(/Logout/i)).toBeInTheDocument();
  });
});

// ── Labeling Components ─────────────────────────────────────────────────────

import ClipList from '../components/labeling/ClipList/ClipList';
import RatingsTable from '../components/labeling/RatingsTable/RatingsTable';
import LabelForm from '../components/labeling/LabelForm/LabelForm';

describe('ClipList', () => {
  test('renders clip thumbnails', () => {
    render(
      <ClipList
        clips={mockClips}
        selectedClipId="001"
        onSelect={jest.fn()}
        mode="all"
        onModeChange={jest.fn()}
        onRandom={jest.fn()}
      />
    );
    // ClipList renders clip items — check that clips are listed
    const clipElements = document.querySelectorAll('.clip-thumb');
    expect(clipElements.length).toBeGreaterThan(0);
  });

  test('renders mode buttons', () => {
    render(
      <ClipList
        clips={mockClips}
        selectedClipId={null}
        onSelect={jest.fn()}
        mode="unlabeled"
        onModeChange={jest.fn()}
        onRandom={jest.fn()}
      />
    );
    expect(screen.getByText(/Unlabeled/i)).toBeInTheDocument();
  });
});

describe('RatingsTable', () => {
  test('renders labels in table', () => {
    render(<RatingsTable labels={mockLabels} currentUsername="testuser" />);
    expect(screen.getByText('testuser')).toBeInTheDocument();
    expect(screen.getByText('alice')).toBeInTheDocument();
  });

  test('renders empty state', () => {
    const { container } = render(
      <RatingsTable labels={[]} currentUsername="testuser" />
    );
    expect(container).toBeTruthy();
  });
});

describe('LabelForm', () => {
  test('renders rating dimensions', () => {
    render(
      <LabelForm
        clipId="001"
        onSave={jest.fn()}
        onSkip={jest.fn()}
        onPrev={jest.fn()}
        onNext={jest.fn()}
        saving={false}
      />
    );
    // Dimension labels are abbreviated in the UI
    expect(screen.getByText('Sync')).toBeInTheDocument();
    expect(screen.getByText('Harmony')).toBeInTheDocument();
    expect(screen.getByText('Aesthetic')).toBeInTheDocument();
  });

  test('renders with existing label', () => {
    render(
      <LabelForm
        clipId="001"
        existingLabel={mockExistingLabelFull}
        autoLabel={mockAutoLabel}
        onSave={jest.fn()}
        onSkip={jest.fn()}
        onPrev={jest.fn()}
        onNext={jest.fn()}
        saving={false}
      />
    );
    expect(screen.getByText('Rate This Clip')).toBeInTheDocument();
    // Check that the selected dots reflect existing label values
    const selectedDots = document.querySelectorAll('.rating-dot.selected');
    expect(selectedDots.length).toBeGreaterThan(0);
  });
});

// ── Community Components ────────────────────────────────────────────────────

import StatsPanel from '../components/community/StatsPanel/StatsPanel';

describe('StatsPanel', () => {
  test('renders stat values', () => {
    render(<StatsPanel stats={mockStats} />);
    expect(screen.getByText('83')).toBeInTheDocument(); // total_clips
  });
});

// ── LoginPage ───────────────────────────────────────────────────────────────

import LoginPage from '../components/auth/LoginPage/LoginPage';

describe('LoginPage', () => {
  test('renders login form', () => {
    render(<LoginPage onLogin={jest.fn()} googleClientId={null} />);
    expect(screen.getByText('The Wellspring')).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
  });
});
