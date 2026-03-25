"""
Port of MATLAB flowAMP — smooth energy envelope for wave speed modulation.
From piperecord11_LE-2C.m lines 323-373.

The energy envelope modulates the traveling wave speed along the spiral,
creating a breathing/pulsing effect synchronized with the music's energy.
"""

import numpy as np
from scipy.signal import lfilter


def compute_flow_amp(amplitude_data: np.ndarray) -> np.ndarray:
    """
    Compute smooth energy envelope from amplitude data.

    Applies a cascade of exponential-decay IIR filters to the mean power
    spectrum, producing a smooth curve that tracks musical energy.

    Args:
        amplitude_data: [num_freq_bins, num_frames] amplitude matrix

    Returns:
        [num_frames] energy envelope normalized to [0, 1]
    """
    num_bins, num_frames = amplitude_data.shape

    # Step 1: Power spectrum mean across frequency bins
    power = np.abs(amplitude_data) ** 2 / num_frames
    mean_power = np.mean(power, axis=0)
    mean_power = np.abs(mean_power)

    # Normalize to [0, 2]
    max_val = np.max(mean_power)
    if max_val > 0:
        mean_power = (mean_power / max_val) * 2

    # Step 2: Initial 1/i weighted low-pass filter
    b_init = np.array([1.0 / (i + 1) for i in range(50)])
    filtered = lfilter(b_init, [1.0], mean_power)

    # Step 3: Cascade of exponential-decay filters (5 passes)
    # Window sizes: 25, 20, 15, 10, 5
    for i2 in range(1, 25, 5):
        ws = 26 - i2
        b = np.array([1.0 - np.exp(-(i + 1) / ws) for i in range(ws)])
        b = b[::-1]
        b = b / np.sum(b)
        filtered = lfilter(b, [1.0], filtered)

    # Step 4: Compensate filter delay
    filtered = np.roll(filtered, -30)

    # Step 5: Normalize to [0, 1]
    max_val = np.max(np.abs(filtered))
    if max_val > 0:
        filtered = filtered / max_val

    return np.clip(filtered, 0, 1)
