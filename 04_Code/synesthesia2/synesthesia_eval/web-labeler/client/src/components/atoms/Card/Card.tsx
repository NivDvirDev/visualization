import React from 'react';
import './Card.css';

export type CardVariant = 'default' | 'elevated' | 'glass' | 'outlined';
export type CardPadding = 'none' | 'sm' | 'md' | 'lg';

export interface CardProps {
  variant?: CardVariant;
  padding?: CardPadding;
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
  onClick?: () => void;
  hoverable?: boolean;
}

/**
 * Card — general-purpose content container atom.
 * Variants: default (parchment) | elevated (white) | glass (morphism) | outlined.
 * Always compose with CardHeader, CardTitle, CardDescription, CardContent, CardFooter.
 */
export const Card: React.FC<CardProps> = ({
  variant = 'default',
  padding = 'md',
  className = '',
  style,
  children,
  onClick,
  hoverable = false,
}) => (
  <div
    className={[
      'atom-card',
      `atom-card--${variant}`,
      `atom-card--pad-${padding}`,
      hoverable ? 'atom-card--hoverable' : '',
      onClick ? 'atom-card--clickable' : '',
      className,
    ].filter(Boolean).join(' ')}
    style={style}
    onClick={onClick}
    role={onClick ? 'button' : undefined}
    tabIndex={onClick ? 0 : undefined}
    onKeyDown={onClick ? (e) => { if (e.key === 'Enter' || e.key === ' ') onClick(); } : undefined}
  >
    {children}
  </div>
);

/* ---- Sub-components ---- */

export interface CardHeaderProps {
  className?: string;
  children?: React.ReactNode;
}

export const CardHeader: React.FC<CardHeaderProps> = ({ className = '', children }) => (
  <div className={['atom-card__header', className].filter(Boolean).join(' ')}>
    {children}
  </div>
);

export interface CardTitleProps {
  className?: string;
  children?: React.ReactNode;
  as?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';
}

export const CardTitle: React.FC<CardTitleProps> = ({ className = '', children, as: Tag = 'h3' }) => (
  <Tag className={['atom-card__title', className].filter(Boolean).join(' ')}>
    {children}
  </Tag>
);

export interface CardDescriptionProps {
  className?: string;
  children?: React.ReactNode;
}

export const CardDescription: React.FC<CardDescriptionProps> = ({ className = '', children }) => (
  <p className={['atom-card__description', className].filter(Boolean).join(' ')}>
    {children}
  </p>
);

export interface CardContentProps {
  className?: string;
  children?: React.ReactNode;
}

export const CardContent: React.FC<CardContentProps> = ({ className = '', children }) => (
  <div className={['atom-card__content', className].filter(Boolean).join(' ')}>
    {children}
  </div>
);

export interface CardFooterProps {
  className?: string;
  children?: React.ReactNode;
}

export const CardFooter: React.FC<CardFooterProps> = ({ className = '', children }) => (
  <div className={['atom-card__footer', className].filter(Boolean).join(' ')}>
    {children}
  </div>
);
