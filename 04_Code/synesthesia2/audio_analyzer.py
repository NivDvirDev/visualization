"""
SYNESTHESIA 2.0 - Audio Analysis Module
Port of record15_LEF.m to Python

Extracts frequency, amplitude, and phase information from audio files
for cochlear spiral visualization.
"""

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.interpolate import interp1d
import warnings
from dataclasses import dataclass
from typing import Tuple, Optional, List
import os

try:
    import cupy as cp
    HAS_GPU = True
except ImportError:
    HAS_GPU = False
    cp = np  # Fallback to numpy


@dataclass
class AudioAnalysisConfig:
    """Configuration for audio analysis matching MATLAB parameters."""
    frame_rate: int = 60  # Frames per second for video
    num_frequency_bins: int = 381  # Number of frequency bins (matching MATLAB)
    freq_min: float = 20.0  # Minimum frequency (Hz)
    freq_max: float = 8000.0  # Maximum frequency (Hz)
    inner_circle_points: int = 60  # Points around the tube circumference
    window_samples: int = 12000  # Extra samples for windowing (m in MATLAB)
    use_gpu: bool = True  # Use GPU acceleration if available


@dataclass
class AnalysisResult:
    """Container for audio analysis results."""
    amplitude_data: np.ndarray  # cDisplay3AMP equivalent [FreqIndex, TotalFrameNumber]
    phase_data: np.ndarray  # cDisplay3PHAZ equivalent [TotalFrameNumber, FreqIndex, InerCircel]
    frequencies: np.ndarray  # Frequency bins
    sample_rate: int
    total_frames: int
    duration_seconds: float


def iso226_loudness(phon: float, freq: float) -> float:
    """
    ISO 226 equal-loudness contour calculation.
    Returns the SPL offset for perceptual normalization.

    Port of iso226.m from MATLAB.
    """
    # ISO 226 reference frequencies and parameters
    f_ref = np.array([20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630,
                      800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000, 12500])

    alpha_f = np.array([0.532, 0.506, 0.480, 0.455, 0.432, 0.409, 0.387, 0.367, 0.349, 0.330,
                        0.315, 0.301, 0.288, 0.276, 0.267, 0.259, 0.253, 0.250, 0.246, 0.244,
                        0.243, 0.243, 0.243, 0.242, 0.242, 0.245, 0.254, 0.271, 0.301])

    L_U = np.array([-31.6, -27.2, -23.0, -19.1, -15.9, -13.0, -10.3, -8.1, -6.2, -4.5,
                    -3.1, -2.0, -1.1, -0.4, 0.0, 0.3, 0.5, 0.0, -2.7, -4.1,
                    -1.0, 1.7, 2.5, 1.2, -2.1, -7.1, -11.2, -10.7, -3.1])

    T_f = np.array([78.5, 68.7, 59.5, 51.1, 44.0, 37.5, 31.5, 26.5, 22.1, 17.9,
                    14.4, 11.4, 8.6, 6.2, 4.4, 3.0, 2.2, 2.4, 3.5, 1.7,
                    -1.3, -4.2, -6.0, -5.4, -1.5, 6.0, 12.6, 13.9, 12.3])

    # Interpolate for the given frequency
    if freq < f_ref[0]:
        freq = f_ref[0]
    elif freq > f_ref[-1]:
        freq = f_ref[-1]

    alpha_interp = interp1d(f_ref, alpha_f, kind='linear', fill_value='extrapolate')
    L_U_interp = interp1d(f_ref, L_U, kind='linear', fill_value='extrapolate')
    T_f_interp = interp1d(f_ref, T_f, kind='linear', fill_value='extrapolate')

    alpha = float(alpha_interp(freq))
    L_U_val = float(L_U_interp(freq))
    T_f_val = float(T_f_interp(freq))

    # Calculate SPL from phon
    A_f = 0.00447 * (10 ** (0.025 * phon) - 1.15) + \
          (0.4 * 10 ** (((T_f_val + L_U_val) / 10) - 9)) ** alpha

    if A_f > 0:
        L_p = ((10 / alpha) * np.log10(A_f)) - L_U_val + 94
    else:
        L_p = T_f_val

    return L_p / 20  # Return normalized value as in MATLAB


def create_frequency_bins(config: AudioAnalysisConfig) -> np.ndarray:
    """
    Create logarithmically-spaced frequency bins matching the cochlear spiral.
    """
    # Logarithmic spacing to match human hearing (cochlear tonotopy)
    frequencies = np.logspace(
        np.log10(config.freq_min),
        np.log10(config.freq_max),
        config.num_frequency_bins
    )
    return frequencies


def create_analysis_kernel(frequencies: np.ndarray,
                           sample_rate: int,
                           window_samples: int,
                           config: AudioAnalysisConfig) -> np.ndarray:
    """
    Create the complex exponential kernel for frequency analysis.
    Port of the GPU_preh calculation from MATLAB.
    """
    dt = 1.0 / sample_rate
    num_freqs = len(frequencies)

    # Create phase array (matching MATLAB: array=(-pi):(2*pi/m):(pi))
    phase_array = np.linspace(-np.pi, np.pi, window_samples + 1)

    # Create frequency-phase matrix (preh in MATLAB)
    # preh = ((array) * (preh)).' where preh(i) = Freq(i)
    freq_matrix = np.outer(frequencies, phase_array)

    # Complex exponential: exp(complex((pi)/2, preh))
    kernel = np.exp(1j * (np.pi / 2 + freq_matrix))

    return kernel


def create_amplitude_mask(frequencies: np.ndarray,
                          sample_rate: int,
                          samples_per_frame: int,
                          window_samples: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create the amplitude mask for frequency-dependent windowing.
    Port of CreateMask function from MATLAB.
    """
    dt = 1.0 / sample_rate
    num_freqs = len(frequencies)
    width = window_samples + 1

    mask = np.ones((num_freqs, width))
    amp_dynamic = np.zeros(num_freqs)

    middle = width // 2

    # Frequency-dependent effective window (matching MATLAB logic)
    # m_effective = flip(normalize(Freq.^2, 'range', [(1/Freq(end))/dt, W/2]))
    freq_squared = frequencies ** 2
    m_effective = np.interp(
        freq_squared,
        [freq_squared.min(), freq_squared.max()],
        [(1 / frequencies[-1]) / dt, width / 2]
    )
    m_effective = m_effective[::-1]  # flip

    for l in range(num_freqs):
        border = samples_per_frame / 2  # As in MATLAB: border = m_real/2
        amp_dynamic[l] = (100 / width) * (2 * border)

        for w in range(width):
            pixel = (width / 2) - w
            if pixel != 0:
                gain = border / pixel
                if abs(gain) < 1:
                    mask[l, w] = abs(gain)
                else:
                    mask[l, w] = 2 - (1 / abs(gain))
            else:
                mask[l, w] = 1.0

    return mask, amp_dynamic


class AudioAnalyzer:
    """
    Main audio analysis class for SYNESTHESIA visualization.
    Extracts amplitude and phase data for each frame of the video.
    """

    def __init__(self, config: Optional[AudioAnalysisConfig] = None):
        self.config = config or AudioAnalysisConfig()
        self.frequencies = create_frequency_bins(self.config)
        self._kernel = None
        self._mask = None
        self._amp_dynamic = None
        self._iso226_weights = None

    def _initialize_for_sample_rate(self, sample_rate: int):
        """Initialize analysis kernels for a specific sample rate."""
        samples_per_frame = int(sample_rate / self.config.frame_rate)

        # Create analysis kernel
        self._kernel = create_analysis_kernel(
            self.frequencies,
            sample_rate,
            self.config.window_samples,
            self.config
        )

        # Create amplitude mask
        self._mask, self._amp_dynamic = create_amplitude_mask(
            self.frequencies,
            sample_rate,
            samples_per_frame,
            self.config.window_samples
        )

        # Apply mask to kernel (as in MATLAB: GPU_preh = gather(GPU_preh).*mask)
        self._kernel = self._kernel * self._mask.astype(complex)

        # Calculate ISO 226 weights for perceptual normalization
        self._iso226_weights = np.array([
            iso226_loudness(40, freq) for freq in self.frequencies
        ])
        self._max_iso226 = 1 + np.max(self._iso226_weights)

        # Normalize amplitude dynamics
        self._amp_normalized = self._amp_dynamic * 22  # Scaling factor from MATLAB

    def analyze(self, audio_path: str,
                start_time: float = 0,
                duration: Optional[float] = None,
                progress_callback=None) -> AnalysisResult:
        """
        Analyze an audio file and extract visualization data.

        Args:
            audio_path: Path to audio file (WAV, MP3, etc.)
            start_time: Start time in seconds
            duration: Duration to analyze (None = entire file)
            progress_callback: Optional callback(frame, total_frames)

        Returns:
            AnalysisResult containing amplitude and phase data
        """
        # Load audio
        sample_rate, audio_data = self._load_audio(audio_path)

        # Convert to mono if stereo
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)

        # Normalize to [-1, 1]
        audio_data = audio_data.astype(np.float32)
        if audio_data.max() > 1.0:
            audio_data = audio_data / 32768.0  # Assuming 16-bit audio

        # Calculate parameters
        dt = 1.0 / sample_rate
        samples_per_frame = int(sample_rate / self.config.frame_rate)
        m = self.config.window_samples

        # Apply time range
        start_sample = int(start_time * sample_rate)
        if duration:
            end_sample = min(start_sample + int(duration * sample_rate), len(audio_data))
        else:
            end_sample = len(audio_data)

        audio_data = audio_data[start_sample:end_sample]
        total_samples = len(audio_data)
        total_frames = int((total_samples - 2 * m) / samples_per_frame)

        # Initialize kernels
        self._initialize_for_sample_rate(sample_rate)

        # Prepare output arrays
        amplitude_data = np.zeros((self.config.num_frequency_bins, total_frames))
        phase_data = np.zeros((total_frames, self.config.num_frequency_bins,
                               self.config.inner_circle_points))

        # Use GPU if available
        if self.config.use_gpu and HAS_GPU:
            kernel_gpu = cp.asarray(self._kernel)
            amp_gpu = cp.asarray(self._amp_normalized)
        else:
            kernel_gpu = self._kernel
            amp_gpu = self._amp_normalized

        # Process each frame (matching MATLAB loop structure)
        print(f"Analyzing {total_frames} frames...")

        for frame_idx in range(total_frames):
            record = int(0.5 * m) + frame_idx * samples_per_frame

            # Extract window around current position
            window_start = record - int(0.5 * m)
            window_end = record + int(0.5 * m) + 1

            if window_end > len(audio_data):
                break

            window = audio_data[window_start:window_end]

            # Ensure correct length
            if len(window) < self.config.window_samples + 1:
                window = np.pad(window, (0, self.config.window_samples + 1 - len(window)))

            # Complex multiplication with kernel (GPU_g = GPU_preh * GPU_g in MATLAB)
            if self.config.use_gpu and HAS_GPU:
                window_gpu = cp.asarray(window.astype(complex))
                result = cp.abs(kernel_gpu @ window_gpu)
                spiral = cp.asnumpy(result) * self._amp_normalized
            else:
                result = np.abs(kernel_gpu @ window.astype(complex))
                spiral = result * self._amp_normalized

            amplitude_data[:, frame_idx] = spiral

            # Extract phase/waveform data for significant amplitudes
            for freq_idx in range(self.config.num_frequency_bins):
                if spiral[freq_idx] > 4:  # Threshold from MATLAB
                    T = 1.0 / self.frequencies[freq_idx]
                    T_samples = int(T * sample_rate)

                    if T_samples > 0 and T_samples < len(window):
                        # Extract cycles and average (matching MATLAB printcycle)
                        num_cycles = len(window) // T_samples
                        if num_cycles > 0:
                            waveform = window[:num_cycles * T_samples].reshape(num_cycles, T_samples)
                            mean_wave = np.mean(waveform, axis=0)

                            # Interpolate to inner_circle_points
                            x_old = np.linspace(0, 1, len(mean_wave))
                            x_new = np.linspace(0, 1, self.config.inner_circle_points)
                            interp_func = interp1d(x_old, mean_wave, kind='linear', fill_value='extrapolate')
                            phase_data[frame_idx, freq_idx, :] = interp_func(x_new)

            if progress_callback and frame_idx % 100 == 0:
                progress_callback(frame_idx, total_frames)

        print(f"Analysis complete: {total_frames} frames")

        return AnalysisResult(
            amplitude_data=amplitude_data,
            phase_data=phase_data,
            frequencies=self.frequencies,
            sample_rate=sample_rate,
            total_frames=total_frames,
            duration_seconds=total_frames / self.config.frame_rate
        )

    def _load_audio(self, audio_path: str) -> Tuple[int, np.ndarray]:
        """Load audio from various formats."""
        ext = os.path.splitext(audio_path)[1].lower()

        if ext == '.wav':
            sample_rate, audio_data = wavfile.read(audio_path)
            return sample_rate, audio_data
        else:
            # Try librosa for other formats
            try:
                import librosa
                audio_data, sample_rate = librosa.load(audio_path, sr=None, mono=False)
                if len(audio_data.shape) > 1:
                    audio_data = audio_data.T  # librosa returns (channels, samples)
                return sample_rate, audio_data
            except ImportError:
                raise ImportError(f"librosa required for {ext} files. Install: pip install librosa")


def analyze_audio_file(audio_path: str,
                       output_path: Optional[str] = None,
                       config: Optional[AudioAnalysisConfig] = None) -> AnalysisResult:
    """
    Convenience function to analyze an audio file.

    Args:
        audio_path: Path to audio file
        output_path: Optional path to save analysis results (.npz)
        config: Optional configuration

    Returns:
        AnalysisResult
    """
    analyzer = AudioAnalyzer(config)
    result = analyzer.analyze(audio_path)

    if output_path:
        np.savez_compressed(
            output_path,
            amplitude_data=result.amplitude_data,
            phase_data=result.phase_data,
            frequencies=result.frequencies,
            sample_rate=result.sample_rate,
            total_frames=result.total_frames,
            duration_seconds=result.duration_seconds
        )
        print(f"Saved analysis to {output_path}")

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SYNESTHESIA Audio Analyzer")
    parser.add_argument("audio_file", help="Path to audio file")
    parser.add_argument("--output", "-o", help="Output path for analysis data (.npz)")
    parser.add_argument("--frame-rate", type=int, default=60, help="Video frame rate")
    parser.add_argument("--no-gpu", action="store_true", help="Disable GPU acceleration")

    args = parser.parse_args()

    config = AudioAnalysisConfig(
        frame_rate=args.frame_rate,
        use_gpu=not args.no_gpu
    )

    result = analyze_audio_file(args.audio_file, args.output, config)
    print(f"Analyzed {result.duration_seconds:.2f}s of audio")
    print(f"Amplitude data shape: {result.amplitude_data.shape}")
    print(f"Phase data shape: {result.phase_data.shape}")
