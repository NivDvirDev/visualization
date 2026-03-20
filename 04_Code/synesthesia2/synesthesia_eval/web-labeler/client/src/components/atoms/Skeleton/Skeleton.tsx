import React from 'react';
import './Skeleton.css';

export type SkeletonVariant = 'text' | 'rect' | 'circle' | 'card';

export interface SkeletonProps {
  variant?: SkeletonVariant;
  width?: string | number;
  height?: string | number;
  lines?: number;
  animated?: boolean;
  className?: string;
}

function toCSSValue(v: string | number): string {
  return typeof v === 'number' ? `${v}px` : v;
}

/**
 * Skeleton — loading placeholder atom.
 * Renders a shimmer block that mirrors the shape of incoming content.
 */
export const Skeleton: React.FC<SkeletonProps> = ({
  variant = 'rect',
  width,
  height,
  lines = 3,
  animated = true,
  className = '',
}) => {
  if (variant === 'text') {
    return (
      <span
        className={[
          'atom-skeleton-text-group',
          className,
        ]
          .filter(Boolean)
          .join(' ')}
      >
        {Array.from({ length: lines }).map((_, i) => (
          <span
            key={i}
            className={[
              'atom-skeleton',
              'atom-skeleton--text',
              animated ? 'atom-skeleton--animated' : '',
            ]
              .filter(Boolean)
              .join(' ')}
            style={{
              width: i === lines - 1 && lines > 1 ? '65%' : width ? toCSSValue(width) : undefined,
            }}
          />
        ))}
      </span>
    );
  }

  return (
    <span
      className={[
        'atom-skeleton',
        `atom-skeleton--${variant}`,
        animated ? 'atom-skeleton--animated' : '',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
      style={{
        width: width ? toCSSValue(width) : undefined,
        height: height ? toCSSValue(height) : undefined,
      }}
    />
  );
};

/**
 * SkeletonText — pre-composed multi-line text block skeleton.
 */
export const SkeletonText: React.FC<{ lines?: number; animated?: boolean }> = ({
  lines = 3,
  animated = true,
}) => <Skeleton variant="text" lines={lines} animated={animated} />;

/**
 * SkeletonCard — pre-composed card skeleton (thumbnail + title + meta).
 */
export const SkeletonCard: React.FC<{ animated?: boolean }> = ({
  animated = true,
}) => (
  <span className="atom-skeleton-card">
    <Skeleton variant="rect" height={160} animated={animated} className="atom-skeleton-card__thumb" />
    <span className="atom-skeleton-card__body">
      <Skeleton variant="text" lines={1} width="60%" animated={animated} />
      <Skeleton variant="text" lines={2} animated={animated} />
      <span className="atom-skeleton-card__meta">
        <Skeleton variant="circle" width={32} height={32} animated={animated} />
        <Skeleton variant="text" lines={1} width={100} animated={animated} />
      </span>
    </span>
  </span>
);
