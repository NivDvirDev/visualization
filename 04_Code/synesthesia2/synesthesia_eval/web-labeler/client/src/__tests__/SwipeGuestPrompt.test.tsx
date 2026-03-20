import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

import SwipeGuestPrompt from '../components/labeling/SwipeGuestPrompt/SwipeGuestPrompt';

describe('SwipeGuestPrompt', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
  });

  it('renders heading "You\'ve rated 3 clips!"', () => {
    render(
      <MemoryRouter>
        <SwipeGuestPrompt onContinue={jest.fn()} />
      </MemoryRouter>
    );
    expect(screen.getByText("You've rated 3 clips!")).toBeInTheDocument();
  });

  it('renders Sign Up CTA button', () => {
    render(
      <MemoryRouter>
        <SwipeGuestPrompt onContinue={jest.fn()} />
      </MemoryRouter>
    );
    expect(screen.getByText('Sign Up to Save Scores')).toBeInTheDocument();
  });

  it('renders Keep exploring button', () => {
    render(
      <MemoryRouter>
        <SwipeGuestPrompt onContinue={jest.fn()} />
      </MemoryRouter>
    );
    expect(screen.getByText('Keep exploring (scores won\'t be saved)')).toBeInTheDocument();
  });

  it('Sign Up button calls navigate("/app")', () => {
    render(
      <MemoryRouter>
        <SwipeGuestPrompt onContinue={jest.fn()} />
      </MemoryRouter>
    );
    fireEvent.click(screen.getByText('Sign Up to Save Scores'));
    expect(mockNavigate).toHaveBeenCalledWith('/app');
  });

  it('Keep exploring button calls onContinue', () => {
    const onContinue = jest.fn();
    render(
      <MemoryRouter>
        <SwipeGuestPrompt onContinue={onContinue} />
      </MemoryRouter>
    );
    fireEvent.click(screen.getByText('Keep exploring (scores won\'t be saved)'));
    expect(onContinue).toHaveBeenCalled();
  });

  it('renders the 🎧 icon', () => {
    render(
      <MemoryRouter>
        <SwipeGuestPrompt onContinue={jest.fn()} />
      </MemoryRouter>
    );
    expect(screen.getByText('🎧')).toBeInTheDocument();
  });

  it('renders sign-up description text', () => {
    render(
      <MemoryRouter>
        <SwipeGuestPrompt onContinue={jest.fn()} />
      </MemoryRouter>
    );
    expect(screen.getByText(/earn badges/i)).toBeInTheDocument();
  });
});
