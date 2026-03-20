import React from 'react';
import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { GlassPanel } from './GlassPanel';

const meta: Meta<typeof GlassPanel> = {
  title: 'Atoms/GlassPanel',
  component: GlassPanel,
  parameters: {
    layout: 'padded',
    backgrounds: {
      default: 'brand',
      values: [{ name: 'brand', value: 'radial-gradient(ellipse at bottom right, #2D4263 0%, #F5F1E8 80%)' }],
    },
  },
  argTypes: {
    variant: { control: 'select', options: ['default', 'strong', 'overlay'] },
    padding: { control: 'select', options: ['none', 'sm', 'md', 'lg'] },
  },
};
export default meta;
type Story = StoryObj<typeof GlassPanel>;

const Content = () => (
  <div>
    <strong style={{ fontFamily: 'var(--font-display)', fontSize: '0.9rem' }}>Panel Content</strong>
    <p style={{ marginTop: 8, fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
      Glassmorphism container — used for cards, headers, footers, and overlays.
    </p>
  </div>
);

export const Default: Story = { args: { variant: 'default', children: <Content /> } };
export const Strong: Story = { args: { variant: 'strong', children: <Content /> } };
export const Overlay: Story = { args: { variant: 'overlay', children: <Content /> } };

export const AllVariants: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, maxWidth: 400 }}>
      {(['default','strong','overlay'] as const).map(v => (
        <GlassPanel key={v} variant={v}>
          <strong style={{ display: 'block', marginBottom: 4, fontFamily: 'var(--font-display)', fontSize: '0.75rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>{v}</strong>
          <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>Glass panel variant</p>
        </GlassPanel>
      ))}
    </div>
  ),
};
