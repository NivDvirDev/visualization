import React, { useEffect, useRef } from 'react';
import ReactDOM from 'react-dom';
import './Modal.css';

export type ModalSize = 'sm' | 'md' | 'lg' | 'full';

export interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  size?: ModalSize;
  children?: React.ReactNode;
  footer?: React.ReactNode;
  closeOnBackdrop?: boolean;
}

/**
 * Modal — portal-based overlay dialog atom.
 * Renders into document.body via ReactDOM.createPortal.
 * Supports slide-in animation, glass-morphism panel, and backdrop dismiss.
 */
export const Modal: React.FC<ModalProps> = ({
  open,
  onClose,
  title,
  size = 'md',
  children,
  footer,
  closeOnBackdrop = true,
}) => {
  const panelRef = useRef<HTMLDivElement>(null);

  // Close on Escape key
  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [open, onClose]);

  // Prevent body scroll when open
  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [open]);

  if (!open) return null;

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (closeOnBackdrop && e.target === e.currentTarget) onClose();
  };

  return ReactDOM.createPortal(
    <div
      className="atom-modal-backdrop"
      onClick={handleBackdropClick}
      aria-modal="true"
      role="dialog"
      aria-label={title}
    >
      <div
        ref={panelRef}
        className={['atom-modal', `atom-modal--${size}`].join(' ')}
      >
        <div className="atom-modal__header">
          {title && <h2 className="atom-modal__title">{title}</h2>}
          <button
            className="atom-modal__close"
            onClick={onClose}
            aria-label="Close modal"
          >
            ×
          </button>
        </div>

        {children && (
          <div className="atom-modal__body">
            {children}
          </div>
        )}

        {footer && (
          <div className="atom-modal__footer">
            {footer}
          </div>
        )}
      </div>
    </div>,
    document.body,
  );
};
