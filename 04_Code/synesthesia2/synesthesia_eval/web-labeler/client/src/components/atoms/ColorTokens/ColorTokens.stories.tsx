import React from 'react';
import type { Meta } from '@storybook/react-webpack5';

const meta: Meta = {
  title: 'Atoms/ColorTokens',
  parameters: { layout: 'padded' },
};
export default meta;

type Swatch = { token: string; hex: string; label: string };

const Palette: React.FC<{ title: string; swatches: Swatch[] }> = ({ title, swatches }) => (
  <div style={{ marginBottom: 32 }}>
    <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '0.75rem', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 12, color: 'var(--color-text-secondary)' }}>{title}</h3>
    <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
      {swatches.map(({ token, hex, label }) => (
        <div key={token} style={{ textAlign: 'center', width: 88 }}>
          <div style={{ width: 88, height: 56, borderRadius: 8, background: hex, border: '1px solid rgba(0,0,0,0.1)', marginBottom: 6 }} />
          <div style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--color-text-primary)', wordBreak: 'break-all' }}>{token}</div>
          <div style={{ fontSize: 10, color: 'var(--color-text-muted)', marginTop: 2 }}>{label}</div>
        </div>
      ))}
    </div>
  </div>
);

export const AllTokens = () => (
  <div style={{ padding: 8 }}>
    <Palette title="Accent — Flame" swatches={[
      { token: '--color-accent',       hex: '#FF6B35', label: 'Flame' },
      { token: '--color-accent-bright',hex: '#FFB627', label: 'Gold' },
      { token: '--color-accent-pink',  hex: '#D84315', label: 'Deep' },
      { token: '--color-accent-soft',  hex: '#FF8F60', label: 'Soft' },
      { token: '--color-accent-muted', hex: '#E65100', label: 'Muted' },
    ]} />
    <Palette title="Background — Parchment" swatches={[
      { token: '--color-bg-primary',      hex: '#F5F1E8', label: 'Parchment' },
      { token: '--color-bg-secondary',    hex: '#EDE8DC', label: 'Secondary' },
      { token: '--color-bg-elevated',     hex: '#FFFFFF',  label: 'Elevated' },
      { token: '--color-bg-elevated-alt', hex: '#FAF8F3', label: 'Alt' },
      { token: '--color-bg-deep',         hex: '#E8E3D8', label: 'Deep' },
    ]} />
    <Palette title="Text" swatches={[
      { token: '--color-text-primary',   hex: '#1A1A2E', label: 'Primary' },
      { token: '--color-text-secondary', hex: '#8B7355', label: 'Secondary' },
      { token: '--color-text-muted',     hex: '#A89A88', label: 'Muted' },
      { token: '--color-text-mid',       hex: '#5A4E42', label: 'Mid' },
      { token: '--color-text-light',     hex: '#2D4263', label: 'Blue' },
    ]} />
    <Palette title="Status" swatches={[
      { token: '--color-success', hex: '#2E7D32', label: 'Success' },
      { token: '--color-warning', hex: '#E65100', label: 'Warning' },
      { token: '--color-error',   hex: '#D84315', label: 'Error' },
      { token: '--color-bright',  hex: '#FFB627', label: 'Bright' },
    ]} />
  </div>
);
