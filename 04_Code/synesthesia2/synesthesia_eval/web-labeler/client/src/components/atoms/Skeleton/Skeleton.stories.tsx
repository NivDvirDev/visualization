import React from 'react';
import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { Skeleton, SkeletonText, SkeletonCard } from './Skeleton';

const meta: Meta<typeof Skeleton> = {
  title: 'Atoms/Skeleton',
  component: Skeleton,
  parameters: {
    layout: 'padded',
    backgrounds: { default: 'parchment', values: [{ name: 'parchment', value: '#F5F1E8' }] },
  },
  argTypes: {
    variant: { control: 'select', options: ['text', 'rect', 'circle', 'card'] },
    animated: { control: 'boolean' },
    lines: { control: 'number' },
  },
};
export default meta;
type Story = StoryObj<typeof Skeleton>;

/* ---- Basic variants ---- */

export const RectDefault: Story = {
  args: { variant: 'rect', animated: true },
  render: (args: React.ComponentProps<typeof Skeleton>) => (
    <div style={{ width: 300 }}>
      <Skeleton {...args} />
    </div>
  ),
};

export const RectCustomSize: Story = {
  args: { variant: 'rect', width: 240, height: 180, animated: true },
};

export const CircleDefault: Story = {
  args: { variant: 'circle', width: 48, height: 48, animated: true },
};

export const CircleSizes: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
      <Skeleton variant="circle" width={24} height={24} />
      <Skeleton variant="circle" width={32} height={32} />
      <Skeleton variant="circle" width={40} height={40} />
      <Skeleton variant="circle" width={56} height={56} />
      <Skeleton variant="circle" width={72} height={72} />
    </div>
  ),
};

export const TextSingleLine: Story = {
  args: { variant: 'text', lines: 1, animated: true },
  render: (args: React.ComponentProps<typeof Skeleton>) => (
    <div style={{ width: 300 }}>
      <Skeleton {...args} />
    </div>
  ),
};

export const TextMultiLine: Story = {
  args: { variant: 'text', lines: 4, animated: true },
  render: (args: React.ComponentProps<typeof Skeleton>) => (
    <div style={{ width: 300 }}>
      <Skeleton {...args} />
    </div>
  ),
};

/* ---- Animated vs static ---- */
export const NotAnimated: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, width: 300 }}>
      <Skeleton variant="rect" height={80} animated={false} />
      <Skeleton variant="text" lines={3} animated={false} />
    </div>
  ),
};

/* ---- Pre-composed SkeletonText ---- */
export const ComposedSkeletonText: Story = {
  render: () => (
    <div style={{ width: 320 }}>
      <SkeletonText lines={4} />
    </div>
  ),
};

/* ---- Pre-composed SkeletonCard ---- */
export const ComposedSkeletonCard: Story = {
  render: () => (
    <div style={{ width: 280 }}>
      <SkeletonCard />
    </div>
  ),
};

/* ---- Multiple cards (loading grid) ---- */
export const CardGrid: Story = {
  render: () => (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, width: 700 }}>
      <SkeletonCard />
      <SkeletonCard />
      <SkeletonCard />
    </div>
  ),
};

/* ---- List rows ---- */
export const ListRows: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, width: 360 }}>
      {[1, 2, 3, 4].map((i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Skeleton variant="circle" width={40} height={40} />
          <div style={{ flex: 1 }}>
            <Skeleton variant="text" lines={1} width="55%" />
            <Skeleton variant="text" lines={1} width="80%" />
          </div>
        </div>
      ))}
    </div>
  ),
};
