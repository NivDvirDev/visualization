import React from 'react';
import { render, screen } from '@testing-library/react';
import SwipeScoreOverlay from '../components/labeling/SwipeScoreOverlay/SwipeScoreOverlay';

describe('SwipeScoreOverlay', () => {
  it('renders nothing when score is null', () => {
    const { container } = render(<SwipeScoreOverlay score={null} ratio={0} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('renders score number for score 4', () => {
    render(<SwipeScoreOverlay score={4} ratio={0.7} />);
    expect(screen.getByText('4')).toBeInTheDocument();
  });

  it('shows "Awful" for score 1', () => {
    render(<SwipeScoreOverlay score={1} ratio={-0.8} />);
    expect(screen.getByText('Awful')).toBeInTheDocument();
  });

  it('shows "Bad" for score 2', () => {
    render(<SwipeScoreOverlay score={2} ratio={-0.4} />);
    expect(screen.getByText('Bad')).toBeInTheDocument();
  });

  it('shows "OK" for score 3', () => {
    render(<SwipeScoreOverlay score={3} ratio={0.1} />);
    expect(screen.getByText('OK')).toBeInTheDocument();
  });

  it('shows "Good" for score 4', () => {
    render(<SwipeScoreOverlay score={4} ratio={0.4} />);
    expect(screen.getByText('Good')).toBeInTheDocument();
  });

  it('shows "Love it!" for score 5', () => {
    render(<SwipeScoreOverlay score={5} ratio={0.9} />);
    expect(screen.getByText('Love it!')).toBeInTheDocument();
  });

  it('renders emoji for each score', () => {
    const { rerender } = render(<SwipeScoreOverlay score={1} ratio={-0.8} />);
    // Score 1 → ❌
    expect(screen.getByText('❌')).toBeInTheDocument();

    rerender(<SwipeScoreOverlay score={5} ratio={0.8} />);
    // Score 5 → ✨
    expect(screen.getByText('✨')).toBeInTheDocument();
  });

  it('renders the numeric score value in the overlay', () => {
    render(<SwipeScoreOverlay score={3} ratio={0.5} />);
    expect(screen.getByText('3')).toBeInTheDocument();
  });
});
