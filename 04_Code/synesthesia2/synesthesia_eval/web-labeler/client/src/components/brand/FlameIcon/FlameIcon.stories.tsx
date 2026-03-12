import React from 'react';
import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { FlameIcon } from './FlameIcon';

const meta: Meta<typeof FlameIcon> = {
  title: 'Branding/FlameIcon',
  component: FlameIcon,
  parameters: { layout: 'centered' },
  argTypes: {
    size: { control: { type: 'range', min: 20, max: 200, step: 5 } },
    animate: { control: 'boolean' },
  },
};
export default meta;
type Story = StoryObj<typeof FlameIcon>;

export const Default: Story = {
  args: { size: 44, animate: true },
};

export const HeaderSize: Story = {
  args: { size: 40, animate: true },
};

export const Large: Story = {
  args: { size: 120, animate: true },
};

export const Static: Story = {
  args: { size: 44, animate: false },
};

export const OnDarkBackground: Story = {
  args: { size: 80, animate: true },
  decorators: [
    (Story: React.ComponentType) => (
      <div style={{ background: '#1A1A2E', padding: 40, borderRadius: 12 }}>
        <Story />
      </div>
    ),
  ],
};

export const AllSizes: Story = {
  render: () => (
    <div style={{ display: 'flex', alignItems: 'center', gap: 16, padding: 20 }}>
      <FlameIcon size={24} />
      <FlameIcon size={40} />
      <FlameIcon size={60} />
      <FlameIcon size={100} />
    </div>
  ),
};
