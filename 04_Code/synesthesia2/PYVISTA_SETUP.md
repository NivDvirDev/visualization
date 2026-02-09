# SYNESTHESIA - PyVista/VTK Local GPU Rendering Setup

## Overview

The `merkabah_pyvista_renderer.py` uses PyVista/VTK for true 3D GPU-accelerated rendering. This produces significantly higher quality output than the software Cairo renderer, with proper lighting, shadows, and hardware anti-aliasing.

## Requirements

You already have these installed and working:
- PyVista 0.46.5
- VTK 9.5.2
- Off-screen rendering: Working

### Additional Dependencies

```bash
pip install numpy scipy pillow librosa
```

If not already installed:
```bash
pip install pyvista vtk
```

## Quick Test

Run a quick test to verify everything works:

```bash
cd /path/to/synesthesia2
python merkabah_pyvista_renderer.py --test
```

This will generate a single test frame at `merkabah_pyvista_test.png`.

## Generate Video

### Basic Usage

```bash
python merkabah_pyvista_renderer.py input_audio.mp3 -o output.mp4
```

### With Duration Limit (for testing)

```bash
python merkabah_pyvista_renderer.py input_audio.mp3 -o output.mp4 --duration 30
```

### Example with Papaoutai

```bash
python merkabah_pyvista_renderer.py "Stromae - Papaoutai.mp3" -o Papaoutai_PYVISTA.mp4 --duration 30
```

## What the Renderer Creates

### 3D Geometry
- **Star Tetrahedron (Merkabah)**: Two interlocking tetrahedra with proper flipped orientation
  - Upper tetrahedron: base at top, apex pointing down (points toward Chayot)
  - Lower tetrahedron: base at bottom, apex pointing up (points toward heavens)
- **Ophanim Wheels**: Nested rotating ring structures with eyes
- **Chayot HaKodesh Planes**: Four elemental living creatures
- **Fire Particles**: Dynamic flame particles around the structure
- **Star Field**: Background stars with depth

### Visual Effects
- Hardware MSAA anti-aliasing
- Proper 3D lighting with ambient, diffuse, and specular components
- Metallic material shaders
- Post-processing bloom (optional)
- Vignette effect

### Audio Reactivity
- Bass frequencies drive tetrahedron rotation speed
- Treble affects inner structure glow
- Beats trigger pulse effects
- Energy (RMS) controls overall brightness
- Pitch modulates color temperature

## Configuration Options

Edit the `PyVistaConfig` in the script to customize:

```python
config = PyVistaConfig(
    frame_width=1920,       # Output resolution
    frame_height=1080,
    background_color=(0.02, 0.02, 0.05),  # Deep space blue

    # Merkabah geometry
    tetra_size=2.0,
    tetra_opacity=0.85,

    # Ophanim wheels
    num_wheels=3,
    wheel_segments=64,      # Smoothness of wheels

    # Chayot planes
    plane_count=4,
    plane_size=1.5,

    # Effects
    num_stars=200,
    fire_particles=50,
)
```

## Troubleshooting

### "No module named 'pyvista'"
```bash
pip install pyvista
```

### "VTK not found"
```bash
pip install vtk
```

### Black or empty output
- Check that off-screen rendering is working: `python -c "import pyvista; print(pyvista.OFF_SCREEN)"`
- Try setting: `pyvista.OFF_SCREEN = True` at the start of the script

### Slow rendering
- Reduce resolution in config
- Reduce `wheel_segments` and `num_stars`
- Use shorter duration for testing

### Memory issues
- The renderer processes frames sequentially to minimize memory usage
- For very long videos, consider rendering in segments

## Output Quality

Expected performance on a modern GPU:
- 720p: ~5-10 fps rendering
- 1080p: ~2-5 fps rendering
- 4K: ~0.5-1 fps rendering

A 30-second video at 30fps (900 frames) at 1080p takes approximately 3-7 minutes depending on GPU.

## Files Structure

```
synesthesia2/
├── merkabah_pyvista_renderer.py   # Main PyVista renderer (run locally)
├── merkabah_hdr_renderer.py       # Software HDR renderer (fallback)
├── merkabah_hdr_gen.py            # Video generation with HDR renderer
├── audio_analyzer.py              # Audio analysis utilities
├── temporal_analyzer.py           # Beat/tempo detection
└── PYVISTA_SETUP.md              # This file
```

## Comparison: PyVista vs Software Renderer

| Feature | PyVista/VTK | Software (Cairo) |
|---------|-------------|------------------|
| True 3D geometry | ✅ | ❌ (2D projection) |
| Hardware anti-aliasing | ✅ MSAA | ❌ (supersampling) |
| GPU acceleration | ✅ | ❌ |
| Proper lighting | ✅ | Simulated |
| Render speed | Fast | Slow |
| Quality | Higher | Good |

## Next Steps

1. Run the test to verify setup
2. Generate a short test video (10-30 seconds)
3. Adjust config parameters to your liking
4. Generate full-length videos

Enjoy your GPU-accelerated Merkabah visualizations!
