import React from 'react';
import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { Tooltip } from './Tooltip';

const meta: Meta<typeof Tooltip> = {
  title: 'Atoms/Tooltip',
  component: Tooltip,
  parameters: {
    layout: 'centered',
    backgrounds: { default: 'parchment', values: [{ name: 'parchment', value: '#F5F1E8' }] },
  },
  argTypes: {
    placement: { control: 'select', options: ['top', 'bottom', 'left', 'right'] },
    delay: { control: 'number' },
    disabled: { control: 'boolean' },
    maxWidth: { control: 'number' },
  },
};
export default meta;
type Story = StoryObj<typeof Tooltip>;

/* ---- Helper trigger button ---- */
const TriggerBtn: React.FC<{ label: string }> = ({ label }) => (
  <button
    style={{
      padding: '8px 16px',
      background: 'var(--color-bg-elevated)',
      border: '1px solid var(--color-bg-deep)',
      borderRadius: 6,
      fontSize: 13,
      fontFamily: 'var(--font-body)',
      color: 'var(--color-text-primary)',
      cursor: 'pointer',
    }}
  >
    {label}
  </button>
);

/* ---- Single placement stories ---- */

export const Top: Story = {
  render: () => (
    <Tooltip content="This tooltip appears above" placement="top">
      <TriggerBtn label="Hover me (top)" />
    </Tooltip>
  ),
};

export const Bottom: Story = {
  render: () => (
    <Tooltip content="This tooltip appears below" placement="bottom">
      <TriggerBtn label="Hover me (bottom)" />
    </Tooltip>
  ),
};

export const Left: Story = {
  render: () => (
    <Tooltip content="Appears to the left" placement="left">
      <TriggerBtn label="Hover me (left)" />
    </Tooltip>
  ),
};

export const Right: Story = {
  render: () => (
    <Tooltip content="Appears to the right" placement="right">
      <TriggerBtn label="Hover me (right)" />
    </Tooltip>
  ),
};

/* ---- All placements ---- */
export const AllPlacements: Story = {
  render: () => (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 32 }}>
      {(['top', 'bottom', 'left', 'right'] as const).map((p) => (
        <Tooltip key={p} content={`Placement: ${p}`} placement={p} delay={0}>
          <TriggerBtn label={p} />
        </Tooltip>
      ))}
    </div>
  ),
};

/* ---- Rich content ---- */
export const RichContent: Story = {
  render: () => (
    <Tooltip
      placement="top"
      delay={0}
      maxWidth={240}
      content={
        <span>
          <strong style={{ display: 'block', marginBottom: 4 }}>Sync Quality</strong>
          How well the visuals synchronize with the beat and rhythm of the audio track.
        </span>
      }
    >
      <TriggerBtn label="What is Sync Quality?" />
    </Tooltip>
  ),
};

/* ---- Long text wrapping ---- */
export const LongText: Story = {
  render: () => (
    <Tooltip
      placement="top"
      delay={0}
      maxWidth={220}
      content="This is a longer description that spans multiple lines to demonstrate text wrapping behaviour inside the tooltip bubble."
    >
      <TriggerBtn label="Long tooltip text" />
    </Tooltip>
  ),
};

/* ---- No delay (instant) ---- */
export const NoDelay: Story = {
  render: () => (
    <Tooltip content="Shows instantly" placement="top" delay={0}>
      <TriggerBtn label="Instant tooltip" />
    </Tooltip>
  ),
};

/* ---- Disabled ---- */
export const Disabled: Story = {
  render: () => (
    <Tooltip content="You won't see this" placement="top" disabled>
      <TriggerBtn label="Tooltip disabled" />
    </Tooltip>
  ),
};

/* ---- On an icon ---- */
export const OnIcon: Story = {
  render: () => (
    <Tooltip content="Rate this visualization clip" placement="right" delay={0}>
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: 36,
          height: 36,
          borderRadius: '50%',
          background: 'var(--color-accent-12)',
          cursor: 'help',
          fontSize: 18,
        }}
      >
        ★
      </span>
    </Tooltip>
  ),
};
