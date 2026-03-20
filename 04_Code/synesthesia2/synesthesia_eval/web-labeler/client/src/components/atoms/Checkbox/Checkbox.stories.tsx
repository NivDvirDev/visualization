import React, { useState } from 'react';
import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { Checkbox } from './Checkbox';

const meta: Meta<typeof Checkbox> = {
  title: 'Atoms/Checkbox',
  component: Checkbox,
  parameters: {
    layout: 'centered',
    backgrounds: { default: 'parchment', values: [{ name: 'parchment', value: '#F5F1E8' }] },
  },
  decorators: [
    (Story: React.ComponentType) => (
      <div style={{ minWidth: 280, padding: 8 }}>
        <Story />
      </div>
    ),
  ],
};
export default meta;
type Story = StoryObj<typeof Checkbox>;

/* ---- Uncontrolled (defaultChecked) ---- */
export const Default: Story = {
  args: { label: 'Accept terms', defaultChecked: false },
};

export const DefaultChecked: Story = {
  args: { label: 'Already opted in', defaultChecked: true },
};

/* ---- Controlled ---- */
export const Controlled: Story = {
  render: () => {
    const [checked, setChecked] = useState(false);
    return (
      <Checkbox
        label={checked ? 'Enabled' : 'Disabled'}
        checked={checked}
        onChange={setChecked}
        description="Click to toggle controlled state"
      />
    );
  },
};

/* ---- With description ---- */
export const WithDescription: Story = {
  args: {
    label: 'Email notifications',
    description: "We'll send you weekly digest emails.",
    defaultChecked: true,
  },
};

/* ---- No label (icon-only checkbox) ---- */
export const NoLabel: Story = {
  args: { defaultChecked: false },
};

/* ---- Sizes ---- */
export const SizeSmall: Story = {
  args: { label: 'Small (sm)', size: 'sm', defaultChecked: true },
};
export const SizeMedium: Story = {
  args: { label: 'Medium (md) — default', size: 'md', defaultChecked: true },
};
export const SizeLarge: Story = {
  args: { label: 'Large (lg)', size: 'lg', defaultChecked: true },
};

export const AllSizes: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <Checkbox label="Small" size="sm" defaultChecked />
      <Checkbox label="Medium" size="md" defaultChecked />
      <Checkbox label="Large" size="lg" defaultChecked />
    </div>
  ),
};

/* ---- Indeterminate ---- */
export const Indeterminate: Story = {
  args: {
    label: 'Select all',
    description: '3 of 7 items selected',
    indeterminate: true,
  },
};

export const IndeterminateControlled: Story = {
  render: () => {
    const [state, setState] = useState<'none' | 'some' | 'all'>('some');
    const checked = state === 'all';
    const indeterminate = state === 'some';
    const handleChange = (next: boolean) => setState(next ? 'all' : 'none');
    return (
      <Checkbox
        label="Select all items"
        description={`State: ${state}`}
        checked={checked}
        indeterminate={indeterminate}
        onChange={handleChange}
      />
    );
  },
};

/* ---- Error state ---- */
export const WithError: Story = {
  args: {
    label: 'I agree to the terms',
    error: 'You must agree to the terms to continue.',
  },
};

export const WithErrorAndDescription: Story = {
  args: {
    label: 'Subscribe to newsletter',
    description: 'Max one email per week.',
    error: 'This field is required.',
  },
};

/* ---- Disabled ---- */
export const Disabled: Story = {
  args: { label: 'Disabled unchecked', disabled: true },
};

export const DisabledChecked: Story = {
  args: { label: 'Disabled checked', disabled: true, defaultChecked: true },
};

/* ---- Full showcase ---- */
export const Showcase: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, minWidth: 320 }}>
      <Checkbox label="Default unchecked" />
      <Checkbox label="Default checked" defaultChecked />
      <Checkbox label="With description" description="Some helper text here." defaultChecked />
      <Checkbox label="Indeterminate" indeterminate />
      <Checkbox label="Error state" error="Required field." />
      <Checkbox label="Disabled" disabled />
      <Checkbox label="Disabled + checked" disabled defaultChecked />
    </div>
  ),
};
