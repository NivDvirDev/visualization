import React, { useState } from 'react';
import './Accordion.css';

export interface AccordionItem {
  id: string;
  title: string;
  content: React.ReactNode;
  disabled?: boolean;
}

export interface AccordionProps {
  items: AccordionItem[];
  allowMultiple?: boolean;
  defaultOpen?: string[];
  variant?: 'default' | 'flush' | 'glass';
}

/**
 * Accordion — collapsible content sections atom.
 * Variants: default (bordered cards), flush (no borders, edge-to-edge), glass (glass morphism).
 * Supports single or multi-open mode.
 */
export const Accordion: React.FC<AccordionProps> = ({
  items,
  allowMultiple = false,
  defaultOpen = [],
  variant = 'default',
}) => {
  const [openIds, setOpenIds] = useState<string[]>(defaultOpen);

  const toggle = (id: string) => {
    setOpenIds((prev) => {
      const isOpen = prev.includes(id);
      if (isOpen) {
        return prev.filter((x) => x !== id);
      }
      return allowMultiple ? [...prev, id] : [id];
    });
  };

  return (
    <div className={['atom-accordion', `atom-accordion--${variant}`].join(' ')}>
      {items.map((item) => {
        const isOpen = openIds.includes(item.id);
        return (
          <div
            key={item.id}
            className={[
              'atom-accordion-item',
              isOpen ? 'atom-accordion-item--open' : '',
              item.disabled ? 'atom-accordion-item--disabled' : '',
            ].filter(Boolean).join(' ')}
          >
            <button
              className="atom-accordion-trigger"
              aria-expanded={isOpen}
              aria-disabled={item.disabled}
              disabled={item.disabled}
              onClick={() => !item.disabled && toggle(item.id)}
            >
              <span className="atom-accordion-title">{item.title}</span>
              <span className="atom-accordion-chevron" aria-hidden="true">▾</span>
            </button>
            <div
              className="atom-accordion-body"
              style={{ maxHeight: isOpen ? 600 : 0 }}
              aria-hidden={!isOpen}
            >
              <div className="atom-accordion-content">{item.content}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
