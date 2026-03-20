import React from 'react';
import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { Avatar, AvatarGroup } from './Avatar';

const meta: Meta<typeof Avatar> = {
  title: 'Atoms/Avatar',
  component: Avatar,
  parameters: {
    layout: 'centered',
    backgrounds: { default: 'parchment', values: [{ name: 'parchment', value: '#F5F1E8' }] },
  },
  argTypes: {
    size: { control: 'select', options: ['xs', 'sm', 'md', 'lg', 'xl'] },
    variant: { control: 'select', options: ['circle', 'square'] },
    status: { control: 'select', options: [undefined, 'online', 'offline', 'away'] },
  },
};
export default meta;
type Story = StoryObj<typeof Avatar>;

/* ---- Single avatar stories ---- */

export const WithImage: Story = {
  args: {
    src: 'https://i.pravatar.cc/150?img=11',
    alt: 'Niv Dvir',
    size: 'md',
    variant: 'circle',
  },
};

export const InitialsFallback: Story = {
  args: {
    name: 'Niv Dvir',
    size: 'md',
    variant: 'circle',
  },
};

export const SingleInitial: Story = {
  args: {
    name: 'Ronen',
    size: 'md',
    variant: 'circle',
  },
};

export const WithStatusOnline: Story = {
  args: {
    src: 'https://i.pravatar.cc/150?img=3',
    name: 'Maya Cohen',
    size: 'md',
    variant: 'circle',
    status: 'online',
  },
};

export const WithStatusAway: Story = {
  args: {
    name: 'Daniel Levi',
    size: 'md',
    variant: 'circle',
    status: 'away',
  },
};

export const WithStatusOffline: Story = {
  args: {
    name: 'Sara Katz',
    size: 'md',
    variant: 'circle',
    status: 'offline',
  },
};

export const SquareVariant: Story = {
  args: {
    name: 'Tom Green',
    size: 'lg',
    variant: 'square',
    status: 'online',
  },
};

/* ---- All sizes ---- */
export const AllSizes: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
      <Avatar name="Niv Dvir" size="xs" />
      <Avatar name="Niv Dvir" size="sm" />
      <Avatar name="Niv Dvir" size="md" />
      <Avatar name="Niv Dvir" size="lg" />
      <Avatar name="Niv Dvir" size="xl" />
    </div>
  ),
};

/* ---- All sizes with image ---- */
export const AllSizesWithImage: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
      {(['xs', 'sm', 'md', 'lg', 'xl'] as const).map((size) => (
        <Avatar key={size} src={`https://i.pravatar.cc/150?img=5`} alt="User" size={size} />
      ))}
    </div>
  ),
};

/* ---- All statuses ---- */
export const AllStatuses: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: 20, alignItems: 'center' }}>
      <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
        <Avatar name="Maya Cohen" size="md" status="online" />
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>online</span>
      </div>
      <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
        <Avatar name="Daniel Levi" size="md" status="away" />
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>away</span>
      </div>
      <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
        <Avatar name="Sara Katz" size="md" status="offline" />
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>offline</span>
      </div>
      <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
        <Avatar name="Ron Ben" size="md" />
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>no status</span>
      </div>
    </div>
  ),
};

/* ---- Shape variants ---- */
export const ShapeVariants: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
      <Avatar src="https://i.pravatar.cc/150?img=7" size="lg" variant="circle" />
      <Avatar src="https://i.pravatar.cc/150?img=7" size="lg" variant="square" />
      <Avatar name="Alex Ben-David" size="lg" variant="circle" />
      <Avatar name="Alex Ben-David" size="lg" variant="square" />
    </div>
  ),
};

/* ---- AvatarGroup ---- */
export const Group: Story = {
  render: () => (
    <AvatarGroup
      size="md"
      avatars={[
        { src: 'https://i.pravatar.cc/150?img=10', name: 'Niv Dvir', status: 'online' },
        { src: 'https://i.pravatar.cc/150?img=11', name: 'Maya Cohen' },
        { name: 'Daniel Levi', status: 'away' },
        { name: 'Sara Katz', status: 'offline' },
        { name: 'Ron Ben-David' },
        { src: 'https://i.pravatar.cc/150?img=14', name: 'Gal Harari' },
      ]}
      max={4}
    />
  ),
};

export const GroupSmall: Story = {
  render: () => (
    <AvatarGroup
      size="sm"
      avatars={[
        { name: 'Niv Dvir', status: 'online' },
        { name: 'Maya Cohen' },
        { name: 'Daniel Levi' },
        { name: 'Sara Katz' },
        { name: 'Ron Ben-David' },
      ]}
      max={3}
    />
  ),
};

export const GroupNoOverflow: Story = {
  render: () => (
    <AvatarGroup
      size="md"
      avatars={[
        { src: 'https://i.pravatar.cc/150?img=20', name: 'Niv Dvir', status: 'online' },
        { name: 'Maya Cohen', status: 'away' },
        { name: 'Daniel Levi' },
      ]}
      max={5}
    />
  ),
};
