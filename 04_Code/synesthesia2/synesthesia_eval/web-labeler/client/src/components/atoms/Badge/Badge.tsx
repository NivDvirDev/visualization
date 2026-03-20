import React from 'react';
import './Badge.css';

export type BadgeVariant = 'accent' | 'success' | 'error' | 'warning' | 'neutral' | 'bright';
export type BadgeSize = 'sm' | 'md';

export interface BadgeProps {
  variant?: BadgeVariant;
  size?: BadgeSize;
  dot?: boolean;
  className?: string;
  children: React.ReactNode;
}

/**
 * Badge — inline status/count indicator atom.
 * Use for counts, status labels, achievement tiers.
 */
export const Badge: React.FC<BadgeProps> = ({
  variant = 'accent',
  size = 'sm',
  dot = false,
  className = '',
  children,
}) => (
  <span
    className={[
      'atom-badge',
      `atom-badge--${variant}`,
      `atom-badge--${size}`,
      className,
    ].filter(Boolean).join(' ')}
  >
    {dot && <span className="atom-badge-dot" aria-hidden="true" />}
    {children}
  </span>
);
