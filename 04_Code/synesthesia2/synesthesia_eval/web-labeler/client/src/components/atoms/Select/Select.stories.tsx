import React, { useState } from 'react';
import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { Select } from './Select';

const meta: Meta<typeof Select> = {
  title: 'Atoms/Select',
  component: Select,
  parameters: {
    layout: 'padded',
    backgrounds: {
      default: 'parchment',
      values: [{ name: 'parchment', value: '#F5F1E8' }],
    },
  },
  argTypes: {
    size: { control: 'select', options: ['sm', 'md', 'lg'] },
    disabled: { control: 'boolean' },
  },
  decorators: [(Story: React.ComponentType) => <div style={{ width: 320, paddingBottom: 260 }}><Story /></div>],
};
export default meta;
type Story = StoryObj<typeof Select>;

const RENDERER_OPTIONS = [
  { value: 'mesh3d', label: '3D Wireframe (mesh3d)' },
  { value: '2d_spiral', label: '2D Spiral' },
  { value: 'harmonic', label: 'Harmonic Forces' },
  { value: 'seismograph', label: 'Radial Seismograph', disabled: true },
];

const SORT_OPTIONS = [
  { value: 'newest', label: 'Newest first' },
  { value: 'oldest', label: 'Oldest first' },
  { value: 'highest_rated', label: 'Highest rated' },
  { value: 'most_labeled', label: 'Most labeled' },
];

const QUALITY_OPTIONS = [
  { value: '480p', label: '480p — Standard' },
  { value: '720p', label: '720p — HD' },
  { value: '1080p', label: '1080p — Full HD' },
  { value: '4k', label: '4K — Ultra HD' },
];

/* Interactive wrapper */
const SelectDemo: React.FC<{
  options: typeof RENDERER_OPTIONS;
  label?: string;
  placeholder?: string;
  size?: 'sm' | 'md' | 'lg';
  error?: string;
  disabled?: boolean;
}> = ({ options, label, placeholder, size = 'md', error, disabled }) => {
  const [value, setValue] = useState<string | undefined>(undefined);
  return (
    <Select
      options={options}
      value={value}
      onChange={setValue}
      label={label}
      placeholder={placeholder}
      size={size}
      error={error}
      disabled={disabled}
    />
  );
};

export const Default: Story = {
  render: () => (
    <SelectDemo options={RENDERER_OPTIONS} label="Renderer" placeholder="Choose renderer…" />
  ),
};

export const WithPreselected: Story = {
  render: () => {
    const [value, setValue] = useState('newest');
    return (
      <Select
        options={SORT_OPTIONS}
        value={value}
        onChange={setValue}
        label="Sort by"
      />
    );
  },
};

export const WithError: Story = {
  render: () => (
    <SelectDemo
      options={RENDERER_OPTIONS}
      label="Renderer"
      error="Please select a valid renderer before continuing."
    />
  ),
};

export const Disabled: Story = {
  render: () => (
    <Select
      options={RENDERER_OPTIONS}
      value="mesh3d"
      onChange={() => {}}
      label="Renderer"
      disabled
    />
  ),
};

export const SizeSm: Story = {
  render: () => (
    <SelectDemo options={QUALITY_OPTIONS} label="Quality" placeholder="Select quality" size="sm" />
  ),
};

export const SizeLg: Story = {
  render: () => (
    <SelectDemo options={QUALITY_OPTIONS} label="Quality" placeholder="Select quality" size="lg" />
  ),
};

export const AllSizes: Story = {
  render: () => {
    const [v1, setV1] = useState<string | undefined>(undefined);
    const [v2, setV2] = useState<string | undefined>('720p');
    const [v3, setV3] = useState<string | undefined>(undefined);
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20, paddingBottom: 260 }}>
        <Select options={QUALITY_OPTIONS} value={v1} onChange={setV1} label="Small" size="sm" placeholder="Select…" />
        <Select options={QUALITY_OPTIONS} value={v2} onChange={setV2} label="Medium" size="md" placeholder="Select…" />
        <Select options={QUALITY_OPTIONS} value={v3} onChange={setV3} label="Large" size="lg" placeholder="Select…" />
      </div>
    );
  },
};

export const NoLabel: Story = {
  render: () => (
    <SelectDemo options={SORT_OPTIONS} placeholder="Sort clips…" />
  ),
};

export const WithDisabledOption: Story = {
  render: () => (
    <SelectDemo
      options={RENDERER_OPTIONS}
      label="Renderer"
      placeholder="Choose renderer…"
    />
  ),
};
