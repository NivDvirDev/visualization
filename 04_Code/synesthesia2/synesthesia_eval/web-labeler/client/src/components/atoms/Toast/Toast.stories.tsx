import React, { useState } from 'react';
import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { Toast, ToastContainer, useToast } from './Toast';
import type { ToastItem } from './Toast';
import { Button } from '../Button/Button';

const meta: Meta = {
  title: 'Atoms/Toast',
  parameters: {
    layout: 'centered',
    backgrounds: { default: 'parchment' },
  },
};
export default meta;
type Story = StoryObj;

/* ---- Individual Toast (static preview) ---- */

export const SingleDefault: Story = {
  render: () => (
    <div style={{ position: 'relative', width: 380, height: 80 }}>
      <Toast
        id="t1"
        message="Your rating has been saved."
        variant="default"
        duration={0}
        onDismiss={() => {}}
      />
    </div>
  ),
};

export const SingleSuccess: Story = {
  render: () => (
    <Toast id="t2" message="Labels synced to HuggingFace." variant="success" duration={0} onDismiss={() => {}} />
  ),
};

export const SingleWarning: Story = {
  render: () => (
    <Toast id="t3" message="Only 32 clips labeled — need 50+ to train." variant="warning" duration={0} onDismiss={() => {}} />
  ),
};

export const SingleError: Story = {
  render: () => (
    <Toast id="t4" message="Failed to submit rating. Try again." variant="error" duration={0} onDismiss={() => {}} />
  ),
};

/* ---- Static stack (all variants) ---- */

export const AllVariants: Story = {
  render: () => {
    const items: ToastItem[] = [
      { id: '1', message: 'Default notification message here.', variant: 'default', duration: 0 },
      { id: '2', message: 'Rating saved successfully!', variant: 'success', duration: 0 },
      { id: '3', message: 'Dataset sync took longer than expected.', variant: 'warning', duration: 0 },
      { id: '4', message: 'Authentication failed.', variant: 'error', duration: 0 },
    ];
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, width: 380 }}>
        {items.map((t) => (
          <Toast key={t.id} {...t} onDismiss={() => {}} />
        ))}
      </div>
    );
  },
};

/* ---- Interactive: useToast hook ---- */

export const Interactive: Story = {
  render: () => {
    const { toasts, toast, dismiss } = useToast();
    return (
      <>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'center' }}>
          <Button variant="primary" size="sm" onClick={() => toast('Rating saved successfully!', { variant: 'success' })}>
            Success Toast
          </Button>
          <Button variant="secondary" size="sm" onClick={() => toast('Dataset sync in progress…', { variant: 'warning' })}>
            Warning Toast
          </Button>
          <Button variant="danger" size="sm" onClick={() => toast('Could not reach server.', { variant: 'error' })}>
            Error Toast
          </Button>
          <Button variant="ghost" size="sm" onClick={() => toast('Clip #031 loaded.', { variant: 'default' })}>
            Default Toast
          </Button>
          <Button variant="ghost" size="sm" onClick={() => toast('This toast stays until dismissed.', { variant: 'info' as any, duration: 0 })}>
            Persistent Toast
          </Button>
        </div>
        <ToastContainer toasts={toasts} onDismiss={dismiss} />
      </>
    );
  },
};

/* ---- Rapid fire ---- */

export const RapidFire: Story = {
  render: () => {
    const { toasts, toast, dismiss } = useToast();
    const messages = [
      { msg: 'Clip #001 rated', variant: 'success' as const },
      { msg: 'Clip #002 rated', variant: 'success' as const },
      { msg: 'Streak extended to 8 days!', variant: 'default' as const },
      { msg: 'HuggingFace sync started', variant: 'warning' as const },
    ];
    let i = 0;
    return (
      <>
        <Button
          variant="primary"
          onClick={() => {
            const m = messages[i % messages.length];
            toast(m.msg, { variant: m.variant, duration: 4000 });
            i++;
          }}
        >
          Fire Next Toast
        </Button>
        <ToastContainer toasts={toasts} onDismiss={dismiss} />
      </>
    );
  },
};

/* ---- Long duration / persistent ---- */

export const Persistent: Story = {
  render: () => {
    const { toasts, toast, dismiss } = useToast();
    return (
      <>
        <Button variant="secondary" onClick={() => toast('This toast will not auto-dismiss. Click × to close.', { duration: 0 })}>
          Show Persistent Toast
        </Button>
        <ToastContainer toasts={toasts} onDismiss={dismiss} />
      </>
    );
  },
};

/* ---- Full system demo ---- */

export const SystemDemo: Story = {
  render: () => {
    const { toasts, toast, dismiss } = useToast();
    const [count, setCount] = useState(0);

    const handleRate = () => {
      const c = count + 1;
      setCount(c);
      toast(`Clip #0${String(c).padStart(2, '0')} rated!`, { variant: 'success', duration: 3000 });
      if (c % 5 === 0) {
        setTimeout(() => toast(`Streak milestone: ${c} clips rated!`, { variant: 'default', duration: 5000 }), 400);
      }
    };

    return (
      <>
        <div style={{ textAlign: 'center' }}>
          <p style={{ marginBottom: 16, fontSize: 14, color: '#8B7355' }}>
            Rated: <strong>{count}</strong> clips
          </p>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
            <Button variant="primary" onClick={handleRate}>Rate Clip</Button>
            <Button variant="danger" size="sm" onClick={() => toast('Label deleted.', { variant: 'error' })}>Delete Label</Button>
            <Button variant="ghost" size="sm" onClick={() => toast('Sync complete.', { variant: 'success' })}>Sync HF</Button>
          </div>
        </div>
        <ToastContainer toasts={toasts} onDismiss={dismiss} />
      </>
    );
  },
};
