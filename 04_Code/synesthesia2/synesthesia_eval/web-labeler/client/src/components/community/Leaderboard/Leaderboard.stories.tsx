import React from 'react';
import type { Meta, StoryObj } from '@storybook/react-webpack5';
import Leaderboard from './Leaderboard';
import {
  mockUser,
  mockLeaderboard,
  mockMyStats,
  mockMyStatsWithAllBadges,
} from '../../../stories/mockData';

const meta: Meta<typeof Leaderboard> = {
  title: 'Stats/Leaderboard',
  component: Leaderboard,
  parameters: { layout: 'centered' },
};
export default meta;
type Story = StoryObj<typeof Leaderboard>;

export const WithData: Story = {
  args: {
    user: mockUser,
  },
  decorators: [
    (Story: React.ComponentType) => {
      const originalFetch = window.fetch;
      window.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = typeof input === 'string' ? input : input.toString();
        if (url.includes('/api/stats/leaderboard')) {
          return new Response(JSON.stringify(mockLeaderboard), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          });
        }
        if (url.includes('/api/stats/me')) {
          return new Response(JSON.stringify(mockMyStats), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          });
        }
        return originalFetch(input, init);
      }) as typeof fetch;
      return <Story />;
    },
  ],
};

export const WithBadges: Story = {
  args: {
    user: mockUser,
  },
  decorators: [
    (Story: React.ComponentType) => {
      const originalFetch = window.fetch;
      window.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = typeof input === 'string' ? input : input.toString();
        if (url.includes('/api/stats/leaderboard')) {
          return new Response(JSON.stringify(mockLeaderboard), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          });
        }
        if (url.includes('/api/stats/me')) {
          return new Response(JSON.stringify(mockMyStatsWithAllBadges), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          });
        }
        return originalFetch(input, init);
      }) as typeof fetch;
      return <Story />;
    },
  ],
};
