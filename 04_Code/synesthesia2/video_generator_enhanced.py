"""
SYNESTHESIA 3.0 ENHANCED - Temporal Video Generator
===================================================
Complete pipeline for spectacular audio-to-video transformation:
- Uses the enhanced temporal renderer with brighter visuals
- Optimized for Full HD (1920x1080) showcase videos
- Better FFmpeg encoding settings for higher quality
- Enhanced progress reporting and error handling

This generator creates showcase-quality videos with:
- Brilliant, vivid colors and effects
- Smooth 30fps animations 
- Multi-layer glow and bloom
- Dynamic beat responses
- Rich backgrounds
"""

import numpy as np
import os
import subprocess
import tempfile
import shutil
from dataclasses import dataclass
from typing import Optional, Callable, List
from pathlib import Path
import json
import time

from audio_analyzer import AudioAnalyzer, AudioAnalysisConfig, AnalysisResult
from temporal_analyzer import TemporalAudioAnalyzer, TemporalConfig, TemporalFeatures
from temporal_renderer_enhanced import EnhancedTemporalSpiralRenderer, EnhancedTemporalRenderConfig


@dataclass
class EnhancedVideoConfig:
    """Configuration for enhanced showcase video generation."""
    # Output settings - optimized for showcase quality
    output_width: int = 1920
    output_height: int = 1080
    frame_rate: int = 30
    video_codec: str = "libx264"
    video_preset: str = "slow"  # Better quality
    video_crf: int = 18  # Higher quality (lower CRF)
    video_profile: str = "high"
    video_level: str = "4.1"
    audio_codec: str = "aac"
    audio_bitrate: str = "320k"
    
    # Enhanced visual settings
    enable_hdr_tone_mapping: bool = True
    color_saturation: float = 1.4
    color_brightness: float = 1.3
    contrast_boost: float = 1.5
    gamma_correction: float = 0.7
    
    # Enhanced temporal features
    enable_melody_trail: bool = True
    enable_rhythm_pulse: bool = True
    enable_harmonic_aura: bool = True
    enable_rich_background: bool = True
    background_type: str = "gradient_particle"
    
    # Processing settings
    temp_dir: Optional[str] = None
    keep_frames: bool = False
    ffmpeg_path: str = "/opt/homebrew/bin/ffmpeg"  # macOS Homebrew path
    
    # Quality settings
    png_compression: int = 6  # 0-9, 6 is good balance
    png_optimize: bool = True


class EnhancedVideoGenerator:
    """
    SYNESTHESIA 3.0 ENHANCED - Spectacular video generation pipeline.
    
    Creates showcase-quality visualizations with:
    - Enhanced 2D spiral renderer with brilliant colors
    - Multi-layer glow and bloom effects
    - Dynamic beat response and wave propagation
    - Rich gradient/particle backgrounds
    - Full HD resolution at 30fps
    - Optimized encoding for highest quality
    """
    
    def __init__(self, config: Optional[EnhancedVideoConfig] = None):
        self.config = config or EnhancedVideoConfig()
        
        # Verify FFmpeg
        if not os.path.exists(self.config.ffmpeg_path):
            print(f"Warning: FFmpeg not found at {self.config.ffmpeg_path}")
            self.config.ffmpeg_path = "ffmpeg"  # Try system PATH
        
        # Audio analysis configs
        self.audio_config = AudioAnalysisConfig(frame_rate=self.config.frame_rate)
        self.temporal_config = TemporalConfig(frame_rate=self.config.frame_rate)
        
        # Enhanced render config
        self.render_config = EnhancedTemporalRenderConfig(
            frame_width=self.config.output_width,
            frame_height=self.config.output_height,
            color_saturation=self.config.color_saturation,
            color_brightness=self.config.color_brightness,
            contrast_boost=self.config.contrast_boost,
            gamma_correction=self.config.gamma_correction,
            hdr_tone_mapping=self.config.enable_hdr_tone_mapping,
            enable_melody_trail=self.config.enable_melody_trail,
            enable_rhythm_pulse=self.config.enable_rhythm_pulse,
            enable_harmonic_aura=self.config.enable_harmonic_aura,
            enable_rich_background=self.config.enable_rich_background,
            background_type=self.config.background_type,
        )
        
        # Initialize analyzers
        self.frame_analyzer = AudioAnalyzer(self.audio_config)
        self.temporal_analyzer = TemporalAudioAnalyzer(self.temporal_config)
        
        # Initialize enhanced renderer
        self.renderer = EnhancedTemporalSpiralRenderer(self.render_config, self.config.frame_rate)
        
        print("🎨 SYNESTHESIA 3.0 ENHANCED - Video Generator Initialized")
        print(f"   Resolution: {self.config.output_width}x{self.config.output_height} @ {self.config.frame_rate}fps")
        print(f"   Features: Enhanced colors, multi-layer glow, rich backgrounds")
    
    def generate(self,
                 audio_path: str,
                 output_path: str,
                 start_time: float = 0,
                 duration: Optional[float] = None,
                 progress_callback: Optional[Callable[[int, int, str], None]] = None) -> str:
        """
        Generate an enhanced SYNESTHESIA 3.0 visualization video.
        
        Args:
            audio_path: Path to input audio file
            output_path: Path for output video file
            start_time: Start time in audio (seconds)
            duration: Duration to process (None = entire file)
            progress_callback: Optional callback(current_frame, total_frames, stage)
            
        Returns:
            Path to generated video
        """
        start_time_total = time.time()
        
        # Create temp directory
        temp_dir = self.config.temp_dir or tempfile.mkdtemp(prefix="synesthesia3_enhanced_")
        frames_dir = os.path.join(temp_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)
        
        print(f"\n🎵 Processing: {os.path.basename(audio_path)}")
        print(f"🎬 Output: {output_path}")
        print(f"📁 Temp: {temp_dir}")
        
        try:
            # Stage 1: Frame-level audio analysis
            print(f"\n📊 Stage 1: Frame-level analysis...")
            if progress_callback:
                progress_callback(0, 100, "Analyzing frame-level audio...")
            
            frame_analysis = self.frame_analyzer.analyze(
                audio_path,
                start_time=start_time,
                duration=duration
            )
            
            total_frames = frame_analysis.total_frames
            duration_actual = frame_analysis.duration_seconds
            
            print(f"   ✅ Analyzed {total_frames} frames ({duration_actual:.2f}s)")
            
            # Stage 2: Temporal analysis (melody, rhythm, harmony, atmosphere)
            print(f"\n🎼 Stage 2: Temporal analysis (melody, rhythm, harmony)...")
            if progress_callback:
                progress_callback(0, 100, "Analyzing temporal features...")
            
            temporal_features = self.temporal_analyzer.analyze(
                audio_path,
                start_time=start_time,
                duration=duration
            )
            
            # Report detected features
            if temporal_features.tempo:
                print(f"   🥁 Detected tempo: {temporal_features.tempo:.1f} BPM")
            if temporal_features.chord_labels and len(temporal_features.chord_labels) > 0:
                unique_chords = list(set(temporal_features.chord_labels[:10]))
                print(f"   🎵 Detected chords: {', '.join(unique_chords[:5])}...")
            if temporal_features.beat_frames is not None:
                num_beats = len(temporal_features.beat_frames)
                print(f"   ♩ Detected beats: {num_beats}")
            
            # Stage 3: Pre-compute beat and chord timelines
            print(f"\n⚡ Stage 3: Building timelines...")
            if progress_callback:
                progress_callback(0, 100, "Building temporal timelines...")
            
            beat_frame_set = set(temporal_features.beat_frames) if temporal_features.beat_frames is not None else set()
            downbeat_frame_set = set(temporal_features.downbeat_frames) if temporal_features.downbeat_frames is not None else set()
            chord_timeline = self._build_chord_timeline(temporal_features, total_frames)
            
            print(f"   ✅ Built timelines: {len(beat_frame_set)} beats, {len(chord_timeline)} chord changes")
            
            # Stage 4: Enhanced frame rendering
            print(f"\n🎨 Stage 4: Rendering {total_frames} enhanced frames...")
            if progress_callback:
                progress_callback(0, total_frames, "Rendering enhanced visualization...")
            
            render_start = time.time()
            frames_per_second = 0
            
            for frame_idx in range(total_frames):
                # Get frame-level amplitude
                amplitude = frame_analysis.amplitude_data[:, frame_idx]
                
                # Get temporal features for this frame
                pitch_hz = 0.0
                pitch_confidence = 0.0
                if temporal_features.pitch_contour is not None and frame_idx < len(temporal_features.pitch_contour):
                    pitch_hz = temporal_features.pitch_contour[frame_idx]
                    if temporal_features.pitch_confidence is not None:
                        pitch_confidence = temporal_features.pitch_confidence[frame_idx]
                
                # Beat detection
                is_beat = frame_idx in beat_frame_set
                is_downbeat = frame_idx in downbeat_frame_set
                beat_strength = 0.0
                if is_beat and temporal_features.beat_strength is not None:
                    if frame_idx < len(temporal_features.beat_strength):
                        beat_strength = temporal_features.beat_strength[frame_idx]
                
                # Chord
                chord_label = chord_timeline.get(frame_idx, "N")
                
                # Energy, tension, brightness
                energy = 0.5
                tension = 0.3
                brightness = 0.5
                
                if temporal_features.energy_curve is not None and frame_idx < len(temporal_features.energy_curve):
                    energy = float(temporal_features.energy_curve[frame_idx])
                    if temporal_features.energy_curve.max() > 0:
                        energy = energy / temporal_features.energy_curve.max()
                
                if temporal_features.tension_curve is not None and frame_idx < len(temporal_features.tension_curve):
                    tension = float(temporal_features.tension_curve[frame_idx])
                
                if temporal_features.spectral_centroid is not None and frame_idx < len(temporal_features.spectral_centroid):
                    centroid = temporal_features.spectral_centroid[frame_idx]
                    brightness = min(1.0, centroid / 4000)
                
                # Update enhanced renderer with temporal features
                self.renderer.update_temporal_features(
                    pitch_hz=float(pitch_hz) if pitch_hz else 0,
                    pitch_confidence=float(pitch_confidence) if pitch_confidence else 0,
                    is_beat=is_beat,
                    is_downbeat=is_downbeat,
                    beat_strength=float(beat_strength),
                    chord_label=chord_label,
                    energy=energy,
                    tension=tension,
                    brightness=brightness
                )
                
                # Render enhanced frame
                frame_path = os.path.join(frames_dir, f"frame_{frame_idx:06d}.png")
                self.renderer.save_frame(
                    amplitude_data=amplitude,
                    output_path=frame_path,
                    frame_idx=frame_idx,
                    frequencies=frame_analysis.frequencies
                )
                
                # Progress reporting with ETA
                if frame_idx % 30 == 0:  # Every second
                    elapsed = time.time() - render_start
                    if frame_idx > 0:
                        frames_per_second = frame_idx / elapsed
                        eta_seconds = (total_frames - frame_idx) / frames_per_second
                        eta_str = f" (ETA: {eta_seconds:.0f}s)"
                    else:
                        eta_str = ""
                    
                    print(f"   🖼️  Frame {frame_idx}/{total_frames} ({frame_idx/total_frames*100:.1f}%){eta_str}")
                    
                    if progress_callback:
                        progress_callback(frame_idx, total_frames, "Rendering enhanced visualization...")
            
            render_time = time.time() - render_start
            print(f"   ✅ Rendered {total_frames} frames in {render_time:.1f}s ({frames_per_second:.1f} fps)")
            
            # Stage 5: Enhanced video encoding
            print(f"\n🎬 Stage 5: Encoding enhanced video...")
            if progress_callback:
                progress_callback(total_frames, total_frames, "Encoding high-quality video...")
            
            encode_start = time.time()
            self._encode_enhanced_video(
                frames_dir=frames_dir,
                audio_path=audio_path,
                output_path=output_path,
                start_time=start_time,
                duration=duration_actual
            )
            encode_time = time.time() - encode_start
            
            # Final statistics
            total_time = time.time() - start_time_total
            file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            
            print(f"\n🎉 ENHANCED VIDEO COMPLETE!")
            print(f"   📁 Output: {output_path}")
            print(f"   📏 Size: {file_size_mb:.1f} MB")
            print(f"   ⏱️  Total time: {total_time:.1f}s")
            print(f"   🎨 Render: {render_time:.1f}s ({frames_per_second:.1f} fps)")
            print(f"   🎬 Encode: {encode_time:.1f}s")
            print(f"   🎵 Features: Enhanced colors, glow effects, rich backgrounds")
            
            # Save enhanced metadata
            self._save_enhanced_metadata(output_path, audio_path, frame_analysis, temporal_features,
                                       render_time, encode_time, total_time)
            
            return output_path
            
        except Exception as e:
            print(f"\n❌ Error during video generation: {e}")
            raise
        finally:
            if not self.config.keep_frames:
                print(f"🧹 Cleaning up temp files...")
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _build_chord_timeline(self, temporal_features: TemporalFeatures,
                             total_frames: int) -> dict:
        """Build frame-to-chord mapping."""
        timeline = {}
        
        if temporal_features.chord_frames is None or len(temporal_features.chord_labels) == 0:
            return timeline
        
        chord_frames = temporal_features.chord_frames
        chord_labels = temporal_features.chord_labels
        
        current_chord_idx = 0
        for frame_idx in range(total_frames):
            # Check if we've passed to next chord
            while (current_chord_idx < len(chord_frames) - 1 and
                   frame_idx >= chord_frames[current_chord_idx + 1]):
                current_chord_idx += 1
            
            if current_chord_idx < len(chord_labels):
                timeline[frame_idx] = chord_labels[current_chord_idx]
        
        return timeline
    
    def _encode_enhanced_video(self, frames_dir: str, audio_path: str, output_path: str,
                              start_time: float, duration: float):
        """Encode frames to video with enhanced quality settings."""
        
        # Enhanced FFmpeg command for showcase quality
        cmd = [
            self.config.ffmpeg_path, "-y",
            "-framerate", str(self.config.frame_rate),
            "-i", os.path.join(frames_dir, "frame_%06d.png"),
            "-ss", str(start_time),
            "-t", str(duration),
            "-i", audio_path,
            "-c:v", self.config.video_codec,
            "-preset", self.config.video_preset,
            "-crf", str(self.config.video_crf),
            "-profile:v", self.config.video_profile,
            "-level:v", self.config.video_level,
            "-c:a", self.config.audio_codec,
            "-b:a", self.config.audio_bitrate,
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",  # Better streaming
            "-shortest",
            output_path
        ]
        
        print(f"   🔧 FFmpeg command: {' '.join(cmd[:8])}...")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)  # 10 min timeout
            
            if result.returncode != 0:
                print(f"❌ FFmpeg error: {result.stderr}")
                raise RuntimeError(f"FFmpeg encoding failed: {result.stderr}")
            else:
                print(f"   ✅ Video encoded successfully")
                
        except subprocess.TimeoutExpired:
            raise RuntimeError("FFmpeg encoding timed out (>10 minutes)")
    
    def _save_enhanced_metadata(self, video_path: str, audio_path: str,
                               frame_analysis: AnalysisResult, temporal_features: TemporalFeatures,
                               render_time: float, encode_time: float, total_time: float):
        """Save enhanced generation metadata."""
        metadata = {
            "generator": "SYNESTHESIA 3.0 ENHANCED",
            "version": "3.0-enhanced",
            "audio_source": os.path.basename(audio_path),
            "duration_seconds": frame_analysis.duration_seconds,
            "total_frames": frame_analysis.total_frames,
            "resolution": f"{self.config.output_width}x{self.config.output_height}",
            "frame_rate": self.config.frame_rate,
            "enhancements": {
                "enhanced_colors": True,
                "multi_layer_glow": True,
                "rich_background": self.config.enable_rich_background,
                "background_type": self.config.background_type,
                "hdr_tone_mapping": self.config.enable_hdr_tone_mapping,
                "gamma_correction": self.config.gamma_correction,
                "color_saturation": self.config.color_saturation,
                "color_brightness": self.config.color_brightness,
                "contrast_boost": self.config.contrast_boost,
            },
            "temporal_features": {
                "melody_trail": self.config.enable_melody_trail,
                "rhythm_pulse": self.config.enable_rhythm_pulse,
                "harmonic_aura": self.config.enable_harmonic_aura,
                "rich_background": self.config.enable_rich_background,
            },
            "detected_features": {
                "tempo": float(temporal_features.tempo) if temporal_features.tempo else None,
                "num_beats": len(temporal_features.beat_frames) if temporal_features.beat_frames else 0,
                "num_chords": len(set(temporal_features.chord_labels)) if temporal_features.chord_labels else 0,
                "sample_chords": temporal_features.chord_labels[:10] if temporal_features.chord_labels else [],
            },
            "performance": {
                "render_time_seconds": render_time,
                "encode_time_seconds": encode_time,
                "total_time_seconds": total_time,
                "frames_per_second": frame_analysis.total_frames / render_time if render_time > 0 else 0,
            },
            "encoding": {
                "video_codec": self.config.video_codec,
                "video_preset": self.config.video_preset,
                "video_crf": self.config.video_crf,
                "audio_codec": self.config.audio_codec,
                "audio_bitrate": self.config.audio_bitrate,
            },
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        metadata_path = video_path.rsplit(".", 1)[0] + "_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        print(f"   📄 Metadata saved: {os.path.basename(metadata_path)}")


def main():
    """Command-line interface for enhanced video generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="SYNESTHESIA 3.0 ENHANCED - Temporal Video Generator")
    parser.add_argument("audio_file", help="Path to audio file")
    parser.add_argument("--output", "-o", default="synth3_enhanced_output.mp4", help="Output video path")
    parser.add_argument("--start", "-s", type=float, default=0, help="Start time (seconds)")
    parser.add_argument("--duration", "-d", type=float, help="Duration (seconds)")
    
    # Visual settings
    parser.add_argument("--no-melody", action="store_true", help="Disable melody trail")
    parser.add_argument("--no-rhythm", action="store_true", help="Disable rhythm pulse")
    parser.add_argument("--no-harmony", action="store_true", help="Disable harmonic aura")
    parser.add_argument("--no-background", action="store_true", help="Disable rich background")
    parser.add_argument("--background-type", choices=["gradient", "particle", "gradient_particle"], 
                        default="gradient_particle", help="Background type")
    
    # Quality settings
    parser.add_argument("--resolution", choices=["720p", "1080p"], default="1080p", help="Output resolution")
    parser.add_argument("--fps", type=int, default=30, help="Frame rate")
    parser.add_argument("--quality", choices=["high", "ultra"], default="high", help="Encoding quality")
    
    # Processing
    parser.add_argument("--keep-frames", action="store_true", help="Keep rendered frames")
    parser.add_argument("--ffmpeg-path", default="/opt/homebrew/bin/ffmpeg", help="Path to FFmpeg")
    
    args = parser.parse_args()
    
    # Configuration
    if args.resolution == "720p":
        width, height = 1280, 720
    else:
        width, height = 1920, 1080
    
    if args.quality == "ultra":
        crf, preset = 15, "veryslow"
    else:
        crf, preset = 18, "slow"
    
    config = EnhancedVideoConfig(
        output_width=width,
        output_height=height,
        frame_rate=args.fps,
        video_crf=crf,
        video_preset=preset,
        enable_melody_trail=not args.no_melody,
        enable_rhythm_pulse=not args.no_rhythm,
        enable_harmonic_aura=not args.no_harmony,
        enable_rich_background=not args.no_background,
        background_type=args.background_type,
        keep_frames=args.keep_frames,
        ffmpeg_path=args.ffmpeg_path,
    )
    
    # Generate enhanced video
    generator = EnhancedVideoGenerator(config)
    
    try:
        output_file = generator.generate(
            audio_path=args.audio_file,
            output_path=args.output,
            start_time=args.start,
            duration=args.duration,
            progress_callback=lambda current, total, stage: print(f"Progress: {current}/{total} - {stage}")
        )
        
        print(f"\n🎉 SUCCESS: Enhanced video generated at {output_file}")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Generation cancelled by user")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())