"""
Port of MATLAB myjet colormap — octave-aligned HSV rainbow.
From sound8_LEF.m colormap construction.

FUNDAMENTAL PRINCIPLE:
  Each 360° spiral revolution = one octave (frequency doubles per turn).
  The 7 musical pitches (Do Re Mi Fa Sol La Si) within each octave
  align radially — the same note at every octave falls on the same
  radial line from center outward. The colormap reinforces this:
  hue is determined by angular position within the turn, so the same
  pitch gets the same color across all octaves.
"""

import numpy as np
import colorsys


def create_myjet_colormap(num_bins: int = 381,
                          theta: np.ndarray = None) -> np.ndarray:
    """
    Create the myjet colormap: HSV rainbow cycling once per octave.

    If theta (spiral angles) is provided, hue is derived from the
    angular position within each 2π revolution. This ensures:
    - Same radial direction = same color across all octaves
    - 7 pitches per octave get 7 distinct hue bands
    - Color pattern repeats every 360°

    Args:
        num_bins: Number of frequency bins
        theta: Spiral angle for each bin (from spiral_freq_data.npz).
               If None, falls back to uniform hue cycling.

    Returns:
        [num_bins, 3] RGB float values in [0, 1]
    """
    colors = np.zeros((num_bins, 3), dtype=np.float32)

    if theta is not None and len(theta) == num_bins:
        # Angular position within each revolution determines hue
        # theta mod 2π gives position within current octave turn
        for i in range(num_bins):
            hue = (theta[i] % (2 * np.pi)) / (2 * np.pi)
            r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            colors[i] = [r, g, b]
    else:
        # Fallback: uniform cycling (less accurate)
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
    Apply amplitude-based brightness modulation to the colormap.

    Faithful port of MATLAB per-frame color computation:
        maxWhite = max(flip(u) .* (0.001 * amp));
        cc = c - flip(u)*0.01 + flip(u)*(0.001*amp) / maxWhite;

    Args:
        base_colors: [num_bins, 3] base colormap RGB in [0, 1]
        amplitude: [num_bins] amplitude values for current frame
        theta: [num_bins] spiral angle values (flip(u) in MATLAB)

    Returns:
        [num_bins, 3] brightness-modulated RGB colors in [0, 1]
    """
    # MATLAB uses flip(u) — reverse theta so low frequencies get larger weight
    flip_u = theta[::-1]

    # Additive brightness from amplitude (MATLAB formula)
    brightness = flip_u * 0.001 * amplitude
    max_white = np.max(brightness)

    if max_white > 0:
        additive = (brightness / max_white)[:, np.newaxis]
    else:
        additive = np.zeros((len(amplitude), 1), dtype=np.float32)

    # Uniform ambient: all turns equally visible.
    # Active regions get amplitude-driven boost preserving hue saturation.
    ambient = base_colors * 0.55
    # Mix hue-preserving boost with white push for glow effect on peaks
    amp_boost = additive * (base_colors * 1.2 + 0.3)
    modulated = ambient + amp_boost
    return np.clip(modulated, 0, 1).astype(np.float32)
