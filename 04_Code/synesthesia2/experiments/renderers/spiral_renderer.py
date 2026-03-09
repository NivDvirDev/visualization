"""
SYNESTHESIA 2.0 - 3D Spiral Tube Renderer
Port of piperecord11_LEF.m to Python

Renders the cochlear-inspired 3D spiral tube visualization with:
- Radial wave animation
- HSV color mapping (chromesthesia)
- Dynamic camera motion
- Solfège note labels
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict
import colorsys
import os

# Visualization backends
try:
    import os
    # Enable off-screen rendering for macOS (uses native Cocoa/OpenGL)
    if 'PYVISTA_OFF_SCREEN' not in os.environ:
        os.environ['PYVISTA_OFF_SCREEN'] = 'true'
    import pyvista as pv
    HAS_PYVISTA = True
except ImportError:
    HAS_PYVISTA = False

try:
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


# Golden Ratio - used throughout MATLAB code
PHI = 1.6180339887498948482


@dataclass
class RenderConfig:
    """Configuration for spiral tube rendering."""
    # Resolution
    frame_width: int = 1920
    frame_height: int = 1080
    frame_rate: int = 60

    # Spiral geometry
    num_frequency_bins: int = 381
    inner_circle_points: int = 60
    spiral_turns: float = 7.0  # Number of spiral rotations
    tube_base_radius: float = 0.01
    tube_amplitude_scale: float = 0.0015

    # Wave animation parameters
    wave_speed: float = 700.0  # From MATLAB: speed=700*dFrame
    wave_lambda: float = 4.8701  # From MATLAB
    wave_v0: float = 4.7124  # Initial velocity

    # Camera parameters
    initial_azimuth: float = 270.0
    initial_elevation: float = 30.0
    azimuth_speed: float = 0.3  # degrees per frame
    elevation_min: float = 9.95
    elevation_max: float = 30.95
    elevation_speed: float = 0.05

    # View bounds
    view_bounds: float = 75.0
    z_offset: float = -40.0

    # Colors (chromesthesia mapping)
    background_color: Tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass
class SolfegeNote:
    """Solfège note definition with frequencies across octaves."""
    name: str
    frequencies: List[float]
    color: Tuple[float, float, float] = (1.0, 1.0, 1.0)


# Solfège notes matching MATLAB (7 notes, 11 octaves each)
SOLFEGE_NOTES = [
    SolfegeNote("Do", [4.088, 8.176, 16.352, 32.703, 65.406, 130.813, 261.626, 523.251, 1046.502, 2093.005, 4186.009],
                (0.0, 0.0, 1.0)),  # Blue
    SolfegeNote("Re", [4.5885, 9.177, 18.354, 36.708, 73.416, 146.832, 293.665, 587.33, 1174.659, 2349.318, 4698.636],
                (1.0, 0.4, 0.7)),  # Pink
    SolfegeNote("Mi", [5.150, 10.301, 20.602, 41.203, 82.407, 164.814, 329.628, 659.255, 1318.51, 2637.02, 5274.041],
                (1.0, 0.0, 0.0)),  # Red
    SolfegeNote("Fa", [5.456, 10.913, 21.827, 43.654, 87.307, 174.614, 349.228, 698.456, 1396.913, 2793.826, 5587.652],
                (1.0, 0.5, 0.0)),  # Orange
    SolfegeNote("Sol", [6.125, 12.25, 24.5, 48.999, 97.999, 195.998, 391.995, 783.991, 1567.982, 3135.963, 6271.927],
                (1.0, 1.0, 0.0)),  # Yellow
    SolfegeNote("La", [6.875, 13.75, 27.5, 55, 110, 220, 440, 880, 1760, 3520, 7040],
                (0.0, 1.0, 0.0)),  # Green
    SolfegeNote("Si", [7.717, 15.434, 30.868, 61.735, 123.471, 246.942, 493.883, 987.767, 1975.533, 3951.066, 7902.133],
                (0.0, 1.0, 1.0)),  # Cyan
]


def create_chromesthesia_colormap(num_bins: int) -> np.ndarray:
    """
    Create the chromesthesia-inspired colormap.
    Maps frequency to color using HSV with frequency-dependent hue.
    """
    colors = np.zeros((num_bins, 3))

    for i in range(num_bins):
        # Map frequency index to hue (0-1)
        # Lower frequencies = warmer colors (red/orange)
        # Higher frequencies = cooler colors (blue/cyan)
        t = i / (num_bins - 1)

        # HSV mapping: hue rotates through spectrum
        hue = (1 - t) * 0.0 + t * 0.7  # Red to cyan
        saturation = 0.9
        value = 0.9

        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        colors[i] = [r, g, b]

    return colors


def create_spiral_coordinates(num_frequency_bins: int,
                              spiral_turns: float = 7.0) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create the base spiral (theta) coordinates.
    This is a Fermat-like spiral matching the cochlear structure.
    """
    # theta ranges from 0 to spiral_turns * 2*pi
    theta = np.linspace(0, spiral_turns * 2 * np.pi, num_frequency_bins)

    # Radius increases with sqrt for Fermat spiral
    # Modified to create the tube shape seen in MATLAB
    radius = theta.copy()  # Linear increase with angle

    return theta, radius


class SpiralTubeRenderer:
    """
    Renders the 3D spiral tube visualization frame by frame.
    """

    def __init__(self, config: Optional[RenderConfig] = None):
        self.config = config or RenderConfig()

        # Initialize spiral geometry
        self.theta, self.base_radius = create_spiral_coordinates(
            self.config.num_frequency_bins,
            self.config.spiral_turns
        )

        # Create color map
        self.colormap = create_chromesthesia_colormap(self.config.num_frequency_bins)

        # Inner circle angle (R in MATLAB)
        self.inner_angles = np.linspace(-np.pi, np.pi, self.config.inner_circle_points)

        # Create meshgrid for tube surface
        self.u, self.v = np.meshgrid(self.theta, self.inner_angles)

        # Camera state
        self.azimuth = self.config.initial_azimuth
        self.elevation = self.config.initial_elevation
        self.elevation_direction = -1  # Start moving down

        # Wave animation state
        self.time = 0.0
        self.phase = 0.0

    def compute_tube_mesh(self,
                          amplitude_data: np.ndarray,
                          phase_data: Optional[np.ndarray] = None,
                          frame_idx: int = 0) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute the tube mesh vertices and colors for a single frame.

        Args:
            amplitude_data: [num_frequency_bins] amplitude values for this frame
            phase_data: Optional [num_frequency_bins, inner_circle_points] phase waveform
            frame_idx: Current frame index

        Returns:
            x, y, z, colors: Mesh coordinates and colors
        """
        num_freqs = self.config.num_frequency_bins
        num_points = self.config.inner_circle_points

        # Base tube radius modulated by amplitude
        # tsul in MATLAB: tsul = flip(u) .* (0.0003 * cDisplay9AMP + 0.00288 * phase_data)
        tsul = np.zeros((num_points, num_freqs))

        amp_contribution = self.config.tube_base_radius + \
                           self.config.tube_amplitude_scale * amplitude_data

        for i in range(num_points):
            if phase_data is not None:
                phase_contribution = 0.00288 * np.real(phase_data[:, min(i, phase_data.shape[1] - 1)])
            else:
                phase_contribution = 0

            # Flip and modulate (matching MATLAB: flip(u))
            tsul[i, :] = np.flip(self.u[i, :]) * (0.0003 * amplitude_data + phase_contribution)

        # Calculate draft (integral for smooth tube) - uses Golden Ratio
        draft = self._compute_draft(np.mean(tsul, axis=0))

        # Compute radial wave (PeriodicWave in MATLAB)
        wave = self._compute_radial_wave(frame_idx)

        # Compute X, Y, Z coordinates
        # xy = (theta + Draft + tsul * cos(v))
        # zz = (wave) + tsul * sin(v) + z_offset + Draft * PHI

        xy = self.theta + draft + tsul * np.cos(self.v)

        x = xy * np.cos(self.u + np.pi / 2)
        y = xy * np.sin(self.u + np.pi / 2)
        z = (2 * wave) + tsul * np.sin(self.v) + self.config.z_offset + draft * PHI

        # Compute colors based on amplitude
        colors = self._compute_colors(amplitude_data, tsul)

        return x, y, z, colors

    def _compute_draft(self, mean_radius: np.ndarray) -> np.ndarray:
        """
        Compute the draft (integral) for smooth tube shape.
        Port of draftTsul function from MATLAB.
        """
        num_freqs = len(mean_radius)
        draft = np.zeros(num_freqs)

        for i in range(num_freqs):
            # Find previous position one full rotation back
            prev_idx = self._find_back_360(i)
            draft[i] = (mean_radius[i] / PHI) + draft[prev_idx]

        return draft

    def _find_back_360(self, index: int) -> int:
        """Find the index one full rotation (2*pi) back."""
        target_theta = self.theta[index] - 2 * np.pi
        if target_theta < 0:
            return 0
        distances = np.abs(self.theta - target_theta)
        return int(np.argmin(distances))

    def _compute_radial_wave(self, frame_idx: int) -> np.ndarray:
        """
        Compute the periodic radial wave animation.
        Port of SetRadialWave from MATLAB.
        """
        dt = 1.0 / self.config.frame_rate
        self.time = frame_idx * dt

        # Wave parameters from MATLAB
        T = 100 * dt
        f = 1.0 / T
        omega = 2 * np.pi * f
        k = omega / self.config.wave_v0
        lmda = self.config.wave_lambda

        # Phase advances with time
        self.phase = omega * (self.time * 4) * (-1)

        # Compute wave at each point
        u_min = np.min(self.u)
        u_max = np.max(self.u)
        u_range = (u_max - u_min) / 2

        # PeriodicWave: sin(phase + (u - u_min) * (lambda / u_range))
        wave_arg = self.phase + (self.u - u_min) * (lmda / u_range)
        wave = np.sin(wave_arg)
        wave[wave < 0] = 0  # Only positive half (heaviside-like)

        return wave

    def _compute_colors(self, amplitude_data: np.ndarray, tsul: np.ndarray) -> np.ndarray:
        """
        Compute colors for the mesh based on amplitude.
        """
        num_points, num_freqs = tsul.shape

        # Base colors from colormap
        colors = np.zeros((num_points, num_freqs, 3))
        for i in range(num_points):
            colors[i, :, :] = self.colormap

        # Modulate brightness by amplitude
        # amplitude_data is [num_freqs], need to broadcast properly
        amp_broadcast = amplitude_data.reshape(1, -1)  # [1, num_freqs]
        u_flipped = np.flip(self.u, axis=1)  # [num_points, num_freqs]

        brightness_map = u_flipped * (0.001 * amp_broadcast)
        max_white = np.max(brightness_map)

        if max_white > 0:
            brightness_map = brightness_map / max_white
            # Apply brightness modulation to colors
            for c in range(3):
                colors[:, :, c] = colors[:, :, c] * (0.5 + 0.5 * brightness_map)

        return colors

    def update_camera(self, frame_idx: int, total_frames: int):
        """
        Update camera position for dynamic view.
        Port of SetCameraMotion from MATLAB.
        """
        # Azimuth continuously rotates
        self.azimuth -= self.config.azimuth_speed

        # Elevation oscillates (only in second half of video)
        if frame_idx >= total_frames // 2:
            self.elevation += self.elevation_direction * self.config.elevation_speed * \
                              np.cos(np.pi * self.elevation / 180)

            if self.elevation >= self.config.elevation_max:
                self.elevation_direction = -1
            elif self.elevation <= self.config.elevation_min:
                self.elevation_direction = 1

    def get_solfege_positions(self,
                              frequencies: np.ndarray,
                              x: np.ndarray,
                              y: np.ndarray,
                              z: np.ndarray) -> List[Dict]:
        """
        Get 3D positions for solfège note labels.
        """
        positions = []
        text_row = 15  # Row index for label placement (from MATLAB)

        for note in SOLFEGE_NOTES:
            for octave, freq in enumerate(note.frequencies):
                # Find closest frequency bin
                freq_idx = int(np.argmin(np.abs(frequencies - freq)))

                if freq_idx < x.shape[1]:
                    positions.append({
                        'name': note.name,
                        'frequency': freq,
                        'octave': octave + 1,
                        'x': x[text_row, freq_idx],
                        'y': y[text_row, freq_idx],
                        'z': z[text_row, freq_idx],
                        'color': note.color,
                        'font_size': 8 + octave * 0.5
                    })

        return positions

    def render_frame_matplotlib(self,
                                amplitude_data: np.ndarray,
                                phase_data: Optional[np.ndarray] = None,
                                frame_idx: int = 0,
                                frequencies: Optional[np.ndarray] = None,
                                show_labels: bool = True,
                                save_path: Optional[str] = None) -> np.ndarray:
        """
        Render a single frame using Matplotlib.
        Returns the frame as a numpy array.
        """
        if not HAS_MATPLOTLIB:
            raise ImportError("Matplotlib required for rendering")

        # Compute mesh
        x, y, z, colors = self.compute_tube_mesh(amplitude_data, phase_data, frame_idx)

        # Create figure
        fig = plt.figure(figsize=(self.config.frame_width / 100,
                                  self.config.frame_height / 100),
                         dpi=100)
        ax = fig.add_subplot(111, projection='3d', computed_zorder=False)

        # Set black background
        fig.patch.set_facecolor('black')
        ax.set_facecolor('black')

        # Plot surface
        # Reshape colors for plot_surface
        facecolors = colors.reshape(-1, 3)

        # Use plot_surface with facecolors
        surf = ax.plot_surface(x, y, z,
                               facecolors=colors,
                               shade=True,
                               antialiased=True,
                               rcount=50,
                               ccount=50)

        # Set view
        ax.view_init(elev=self.elevation, azim=self.azimuth)

        # Set bounds
        bounds = self.config.view_bounds
        ax.set_xlim(-bounds, bounds)
        ax.set_ylim(-bounds, bounds)
        ax.set_zlim(-75, 45)

        # Hide axes
        ax.set_axis_off()

        # Add solfège labels
        if show_labels and frequencies is not None:
            positions = self.get_solfege_positions(frequencies, x, y, z)
            for pos in positions:
                ax.text(pos['x'], pos['y'], pos['z'],
                        f"{pos['frequency']:.0f}Hz",
                        color=pos['color'],
                        fontsize=pos['font_size'],
                        fontweight='bold',
                        fontstyle='italic')

        plt.tight_layout(pad=0)

        if save_path:
            plt.savefig(save_path, facecolor='black', edgecolor='none',
                        bbox_inches='tight', pad_inches=0)

        # Convert to numpy array
        fig.canvas.draw()
        # Modern matplotlib uses buffer_rgba instead of tostring_rgb
        buf = fig.canvas.buffer_rgba()
        frame = np.asarray(buf)[:, :, :3]  # Remove alpha channel

        plt.close(fig)

        return frame

    def render_frame_pyvista(self,
                             amplitude_data: np.ndarray,
                             phase_data: Optional[np.ndarray] = None,
                             frame_idx: int = 0,
                             frequencies: Optional[np.ndarray] = None,
                             show_labels: bool = True,
                             save_path: Optional[str] = None) -> np.ndarray:
        """
        Render a single frame using PyVista for high-quality 3D visualization.

        Uses off-screen rendering (native Cocoa/OpenGL on macOS).
        Returns the frame as a numpy array.
        """
        if not HAS_PYVISTA:
            raise ImportError("PyVista required for rendering. Install with: pip install pyvista")

        # Compute mesh
        x, y, z, colors = self.compute_tube_mesh(amplitude_data, phase_data, frame_idx)

        # Create StructuredGrid from mesh coordinates
        # PyVista expects shape (n_points_i, n_points_j, n_points_k, 3) for structured grid
        num_points, num_freqs = x.shape

        # Stack coordinates into grid format
        grid = pv.StructuredGrid(x, y, z)

        # Flatten colors for point data (RGB values)
        colors_flat = colors.reshape(-1, 3)
        # Convert to 0-255 range for PyVista
        colors_uint8 = (colors_flat * 255).astype(np.uint8)
        grid.point_data['colors'] = colors_uint8

        # Create off-screen plotter
        plotter = pv.Plotter(
            off_screen=True,
            window_size=(self.config.frame_width, self.config.frame_height)
        )

        # Set black background
        plotter.set_background('black')

        # Add the mesh with vertex colors
        plotter.add_mesh(
            grid,
            scalars='colors',
            rgb=True,
            smooth_shading=True,
            show_edges=False
        )

        # Set camera position
        # Convert spherical (azimuth, elevation) to Cartesian camera position
        distance = 150.0  # Camera distance from origin
        az_rad = np.radians(self.azimuth)
        el_rad = np.radians(self.elevation)

        cam_x = distance * np.cos(el_rad) * np.cos(az_rad)
        cam_y = distance * np.cos(el_rad) * np.sin(az_rad)
        cam_z = distance * np.sin(el_rad)

        # Focus point (center of spiral)
        focus = (0, 0, self.config.z_offset / 2)

        plotter.camera_position = [
            (cam_x, cam_y, cam_z),  # Camera position
            focus,                   # Focal point
            (0, 0, 1)               # View up vector
        ]

        # Add solfège labels if requested
        if show_labels and frequencies is not None:
            positions = self.get_solfege_positions(frequencies, x, y, z)
            for pos in positions:
                plotter.add_point_labels(
                    [[pos['x'], pos['y'], pos['z']]],
                    [f"{pos['frequency']:.0f}Hz"],
                    font_size=int(pos['font_size'] * 2),
                    text_color=pos['color'],
                    point_size=0,
                    render_points_as_spheres=False,
                    always_visible=True,
                    shape=None
                )

        # Render to image
        if save_path:
            plotter.screenshot(save_path)

        # Get frame as numpy array
        frame = plotter.screenshot(return_img=True)

        plotter.close()

        return frame


def render_test_frame(output_path: str = "test_frame.png", use_pyvista: bool = False):
    """Generate a test frame with synthetic data.

    Args:
        output_path: Path to save the rendered frame
        use_pyvista: If True, use PyVista renderer; otherwise use Matplotlib
    """
    renderer = SpiralTubeRenderer()

    # Create synthetic amplitude data (simulate music)
    num_bins = renderer.config.num_frequency_bins
    t = np.linspace(0, 1, num_bins)

    # Simulate harmonics at different frequencies
    amplitude = np.zeros(num_bins)
    for harmonic in [0.1, 0.25, 0.4, 0.55, 0.7]:
        amplitude += 20 * np.exp(-((t - harmonic) ** 2) / 0.01)

    amplitude += np.random.random(num_bins) * 2  # Add some noise

    # Create frequency array
    frequencies = np.logspace(np.log10(20), np.log10(8000), num_bins)

    # Render with selected backend
    if use_pyvista:
        if not HAS_PYVISTA:
            print("PyVista not available, falling back to Matplotlib")
            use_pyvista = False
        else:
            frame = renderer.render_frame_pyvista(
                amplitude_data=amplitude,
                frame_idx=100,
                frequencies=frequencies,
                show_labels=True,
                save_path=output_path
            )
            print(f"Test frame (PyVista) saved to {output_path}")
            return frame

    # Matplotlib fallback
    frame = renderer.render_frame_matplotlib(
        amplitude_data=amplitude,
        frame_idx=100,
        frequencies=frequencies,
        show_labels=True,
        save_path=output_path
    )

    print(f"Test frame (Matplotlib) saved to {output_path}")
    return frame


if __name__ == "__main__":
    import sys
    use_pyvista = '--pyvista' in sys.argv or '-p' in sys.argv
    output = sys.argv[-1] if len(sys.argv) > 1 and not sys.argv[-1].startswith('-') else "test_frame.png"
    render_test_frame(output, use_pyvista=use_pyvista)
