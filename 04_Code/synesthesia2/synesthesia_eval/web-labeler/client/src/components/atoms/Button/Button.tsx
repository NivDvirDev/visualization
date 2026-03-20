import React from 'react';
import './Button.css';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
}

/**
 * Button — core interactive atom.
 * Maps to global .btn-join (primary) and .btn-outline (secondary).
 * Always consume this atom — never write ad-hoc button styles.
 */
export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  className = '',
  children,
  ...rest
}) => (
  <button
    className={[
      'atom-btn',
      `atom-btn--${variant}`,
      `atom-btn--${size}`,
      loading ? 'atom-btn--loading' : '',
      className,
    ].filter(Boolean).join(' ')}
    disabled={disabled || loading}
    {...rest}
  >
    {loading && <span className="atom-btn-spinner" aria-hidden="true" />}
    {children}
  </button>
);
