import React from 'react';
import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from './Card';
import { Button } from '../Button/Button';
import { Badge } from '../Badge/Badge';

const meta: Meta<typeof Card> = {
  title: 'Atoms/Card',
  component: Card,
  parameters: {
    layout: 'centered',
    backgrounds: { default: 'parchment' },
  },
  argTypes: {
    variant: { control: 'select', options: ['default', 'elevated', 'glass', 'outlined'] },
    padding: { control: 'select', options: ['none', 'sm', 'md', 'lg'] },
    hoverable: { control: 'boolean' },
  },
};
export default meta;
type Story = StoryObj<typeof Card>;

/* ---- Basic variants ---- */

export const Default: Story = {
  args: {
    variant: 'default',
    children: (
      <>
        <CardHeader>
          <CardTitle>Visualization Clip #027</CardTitle>
        </CardHeader>
        <CardDescription>Spectral view of music — synesthesia style</CardDescription>
        <CardContent>Rated by 14 labelers. Average score: 4.2 / 5.</CardContent>
      </>
    ),
  },
};

export const Elevated: Story = {
  args: {
    variant: 'elevated',
    children: (
      <>
        <CardHeader>
          <CardTitle>Elevated Card</CardTitle>
        </CardHeader>
        <CardDescription>White background with stronger shadow lift</CardDescription>
        <CardContent>Use for primary content areas that need visual prominence.</CardContent>
      </>
    ),
  },
};

export const Glass: Story = {
  args: {
    variant: 'glass',
    children: (
      <>
        <CardHeader>
          <CardTitle>Glass Card</CardTitle>
        </CardHeader>
        <CardDescription>Frosted-glass morphism surface</CardDescription>
        <CardContent>Best over rich background images or gradient backdrops.</CardContent>
      </>
    ),
  },
};

export const Outlined: Story = {
  args: {
    variant: 'outlined',
    children: (
      <>
        <CardHeader>
          <CardTitle>Outlined Card</CardTitle>
        </CardHeader>
        <CardDescription>Transparent with accent border only</CardDescription>
        <CardContent>Use for secondary or de-emphasised content regions.</CardContent>
      </>
    ),
  },
};

/* ---- Sub-components ---- */

export const WithFooter: Story = {
  render: () => (
    <Card variant="elevated" style={{ width: 340 }}>
      <CardHeader>
        <CardTitle>Audio Visualization</CardTitle>
        <Badge variant="accent">Hot</Badge>
      </CardHeader>
      <CardDescription>Merkabah 3D renderer — Blender geometry nodes</CardDescription>
      <CardContent>
        A 3D wireframe double-helix responding to harmonic frequency bins.
        Rated by the community on sync, aesthetics, and motion quality.
      </CardContent>
      <CardFooter>
        <Button variant="ghost" size="sm">Skip</Button>
        <Button variant="primary" size="sm">Rate Now</Button>
      </CardFooter>
    </Card>
  ),
};

export const HoverableClickable: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
      <Card variant="default" hoverable onClick={() => alert('Card clicked!')} style={{ width: 220 }}>
        <CardTitle as="h4">Click Me</CardTitle>
        <CardContent>Hoverable + clickable card with lift effect on hover.</CardContent>
      </Card>
      <Card variant="glass" hoverable onClick={() => alert('Glass card clicked!')} style={{ width: 220 }}>
        <CardTitle as="h4">Glass Hover</CardTitle>
        <CardContent>Glass variant with enhanced background on hover.</CardContent>
      </Card>
    </div>
  ),
};

/* ---- Padding variants ---- */

export const AllPaddings: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'flex-start' }}>
      {(['none', 'sm', 'md', 'lg'] as const).map((p) => (
        <Card key={p} variant="elevated" padding={p} style={{ width: 160, minHeight: 60 }}>
          <CardContent>padding="{p}"</CardContent>
        </Card>
      ))}
    </div>
  ),
};

/* ---- All variants side-by-side ---- */

export const AllVariants: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'flex-start' }}>
      {(['default', 'elevated', 'glass', 'outlined'] as const).map((v) => (
        <Card key={v} variant={v} style={{ width: 200 }}>
          <CardTitle as="h4">{v}</CardTitle>
          <CardContent>Variant preview card content.</CardContent>
        </Card>
      ))}
    </div>
  ),
};

/* ---- Real-world: Clip list item ---- */

export const ClipListItem: Story = {
  render: () => (
    <Card variant="elevated" hoverable style={{ width: 360 }}>
      <CardHeader>
        <div style={{ flex: 1 }}>
          <CardTitle>Spiral Radial Seismograph v3</CardTitle>
          <CardDescription>Generated · 2026-03-09</CardDescription>
        </div>
        <Badge variant="success">4.7</Badge>
      </CardHeader>
      <CardContent>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <Badge variant="neutral" size="sm">Sync: 5</Badge>
          <Badge variant="neutral" size="sm">Align: 4</Badge>
          <Badge variant="neutral" size="sm">Aesthetic: 5</Badge>
          <Badge variant="neutral" size="sm">Motion: 4</Badge>
        </div>
      </CardContent>
      <CardFooter>
        <Button variant="secondary" size="sm">View Detail</Button>
        <Button variant="primary" size="sm">Rate</Button>
      </CardFooter>
    </Card>
  ),
};
