import React, { useState, useRef, useEffect, useCallback, useId } from 'react';
import './Select.css';

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface SelectProps {
  options: SelectOption[];
  value?: string;
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg';
  error?: string;
  label?: string;
}

/**
 * Select — custom dropdown atom.
 * Custom-built (no native <select>) to match Input atom styling.
 * Keyboard: ArrowUp/Down to navigate, Enter to select, Escape to close.
 * Click outside closes the dropdown.
 */
export const Select: React.FC<SelectProps> = ({
  options,
  value,
  onChange,
  placeholder = 'Choose an option…',
  disabled = false,
  size = 'md',
  error,
  label,
}) => {
  const uid = useId();
  const [open, setOpen] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState<number>(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  const selectedOption = options.find((o) => o.value === value);

  /* Close on outside click */
  useEffect(() => {
    if (!open) return;
    const handleMouseDown = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handleMouseDown);
    return () => document.removeEventListener('mousedown', handleMouseDown);
  }, [open]);

  /* Scroll focused option into view */
  useEffect(() => {
    if (!open || focusedIndex < 0 || !listRef.current) return;
    const el = listRef.current.children[focusedIndex] as HTMLElement | null;
    el?.scrollIntoView({ block: 'nearest' });
  }, [focusedIndex, open]);

  const toggleOpen = () => {
    if (disabled) return;
    if (!open) {
      const currentIdx = options.findIndex((o) => o.value === value);
      setFocusedIndex(currentIdx >= 0 ? currentIdx : 0);
    }
    setOpen((v) => !v);
  };

  const selectOption = useCallback(
    (opt: SelectOption) => {
      if (opt.disabled) return;
      onChange(opt.value);
      setOpen(false);
    },
    [onChange],
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    const enabledIndices = options
      .map((o, i) => ({ o, i }))
      .filter(({ o }) => !o.disabled)
      .map(({ i }) => i);

    if (!open) {
      if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown') {
        e.preventDefault();
        setFocusedIndex(enabledIndices[0] ?? 0);
        setOpen(true);
      }
      return;
    }

    if (e.key === 'Escape') {
      e.preventDefault();
      setOpen(false);
      return;
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      const next = enabledIndices.find((i) => i > focusedIndex);
      if (next !== undefined) setFocusedIndex(next);
      return;
    }

    if (e.key === 'ArrowUp') {
      e.preventDefault();
      const prev = [...enabledIndices].reverse().find((i) => i < focusedIndex);
      if (prev !== undefined) setFocusedIndex(prev);
      return;
    }

    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      const opt = options[focusedIndex];
      if (opt && !opt.disabled) selectOption(opt);
      return;
    }

    /* Type-ahead: jump to first matching option */
    if (e.key.length === 1) {
      const char = e.key.toLowerCase();
      const match = enabledIndices.find((i) => options[i].label.toLowerCase().startsWith(char));
      if (match !== undefined) setFocusedIndex(match);
    }
  };

  const triggerId = `${uid}-trigger`;
  const listId = `${uid}-list`;

  return (
    <div className="atom-select-wrapper" ref={containerRef}>
      {label && (
        <label className="atom-select-label" htmlFor={triggerId}>
          {label}
        </label>
      )}

      {/* Trigger button */}
      <button
        id={triggerId}
        type="button"
        role="combobox"
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-controls={listId}
        aria-disabled={disabled}
        aria-invalid={!!error}
        disabled={disabled}
        className={[
          'atom-select-trigger',
          `atom-select-trigger--${size}`,
          open ? 'atom-select-trigger--open' : '',
          error ? 'atom-select-trigger--error' : '',
          !selectedOption ? 'atom-select-trigger--placeholder' : '',
        ].filter(Boolean).join(' ')}
        onClick={toggleOpen}
        onKeyDown={handleKeyDown}
      >
        <span className="atom-select-value">
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <span className="atom-select-chevron" aria-hidden="true">▾</span>
      </button>

      {/* Dropdown panel */}
      {open && (
        <ul
          id={listId}
          ref={listRef}
          role="listbox"
          aria-label={label ?? 'Options'}
          className="atom-select-dropdown"
        >
          {options.map((opt, i) => (
            <li
              key={opt.value}
              role="option"
              aria-selected={opt.value === value}
              aria-disabled={opt.disabled}
              className={[
                'atom-select-option',
                opt.value === value ? 'atom-select-option--selected' : '',
                i === focusedIndex ? 'atom-select-option--focused' : '',
                opt.disabled ? 'atom-select-option--disabled' : '',
              ].filter(Boolean).join(' ')}
              onMouseDown={(e) => e.preventDefault()} /* prevent blur before click */
              onClick={() => selectOption(opt)}
              onMouseEnter={() => !opt.disabled && setFocusedIndex(i)}
            >
              {opt.label}
            </li>
          ))}
        </ul>
      )}

      {/* Error message */}
      {error && (
        <span className="atom-select-error" role="alert">
          {error}
        </span>
      )}
    </div>
  );
};
