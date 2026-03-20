import React, { useState } from 'react';
import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { Tabs, TabPanel } from './Tabs';

const meta: Meta<typeof Tabs> = {
  title: 'Atoms/Tabs',
  component: Tabs,
  parameters: {
    layout: 'padded',
    backgrounds: {
      default: 'parchment',
      values: [{ name: 'parchment', value: '#F5F1E8' }],
    },
  },
  argTypes: {
    variant: { control: 'select', options: ['default', 'pills', 'underline'] },
    size: { control: 'select', options: ['sm', 'md', 'lg'] },
  },
};
export default meta;
type Story = StoryObj<typeof Tabs>;

const SAMPLE_TABS = [
  { id: 'overview', label: 'Overview' },
  { id: 'ratings', label: 'Ratings' },
  { id: 'details', label: 'Details' },
  { id: 'history', label: 'History', disabled: true },
];

/* ---- Interactive wrapper ---- */
const InteractiveDemo: React.FC<{ variant?: 'default' | 'pills' | 'underline'; size?: 'sm' | 'md' | 'lg' }> = ({
  variant = 'default',
  size = 'md',
}) => {
  const [active, setActive] = useState('overview');
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, width: 480 }}>
      <Tabs tabs={SAMPLE_TABS} activeTab={active} onChange={setActive} variant={variant} size={size} />
      <TabPanel id="overview" activeTab={active}>
        <div style={{ padding: '16px 0', color: 'var(--color-text-primary)', fontFamily: 'var(--font-body)', fontSize: 14, lineHeight: 1.6 }}>
          <strong>Clip Overview</strong>
          <p style={{ marginTop: 8 }}>This spiral visualization maps audio frequency bands to a logarithmic cochlear spiral. Motion smoothness is rated 4.2/5, sync quality 3.8/5.</p>
        </div>
      </TabPanel>
      <TabPanel id="ratings" activeTab={active}>
        <div style={{ padding: '16px 0', color: 'var(--color-text-primary)', fontFamily: 'var(--font-body)', fontSize: 14, lineHeight: 1.6 }}>
          <strong>Community Ratings</strong>
          <p style={{ marginTop: 8 }}>42 raters have submitted labels for this clip. Average aesthetic score: 4.1. Sync quality: 3.9.</p>
        </div>
      </TabPanel>
      <TabPanel id="details" activeTab={active}>
        <div style={{ padding: '16px 0', color: 'var(--color-text-primary)', fontFamily: 'var(--font-body)', fontSize: 14, lineHeight: 1.6 }}>
          <strong>Technical Details</strong>
          <p style={{ marginTop: 8 }}>Renderer: mesh3d · Resolution: 4K · Frame rate: 60fps · Trail length: 10 frames · Decay: 0.70</p>
        </div>
      </TabPanel>
    </div>
  );
};

export const Default: Story = {
  render: () => <InteractiveDemo variant="default" />,
};

export const Pills: Story = {
  render: () => <InteractiveDemo variant="pills" />,
};

export const Underline: Story = {
  render: () => <InteractiveDemo variant="underline" />,
};

export const SizeSm: Story = {
  render: () => <InteractiveDemo variant="default" size="sm" />,
};

export const SizeLg: Story = {
  render: () => <InteractiveDemo variant="pills" size="lg" />,
};

export const AllVariants: Story = {
  render: () => {
    const [active1, setActive1] = useState('overview');
    const [active2, setActive2] = useState('ratings');
    const [active3, setActive3] = useState('details');
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 32, width: 480 }}>
        <div>
          <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>Default</p>
          <Tabs tabs={SAMPLE_TABS} activeTab={active1} onChange={setActive1} variant="default" />
        </div>
        <div>
          <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>Pills</p>
          <Tabs tabs={SAMPLE_TABS} activeTab={active2} onChange={setActive2} variant="pills" />
        </div>
        <div>
          <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>Underline</p>
          <Tabs tabs={SAMPLE_TABS} activeTab={active3} onChange={setActive3} variant="underline" />
        </div>
      </div>
    );
  },
};

export const WithDisabledTab: Story = {
  render: () => {
    const [active, setActive] = useState('overview');
    const tabs = [
      { id: 'overview', label: 'Overview' },
      { id: 'locked', label: 'Premium', disabled: true },
      { id: 'ratings', label: 'Ratings' },
    ];
    return <Tabs tabs={tabs} activeTab={active} onChange={setActive} variant="default" />;
  },
};
