import React from 'react';
import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { Typography } from './Typography';

const meta: Meta<typeof Typography> = {
  title: 'Atoms/Typography',
  component: Typography,
  parameters: { layout: 'padded' },
  argTypes: {
    variant: {
      control: 'select',
      options: ['display-xl','display-lg','display-md','display-sm','body-lg','body-md','body-sm','label','caption','mono','mono-stat'],
    },
    color: { control: 'select', options: ['primary','secondary','muted','accent','bright','gradient'] },
  },
};
export default meta;
type Story = StoryObj<typeof Typography>;

export const Default: Story = {
  args: { variant: 'display-lg', children: 'The Wellspring' },
};

export const TypeScale: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div>
        <Typography variant="caption" color="muted">display-xl · Orbitron 700</Typography>
        <Typography variant="display-xl">The Wellspring</Typography>
      </div>
      <div>
        <Typography variant="caption" color="muted">display-lg · Orbitron 700</Typography>
        <Typography variant="display-lg">Quick Rate</Typography>
      </div>
      <div>
        <Typography variant="caption" color="muted">display-md · Orbitron 600</Typography>
        <Typography variant="display-md">How It Works</Typography>
      </div>
      <div>
        <Typography variant="caption" color="muted">display-sm · Orbitron uppercase</Typography>
        <Typography variant="display-sm">Section Label</Typography>
      </div>
      <hr style={{ borderColor: 'var(--border-separator)' }} />
      <div>
        <Typography variant="caption" color="muted">body-lg · Inter 400</Typography>
        <Typography variant="body-lg">Watch audio visualizations. Rate them on sync, aesthetics, and motion.</Typography>
      </div>
      <div>
        <Typography variant="caption" color="muted">body-md · Inter 400</Typography>
        <Typography variant="body-md">Compare your perception with AI. Climb the leaderboard.</Typography>
      </div>
      <div>
        <Typography variant="caption" color="muted">body-sm · Inter 400</Typography>
        <Typography variant="body-sm">Your ratings help train AI to understand visual music.</Typography>
      </div>
      <hr style={{ borderColor: 'var(--border-separator)' }} />
      <div>
        <Typography variant="caption" color="muted">mono · Space Mono</Typography>
        <Typography variant="mono">clip_001.mp4 · score: 4.2</Typography>
      </div>
      <div>
        <Typography variant="caption" color="muted">mono-stat · Space Mono 700</Typography>
        <Typography variant="mono-stat" color="accent">4.2</Typography>
      </div>
    </div>
  ),
};

export const Colors: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {(['primary','secondary','muted','accent','bright','gradient'] as const).map(c => (
        <Typography key={c} variant="display-md" color={c}>{c}</Typography>
      ))}
    </div>
  ),
};
