import React from 'react';
import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { Badge } from './Badge';

const meta: Meta<typeof Badge> = {
  title: 'Atoms/Badge',
  component: Badge,
  parameters: { layout: 'centered' },
  argTypes: {
    variant: { control: 'select', options: ['accent','success','error','warning','neutral','bright'] },
    size: { control: 'select', options: ['sm','md'] },
    dot: { control: 'boolean' },
  },
};
export default meta;
type Story = StoryObj<typeof Badge>;

export const Default: Story = { args: { variant: 'accent', children: '12' } };
export const WithDot: Story = { args: { variant: 'success', dot: true, children: 'Live' } };

export const AllVariants: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
      <Badge variant="accent">Accent · 42</Badge>
      <Badge variant="success" dot>Saved</Badge>
      <Badge variant="error">Error</Badge>
      <Badge variant="warning">Caution</Badge>
      <Badge variant="neutral">Neutral</Badge>
      <Badge variant="bright">Gold</Badge>
    </div>
  ),
};
