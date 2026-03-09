---
paths:
  - "04_Code/synesthesia2/*.py"
  - "04_Code/synesthesia2/research/**"
---

# Visualization Pipeline

## Versions

| Version | File | Description |
|---------|------|-------------|
| 3.0 "Enhanced" | generate_enhanced.py | Circles with glow, white-hot cores |
| 3.5 "Radial Seismograph" | generate_hybrid_trails.py | Trails expand outward |
| 3.5-sharp | — | Crisp trails (order=0, high fade_rate) |
| 3.5-sharper | — | Maximum sharpness (low accumulation_strength) |
| Harmonic Forces (NEW) | harmonic_connections.py | Physics-based consonance/dissonance lines |

## Rendering Parameters

| Parameter | Effect |
|-----------|--------|
| `order=0` | Nearest-neighbor = sharp edges |
| `order=1` | Bilinear = soft/blurry |
| `fade_rate` | Higher = faster decay = sharper trails |
| `accumulation_strength` | Lower = less blending = crisper |

## Research-Validated Values (from VISUALIZATION_LAWS.md)

- Trail length: 10 frames (decay: 0.70)
- Color mapping: Rainbow with mel-scale normalization, saturation 0.95
- Harmony blend time: 4.0 seconds
- Rhythm intensity: 0.50
- Atmosphere window: 60 seconds
- Spiral: 3.5 turns, logarithmic frequency mapping

## Environment

```bash
cd /Users/guydvir/Project/04_Code/synesthesia2
source .venv/bin/activate   # Python 3.14
```

## Harmonic Forces (Experimental)

- `harmonic_forces_poc.py` — POC: spring simulation, consonant intervals attract, dissonant repel
- `harmonic_connections.py` — Production: dynamic connection lines between harmonically related notes
- Output: `harmonic_forces_animated.gif`
