import React from 'react';
import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { ScoreBar } from './ScoreBar';

const meta: Meta<typeof ScoreBar> = {
  title: 'Atoms/ScoreBar',
  component: ScoreBar,
  parameters: { layout: 'padded' },
  decorators: [(Story: React.ComponentType) => <div style={{ maxWidth: 320 }}><Story /></div>],
  argTypes: {
    size: { control: 'select', options: ['sm', 'md', 'lg'] },
    value: { control: { type: 'range', min: 0, max: 5, step: 0.1 } },
  },
};
export default meta;
type Story = StoryObj<typeof ScoreBar>;

export const Default: Story = { args: { value: 3.7 } };
export const Full: Story = { args: { value: 5 } };
export const Zero: Story = { args: { value: 0 } };

export const AllSizes: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <ScoreBar size="sm" value={4.2} />
      <ScoreBar size="md" value={3.5} />
      <ScoreBar size="lg" value={2.8} />
    </div>
  ),
};

export const ScoreList: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {[['Sync', 4.2], ['Alignment', 3.8], ['Aesthetic', 4.7], ['Motion', 3.1]].map(([label, val]) => (
        <div key={label as string} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ width: 72, fontSize: '0.8rem', color: 'var(--color-text-secondary)', flexShrink: 0 }}>{label}</span>
          <ScoreBar value={val as number} size="md" />
        </div>
      ))}
    </div>
  ),
};
