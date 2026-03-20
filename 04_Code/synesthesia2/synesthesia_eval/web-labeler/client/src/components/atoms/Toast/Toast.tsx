import React, { useEffect, useState, useCallback } from 'react';
import ReactDOM from 'react-dom';
import './Toast.css';

export type ToastVariant = 'default' | 'success' | 'warning' | 'error';

export interface ToastItem {
  id: string;
  message: string;
  variant?: ToastVariant;
  duration?: number;
}

export interface ToastProps extends ToastItem {
  onDismiss: (id: string) => void;
}

const VARIANT_ICONS: Record<ToastVariant, string> = {
  default: '💬',
  success: '✅',
  warning: '⚠️',
  error: '❌',
};

/**
 * Toast — individual auto-dismissing notification atom.
 * Rendered inside ToastContainer — never use directly in layouts.
 */
export const Toast: React.FC<ToastProps> = ({
  id,
  message,
  variant = 'default',
  duration = 3000,
  onDismiss,
}) => {
  const [visible, setVisible] = useState(false);

  // Trigger enter animation on mount
  useEffect(() => {
    const raf = requestAnimationFrame(() => setVisible(true));
    return () => cancelAnimationFrame(raf);
  }, []);

  // Auto-dismiss after duration (0 = persistent)
  useEffect(() => {
    if (!duration) return;
    const timer = setTimeout(() => onDismiss(id), duration);
    return () => clearTimeout(timer);
  }, [id, duration, onDismiss]);

  return (
    <div
      className={[
        'atom-toast',
        `atom-toast--${variant}`,
        visible ? 'atom-toast--visible' : '',
      ].filter(Boolean).join(' ')}
      role="status"
      aria-live="polite"
    >
      <span className="atom-toast__icon" aria-hidden="true">
        {VARIANT_ICONS[variant]}
      </span>
      <span className="atom-toast__message">{message}</span>
      <button
        className="atom-toast__dismiss"
        onClick={() => onDismiss(id)}
        aria-label="Dismiss notification"
      >
        ×
      </button>
    </div>
  );
};

/* ---- ToastContainer ---- */

export interface ToastContainerProps {
  toasts: ToastItem[];
  onDismiss: (id: string) => void;
}

/**
 * ToastContainer — fixed bottom-right stack that renders all active toasts.
 * Mount once at the app root and pass the toasts array from useToast().
 */
export const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onDismiss }) => {
  if (toasts.length === 0) return null;

  return ReactDOM.createPortal(
    <div className="atom-toast-container" aria-label="Notifications">
      {toasts.map((t) => (
        <Toast key={t.id} {...t} onDismiss={onDismiss} />
      ))}
    </div>,
    document.body,
  );
};

/* ---- useToast hook ---- */

let _idCounter = 0;
const nextId = () => `toast-${++_idCounter}`;

export interface UseToastOptions {
  variant?: ToastVariant;
  duration?: number;
}

export interface UseToastReturn {
  toasts: ToastItem[];
  toast: (message: string, opts?: UseToastOptions) => string;
  dismiss: (id: string) => void;
}

/**
 * useToast — manages toast state.
 * Returns { toasts, toast(msg, opts?), dismiss(id) }.
 * Pass toasts and dismiss to <ToastContainer>.
 */
export function useToast(): UseToastReturn {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback((message: string, opts: UseToastOptions = {}): string => {
    const id = nextId();
    const item: ToastItem = {
      id,
      message,
      variant: opts.variant ?? 'default',
      duration: opts.duration !== undefined ? opts.duration : 3000,
    };
    setToasts((prev) => [...prev, item]);
    return id;
  }, []);

  return { toasts, toast, dismiss };
}
