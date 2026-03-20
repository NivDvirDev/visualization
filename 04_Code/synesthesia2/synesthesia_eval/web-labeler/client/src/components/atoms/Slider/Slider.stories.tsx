import React, { useState } from 'react';
import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { Slider } from './Slider';

const meta: Meta<typeof Slider> = {
  title: 'Atoms/Slider',
  component: Slider,
  parameters: {
    layout: 'centered',
    backgrounds: { default: 'parchment', values: [{ name: 'parchment', value: '#F5F1E8' }] },
  },
  decorators: [
    (Story: React.ComponentType) => (
      <div style={{ width: 320, padding: 8 }}>
        <Story />
      </div>
    ),
  ],
};
export default meta;
type Story = StoryObj<typeof Slider>;

/* ---- Default (uncontrolled) ---- */
export const Default: Story = {
  args: { label: 'Volume', defaultValue: 40 },
};

/* ---- Show value ---- */
export const WithValueDisplay: Story = {
  args: { label: 'Brightness', defaultValue: 65, showValue: true },
};

/* ---- Controlled ---- */
export const Controlled: Story = {
  render: () => {
    const [val, setVal] = useState(30);
    return (
      <Slider
        label="Opacity"
        value={val}
        onChange={setVal}
        showValue
        min={0}
        max={100}
      />
    );
  },
};

/* ---- Variants ---- */
export const VariantDefault: Story = {
  args: { label: 'Default (teal)', variant: 'default', defaultValue: 60, showValue: true },
};

export const VariantAccent: Story = {
  args: { label: 'Accent (flame)', variant: 'accent', defaultValue: 60, showValue: true },
};

export const BothVariants: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
      <Slider label="Default (teal)" variant="default" defaultValue={55} showValue />
      <Slider label="Accent (flame)" variant="accent" defaultValue={55} showValue />
    </div>
  ),
};

/* ---- Sizes ---- */
export const SizeSmall: Story = {
  args: { label: 'Small (sm)', size: 'sm', defaultValue: 50, showValue: true },
};
export const SizeMedium: Story = {
  args: { label: 'Medium (md) — default', size: 'md', defaultValue: 50, showValue: true },
};
export const SizeLarge: Story = {
  args: { label: 'Large (lg)', size: 'lg', defaultValue: 50, showValue: true },
};

export const AllSizes: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
      <Slider label="Small" size="sm" defaultValue={50} showValue />
      <Slider label="Medium" size="md" defaultValue={50} showValue />
      <Slider label="Large" size="lg" defaultValue={50} showValue />
    </div>
  ),
};

/* ---- Custom min / max / step ---- */
export const CustomMinMaxStep: Story = {
  args: {
    label: 'Temperature (°C)',
    min: -20,
    max: 40,
    step: 5,
    defaultValue: 20,
    showValue: true,
  },
};

export const StepOne: Story = {
  args: {
    label: 'Rating (1-10)',
    min: 1,
    max: 10,
    step: 1,
    defaultValue: 5,
    showValue: true,
  },
};

export const FloatStep: Story = {
  args: {
    label: 'Gamma correction',
    min: 0.1,
    max: 3.0,
    step: 0.1,
    defaultValue: 1.0,
    showValue: true,
  },
};

/* ---- Marks ---- */
export const WithMarks: Story = {
  args: {
    label: 'Quality',
    defaultValue: 50,
    showValue: true,
    marks: [
      { value: 0,   label: 'Low'  },
      { value: 25 },
      { value: 50,  label: 'Mid'  },
      { value: 75 },
      { value: 100, label: 'High' },
    ],
  },
};

export const WithMarksNoLabels: Story = {
  args: {
    label: 'Steps',
    defaultValue: 3,
    min: 1,
    max: 5,
    step: 1,
    showValue: true,
    marks: [1, 2, 3, 4, 5].map((v) => ({ value: v })),
  },
};

export const WithMarksAccent: Story = {
  args: {
    label: 'Intensity',
    variant: 'accent',
    defaultValue: 75,
    showValue: true,
    marks: [
      { value: 0,   label: '0%'   },
      { value: 25,  label: '25%'  },
      { value: 50,  label: '50%'  },
      { value: 75,  label: '75%'  },
      { value: 100, label: '100%' },
    ],
  },
};

/* ---- onChangeEnd ---- */
export const WithChangeEnd: Story = {
  render: () => {
    const [live, setLive]   = useState(40);
    const [committed, setCommitted] = useState(40);
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <Slider
          label="Drag and release"
          value={live}
          onChange={setLive}
          onChangeEnd={setCommitted}
          showValue
        />
        <p style={{ fontFamily: 'var(--font-body)', fontSize: 12, color: 'var(--color-text-muted)', margin: 0 }}>
          Live: {live} &nbsp;|&nbsp; Committed: {committed}
        </p>
      </div>
    );
  },
};

/* ---- Disabled ---- */
export const Disabled: Story = {
  args: { label: 'Disabled', defaultValue: 40, disabled: true, showValue: true },
};

/* ---- No label ---- */
export const NoLabel: Story = {
  args: { defaultValue: 70 },
};

/* ---- Full showcase ---- */
export const Showcase: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 32, width: 320 }}>
      <Slider label="Default teal" variant="default" defaultValue={40} showValue />
      <Slider label="Accent flame" variant="accent" defaultValue={70} showValue />
      <Slider
        label="With marks"
        defaultValue={50}
        showValue
        marks={[
          { value: 0, label: 'Lo' },
          { value: 50, label: 'Mid' },
          { value: 100, label: 'Hi' },
        ]}
      />
      <Slider label="Custom step (0.1)" min={0} max={1} step={0.1} defaultValue={0.5} showValue />
      <Slider label="Disabled" defaultValue={35} disabled showValue />
    </div>
  ),
};
