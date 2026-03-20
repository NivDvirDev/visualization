import React from 'react';
import './Alert.css';

export type AlertVariant = 'info' | 'success' | 'warning' | 'error';

export interface AlertProps {
  variant?: AlertVariant;
  title?: string;
  children?: React.ReactNode;
  dismissible?: boolean;
  onDismiss?: () => void;
  icon?: boolean;
}

const ICONS: Record<AlertVariant, string> = {
  info: 'ℹ️',
  success: '✅',
  warning: '⚠️',
  error: '❌',
};

/**
 * Alert — inline status message atom.
 * Left-border accent matches variant color. Optionally dismissible.
 * Never use raw div+styles for status messages — consume this atom instead.
 */
export const Alert: React.FC<AlertProps> = ({
  variant = 'info',
  title,
  children,
  dismissible = false,
  onDismiss,
  icon = true,
}) => (
  <div
    className={['atom-alert', `atom-alert--${variant}`].join(' ')}
    role="alert"
  >
    {icon && (
      <span className="atom-alert__icon" aria-hidden="true">
        {ICONS[variant]}
      </span>
    )}

    <div className="atom-alert__body">
      {title && <div className="atom-alert__title">{title}</div>}
      {children && <div className="atom-alert__message">{children}</div>}
    </div>

    {dismissible && (
      <button
        className="atom-alert__dismiss"
        onClick={onDismiss}
        aria-label="Dismiss alert"
      >
        ×
      </button>
    )}
  </div>
);
