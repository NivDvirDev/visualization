import React from 'react';
import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { Input } from './Input';

const meta: Meta<typeof Input> = {
  title: 'Atoms/Input',
  component: Input,
  parameters: { layout: 'centered' },
  decorators: [(Story: React.ComponentType) => <div style={{ width: 320 }}><Story /></div>],
};
export default meta;
type Story = StoryObj<typeof Input>;

export const Default: Story = { args: { label: 'Email', type: 'email', placeholder: 'you@example.com' } };
export const WithHint: Story = { args: { label: 'Username', placeholder: 'yourname', hint: 'Shown on leaderboard' } };
export const WithError: Story = { args: { label: 'Password', type: 'password', error: 'Password must be at least 8 characters' } };
export const Disabled: Story = { args: { label: 'Email', value: 'you@example.com', disabled: true } };
export const Password: Story = { args: { label: 'Password', type: 'password', placeholder: '••••••••' } };
