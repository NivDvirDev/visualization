import React from 'react';
import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { Divider } from './Divider';

const meta: Meta<typeof Divider> = {
  title: 'Atoms/Divider',
  component: Divider,
  parameters: { layout: 'padded' },
  argTypes: {
    variant: { control: 'select', options: ['subtle', 'default', 'strong'] },
    spacing: { control: 'select', options: ['none', 'sm', 'md', 'lg'] },
  },
};
export default meta;
type Story = StoryObj<typeof Divider>;

export const Default: Story = { args: { variant: 'default' } };
export const AllVariants: Story = {
  render: () => (
    <div>
      <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>subtle</p>
      <Divider variant="subtle" />
      <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>default</p>
      <Divider variant="default" />
      <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>strong</p>
      <Divider variant="strong" />
    </div>
  ),
};
