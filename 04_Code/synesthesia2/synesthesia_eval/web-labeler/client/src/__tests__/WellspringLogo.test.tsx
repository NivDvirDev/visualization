import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  Link: ({ children, to }: { children: React.ReactNode; to: string }) => (
    <a href={to}>{children}</a>
  ),
}));

import WellspringLogo from '../components/brand/WellspringLogo/WellspringLogo';

const renderHero = () =>
  render(
    <MemoryRouter>
      <WellspringLogo />
    </MemoryRouter>
  );

describe('WellspringLogo (Hero Section)', () => {
  it('renders "The Wellspring" title', () => {
    renderHero();
    expect(screen.getByText('The Wellspring')).toBeInTheDocument();
    expect(screen.getByText('The Wellspring').tagName).toBe('H1');
  });

  it('renders tagline "The Ancient Dance, Renewed"', () => {
    renderHero();
    expect(screen.getByText('The Ancient Dance, Renewed')).toBeInTheDocument();
  });

  it('renders subline about audio-visual harmony', () => {
    renderHero();
    expect(screen.getByText(/we dance together/)).toBeInTheDocument();
  });

  it('renders "Join the Dance" primary CTA', () => {
    renderHero();
    expect(screen.getByText('Join the Dance')).toBeInTheDocument();
  });

  it('"Join the Dance" links to /swipe', () => {
    renderHero();
    const link = screen.getByText('Join the Dance').closest('a');
    expect(link).toHaveAttribute('href', '/swipe');
  });

  it('renders "Watch a Creation" secondary CTA', () => {
    renderHero();
    expect(screen.getByText('Watch a Creation')).toBeInTheDocument();
  });

  it('"Watch a Creation" links to #featured anchor', () => {
    renderHero();
    const link = screen.getByText('Watch a Creation').closest('a');
    expect(link).toHaveAttribute('href', '#featured');
  });

  it('renders "Rankings" secondary CTA', () => {
    renderHero();
    expect(screen.getByText('Rankings')).toBeInTheDocument();
  });

  it('"Rankings" links to /rankings', () => {
    renderHero();
    const link = screen.getByText('Rankings').closest('a');
    expect(link).toHaveAttribute('href', '/rankings');
  });

  it('renders hero background element', () => {
    const { container } = renderHero();
    expect(container.querySelector('.landing-hero-bg')).toBeInTheDocument();
  });

  it('renders hero glow element', () => {
    const { container } = renderHero();
    expect(container.querySelector('.landing-hero-glow')).toBeInTheDocument();
  });

  it('renders hero content wrapper', () => {
    const { container } = renderHero();
    expect(container.querySelector('.landing-hero-content')).toBeInTheDocument();
  });

  it('hero background is aria-hidden', () => {
    const { container } = renderHero();
    const bg = container.querySelector('.landing-hero-bg');
    expect(bg).toHaveAttribute('aria-hidden', 'true');
  });
});
