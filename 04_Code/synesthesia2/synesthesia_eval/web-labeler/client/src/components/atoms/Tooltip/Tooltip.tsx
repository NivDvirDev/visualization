import React, { useState, useRef } from 'react';
import './Tooltip.css';

export type TooltipPlacement = 'top' | 'bottom' | 'left' | 'right';

export interface TooltipProps {
  content: React.ReactNode;
  placement?: TooltipPlacement;
  delay?: number;
  children: React.ReactElement;
  disabled?: boolean;
  maxWidth?: number;
}

/**
 * Tooltip — hover hint atom.
 * Wraps any single child element and shows a positioned bubble on hover.
 */
export const Tooltip: React.FC<TooltipProps> = ({
  content,
  placement = 'top',
  delay = 300,
  children,
  disabled = false,
  maxWidth = 200,
}) => {
  const [visible, setVisible] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const show = () => {
    if (disabled) return;
    timerRef.current = setTimeout(() => setVisible(true), delay);
  };

  const hide = () => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    setVisible(false);
  };

  return (
    <span
      className="atom-tooltip-wrapper"
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
    >
      {children}
      {visible && !disabled && (
        <span
          role="tooltip"
          className={[
            'atom-tooltip',
            `atom-tooltip--${placement}`,
          ].join(' ')}
          style={{ maxWidth }}
        >
          {content}
          <span className="atom-tooltip__arrow" aria-hidden="true" />
        </span>
      )}
    </span>
  );
};
