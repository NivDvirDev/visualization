import React from 'react';
import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { MemoryRouter } from 'react-router-dom';
import RankingsPage from './RankingsPage';
import {
  mockLeaderboard,
  mockClipRankings,
  mockStats,
} from '../../../stories/mockData';

const meta: Meta<typeof RankingsPage> = {
  title: 'Public/RankingsPage',
  component: RankingsPage,
  parameters: { layout: 'fullscreen' },
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
        if (url.includes('/api/clips/rankings')) {
          return new Response(JSON.stringify(mockClipRankings), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          });
        }
        if (url.includes('/api/stats')) {
          return new Response(JSON.stringify(mockStats), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          });
        }
        return originalFetch(input, init);
      }) as typeof fetch;
      return (
        <MemoryRouter initialEntries={['/rankings']}>
          <Story />
        </MemoryRouter>
      );
    },
  ],
};
export default meta;
type Story = StoryObj<typeof RankingsPage>;

export const ClipsTab: Story = {};

export const RatersTab: Story = {};
