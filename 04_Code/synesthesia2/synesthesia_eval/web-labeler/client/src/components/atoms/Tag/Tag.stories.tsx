import React, { useState } from 'react';
import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { Tag, TagGroup } from './Tag';

const meta: Meta<typeof Tag> = {
  title: 'Atoms/Tag',
  component: Tag,
  parameters: {
    layout: 'centered',
    backgrounds: { default: 'parchment', values: [{ name: 'parchment', value: '#F5F1E8' }] },
  },
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'accent', 'teal', 'success', 'warning', 'error', 'outline'],
    },
    size: { control: 'select', options: ['sm', 'md'] },
    removable: { control: 'boolean' },
    active: { control: 'boolean' },
  },
};
export default meta;
type Story = StoryObj<typeof Tag>;

/* ---- Single tag ---- */
export const Default: Story = {
  args: { label: 'Audio Sync', variant: 'default' },
};

export const Accent: Story = {
  args: { label: 'Flame', variant: 'accent' },
};

export const Teal: Story = {
  args: { label: 'Cochlear', variant: 'teal' },
};

export const Success: Story = {
  args: { label: 'High Quality', variant: 'success' },
};

export const Warning: Story = {
  args: { label: 'Review', variant: 'warning' },
};

export const Error: Story = {
  args: { label: 'Poor Sync', variant: 'error' },
};

export const Outline: Story = {
  args: { label: 'Outline', variant: 'outline' },
};

/* ---- All variants ---- */
export const AllVariants: Story = {
  render: () => (
    <TagGroup gap="md">
      <Tag label="Default" variant="default" />
      <Tag label="Accent" variant="accent" />
      <Tag label="Teal" variant="teal" />
      <Tag label="Success" variant="success" />
      <Tag label="Warning" variant="warning" />
      <Tag label="Error" variant="error" />
      <Tag label="Outline" variant="outline" />
    </TagGroup>
  ),
};

/* ---- Sizes ---- */
export const AllSizes: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, alignItems: 'flex-start' }}>
      <TagGroup gap="sm">
        <Tag label="sm · Blender" size="sm" variant="accent" />
        <Tag label="sm · Python" size="sm" variant="teal" />
        <Tag label="sm · Audio" size="sm" variant="default" />
      </TagGroup>
      <TagGroup gap="sm">
        <Tag label="md · Blender" size="md" variant="accent" />
        <Tag label="md · Python" size="md" variant="teal" />
        <Tag label="md · Audio" size="md" variant="default" />
      </TagGroup>
    </div>
  ),
};

/* ---- Removable ---- */
export const Removable: Story = {
  render: () => {
    const [tags, setTags] = React.useState([
      { id: 1, label: 'Audio Sync', variant: 'accent' as const },
      { id: 2, label: 'Blender', variant: 'teal' as const },
      { id: 3, label: 'High Quality', variant: 'success' as const },
      { id: 4, label: 'Review Needed', variant: 'warning' as const },
    ]);

    return (
      <TagGroup gap="md">
        {tags.map((t) => (
          <Tag
            key={t.id}
            label={t.label}
            variant={t.variant}
            removable
            onRemove={() => setTags((prev) => prev.filter((x) => x.id !== t.id))}
          />
        ))}
        {tags.length === 0 && (
          <span style={{ fontSize: 12, color: 'var(--color-text-muted)', fontFamily: 'var(--font-body)' }}>
            All tags removed
          </span>
        )}
      </TagGroup>
    );
  },
};

/* ---- With icon ---- */
export const WithIcon: Story = {
  render: () => (
    <TagGroup gap="md">
      <Tag label="Synced" variant="success" icon={<span>✓</span>} />
      <Tag label="Flame" variant="accent" icon={<span>🔥</span>} />
      <Tag label="3D" variant="teal" icon={<span>⬡</span>} />
      <Tag label="Caution" variant="warning" icon={<span>⚠</span>} />
    </TagGroup>
  ),
};

/* ---- Clickable toggle ---- */
export const ToggleSingle: Story = {
  render: () => {
    const [active, setActive] = useState(false);
    return (
      <Tag
        label={active ? 'Active' : 'Click to activate'}
        variant="accent"
        active={active}
        onClick={() => setActive((v) => !v)}
      />
    );
  },
};

/* ---- Filter group (multi-toggle) ---- */
export const FilterGroup: Story = {
  render: () => {
    const options = ['All', 'Blender', 'Python', 'Unreal', 'After Effects', 'Three.js'];
    const [selected, setSelected] = useState<Set<string>>(new Set(['All']));

    const toggle = (label: string) => {
      setSelected((prev) => {
        const next = new Set(prev);
        if (label === 'All') return new Set(['All']);
        next.delete('All');
        if (next.has(label)) { next.delete(label); if (next.size === 0) next.add('All'); }
        else next.add(label);
        return next;
      });
    };

    return (
      <div style={{ maxWidth: 420 }}>
        <TagGroup gap="sm">
          {options.map((o) => (
            <Tag
              key={o}
              label={o}
              variant={selected.has(o) ? 'accent' : 'outline'}
              active={selected.has(o)}
              onClick={() => toggle(o)}
              size="md"
            />
          ))}
        </TagGroup>
      </div>
    );
  },
};

/* ---- Real-world: clip labels ---- */
export const ClipLabels: Story = {
  render: () => (
    <div style={{ maxWidth: 380 }}>
      <p style={{ fontSize: 12, color: 'var(--color-text-muted)', fontFamily: 'var(--font-body)', marginBottom: 8 }}>
        Clip #027 — Auto-labeled
      </p>
      <TagGroup gap="sm">
        <Tag label="Spectral" variant="teal" size="sm" />
        <Tag label="High Sync" variant="success" size="sm" />
        <Tag label="3D" variant="accent" size="sm" />
        <Tag label="Blender" variant="default" size="sm" />
        <Tag label="Ambient" variant="default" size="sm" />
        <Tag label="AI Label" variant="outline" size="sm" />
      </TagGroup>
    </div>
  ),
};

/* ---- TagGroup gap variants ---- */
export const TagGroupGaps: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, alignItems: 'flex-start' }}>
      <div>
        <p style={{ fontSize: 11, color: 'var(--color-text-muted)', fontFamily: 'var(--font-body)', marginBottom: 6 }}>gap="sm"</p>
        <TagGroup gap="sm">
          <Tag label="Audio" variant="accent" />
          <Tag label="Visual" variant="teal" />
          <Tag label="Sync" variant="success" />
        </TagGroup>
      </div>
      <div>
        <p style={{ fontSize: 11, color: 'var(--color-text-muted)', fontFamily: 'var(--font-body)', marginBottom: 6 }}>gap="md"</p>
        <TagGroup gap="md">
          <Tag label="Audio" variant="accent" />
          <Tag label="Visual" variant="teal" />
          <Tag label="Sync" variant="success" />
        </TagGroup>
      </div>
    </div>
  ),
};
