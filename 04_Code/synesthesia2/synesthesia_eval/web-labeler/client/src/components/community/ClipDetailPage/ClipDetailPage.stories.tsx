import React from 'react';
import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import ClipDetailPage from './ClipDetailPage';
import { mockClipDetail } from '../../../stories/mockData';

const meta: Meta<typeof ClipDetailPage> = {
  title: 'Public/ClipDetailPage',
  component: ClipDetailPage,
  parameters: { layout: 'fullscreen' },
  decorators: [
    (Story: React.ComponentType) => {
      const originalFetch = window.fetch;
      window.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = typeof input === 'string' ? input : input.toString();
        if (url.includes('/api/clips/')) {
          return new Response(JSON.stringify(mockClipDetail), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          });
        }
        if (url.includes('/api/config')) {
          return new Response(
            JSON.stringify({ useHuggingFace: false, googleClientId: null }),
            {
              status: 200,
              headers: { 'Content-Type': 'application/json' },
            }
          );
        }
        return originalFetch(input, init);
      }) as typeof fetch;
      return (
        <MemoryRouter initialEntries={['/clip/001']}>
          <Routes>
            <Route path="/clip/:id" element={<Story />} />
          </Routes>
        </MemoryRouter>
      );
    },
  ],
};
export default meta;
type Story = StoryObj<typeof ClipDetailPage>;

export const WithData: Story = {};
