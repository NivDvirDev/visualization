import React from 'react';
import './Switch.css';

export interface SwitchProps {
  checked?: boolean;
  defaultChecked?: boolean;
  onChange?: (checked: boolean) => void;
  label?: string;
  description?: string;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'accent';
  id?: string;
  name?: string;
}

/**
 * Switch — pill-shaped toggle atom.
 * Thumb slides via CSS transform. Variants: default (teal) and accent (flame).
 */
export const Switch = React.forwardRef<HTMLInputElement, SwitchProps>(
  (
    {
      checked,
      defaultChecked,
      onChange,
      label,
      description,
      disabled = false,
      size = 'md',
      variant = 'default',
      id,
      name,
    },
    ref
  ) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-') ?? 'switch';

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
          'atom-switch-wrapper',
          `atom-switch-wrapper--${size}`,
          `atom-switch-wrapper--${variant}`,
          disabled ? 'atom-switch-wrapper--disabled' : '',
        ]
          .filter(Boolean)
          .join(' ')}
      >
        <label className="atom-switch-row" htmlFor={inputId}>
          {/* Hidden native checkbox */}
          <input
            ref={ref}
            type="checkbox"
            role="switch"
            id={inputId}
            name={name}
            className="atom-switch-input"
            disabled={disabled}
            aria-describedby={description ? `${inputId}-desc` : undefined}
            {...controlledProps}
          />

          {/* Visual track + thumb */}
          <span className="atom-switch-track" aria-hidden="true">
            <span className="atom-switch-thumb" />
          </span>

          {/* Label + description */}
          {(label || description) && (
            <span className="atom-switch-text">
              {label && <span className="atom-switch-label">{label}</span>}
              {description && (
                <span id={`${inputId}-desc`} className="atom-switch-description">
                  {description}
                </span>
              )}
            </span>
          )}
        </label>
      </div>
    );
  }
);
Switch.displayName = 'Switch';
