import React from 'react';
import './Typography.css';

export type TypographyVariant =
  | 'display-xl' | 'display-lg' | 'display-md' | 'display-sm'
  | 'body-lg' | 'body-md' | 'body-sm'
  | 'label' | 'caption'
  | 'mono' | 'mono-stat';

export type TypographyColor = 'primary' | 'secondary' | 'muted' | 'accent' | 'bright' | 'gradient';

export interface TypographyProps {
  variant: TypographyVariant;
  color?: TypographyColor;
  as?: keyof React.JSX.IntrinsicElements;
  className?: string;
  children: React.ReactNode;
}

const defaultTag: Record<TypographyVariant, keyof React.JSX.IntrinsicElements> = {
  'display-xl': 'h1',
  'display-lg': 'h2',
  'display-md': 'h3',
  'display-sm': 'h4',
  'body-lg': 'p',
  'body-md': 'p',
  'body-sm': 'p',
  'label': 'span',
  'caption': 'span',
  'mono': 'span',
  'mono-stat': 'span',
};

/**
 * Typography — type-scale atom.
 * Always use this instead of inline font-family / font-size rules.
 * Three type scales: Display (Orbitron), Body (Inter), Mono (Space Mono).
 */
export const Typography: React.FC<TypographyProps> = ({
  variant,
  color = 'primary',
  as,
  className = '',
  children,
}) => {
  const Tag = (as ?? defaultTag[variant]) as React.ElementType;
  return (
    <Tag
      className={[
        `atom-type--${variant}`,
        `atom-type-color--${color}`,
        className,
      ].filter(Boolean).join(' ')}
    >
      {children}
    </Tag>
  );
};
