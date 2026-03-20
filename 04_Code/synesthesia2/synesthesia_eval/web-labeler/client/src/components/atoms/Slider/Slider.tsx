import React, { useCallback, useId } from 'react';
import './Slider.css';

export interface SliderMark {
  value: number;
  label?: string;
}

export interface SliderProps {
  value?: number;
  defaultValue?: number;
  min?: number;
  max?: number;
  step?: number;
  onChange?: (value: number) => void;
  onChangeEnd?: (value: number) => void;
  disabled?: boolean;
  label?: string;
  showValue?: boolean;
  marks?: SliderMark[];
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'accent';
  id?: string;
  name?: string;
}

/**
 * Slider — native range input styled with custom track + thumb.
 * Uses --slider-fill-pct CSS custom property for the colored fill segment.
 * Variants: default (teal fill) and accent (flame fill).
 */
export const Slider = React.forwardRef<HTMLInputElement, SliderProps>(
  (
    {
      value,
      defaultValue,
      min = 0,
      max = 100,
      step = 1,
      onChange,
      onChangeEnd,
      disabled = false,
      label,
      showValue = false,
      marks,
      size = 'md',
      variant = 'default',
      id,
      name,
    },
    ref
  ) => {
    const uid = useId();
    const inputId = id ?? (label ? label.toLowerCase().replace(/\s+/g, '-') : uid);

    // Derive current numeric value for fill calculation
    const isControlled = value !== undefined;
    const [internalValue, setInternalValue] = React.useState<number>(
      defaultValue ?? min
    );
    const currentValue = isControlled ? value! : internalValue;

    const fillPct = ((currentValue - min) / (max - min)) * 100;

    const handleChange = useCallback(
      (e: React.ChangeEvent<HTMLInputElement>) => {
        const next = Number(e.target.value);
        if (!isControlled) setInternalValue(next);
        onChange?.(next);
      },
      [isControlled, onChange]
    );

    const handleMouseUp = useCallback(
      (e: React.MouseEvent<HTMLInputElement>) => {
        onChangeEnd?.(Number((e.target as HTMLInputElement).value));
      },
      [onChangeEnd]
    );

    const handleTouchEnd = useCallback(
      (e: React.TouchEvent<HTMLInputElement>) => {
        onChangeEnd?.(Number((e.target as HTMLInputElement).value));
      },
      [onChangeEnd]
    );

    const inputProps = isControlled
      ? { value: currentValue, onChange: handleChange }
      : { defaultValue: internalValue, onChange: handleChange };

    return (
      <div
        className={[
          'atom-slider-wrapper',
          `atom-slider-wrapper--${size}`,
          `atom-slider-wrapper--${variant}`,
          disabled ? 'atom-slider-wrapper--disabled' : '',
        ]
          .filter(Boolean)
          .join(' ')}
      >
        {/* Label row */}
        {(label || showValue) && (
          <div className="atom-slider-header">
            {label && (
              <label className="atom-slider-label" htmlFor={inputId}>
                {label}
              </label>
            )}
            {showValue && (
              <span className="atom-slider-value">{currentValue}</span>
            )}
          </div>
        )}

        {/* Track + input */}
        <div className="atom-slider-track-wrapper">
          <input
            ref={ref}
            type="range"
            id={inputId}
            name={name}
            min={min}
            max={max}
            step={step}
            disabled={disabled}
            className="atom-slider-input"
            style={{ '--slider-fill-pct': `${fillPct}%` } as React.CSSProperties}
            onMouseUp={handleMouseUp}
            onTouchEnd={handleTouchEnd}
            {...inputProps}
          />
        </div>

        {/* Marks */}
        {marks && marks.length > 0 && (
          <div className="atom-slider-marks">
            {marks.map((mark) => {
              const markPct = ((mark.value - min) / (max - min)) * 100;
              const isActive = mark.value <= currentValue;
              return (
                <span
                  key={mark.value}
                  className={[
                    'atom-slider-mark',
                    isActive ? 'atom-slider-mark--active' : '',
                  ]
                    .filter(Boolean)
                    .join(' ')}
                  style={{ left: `${markPct}%` }}
                >
                  <span className="atom-slider-mark-dot" />
                  {mark.label && (
                    <span className="atom-slider-mark-label">{mark.label}</span>
                  )}
                </span>
              );
            })}
          </div>
        )}
      </div>
    );
  }
);
Slider.displayName = 'Slider';
