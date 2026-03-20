import React from 'react';
import './Tag.css';

export type TagVariant =
  | 'default'
  | 'accent'
  | 'teal'
  | 'success'
  | 'warning'
  | 'error'
  | 'outline';
export type TagSize = 'sm' | 'md';

export interface TagProps {
  label: string;
  variant?: TagVariant;
  size?: TagSize;
  removable?: boolean;
  onRemove?: () => void;
  icon?: React.ReactNode;
  onClick?: () => void;
  active?: boolean;
  className?: string;
}

export interface TagGroupProps {
  children: React.ReactNode;
  gap?: 'sm' | 'md';
}

/**
 * Tag — interactive pill label atom.
 * Use for categories, filters, topics, and toggle-able labels.
 */
export const Tag: React.FC<TagProps> = ({
  label,
  variant = 'default',
  size = 'md',
  removable = false,
  onRemove,
  icon,
  onClick,
  active = false,
  className = '',
}) => {
  const isInteractive = Boolean(onClick);

  const handleRemove = (e: React.MouseEvent) => {
    e.stopPropagation();
    onRemove?.();
  };

  return (
    <span
      role={isInteractive ? 'button' : undefined}
      tabIndex={isInteractive ? 0 : undefined}
      onClick={isInteractive ? onClick : undefined}
      onKeyDown={
        isInteractive
          ? (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onClick?.();
              }
            }
          : undefined
      }
      className={[
        'atom-tag',
        `atom-tag--${variant}`,
        `atom-tag--${size}`,
        isInteractive ? 'atom-tag--interactive' : '',
        active ? 'atom-tag--active' : '',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
    >
      {icon && <span className="atom-tag__icon" aria-hidden="true">{icon}</span>}
      <span className="atom-tag__label">{label}</span>
      {removable && (
        <button
          type="button"
          className="atom-tag__remove"
          onClick={handleRemove}
          aria-label={`Remove ${label}`}
          tabIndex={-1}
        >
          ×
        </button>
      )}
    </span>
  );
};

/**
 * TagGroup — wraps multiple tags with configurable gap.
 */
export const TagGroup: React.FC<TagGroupProps> = ({ children, gap = 'md' }) => (
  <span className={`atom-tag-group atom-tag-group--gap-${gap}`}>{children}</span>
);
