import React, { useEffect, useRef } from 'react';
import './Checkbox.css';

export interface CheckboxProps {
  checked?: boolean;
  defaultChecked?: boolean;
  onChange?: (checked: boolean) => void;
  label?: string;
  description?: string;
  disabled?: boolean;
  error?: string;
  size?: 'sm' | 'md' | 'lg';
  indeterminate?: boolean;
  id?: string;
  name?: string;
}

/**
 * Checkbox — custom-styled checkbox atom.
 * Supports checked, indeterminate, error, and all size variants.
 */
export const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  (
    {
      checked,
      defaultChecked,
      onChange,
      label,
      description,
      disabled = false,
      error,
      size = 'md',
      indeterminate = false,
      id,
      name,
    },
    ref
  ) => {
    const internalRef = useRef<HTMLInputElement>(null);
    const resolvedRef = (ref as React.RefObject<HTMLInputElement>) ?? internalRef;

    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-') ?? 'checkbox';

    // Sync indeterminate DOM property (not a real HTML attribute)
    useEffect(() => {
      if (resolvedRef.current) {
        resolvedRef.current.indeterminate = indeterminate;
      }
    }, [indeterminate, resolvedRef]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      onChange?.(e.target.checked);
    };

    const isControlled = checked !== undefined;
    const controlledProps = isControlled
      ? { checked, onChange: handleChange }
      : { defaultChecked, onChange: handleChange };

    return (
      <div
        className={[
          'atom-checkbox-wrapper',
          `atom-checkbox-wrapper--${size}`,
          disabled ? 'atom-checkbox-wrapper--disabled' : '',
          error ? 'atom-checkbox-wrapper--error' : '',
        ]
          .filter(Boolean)
          .join(' ')}
      >
        <label className="atom-checkbox-row" htmlFor={inputId}>
          {/* Hidden native input */}
          <input
            ref={resolvedRef}
            type="checkbox"
            id={inputId}
            name={name}
            className="atom-checkbox-input"
            disabled={disabled}
            aria-invalid={!!error}
            aria-describedby={error ? `${inputId}-error` : description ? `${inputId}-desc` : undefined}
            {...controlledProps}
          />

          {/* Visual control */}
          <span
            className={[
              'atom-checkbox-control',
              indeterminate ? 'atom-checkbox-control--indeterminate' : '',
            ]
              .filter(Boolean)
              .join(' ')}
            aria-hidden="true"
          />

          {/* Label + description */}
          {(label || description) && (
            <span className="atom-checkbox-text">
              {label && <span className="atom-checkbox-label">{label}</span>}
              {description && (
                <span id={`${inputId}-desc`} className="atom-checkbox-description">
                  {description}
                </span>
              )}
            </span>
          )}
        </label>

        {error && (
          <span id={`${inputId}-error`} className="atom-checkbox-error" role="alert">
            {error}
          </span>
        )}
      </div>
    );
  }
);
Checkbox.displayName = 'Checkbox';
