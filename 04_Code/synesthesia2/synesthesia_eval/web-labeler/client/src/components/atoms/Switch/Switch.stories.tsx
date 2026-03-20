import React, { useState } from 'react';
import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { Switch } from './Switch';

const meta: Meta<typeof Switch> = {
  title: 'Atoms/Switch',
  component: Switch,
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
type Story = StoryObj<typeof Switch>;

/* ---- Default (uncontrolled) ---- */
export const Default: Story = {
  args: { label: 'Enable feature', defaultChecked: false },
};

export const DefaultChecked: Story = {
  args: { label: 'Feature enabled', defaultChecked: true },
};

/* ---- Controlled ---- */
export const Controlled: Story = {
  render: () => {
    const [on, setOn] = useState(false);
    return (
      <Switch
        label={on ? 'On' : 'Off'}
        description="Controlled switch — click to toggle"
        checked={on}
        onChange={setOn}
      />
    );
  },
};

/* ---- Variants ---- */
export const VariantDefault: Story = {
  args: { label: 'Default variant (teal)', variant: 'default', defaultChecked: true },
};

export const VariantAccent: Story = {
  args: { label: 'Accent variant (flame)', variant: 'accent', defaultChecked: true },
};

export const BothVariants: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <Switch label="Default (teal)" variant="default" defaultChecked />
      <Switch label="Accent (flame)" variant="accent" defaultChecked />
    </div>
  ),
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
      <Switch label="Small" size="sm" defaultChecked />
      <Switch label="Medium" size="md" defaultChecked />
      <Switch label="Large" size="lg" defaultChecked />
    </div>
  ),
};

/* ---- With description ---- */
export const WithDescription: Story = {
  args: {
    label: 'Dark mode',
    description: 'Apply a dark color scheme to the interface.',
    defaultChecked: false,
  },
};

/* ---- No label ---- */
export const NoLabel: Story = {
  args: { defaultChecked: true },
};

/* ---- Disabled ---- */
export const Disabled: Story = {
  args: { label: 'Disabled off', disabled: true },
};

export const DisabledChecked: Story = {
  args: { label: 'Disabled on', disabled: true, defaultChecked: true },
};

/* ---- All sizes × both variants ---- */
export const SizeVariantMatrix: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {(['sm', 'md', 'lg'] as const).map((size) =>
        (['default', 'accent'] as const).map((variant) => (
          <Switch
            key={`${size}-${variant}`}
            label={`${size} / ${variant}`}
            size={size}
            variant={variant}
            defaultChecked
          />
        ))
      )}
    </div>
  ),
};

/* ---- Full showcase ---- */
export const Showcase: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, minWidth: 320 }}>
      <Switch label="Unchecked" />
      <Switch label="Checked (default)" defaultChecked />
      <Switch label="Checked (accent)" variant="accent" defaultChecked />
      <Switch label="With description" description="Helper text below." defaultChecked />
      <Switch label="Disabled off" disabled />
      <Switch label="Disabled on" disabled defaultChecked />
    </div>
  ),
};
