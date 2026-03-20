import React, { useState } from 'react';
import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { Modal } from './Modal';
import { Button } from '../Button/Button';

const meta: Meta<typeof Modal> = {
  title: 'Atoms/Modal',
  component: Modal,
  parameters: {
    layout: 'centered',
    backgrounds: { default: 'parchment' },
  },
  argTypes: {
    size: { control: 'select', options: ['sm', 'md', 'lg', 'full'] },
    closeOnBackdrop: { control: 'boolean' },
  },
};
export default meta;
type Story = StoryObj<typeof Modal>;

/* ---- Interactive wrapper ---- */

const ModalDemo = ({
  size = 'md' as const,
  title = 'Modal Title',
  footer,
  closeOnBackdrop = true,
  children,
}: {
  size?: 'sm' | 'md' | 'lg' | 'full';
  title?: string;
  footer?: React.ReactNode;
  closeOnBackdrop?: boolean;
  children?: React.ReactNode;
}) => {
  const [open, setOpen] = useState(false);
  return (
    <>
      <Button variant="primary" onClick={() => setOpen(true)}>
        Open {size.toUpperCase()} Modal
      </Button>
      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title={title}
        size={size}
        footer={footer}
        closeOnBackdrop={closeOnBackdrop}
      >
        {children ?? (
          <p style={{ margin: 0, lineHeight: 1.6 }}>
            This is the modal body. It supports arbitrary React content —
            forms, media, detailed clip ratings, confirmation prompts, etc.
            Dismiss with the × button, the Escape key, or by clicking the backdrop.
          </p>
        )}
      </Modal>
    </>
  );
};

/* ---- Stories ---- */

export const Small: Story = {
  render: () => (
    <ModalDemo size="sm" title="Confirm Action">
      <p style={{ margin: 0 }}>Are you sure you want to delete this label? This action cannot be undone.</p>
    </ModalDemo>
  ),
};

export const Medium: Story = {
  render: () => (
    <ModalDemo
      size="md"
      title="Rate This Clip"
      footer={
        <>
          <Button variant="ghost" size="sm">Cancel</Button>
          <Button variant="primary" size="sm">Submit Rating</Button>
        </>
      }
    >
      <p style={{ margin: '0 0 12px' }}>
        Score the clip on all four dimensions (1–5 each).
      </p>
      <div style={{ display: 'grid', gap: 10 }}>
        {['Sync Quality', 'Visual-Audio Alignment', 'Aesthetic Quality', 'Motion Smoothness'].map((dim) => (
          <div key={dim} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 13 }}>{dim}</span>
            <div style={{ display: 'flex', gap: 4 }}>
              {[1, 2, 3, 4, 5].map((n) => (
                <button key={n} style={{
                  width: 28, height: 28, borderRadius: 4, border: '1px solid #ddd',
                  cursor: 'pointer', background: n === 4 ? '#FF6B35' : 'white',
                  color: n === 4 ? 'white' : '#333', fontSize: 12,
                }}>{n}</button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </ModalDemo>
  ),
};

export const Large: Story = {
  render: () => (
    <ModalDemo size="lg" title="Clip Detail — Radial Seismograph v3">
      <div style={{ display: 'flex', gap: 20, flexDirection: 'column' }}>
        <div style={{ background: '#1A1A2E', borderRadius: 8, height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#aaa', fontSize: 13 }}>
          [Video Player Placeholder]
        </div>
        <p style={{ margin: 0, fontSize: 13, lineHeight: 1.6 }}>
          A 3D wireframe cochlear spiral rendered with ModernGL. Frequency bins mapped
          to logarithmic angular positions along the helix. Color encodes octave position
          via HSV rainbow (myjet colormap port from MATLAB).
        </p>
      </div>
    </ModalDemo>
  ),
};

export const FullScreen: Story = {
  render: () => (
    <ModalDemo size="full" title="Fullscreen View" closeOnBackdrop={false}>
      <p style={{ margin: 0 }}>
        Full-screen modal. Backdrop click is disabled (closeOnBackdrop=false).
        Use the × button or Escape key to dismiss.
      </p>
    </ModalDemo>
  ),
};

export const WithFooter: Story = {
  render: () => (
    <ModalDemo
      size="sm"
      title="Delete Label"
      footer={
        <>
          <Button variant="ghost" size="sm">Keep It</Button>
          <Button variant="danger" size="sm">Delete</Button>
        </>
      }
    >
      <p style={{ margin: 0 }}>
        Permanently remove your rating for <strong>Clip #027</strong>?
        You can re-rate at any time.
      </p>
    </ModalDemo>
  ),
};

export const NoBackdropDismiss: Story = {
  render: () => (
    <ModalDemo size="md" title="Required Action" closeOnBackdrop={false}>
      <p style={{ margin: 0 }}>
        closeOnBackdrop is false — clicking outside does nothing.
        You must use the × button or Escape key.
      </p>
    </ModalDemo>
  ),
};

export const AllSizes: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
      {(['sm', 'md', 'lg'] as const).map((s) => (
        <ModalDemo key={s} size={s} title={`${s.toUpperCase()} Modal`} />
      ))}
    </div>
  ),
};
