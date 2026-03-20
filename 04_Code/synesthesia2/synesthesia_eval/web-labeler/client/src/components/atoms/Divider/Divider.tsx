import React from 'react';
import './Divider.css';

export type DividerVariant = 'subtle' | 'default' | 'strong';
export type DividerSpacing = 'none' | 'sm' | 'md' | 'lg';
export type DividerOrientation = 'horizontal' | 'vertical';

export interface DividerProps {
  variant?: DividerVariant;
  spacing?: DividerSpacing;
  orientation?: DividerOrientation;
  className?: string;
}

/**
 * Divider — separator atom.
 * Replaces raw <hr> and border-top inline rules throughout the codebase.
 */
export const Divider: React.FC<DividerProps> = ({
  variant = 'default',
  spacing = 'md',
  orientation = 'horizontal',
  className = '',
}) => (
  <hr
    role="separator"
    className={[
      'atom-divider',
      `atom-divider--${orientation}`,
      `atom-divider--${variant}`,
      spacing !== 'none' ? `atom-divider--spacing-${spacing}` : '',
      className,
    ].filter(Boolean).join(' ')}
  />
);
