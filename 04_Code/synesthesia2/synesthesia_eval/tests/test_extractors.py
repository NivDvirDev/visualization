"""Unit tests for audio and video feature extractors."""

import numpy as np
import pytest
import torch

from synesthesia_eval.extractors import (
    AudioFeatureExtractor,
    AudioFeatures,
    VideoFeatureExtractor,
    VideoFeatures,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_RATE = 22050
DURATION = 2.0  # seconds


def _make_sine_wave(
    freq: float = 440.0, sr: int = SAMPLE_RATE, duration: float = DURATION
) -> np.ndarray:
    """Generate a sine wave for testing."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False, dtype=np.float32)
    return 0.5 * np.sin(2 * np.pi * freq * t)


def _make_video_frames(
    num_frames: int = 16, height: int = 64, width: int = 64, channels: int = 3
) -> np.ndarray:
    """Generate synthetic video frames (T, H, W, C) in [0, 255]."""
    rng = np.random.default_rng(42)
    return rng.integers(0, 256, (num_frames, height, width, channels), dtype=np.uint8)


# ===========================================================================
# Audio Feature Extractor Tests
# ===========================================================================


class TestAudioFeatureExtractor:
    """Tests for AudioFeatureExtractor."""

    @pytest.fixture()
    def extractor(self) -> AudioFeatureExtractor:
        return AudioFeatureExtractor(sample_rate=SAMPLE_RATE)

    @pytest.fixture()
    def sine_wave(self) -> np.ndarray:
        return _make_sine_wave()

    # --- extract_mel_spectrogram ---

    def test_mel_spectrogram_shape(
        self, extractor: AudioFeatureExtractor, sine_wave: np.ndarray
    ) -> None:
        mel = extractor.extract_mel_spectrogram(sine_wave, sr=SAMPLE_RATE)
        assert mel.ndim == 2
        assert mel.shape[0] == extractor.n_mels  # n_mels bands
        assert mel.shape[1] > 0  # time frames

    def test_mel_spectrogram_values(
        self, extractor: AudioFeatureExtractor, sine_wave: np.ndarray
    ) -> None:
        mel = extractor.extract_mel_spectrogram(sine_wave, sr=SAMPLE_RATE)
        assert mel.max() <= 0.0  # log-power relative to max is <= 0 dB
        assert np.isfinite(mel).all()

    # --- extract_rhythm_features ---

    def test_rhythm_features_keys(
        self, extractor: AudioFeatureExtractor, sine_wave: np.ndarray
    ) -> None:
        rhythm = extractor.extract_rhythm_features(sine_wave, sr=SAMPLE_RATE)
        assert "onset_strength" in rhythm
        assert "beat_frames" in rhythm
        assert "tempo" in rhythm

    def test_rhythm_onset_shape(
        self, extractor: AudioFeatureExtractor, sine_wave: np.ndarray
    ) -> None:
        rhythm = extractor.extract_rhythm_features(sine_wave, sr=SAMPLE_RATE)
        assert rhythm["onset_strength"].ndim == 1
        assert len(rhythm["onset_strength"]) > 0

    def test_rhythm_tempo_positive(
        self, extractor: AudioFeatureExtractor, sine_wave: np.ndarray
    ) -> None:
        rhythm = extractor.extract_rhythm_features(sine_wave, sr=SAMPLE_RATE)
        assert isinstance(rhythm["tempo"], float)
        assert rhythm["tempo"] >= 0

    def test_rhythm_beat_frames_array(
        self, extractor: AudioFeatureExtractor, sine_wave: np.ndarray
    ) -> None:
        rhythm = extractor.extract_rhythm_features(sine_wave, sr=SAMPLE_RATE)
        assert isinstance(rhythm["beat_frames"], np.ndarray)

    # --- extract_harmonic_features ---

    def test_harmonic_features_keys(
        self, extractor: AudioFeatureExtractor, sine_wave: np.ndarray
    ) -> None:
        harmonic = extractor.extract_harmonic_features(sine_wave, sr=SAMPLE_RATE)
        assert "mfcc" in harmonic
        assert "chroma" in harmonic

    def test_mfcc_shape(
        self, extractor: AudioFeatureExtractor, sine_wave: np.ndarray
    ) -> None:
        harmonic = extractor.extract_harmonic_features(sine_wave, sr=SAMPLE_RATE)
        assert harmonic["mfcc"].shape[0] == extractor.n_mfcc
        assert harmonic["mfcc"].shape[1] > 0

    def test_chroma_shape(
        self, extractor: AudioFeatureExtractor, sine_wave: np.ndarray
    ) -> None:
        harmonic = extractor.extract_harmonic_features(sine_wave, sr=SAMPLE_RATE)
        assert harmonic["chroma"].shape[0] == 12  # 12 pitch classes
        assert harmonic["chroma"].shape[1] > 0

    # --- extract_all ---

    def test_extract_all_returns_dataclass(
        self, extractor: AudioFeatureExtractor, sine_wave: np.ndarray
    ) -> None:
        features = extractor.extract_all(sine_wave, sr=SAMPLE_RATE)
        assert isinstance(features, AudioFeatures)

    def test_extract_all_fields(
        self, extractor: AudioFeatureExtractor, sine_wave: np.ndarray
    ) -> None:
        features = extractor.extract_all(sine_wave, sr=SAMPLE_RATE)
        assert features.mel_spectrogram.shape[0] == extractor.n_mels
        assert features.mfcc.shape[0] == extractor.n_mfcc
        assert features.chroma.shape[0] == 12
        assert features.onset_strength.ndim == 1
        assert features.tempo >= 0
        assert features.sample_rate == SAMPLE_RATE
        assert abs(features.duration - DURATION) < 0.1

    # --- extract_batch ---

    def test_batch_processing(self, extractor: AudioFeatureExtractor) -> None:
        waves = [_make_sine_wave(freq=f) for f in [220, 440, 880]]
        results = extractor.extract_batch(waves, sr=SAMPLE_RATE)
        assert len(results) == 3
        for r in results:
            assert isinstance(r, AudioFeatures)

    # --- stereo input ---

    def test_stereo_input(self, extractor: AudioFeatureExtractor) -> None:
        mono = _make_sine_wave()
        stereo = np.stack([mono, mono], axis=0)  # (2, samples)
        mel = extractor.extract_mel_spectrogram(stereo, sr=SAMPLE_RATE)
        assert mel.ndim == 2

    # --- error handling ---

    def test_invalid_source_type(self, extractor: AudioFeatureExtractor) -> None:
        with pytest.raises(TypeError):
            extractor.extract_mel_spectrogram(12345)


# ===========================================================================
# Video Feature Extractor Tests
# ===========================================================================


class TestVideoFeatureExtractor:
    """Tests for VideoFeatureExtractor."""

    @pytest.fixture(scope="class")
    def extractor(self) -> VideoFeatureExtractor:
        return VideoFeatureExtractor(pretrained=False, clip_length=8)

    @pytest.fixture()
    def frames_16(self) -> np.ndarray:
        return _make_video_frames(num_frames=16)

    @pytest.fixture()
    def frames_5(self) -> np.ndarray:
        return _make_video_frames(num_frames=5)

    # --- extract_frames ---

    def test_extract_frames_shape(
        self, extractor: VideoFeatureExtractor, frames_16: np.ndarray
    ) -> None:
        feats = extractor.extract_frames(frames_16)
        assert feats.ndim == 2
        assert feats.shape[0] == 16  # one feature per input frame
        assert feats.shape[1] == 2048  # SlowR50 feature dim

    def test_extract_frames_short_video(
        self, extractor: VideoFeatureExtractor, frames_5: np.ndarray
    ) -> None:
        feats = extractor.extract_frames(frames_5)
        assert feats.shape[0] == 5  # trimmed to original frame count

    # --- extract_clip_features ---

    def test_extract_clip_features_shape(
        self, extractor: VideoFeatureExtractor, frames_16: np.ndarray
    ) -> None:
        feats = extractor.extract_clip_features(frames_16)
        assert feats.ndim == 2
        num_clips = 16 // extractor.clip_length
        assert feats.shape[0] == num_clips
        assert feats.shape[1] == 2048

    def test_extract_clip_features_single_clip(
        self, extractor: VideoFeatureExtractor, frames_5: np.ndarray
    ) -> None:
        feats = extractor.extract_clip_features(frames_5)
        assert feats.shape[0] == 1  # padded into one clip

    # --- extract_temporal_features ---

    def test_extract_temporal_features_shape(
        self, extractor: VideoFeatureExtractor, frames_16: np.ndarray
    ) -> None:
        feats = extractor.extract_temporal_features(frames_16)
        assert feats.ndim == 3
        num_clips = 16 // extractor.clip_length
        assert feats.shape[0] == num_clips
        assert feats.shape[2] == 2048  # feature dim

    # --- extract_all ---

    def test_extract_all_returns_dataclass(
        self, extractor: VideoFeatureExtractor, frames_16: np.ndarray
    ) -> None:
        features = extractor.extract_all(frames_16)
        assert isinstance(features, VideoFeatures)

    def test_extract_all_fields(
        self, extractor: VideoFeatureExtractor, frames_16: np.ndarray
    ) -> None:
        features = extractor.extract_all(frames_16)
        assert features.frame_features.shape[0] == 16
        assert features.clip_features.shape[0] == 2
        assert features.temporal_features.shape[0] == 2
        assert features.frame_features.shape[1] == 2048
        assert features.clip_features.shape[1] == 2048

    # --- extract_batch ---

    def test_batch_processing(self, extractor: VideoFeatureExtractor) -> None:
        batch = [_make_video_frames(num_frames=8), _make_video_frames(num_frames=16)]
        results = extractor.extract_batch(batch)
        assert len(results) == 2
        assert isinstance(results[0], VideoFeatures)
        assert isinstance(results[1], VideoFeatures)

    # --- preprocessing ---

    def test_float_input(self, extractor: VideoFeatureExtractor) -> None:
        frames = _make_video_frames(num_frames=8).astype(np.float32) / 255.0
        feats = extractor.extract_frames(frames)
        assert feats.shape[0] == 8

    def test_output_on_cpu(
        self, extractor: VideoFeatureExtractor, frames_16: np.ndarray
    ) -> None:
        feats = extractor.extract_frames(frames_16)
        assert feats.device == torch.device("cpu")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
