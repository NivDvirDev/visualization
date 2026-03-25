"""
Octave-aligned HSV colormap — port of sound8_LEF.m (latest SSD version).

Each 360° spiral revolution = one octave (frequency doubles per turn).
Hue is derived from angular position within each turn, so the same
pitch gets the same color across all octaves.

Color modulation formula from piperecord11_LEF.m:
  maxWhite = max(flip(u).*(0.0035*amp));
  cc = C - flip(u)*0.01 + flip(u)*(0.0035*amp) / maxWhite;
"""

import numpy as np
import colorsys


def create_myjet_colormap(num_bins: int, theta: np.ndarray = None) -> np.ndarray:
    """
    Create octave-aligned HSV rainbow colormap.
    Hue = (theta mod 2π) / 2π — same radial direction = same color.
    """
    colors = np.zeros((num_bins, 3), dtype=np.float32)

    if theta is not None and len(theta) == num_bins:
        for i in range(num_bins):
            hue = (theta[i] % (2 * np.pi)) / (2 * np.pi)
            r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            colors[i] = [r, g, b]
    else:
        bins_per_octave = num_bins / 7.0
        for i in range(num_bins):
            hue = (i % bins_per_octave) / bins_per_octave
            r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            colors[i] = [r, g, b]

    return colors


def modulate_colors(base_colors: np.ndarray,
                    amplitude: np.ndarray,
                    theta: np.ndarray) -> np.ndarray:
    """
    Per-frame color modulation — port of piperecord11_LEF.m line 187.

    MATLAB formula (updated version with 0.0035 scale):
        maxWhite = max(flip(u).*(0.0035*cDisplay9AMP(:,sample)'));
        cc = C - flip(u)*0.01 + flip(u)*(0.0035*amp)/maxWhite;
    """
    flip_u = theta[::-1]

    # Additive brightness from amplitude (0.0035 scale, up from 0.001)
    brightness = flip_u * 0.0035 * amplitude
    max_white = np.max(brightness)

    if max_white > 0:
        additive = (brightness / max_white)[:, np.newaxis]
    else:
        additive = np.zeros((len(amplitude), 1), dtype=np.float32)

    # Darken term
    darken = flip_u[:, np.newaxis] * 0.01

    # Base ambient + amplitude boost
    ambient = base_colors * 0.60
    amp_boost = additive * (base_colors * 1.2 + 0.3)
    modulated = ambient - darken * 0.1 + amp_boost
    return np.clip(modulated, 0, 1).astype(np.float32)
