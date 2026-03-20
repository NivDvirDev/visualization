import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as api from '../api';

jest.mock('../api');

import CreatorControls from '../components/labeling/CreatorControls/CreatorControls';

const defaultProps = {
  clipId: 'clip-1',
  initialCredit: 'My Channel',
  initialLink: 'https://youtube.com/@mychannel',
  initialVisible: true,
  token: 'mytoken',
  onUpdate: jest.fn(),
  onUnclaim: jest.fn(),
};

describe('CreatorControls', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders edit form with initialCredit filled in', () => {
    render(<CreatorControls {...defaultProps} />);
    const input = screen.getByLabelText(/Display name/i) as HTMLInputElement;
    expect(input.value).toBe('My Channel');
  });

  it('can change display name field', async () => {
    render(<CreatorControls {...defaultProps} />);
    const input = screen.getByLabelText(/Display name/i) as HTMLInputElement;
    await userEvent.clear(input);
    await userEvent.type(input, 'New Name');
    expect(input.value).toBe('New Name');
  });

  it('calls updateCreatorDisplay with updated values on save', async () => {
    (api.updateCreatorDisplay as jest.Mock).mockResolvedValue({ ok: true });
    render(<CreatorControls {...defaultProps} />);
    const input = screen.getByLabelText(/Display name/i);
    await userEvent.clear(input);
    await userEvent.type(input, 'Updated Channel');
    await userEvent.click(screen.getByRole('button', { name: /^Save$/i }));
    await waitFor(() =>
      expect(api.updateCreatorDisplay).toHaveBeenCalledWith(
        'clip-1',
        expect.objectContaining({ display_credit: 'Updated Channel' }),
        'mytoken'
      )
    );
  });

  it('toggles credit_visible checkbox and includes in save', async () => {
    (api.updateCreatorDisplay as jest.Mock).mockResolvedValue({ ok: true });
    render(<CreatorControls {...defaultProps} initialVisible={true} />);
    const checkbox = screen.getByRole('checkbox') as HTMLInputElement;
    expect(checkbox.checked).toBe(true);
    await userEvent.click(checkbox);
    expect(checkbox.checked).toBe(false);
    await userEvent.click(screen.getByRole('button', { name: /^Save$/i }));
    await waitFor(() =>
      expect(api.updateCreatorDisplay).toHaveBeenCalledWith(
        'clip-1',
        expect.objectContaining({ credit_visible: false }),
        'mytoken'
      )
    );
  });

  it('shows "Remove Claim" button', () => {
    render(<CreatorControls {...defaultProps} />);
    expect(screen.getByText(/Remove Claim/i)).toBeInTheDocument();
  });

  it('shows confirm dialog on "Remove Claim" click', async () => {
    render(<CreatorControls {...defaultProps} />);
    await userEvent.click(screen.getByText(/Remove Claim/i));
    expect(screen.getByText(/Are you sure\?/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Yes, remove/i })).toBeInTheDocument();
  });

  it('calls unclaimClip on confirm + calls onUnclaim callback', async () => {
    (api.unclaimClip as jest.Mock).mockResolvedValue(undefined);
    const onUnclaim = jest.fn();
    render(<CreatorControls {...defaultProps} onUnclaim={onUnclaim} />);
    await userEvent.click(screen.getByText(/Remove Claim/i));
    await userEvent.click(screen.getByRole('button', { name: /Yes, remove/i }));
    await waitFor(() => {
      expect(api.unclaimClip).toHaveBeenCalledWith('clip-1', 'mytoken');
      expect(onUnclaim).toHaveBeenCalled();
    });
  });
});
