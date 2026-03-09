"""
SYNESTHESIA - Harmonic Forces POC
=================================

Proof of concept for adding harmonic relationships visualization to the spiral.

Key Ideas:
1. Notes that are harmonically related (octaves, fifths, thirds) attract each other
2. Dissonant intervals create repulsion/tension visually
3. Lines connect harmonically related notes
4. Chords form visible geometric shapes

Physics:
- Attraction force proportional to harmonic consonance
- Spring-like connections between related notes
- Emergent organic movement from force simulation

Author: Niv Dvir
Date: February 2026
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.collections import LineCollection
from dataclasses import dataclass
from typing import List, Tuple, Optional
import colorsys


# =============================================================================
# HARMONIC RELATIONSHIPS
# =============================================================================

# Consonance scores for intervals (semitones -> attraction strength)
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
    1: 0.1,    # Minor Second - maximum tension (repulsion)
    6: 0.15,   # Tritone - unstable
}


def get_consonance(semitone_diff: int) -> float:
    """Get consonance score for an interval (0-1, higher = more consonant)."""
    # Normalize to within octave
    interval = abs(semitone_diff) % 12
    return INTERVAL_CONSONANCE.get(interval, 0.3)


def freq_to_midi(freq: float) -> float:
    """Convert frequency to MIDI note number."""
    if freq <= 0:
        return 0
    return 69 + 12 * np.log2(freq / 440.0)


def midi_to_freq(midi: float) -> float:
    """Convert MIDI note number to frequency."""
    return 440.0 * (2 ** ((midi - 69) / 12))


# =============================================================================
# SPIRAL MAPPING (from existing synesthesia)
# =============================================================================

@dataclass
class SpiralConfig:
    """Configuration for the cochlear spiral."""
    turns: float = 2.5
    inner_radius: float = 0.1
    outer_radius: float = 0.9
    freq_min: float = 20.0      # Hz
    freq_max: float = 8000.0    # Hz


def freq_to_spiral_position(freq: float, config: SpiralConfig) -> Tuple[float, float]:
    """Map frequency to x,y position on spiral."""
    if freq < config.freq_min or freq > config.freq_max:
        return (0, 0)
    
    # Logarithmic mapping (matches human perception)
    t = np.log(freq / config.freq_min) / np.log(config.freq_max / config.freq_min)
    
    # Spiral equation
    angle = t * config.turns * 2 * np.pi
    radius = config.inner_radius + t * (config.outer_radius - config.inner_radius)
    
    x = radius * np.cos(angle)
    y = radius * np.sin(angle)
    
    return (x, y)


# =============================================================================
# FORCE SIMULATION
# =============================================================================

@dataclass
class Note:
    """A note in the visualization."""
    freq: float
    amplitude: float
    x: float
    y: float
    vx: float = 0.0  # velocity for physics
    vy: float = 0.0
    target_x: float = 0.0  # spiral position
    target_y: float = 0.0
    color: Tuple[float, float, float] = (1, 1, 1)
    

class HarmonicForceSimulation:
    """
    Physics simulation for harmonic relationships.
    
    Notes attract/repel based on their harmonic relationship.
    Creates organic, musical movement.
    """
    
    def __init__(self, config: SpiralConfig = None):
        self.config = config or SpiralConfig()
        self.notes: List[Note] = []
        
        # Physics parameters
        self.spring_strength = 0.1      # Pull toward spiral position
        self.harmonic_strength = 0.02   # Attraction between harmonics
        self.damping = 0.85             # Velocity decay
        self.repulsion_distance = 0.05  # Minimum distance between notes
        
        # Visualization
        self.show_connections = True
        self.connection_threshold = 0.5  # Minimum consonance to show line
        
    def add_note(self, freq: float, amplitude: float = 1.0):
        """Add a note to the simulation."""
        target_x, target_y = freq_to_spiral_position(freq, self.config)
        
        # Color based on frequency (hue mapping)
        t = np.log(freq / self.config.freq_min) / np.log(self.config.freq_max / self.config.freq_min)
        hue = t * 0.75  # Red to violet
        rgb = colorsys.hsv_to_rgb(hue, 0.9, 0.9)
        
        note = Note(
            freq=freq,
            amplitude=amplitude,
            x=target_x + np.random.uniform(-0.02, 0.02),  # Small random offset
            y=target_y + np.random.uniform(-0.02, 0.02),
            target_x=target_x,
            target_y=target_y,
            color=rgb
        )
        self.notes.append(note)
        return note
    
    def clear(self):
        """Remove all notes."""
        self.notes = []
        
    def step(self, dt: float = 1.0):
        """Advance simulation by one time step."""
        
        for i, note in enumerate(self.notes):
            # Force 1: Spring force toward spiral position
            dx = note.target_x - note.x
            dy = note.target_y - note.y
            note.vx += dx * self.spring_strength
            note.vy += dy * self.spring_strength
            
            # Force 2: Harmonic attraction/repulsion with other notes
            for j, other in enumerate(self.notes):
                if i == j:
                    continue
                    
                # Calculate harmonic relationship
                midi_diff = freq_to_midi(note.freq) - freq_to_midi(other.freq)
                consonance = get_consonance(int(round(midi_diff)))
                
                # Direction vector
                dx = other.x - note.x
                dy = other.y - note.y
                dist = np.sqrt(dx*dx + dy*dy) + 0.001  # Avoid division by zero
                
                # Normalize
                dx /= dist
                dy /= dist
                
                # Consonant = attract, Dissonant = repel
                # Map consonance 0-1 to force -1 to 1
                force = (consonance - 0.3) * self.harmonic_strength
                
                # Apply force (inverse square for attraction, stronger at close range for repulsion)
                if consonance > 0.5:
                    # Attraction
                    strength = force / (dist + 0.1)
                else:
                    # Repulsion (stronger at close range)
                    strength = force / (dist * dist + 0.01)
                
                note.vx += dx * strength * other.amplitude
                note.vy += dy * strength * other.amplitude
            
            # Apply damping
            note.vx *= self.damping
            note.vy *= self.damping
            
            # Update position
            note.x += note.vx * dt
            note.y += note.vy * dt
    
    def get_harmonic_connections(self) -> List[Tuple[Note, Note, float]]:
        """Get pairs of notes that should be connected, with their consonance."""
        connections = []
        
        for i, note1 in enumerate(self.notes):
            for j, note2 in enumerate(self.notes):
                if j <= i:
                    continue
                    
                midi_diff = freq_to_midi(note1.freq) - freq_to_midi(note2.freq)
                consonance = get_consonance(int(round(midi_diff)))
                
                if consonance >= self.connection_threshold:
                    connections.append((note1, note2, consonance))
                    
        return connections


# =============================================================================
# DEMONSTRATION
# =============================================================================

def demo_chord_visualization():
    """
    Demo: Visualize different chords and see their harmonic shapes.
    """
    
    sim = HarmonicForceSimulation()
    
    # Create figure
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('Harmonic Forces: Chord Shapes', fontsize=16, fontweight='bold')
    
    # Different chords to visualize
    chords = {
        'C Major (C-E-G)': [261.63, 329.63, 392.00],  # C4, E4, G4
        'C Minor (C-Eb-G)': [261.63, 311.13, 392.00],  # C4, Eb4, G4
        'C7 (C-E-G-Bb)': [261.63, 329.63, 392.00, 466.16],  # Dominant 7th
        'Cmaj7 (C-E-G-B)': [261.63, 329.63, 392.00, 493.88],  # Major 7th
        'Diminished (C-Eb-Gb)': [261.63, 311.13, 369.99],  # Unstable
        'Tritone (C-F#)': [261.63, 369.99],  # Maximum tension
    }
    
    for ax, (name, freqs) in zip(axes.flat, chords.items()):
        sim.clear()
        
        # Add notes
        for freq in freqs:
            sim.add_note(freq, amplitude=1.0)
        
        # Run simulation to equilibrium
        for _ in range(100):
            sim.step()
        
        # Draw spiral background (faint)
        theta = np.linspace(0, sim.config.turns * 2 * np.pi, 500)
        t_vals = theta / (sim.config.turns * 2 * np.pi)
        r = sim.config.inner_radius + t_vals * (sim.config.outer_radius - sim.config.inner_radius)
        spiral_x = r * np.cos(theta)
        spiral_y = r * np.sin(theta)
        ax.plot(spiral_x, spiral_y, 'gray', alpha=0.2, linewidth=1)
        
        # Draw connections
        connections = sim.get_harmonic_connections()
        for note1, note2, consonance in connections:
            alpha = consonance * 0.8
            color = (0.3, 0.7, 1.0, alpha)  # Blue with varying opacity
            ax.plot([note1.x, note2.x], [note1.y, note2.y], 
                   color=color, linewidth=2 * consonance)
        
        # Draw notes
        for note in sim.notes:
            size = 200 * note.amplitude
            ax.scatter(note.x, note.y, s=size, c=[note.color], 
                      edgecolors='white', linewidths=2, zorder=10)
            
            # Label with frequency
            ax.annotate(f'{note.freq:.0f}Hz', (note.x, note.y), 
                       textcoords="offset points", xytext=(0, 15),
                       ha='center', fontsize=8, color='white')
        
        ax.set_title(name, fontsize=12, fontweight='bold', color='white')
        ax.set_xlim(-1.1, 1.1)
        ax.set_ylim(-1.1, 1.1)
        ax.set_aspect('equal')
        ax.set_facecolor('#1a1a2e')
        ax.axis('off')
    
    fig.patch.set_facecolor('#0f0f1a')
    plt.tight_layout()
    plt.savefig('/Users/guydvir/Project/04_Code/synesthesia2/harmonic_forces_demo.png', 
                dpi=150, facecolor='#0f0f1a', bbox_inches='tight')
    plt.close()
    print("✅ Saved: harmonic_forces_demo.png")


def demo_animated():
    """
    Animated demo: Watch notes find their harmonic equilibrium.
    """
    
    sim = HarmonicForceSimulation()
    sim.harmonic_strength = 0.03
    
    # Setup figure
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_facecolor('#1a1a2e')
    fig.patch.set_facecolor('#0f0f1a')
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Draw spiral
    theta = np.linspace(0, sim.config.turns * 2 * np.pi, 500)
    t_vals = theta / (sim.config.turns * 2 * np.pi)
    r = sim.config.inner_radius + t_vals * (sim.config.outer_radius - sim.config.inner_radius)
    spiral_x = r * np.cos(theta)
    spiral_y = r * np.sin(theta)
    ax.plot(spiral_x, spiral_y, 'gray', alpha=0.3, linewidth=1)
    
    # Add C major chord + some overtones
    frequencies = [
        261.63,  # C4
        329.63,  # E4
        392.00,  # G4
        523.25,  # C5 (octave)
        659.25,  # E5
    ]
    
    for freq in frequencies:
        sim.add_note(freq, amplitude=1.0)
    
    # Animation elements
    scatter = ax.scatter([], [], s=[], c=[], edgecolors='white', linewidths=2)
    lines = []
    
    title = ax.set_title('Harmonic Forces: C Major + Octave\nWatch notes attract...', 
                         fontsize=14, color='white', fontweight='bold')
    
    def init():
        return scatter,
    
    def update(frame):
        # Physics step
        sim.step()
        
        # Update scatter
        xs = [n.x for n in sim.notes]
        ys = [n.y for n in sim.notes]
        sizes = [300 * n.amplitude for n in sim.notes]
        colors = [n.color for n in sim.notes]
        
        scatter.set_offsets(np.c_[xs, ys])
        scatter.set_sizes(sizes)
        scatter.set_facecolors(colors)
        
        # Update lines (remove old, add new)
        for line in lines:
            line.remove()
        lines.clear()
        
        connections = sim.get_harmonic_connections()
        for note1, note2, consonance in connections:
            line, = ax.plot([note1.x, note2.x], [note1.y, note2.y],
                          color=(0.3, 0.8, 1.0, consonance * 0.7),
                          linewidth=2 * consonance)
            lines.append(line)
        
        return scatter, *lines
    
    anim = FuncAnimation(fig, update, init_func=init, 
                        frames=200, interval=50, blit=False)
    
    # Save animation
    print("Creating animation... (this may take a moment)")
    anim.save('/Users/guydvir/Project/04_Code/synesthesia2/harmonic_forces_animated.gif',
              writer='pillow', fps=20, dpi=100)
    print("✅ Saved: harmonic_forces_animated.gif")
    
    plt.close()


if __name__ == '__main__':
    print("=" * 60)
    print("SYNESTHESIA - Harmonic Forces POC")
    print("=" * 60)
    print()
    print("This POC demonstrates:")
    print("1. Harmonic attraction between consonant notes")
    print("2. Visual connections showing harmonic relationships")
    print("3. Emergent geometric shapes from chords")
    print()
    
    # Run static demo first
    print("Generating chord comparison image...")
    demo_chord_visualization()
    
    # Then animated
    print()
    print("Generating animated demo...")
    demo_animated()
    
    print()
    print("Done! Check the output files:")
    print("  - harmonic_forces_demo.png (chord shapes)")
    print("  - harmonic_forces_animated.gif (animation)")
