"""
SYNESTHESIA - Harmonic Connection Renderer
==========================================
Renders dynamic connection lines between harmonically related notes on the spiral.

Consonant intervals (octaves, fifths, thirds) produce bright, thick lines
and attract notes toward each other. Dissonant intervals repel notes apart.

Based on the harmonic_forces_poc.py proof of concept by Niv Dvir.
"""

import numpy as np
from PIL import ImageDraw
from dataclasses import dataclass
from typing import List, Tuple, Optional


# Consonance scores for intervals (semitones -> strength 0-1)
# Based on frequency ratios - simpler ratios = more consonant
INTERVAL_CONSONANCE = {
    0: 1.0,    # Unison (1:1) - maximum
    12: 0.95,  # Octave (2:1) - very strong
    7: 0.8,    # Perfect Fifth (3:2) - strong
    5: 0.75,   # Perfect Fourth (4:3) - strong
    4: 0.6,    # Major Third (5:4) - moderate
    3: 0.55,   # Minor Third (6:5) - moderate
    9: 0.5,    # Major Sixth (5:3) - moderate
    8: 0.45,   # Minor Sixth (8:5) - mild
    2: 0.3,    # Major Second (9:8) - tension
    10: 0.3,   # Minor Seventh - tension
    11: 0.2,   # Major Seventh - high tension
    1: 0.1,    # Minor Second - maximum tension
    6: 0.15,   # Tritone - unstable
}

# Consonance threshold that separates attraction from repulsion
CONSONANCE_NEUTRAL = 0.4


def get_consonance(semitone_diff: int) -> float:
    """Get consonance score for an interval (0-1, higher = more consonant)."""
    interval = abs(semitone_diff) % 12
    return INTERVAL_CONSONANCE.get(interval, 0.3)


def freq_to_midi(freq: float) -> float:
    """Convert frequency to MIDI note number."""
    if freq <= 0:
        return 0
    return 69 + 12 * np.log2(freq / 440.0)


@dataclass
class ActiveNote:
    """A detected active note with its position on the spiral."""
    freq: float
    amplitude: float
    x: float
    y: float
    color: Tuple[int, int, int]
    bin_index: int


@dataclass
class HarmonicConnection:
    """A connection between two harmonically related notes."""
    note1: ActiveNote
    note2: ActiveNote
    consonance: float


class HarmonicConnectionRenderer:
    """
    Renders harmonic connections between active notes on the spiral.

    Detects prominent notes (amplitude peaks), computes their harmonic
    relationships, and draws connection lines whose brightness and
    thickness reflect the strength of the harmonic bond. Consonant notes
    are subtly displaced toward each other; dissonant notes repel.
    """

    def __init__(self,
                 connection_threshold: float = 0.5,
                 max_connections: int = 25,
                 min_amplitude: float = 0.15,
                 peak_distance: int = 8,
                 max_active_notes: int = 20,
                 line_color: Tuple[int, int, int] = (100, 180, 255),
                 line_max_width: int = 3,
                 glow_enabled: bool = True,
                 displacement_enabled: bool = True,
                 displacement_strength: float = 3.0):
        self.connection_threshold = connection_threshold
        self.max_connections = max_connections
        self.min_amplitude = min_amplitude
        self.peak_distance = peak_distance
        self.max_active_notes = max_active_notes
        self.line_color = line_color
        self.line_max_width = line_max_width
        self.glow_enabled = glow_enabled
        self.displacement_enabled = displacement_enabled
        self.displacement_strength = displacement_strength

    def find_active_notes(self,
                          amp_normalized: np.ndarray,
                          frequencies: np.ndarray,
                          x_coords: np.ndarray,
                          y_coords: np.ndarray,
                          colors) -> List[ActiveNote]:
        """
        Find prominent notes by detecting peaks in the amplitude spectrum.

        Args:
            amp_normalized: Normalized amplitude data [num_bins], values 0-1
            frequencies: Frequency values for each bin [num_bins]
            x_coords: X pixel positions for each bin [num_bins]
            y_coords: Y pixel positions for each bin [num_bins]
            colors: RGB color per bin - ndarray [num_bins, 3] or list of tuples

        Returns:
            List of ActiveNote instances sorted by amplitude (strongest first)
        """
        n = len(amp_normalized)
        if n < 3:
            return []

        # Simple peak detection: local maxima above threshold
        peaks = []
        for i in range(1, n - 1):
            if (amp_normalized[i] >= self.min_amplitude and
                    amp_normalized[i] > amp_normalized[i - 1] and
                    amp_normalized[i] > amp_normalized[i + 1]):
                peaks.append(i)

        if not peaks:
            return []

        # Filter by minimum distance (keep the louder peak when too close)
        filtered = [peaks[0]]
        for p in peaks[1:]:
            if p - filtered[-1] >= self.peak_distance:
                filtered.append(p)
            elif amp_normalized[p] > amp_normalized[filtered[-1]]:
                filtered[-1] = p

        # Sort by amplitude descending, take top N
        filtered.sort(key=lambda i: amp_normalized[i], reverse=True)
        filtered = filtered[:self.max_active_notes]

        notes = []
        for idx in filtered:
            if isinstance(colors, np.ndarray):
                c = tuple(int(v) for v in colors[idx])
            elif isinstance(colors, list):
                c = tuple(int(v) for v in colors[idx])
            else:
                c = (255, 255, 255)

            notes.append(ActiveNote(
                freq=float(frequencies[idx]),
                amplitude=float(amp_normalized[idx]),
                x=float(x_coords[idx]),
                y=float(y_coords[idx]),
                color=c,
                bin_index=int(idx)
            ))

        return notes

    def compute_connections(self, notes: List[ActiveNote]) -> List[HarmonicConnection]:
        """
        Compute harmonic connections between all pairs of active notes.

        Returns connections sorted by consonance (strongest first),
        limited to max_connections.
        """
        connections = []

        for i, n1 in enumerate(notes):
            for j, n2 in enumerate(notes):
                if j <= i:
                    continue

                midi_diff = freq_to_midi(n1.freq) - freq_to_midi(n2.freq)
                # Skip near-unison (same note)
                if abs(midi_diff) < 0.5:
                    continue

                consonance = get_consonance(int(round(midi_diff)))

                if consonance >= self.connection_threshold:
                    # Weight by both notes' amplitudes
                    weight = consonance * np.sqrt(n1.amplitude * n2.amplitude)
                    connections.append(HarmonicConnection(n1, n2, weight))

        connections.sort(key=lambda c: c.consonance, reverse=True)
        return connections[:self.max_connections]

    def compute_displacements(self, notes: List[ActiveNote]) -> dict:
        """
        Compute subtle position displacements from harmonic forces.

        Consonant notes attract (displaced toward each other).
        Dissonant notes repel (displaced away from each other).

        Returns:
            Dict mapping bin_index -> (dx, dy) displacement in pixels
        """
        displacements = {n.bin_index: np.array([0.0, 0.0]) for n in notes}

        for i, n1 in enumerate(notes):
            for j, n2 in enumerate(notes):
                if j <= i:
                    continue

                midi_diff = freq_to_midi(n1.freq) - freq_to_midi(n2.freq)
                if abs(midi_diff) < 0.5:
                    continue

                consonance = get_consonance(int(round(midi_diff)))

                dx = n2.x - n1.x
                dy = n2.y - n1.y
                dist = max(1.0, np.sqrt(dx * dx + dy * dy))
                nx, ny = dx / dist, dy / dist

                # Consonant (> NEUTRAL) -> attract, dissonant (< NEUTRAL) -> repel
                force = (consonance - CONSONANCE_NEUTRAL) * self.displacement_strength
                force *= np.sqrt(n1.amplitude * n2.amplitude)

                displacements[n1.bin_index] += np.array([nx * force, ny * force])
                displacements[n2.bin_index] -= np.array([nx * force, ny * force])

        # Clamp total displacement per note
        max_disp = self.displacement_strength * 2
        for idx in displacements:
            d = displacements[idx]
            mag = np.sqrt(d[0] ** 2 + d[1] ** 2)
            if mag > max_disp:
                displacements[idx] = d * (max_disp / mag)

        return displacements

    def render(self,
               draw: ImageDraw.Draw,
               amp_normalized: np.ndarray,
               frequencies: np.ndarray,
               x_coords: np.ndarray,
               y_coords: np.ndarray,
               colors) -> Tuple[np.ndarray, np.ndarray]:
        """
        Full render pipeline: find notes, compute connections, draw lines,
        and return displaced coordinates.

        Call this from a spiral renderer's render_frame method BEFORE
        drawing the spiral circles. Connection lines are drawn first so
        that the note circles appear on top.

        Args:
            draw: PIL ImageDraw instance
            amp_normalized: Normalized amplitudes (0-1) per frequency bin
            frequencies: Frequency array (Hz) per bin
            x_coords: X pixel coordinates per bin
            y_coords: Y pixel coordinates per bin
            colors: Color per bin (ndarray [N,3] or list of tuples)

        Returns:
            (x_displaced, y_displaced) coordinate arrays with harmonic
            displacements applied. Use these for drawing circles.
        """
        x_out = x_coords.astype(float).copy()
        y_out = y_coords.astype(float).copy()

        notes = self.find_active_notes(
            amp_normalized, frequencies, x_coords, y_coords, colors)

        if len(notes) < 2:
            return x_out, y_out

        connections = self.compute_connections(notes)

        # Apply harmonic force displacements
        if self.displacement_enabled:
            displacements = self.compute_displacements(notes)
            for idx, disp in displacements.items():
                x_out[idx] += disp[0]
                y_out[idx] += disp[1]

            # Update note positions so connection lines match displaced dots
            note_map = {n.bin_index: n for n in notes}
            for idx, disp in displacements.items():
                if idx in note_map:
                    note_map[idx].x += disp[0]
                    note_map[idx].y += disp[1]

        # Draw connections (before circles so circles render on top)
        if connections:
            self._draw_connections(draw, connections)

        return x_out, y_out

    def _draw_connections(self, draw: ImageDraw.Draw,
                          connections: List[HarmonicConnection]):
        """Draw connection lines with brightness/thickness based on consonance."""
        br, bg, bb = self.line_color

        for conn in connections:
            c = conn.consonance
            width = max(1, int(c * self.line_max_width))

            # Blend base color with the two notes' colors
            r1, g1, b1 = conn.note1.color
            r2, g2, b2 = conn.note2.color

            brightness = 0.3 + 0.7 * c
            r = int(min(255, (br * 0.5 + (r1 + r2) * 0.25) * brightness))
            g = int(min(255, (bg * 0.5 + (g1 + g2) * 0.25) * brightness))
            b = int(min(255, (bb * 0.5 + (b1 + b2) * 0.25) * brightness))

            x1, y1 = int(conn.note1.x), int(conn.note1.y)
            x2, y2 = int(conn.note2.x), int(conn.note2.y)

            # Glow layer (wider, dimmer)
            if self.glow_enabled and width > 1:
                glow = (max(0, r // 3), max(0, g // 3), max(0, b // 3))
                draw.line([(x1, y1), (x2, y2)], fill=glow, width=width + 2)

            # Main line
            draw.line([(x1, y1), (x2, y2)], fill=(r, g, b), width=width)
