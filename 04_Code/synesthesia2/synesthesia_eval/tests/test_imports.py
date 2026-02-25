"""Test that all required packages can be imported."""
import pytest


def test_torch():
    import torch
    assert torch.__version__ >= "2.0"


def test_torchvision():
    import torchvision


def test_torchaudio():
    import torchaudio


def test_pytorchvideo():
    import pytorchvideo


def test_timm():
    import timm


def test_transformers():
    import transformers


def test_librosa():
    import librosa


@pytest.mark.xfail(
    reason="madmom incompatible with Python 3.10+ (collections.MutableSequence removed)"
)
def test_madmom():
    import madmom


def test_scipy():
    import scipy


def test_sklearn():
    import sklearn


def test_opencv():
    import cv2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
