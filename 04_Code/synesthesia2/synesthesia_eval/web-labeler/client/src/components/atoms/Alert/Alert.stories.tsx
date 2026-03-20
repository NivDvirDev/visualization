import React, { useState } from 'react';
import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { Alert } from './Alert';

const meta: Meta<typeof Alert> = {
  title: 'Atoms/Alert',
  component: Alert,
  parameters: {
    layout: 'padded',
    backgrounds: { default: 'parchment' },
  },
  argTypes: {
    variant: { control: 'select', options: ['info', 'success', 'warning', 'error'] },
    dismissible: { control: 'boolean' },
    icon: { control: 'boolean' },
  },
};
export default meta;
type Story = StoryObj<typeof Alert>;

/* ---- Individual variants ---- */

export const Info: Story = {
  args: {
    variant: 'info',
    title: 'Did you know?',
    children: 'Cochlear spiral visualizations map frequency to angular position logarithmically.',
  },
};

export const Success: Story = {
  args: {
    variant: 'success',
    title: 'Rating Saved',
    children: 'Your labels for Clip #027 have been submitted and synced to HuggingFace.',
  },
};

export const Warning: Story = {
  args: {
    variant: 'warning',
    title: 'Almost There',
    children: 'You need at least 50 labeled clips before training the scoring model.',
  },
};

export const Error: Story = {
  args: {
    variant: 'error',
    title: 'Submission Failed',
    children: 'Could not save your rating. Check your connection and try again.',
  },
};

/* ---- Dismissible (interactive) ---- */

export const Dismissible: Story = {
  render: () => {
    const [visible, setVisible] = useState(true);
    return visible ? (
      <Alert
        variant="info"
        title="Welcome Back"
        dismissible
        onDismiss={() => setVisible(false)}
      >
        Your streak is now 7 days! Keep rating to maintain it.
      </Alert>
    ) : (
      <div style={{ padding: 12, color: '#888', fontSize: 13 }}>
        Alert dismissed. Refresh to see it again.
      </div>
    );
  },
};

export const DismissibleError: Story = {
  render: () => {
    const [visible, setVisible] = useState(true);
    return visible ? (
      <Alert
        variant="error"
        title="Authentication Error"
        dismissible
        onDismiss={() => setVisible(false)}
      >
        Your session has expired. Please sign in again to continue.
      </Alert>
    ) : (
      <div style={{ padding: 12, color: '#888', fontSize: 13 }}>Alert dismissed.</div>
    );
  },
};

/* ---- No icon ---- */

export const NoIcon: Story = {
  args: {
    variant: 'success',
    icon: false,
    title: 'Label Synced',
    children: 'Pushed to HuggingFace dataset NivDvir/synesthesia-eval.',
  },
};

/* ---- Title only / content only ---- */

export const TitleOnly: Story = {
  args: { variant: 'warning', title: 'Model training requires 50+ labeled clips.' },
};

export const ContentOnly: Story = {
  args: { variant: 'info', children: 'Tip: use keyboard shortcuts J / K to navigate clips.' },
};

/* ---- All variants ---- */

export const AllVariants: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, maxWidth: 480 }}>
      <Alert variant="info" title="Info">General informational message for the user.</Alert>
      <Alert variant="success" title="Success">Action completed successfully.</Alert>
      <Alert variant="warning" title="Warning">Attention required — something may be wrong.</Alert>
      <Alert variant="error" title="Error">A critical error has occurred.</Alert>
    </div>
  ),
};

/* ---- All dismissible ---- */

export const AllDismissible: Story = {
  render: () => {
    const [dismissed, setDismissed] = useState<Record<string, boolean>>({});
    const variants = ['info', 'success', 'warning', 'error'] as const;
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, maxWidth: 480 }}>
        {variants.map((v) =>
          dismissed[v] ? null : (
            <Alert
              key={v}
              variant={v}
              title={v.charAt(0).toUpperCase() + v.slice(1)}
              dismissible
              onDismiss={() => setDismissed((d) => ({ ...d, [v]: true }))}
            >
              This is a {v} alert. Click × to dismiss.
            </Alert>
          )
        )}
        {Object.keys(dismissed).length === variants.length && (
          <div style={{ fontSize: 13, color: '#888' }}>All dismissed.</div>
        )}
      </div>
    );
  },
};
