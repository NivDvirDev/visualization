"""
Port of MATLAB myjet colormap — per-octave HSV rainbow + amplitude modulation.
From sound8_LEF.m colormap construction.

The MATLAB builds the colormap by concatenating hsv(n) segments per octave,
creating a repeating rainbow that cycles through all hues within each octave.
"""

import numpy as np
import colorsys


def create_myjet_colormap(num_bins: int = 381) -> np.ndarray:
    """
    Create the myjet colormap: repeating HSV rainbow per octave.

    The MATLAB spiral has ~7 octaves across 381 frequency bins.
    Each octave cycles through the full hue spectrum.

    Args:
        num_bins: Number of frequency bins (default: 381)

    Returns:
        [num_bins, 3] RGB float values in [0, 1]
    """
    bins_per_octave = num_bins / 7.0

    colors = np.zeros((num_bins, 3), dtype=np.float32)
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

    The MATLAB formula is ADDITIVE — it pushes colors toward white
    where amplitude is high, rather than darkening via multiplication.

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

    # Uniform ambient: all turns equally visible (matching YouTube look).
    # Active regions get amplitude-driven boost preserving hue saturation.
    ambient = base_colors * 0.55
    # Mix hue-preserving boost with white push for glow effect on peaks
    amp_boost = additive * (base_colors * 1.2 + 0.3)
    modulated = ambient + amp_boost
    return np.clip(modulated, 0, 1).astype(np.float32)
