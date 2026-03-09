"""
SYNESTHESIA 2.0 - AI-Enhanced Psychoacoustic Visualization

A complete pipeline for transforming audio into stunning cochlear spiral
visualizations with deep learning classification overlays.

Modules:
- audio_analyzer: FFT analysis and feature extraction
- spiral_renderer_2d: Fast 2D spiral renderer (PIL-based)
- video_generator: Complete video generation pipeline
- ai_overlay: AI classification and attention visualization

Usage:
    from synesthesia2 import VideoGenerator, VideoConfig

    config = VideoConfig(output_width=1920, output_height=1080)
    generator = VideoGenerator(video_config=config)
    generator.generate("input.wav", "output.mp4")
"""

from .audio_analyzer import AudioAnalyzer, AudioAnalysisConfig, AnalysisResult
from .spiral_renderer_2d import FastSpiralRenderer, Render2DConfig
from .video_generator import VideoGenerator, VideoConfig

__version__ = "2.0.0"
__author__ = "Niv Dvir"
__all__ = [
    "AudioAnalyzer",
    "AudioAnalysisConfig",
    "AnalysisResult",
    "FastSpiralRenderer",
    "Render2DConfig",
    "VideoGenerator",
    "VideoConfig",
]
