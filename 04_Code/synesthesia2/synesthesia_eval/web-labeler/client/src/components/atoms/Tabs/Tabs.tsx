import React from 'react';
import './Tabs.css';

export interface TabItem {
  id: string;
  label: string;
  disabled?: boolean;
}

export interface TabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (id: string) => void;
  variant?: 'default' | 'pills' | 'underline';
  size?: 'sm' | 'md' | 'lg';
}

export interface TabPanelProps {
  id: string;
  activeTab: string;
  children: React.ReactNode;
}

/**
 * Tabs — horizontal navigation atom.
 * Variants: default (bordered), pills (rounded pill buttons), underline (minimal).
 * Pair with TabPanel for accessible content areas.
 */
export const Tabs: React.FC<TabsProps> = ({
  tabs,
  activeTab,
  onChange,
  variant = 'default',
  size = 'md',
}) => (
  <div
    className={[
      'atom-tabs',
      `atom-tabs--${variant}`,
      `atom-tabs--${size}`,
    ].join(' ')}
    role="tablist"
  >
    {tabs.map((tab) => (
      <button
        key={tab.id}
        role="tab"
        aria-selected={activeTab === tab.id}
        aria-disabled={tab.disabled}
        disabled={tab.disabled}
        className={[
          'atom-tabs-tab',
          activeTab === tab.id ? 'atom-tabs-tab--active' : '',
        ].filter(Boolean).join(' ')}
        onClick={() => !tab.disabled && onChange(tab.id)}
      >
        {tab.label}
      </button>
    ))}
  </div>
);

/**
 * TabPanel — content area paired with Tabs.
 * Renders children only when its id matches activeTab.
 */
export const TabPanel: React.FC<TabPanelProps> = ({ id, activeTab, children }) => {
  if (id !== activeTab) return null;
  return (
    <div className="atom-tab-panel" role="tabpanel" aria-labelledby={id}>
      {children}
    </div>
  );
};
