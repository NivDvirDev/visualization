import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as api from '../api';

jest.mock('../api');

import ClaimCreatorPanel from '../components/labeling/ClaimCreatorPanel/ClaimCreatorPanel';

describe('ClaimCreatorPanel', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders login nudge when no token', () => {
    render(
      <ClaimCreatorPanel clipId="clip-1" token={null} onClaimed={jest.fn()} />
    );
    expect(screen.getByText(/Is this your creation\?/i)).toBeInTheDocument();
    expect(screen.getByText(/Sign in to claim it/i)).toBeInTheDocument();
  });

  it('renders "Is this your creation? Claim it" button when token is provided', () => {
    render(
      <ClaimCreatorPanel clipId="clip-1" token="mytoken" onClaimed={jest.fn()} />
    );
    expect(screen.getByText(/Is this your creation\? Claim it/i)).toBeInTheDocument();
  });

  it('shows form after clicking the button', async () => {
    render(
      <ClaimCreatorPanel clipId="clip-1" token="mytoken" onClaimed={jest.fn()} />
    );
    await userEvent.click(screen.getByText(/Is this your creation\? Claim it/i));
    expect(screen.getByLabelText(/Paste this video's YouTube URL/i)).toBeInTheDocument();
  });

  it('calls claimClip with the URL on submit', async () => {
    (api.claimClip as jest.Mock).mockResolvedValue({ claimed: true });
    render(
      <ClaimCreatorPanel clipId="clip-1" token="mytoken" onClaimed={jest.fn()} />
    );
    await userEvent.click(screen.getByText(/Is this your creation\? Claim it/i));
    const input = screen.getByLabelText(/Paste this video's YouTube URL/i);
    await userEvent.type(input, 'https://www.youtube.com/watch?v=abc123');
    await userEvent.click(screen.getByRole('button', { name: /^Claim$/i }));
    await waitFor(() =>
      expect(api.claimClip).toHaveBeenCalledWith(
        'clip-1',
        'https://www.youtube.com/watch?v=abc123',
        'mytoken'
      )
    );
  });

  it('shows success state after successful claim', async () => {
    (api.claimClip as jest.Mock).mockResolvedValue({ claimed: true });
    render(
      <ClaimCreatorPanel clipId="clip-1" token="mytoken" onClaimed={jest.fn()} />
    );
    await userEvent.click(screen.getByText(/Is this your creation\? Claim it/i));
    const input = screen.getByLabelText(/Paste this video's YouTube URL/i);
    await userEvent.type(input, 'https://www.youtube.com/watch?v=abc123');
    await userEvent.click(screen.getByRole('button', { name: /^Claim$/i }));
    await waitFor(() =>
      expect(screen.getByText(/Claimed!/i)).toBeInTheDocument()
    );
  });

  it('shows error message when claimClip throws "URL doesn\'t match"', async () => {
    (api.claimClip as jest.Mock).mockRejectedValue(new Error("URL doesn't match"));
    render(
      <ClaimCreatorPanel clipId="clip-1" token="mytoken" onClaimed={jest.fn()} />
    );
    await userEvent.click(screen.getByText(/Is this your creation\? Claim it/i));
    const input = screen.getByLabelText(/Paste this video's YouTube URL/i);
    await userEvent.type(input, 'https://www.youtube.com/watch?v=abc123');
    await userEvent.click(screen.getByRole('button', { name: /^Claim$/i }));
    await waitFor(() =>
      expect(screen.getByText(/URL doesn't match/i)).toBeInTheDocument()
    );
  });

  it('calls onClaimed callback with result', async () => {
    const mockResult = { claimed: true, display_credit: 'My Channel' };
    (api.claimClip as jest.Mock).mockResolvedValue(mockResult);
    const onClaimed = jest.fn();
    render(
      <ClaimCreatorPanel clipId="clip-1" token="mytoken" onClaimed={onClaimed} />
    );
    await userEvent.click(screen.getByText(/Is this your creation\? Claim it/i));
    const input = screen.getByLabelText(/Paste this video's YouTube URL/i);
    await userEvent.type(input, 'https://www.youtube.com/watch?v=abc123');
    await userEvent.click(screen.getByRole('button', { name: /^Claim$/i }));
    await waitFor(() => expect(onClaimed).toHaveBeenCalledWith(mockResult));
  });
});
