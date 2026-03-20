/**
 * Route tests — verify the Router-only App.tsx renders correct components
 * for each route path.
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from '../App';

// Mock fetch globally for components that call APIs on mount
beforeEach(() => {
  global.fetch = jest.fn((input: RequestInfo | URL) => {
    const url = typeof input === 'string' ? input : input.toString();

    if (url.includes('/api/config')) {
      return Promise.resolve(
        new Response(
          JSON.stringify({ useHuggingFace: false, googleClientId: null }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      );
    }
    if (url.includes('/api/auth/me')) {
      return Promise.resolve(new Response(null, { status: 401 }));
    }
    if (url.includes('/api/stats/leaderboard')) {
      return Promise.resolve(
        new Response(JSON.stringify([]), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );
    }
    if (url.includes('/api/clips/rankings')) {
      return Promise.resolve(
        new Response(JSON.stringify([]), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );
    }
    if (url.includes('/api/clips/')) {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            id: '001',
            filename: 'test.mp4',
            labels: [],
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      );
    }
    if (url.includes('/api/stats')) {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            total_clips: 10,
            labeled_human: 5,
            labeled_auto: 3,
            unlabeled: 2,
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      );
    }
    if (url.includes('/api/clips')) {
      return Promise.resolve(
        new Response(JSON.stringify([]), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );
    }

    return Promise.resolve(new Response(null, { status: 404 }));
  }) as jest.Mock;
});

afterEach(() => {
  jest.restoreAllMocks();
});

describe('App routing', () => {
  test('root path renders LandingPage', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );
    // Root now shows LandingPage (public landing)
    await waitFor(() => {
      expect(document.querySelector('.landing-page')).toBeInTheDocument();
    });
  });

  test('/rankings path renders RankingsPage', async () => {
    render(
      <MemoryRouter initialEntries={['/rankings']}>
        <App />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(document.querySelector('.rankings-page')).toBeInTheDocument();
    });
  });

  test('/clip/:id path renders ClipDetailPage', async () => {
    render(
      <MemoryRouter initialEntries={['/clip/001']}>
        <App />
      </MemoryRouter>
    );
    await waitFor(() => {
      // ClipDetailPage fetches clip data
      expect(document.querySelector('.clip-detail-page')).toBeInTheDocument();
    });
  });
});
