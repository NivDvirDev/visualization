import React from 'react';
import './GlassPanel.css';

export type GlassPanelVariant = 'default' | 'strong' | 'overlay';
export type GlassPanelPadding = 'none' | 'sm' | 'md' | 'lg';

export interface GlassPanelProps {
  variant?: GlassPanelVariant;
  padding?: GlassPanelPadding;
  className?: string;
  children: React.ReactNode;
  as?: keyof React.JSX.IntrinsicElements;
}

/**
 * GlassPanel — glassmorphism container atom.
 * Use wherever a frosted-glass card or panel is needed.
 * Replaces ad-hoc .glass-panel usages across the codebase.
 */
export const GlassPanel: React.FC<GlassPanelProps> = ({
  variant = 'default',
  padding = 'md',
  className = '',
  children,
  as: Tag = 'div',
}) => (
  <Tag
    className={[
      'atom-glass',
      `atom-glass--${variant}`,
      `atom-glass--pad-${padding}`,
      className,
    ].filter(Boolean).join(' ')}
  >
    {children}
  </Tag>
);
