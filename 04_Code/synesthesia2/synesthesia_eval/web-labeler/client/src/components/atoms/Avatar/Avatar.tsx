import React from 'react';
import './Avatar.css';

export type AvatarSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';
export type AvatarVariant = 'circle' | 'square';
export type AvatarStatus = 'online' | 'offline' | 'away';

export interface AvatarProps {
  src?: string;
  alt?: string;
  name?: string;
  size?: AvatarSize;
  variant?: AvatarVariant;
  status?: AvatarStatus;
  className?: string;
}

export interface AvatarGroupProps {
  avatars: AvatarProps[];
  max?: number;
  size?: AvatarSize;
}

function getInitials(name: string): string {
  return name
    .split(' ')
    .map((w) => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();
}

/**
 * Avatar — user identity atom.
 * Shows profile image or initials fallback with optional status dot.
 */
export const Avatar: React.FC<AvatarProps> = ({
  src,
  alt = '',
  name,
  size = 'md',
  variant = 'circle',
  status,
  className = '',
}) => {
  const initials = name ? getInitials(name) : null;

  return (
    <span
      className={[
        'atom-avatar',
        `atom-avatar--${size}`,
        `atom-avatar--${variant}`,
        className,
      ]
        .filter(Boolean)
        .join(' ')}
      aria-label={alt || name}
    >
      {src ? (
        <img
          className="atom-avatar__img"
          src={src}
          alt={alt || name || ''}
          draggable={false}
        />
      ) : (
        <span className="atom-avatar__initials" aria-hidden="true">
          {initials ?? '?'}
        </span>
      )}
      {status && (
        <span
          className={`atom-avatar__status atom-avatar__status--${status}`}
          aria-label={status}
        />
      )}
    </span>
  );
};

/**
 * AvatarGroup — stacked row of avatars with overflow count.
 */
export const AvatarGroup: React.FC<AvatarGroupProps> = ({
  avatars,
  max = 4,
  size = 'md',
}) => {
  const visible = avatars.slice(0, max);
  const overflow = avatars.length - visible.length;

  return (
    <span className="atom-avatar-group">
      {visible.map((av, i) => (
        <Avatar key={i} {...av} size={size} className="atom-avatar-group__item" />
      ))}
      {overflow > 0 && (
        <span
          className={[
            'atom-avatar',
            'atom-avatar--overflow',
            `atom-avatar--${size}`,
            'atom-avatar--circle',
            'atom-avatar-group__item',
          ].join(' ')}
          aria-label={`${overflow} more`}
        >
          <span className="atom-avatar__initials" aria-hidden="true">
            +{overflow}
          </span>
        </span>
      )}
    </span>
  );
};
