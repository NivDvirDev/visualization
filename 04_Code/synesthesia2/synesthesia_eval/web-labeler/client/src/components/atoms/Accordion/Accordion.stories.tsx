import React from 'react';
import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { Accordion } from './Accordion';

const meta: Meta<typeof Accordion> = {
  title: 'Atoms/Accordion',
  component: Accordion,
  parameters: {
    layout: 'padded',
    backgrounds: {
      default: 'parchment',
      values: [{ name: 'parchment', value: '#F5F1E8' }],
    },
  },
  argTypes: {
    variant: { control: 'select', options: ['default', 'flush', 'glass'] },
    allowMultiple: { control: 'boolean' },
  },
};
export default meta;
type Story = StoryObj<typeof Accordion>;

const ITEMS = [
  {
    id: 'sync',
    title: 'Sync Quality — What does it measure?',
    content: (
      <p>
        Sync quality measures how well the visual motion matches the beat, rhythm, and transients of
        the audio. A perfect score of 5 means every visual pulse aligns precisely with a drum hit or
        melodic accent.
      </p>
    ),
  },
  {
    id: 'alignment',
    title: 'Visual-Audio Alignment — Frequency mapping',
    content: (
      <p>
        This dimension rates how faithfully the cochlear spiral represents the frequency content of
        the audio. Low frequencies should drive the inner spiral; high frequencies the outer rings.
        The mapping follows ISO 226 equal-loudness normalization.
      </p>
    ),
  },
  {
    id: 'aesthetics',
    title: 'Aesthetic Quality — Visual appeal',
    content: (
      <p>
        A holistic rating of how beautiful, coherent, and engaging the visualization looks —
        independent of its technical accuracy. Considers color harmony, trail smoothness, and overall
        compositional balance.
      </p>
    ),
  },
  {
    id: 'motion',
    title: 'Motion Smoothness — Temporal continuity',
    content: (
      <p>
        Rates whether motion feels fluid and organic rather than jittery or discontinuous. Key
        parameters: trail length (10 frames), decay rate (0.70), and frame interpolation quality.
      </p>
    ),
  },
  {
    id: 'locked',
    title: 'Advanced Metrics (Premium)',
    content: <p>Available with a Premium account.</p>,
    disabled: true,
  },
];

export const Default: Story = {
  render: () => (
    <div style={{ width: 520 }}>
      <Accordion items={ITEMS} variant="default" defaultOpen={['sync']} />
    </div>
  ),
};

export const Flush: Story = {
  render: () => (
    <div style={{ width: 520 }}>
      <Accordion items={ITEMS.slice(0, 4)} variant="flush" defaultOpen={['alignment']} />
    </div>
  ),
};

export const Glass: Story = {
  render: () => (
    <div style={{ width: 520 }}>
      <Accordion items={ITEMS.slice(0, 4)} variant="glass" defaultOpen={['aesthetics']} />
    </div>
  ),
};

export const AllowMultiple: Story = {
  render: () => (
    <div style={{ width: 520 }}>
      <Accordion
        items={ITEMS.slice(0, 4)}
        variant="default"
        allowMultiple
        defaultOpen={['sync', 'motion']}
      />
    </div>
  ),
};

export const WithDisabledItem: Story = {
  render: () => (
    <div style={{ width: 520 }}>
      <Accordion items={ITEMS} variant="default" defaultOpen={['sync']} />
    </div>
  ),
};

export const AllVariants: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 40, width: 520 }}>
      <div>
        <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>Default</p>
        <Accordion items={ITEMS.slice(0, 2)} variant="default" defaultOpen={['sync']} />
      </div>
      <div>
        <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>Flush</p>
        <Accordion items={ITEMS.slice(0, 2)} variant="flush" defaultOpen={['alignment']} />
      </div>
      <div>
        <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>Glass</p>
        <Accordion items={ITEMS.slice(0, 2)} variant="glass" defaultOpen={['sync']} />
      </div>
    </div>
  ),
};
