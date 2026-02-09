"""
SYNESTHESIA 2.0 - AI-Enhanced Psychoacoustic Visualization

A complete pipeline for transforming audio into stunning 3D cochlear spiral
visualizations with deep learning classification overlays.

Modules:
- audio_analyzer: FFT analysis and feature extraction
- spiral_renderer: 3D spiral tube visualization
- video_generator: Complete video generation pipeline
- ai_overlay: AI classification and attention visualization

Usage:
    from synesthesia2 import VideoGenerator, VideoConfig

    config = VideoConfig(output_width=1920, output_height=1080)
    generator = VideoGenerator(video_config=config)
    generator.generate("input.wav", "output.mp4")
"""

from .audio_analyzer import AudioAnalyzer, AudioAnalysisConfig, AnalysisResult
from .spiral_renderer import SpiralTubeRenderer, RenderConfig
from .video_generator import VideoGenerator, VideoConfig

__version__ = "2.0.0"
__author__ = "Niv Dvir"
__all__ = [
    "AudioAnalyzer",
    "AudioAnalysisConfig",
    "AnalysisResult",
    "SpiralTubeRenderer",
    "RenderConfig",
    "VideoGenerator",
    "VideoConfig"
]
