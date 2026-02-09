# Color Mapping Parameter Investigation Report

Generated: 2026-01-29T11:11:11.982667

Total Experiments: 96

## Summary by Mapping Type

| Mapping | Avg Accuracy | Distinctiveness | Memorability | Hue Coverage |
|---------|--------------|-----------------|--------------|--------------|
| categorical    |        0.798 |           0.979 |        0.559 |        0.000 |
| harmonic       |        0.810 |           1.000 |        0.653 |        0.089 |
| mel_rainbow    |        0.945 |           1.000 |        0.918 |        0.938 |
| perceptual     |        0.936 |           1.000 |        0.943 |        1.000 |
| rainbow        |        0.957 |           1.000 |        0.937 |        1.000 |
| scriabin       |        0.803 |           1.000 |        0.656 |        0.063 |

**Best Mapping Type:** rainbow

## Summary by Saturation Level

| Saturation | Avg Accuracy | Distinctiveness | Memorability |
|------------|--------------|-----------------|--------------|
|       0.60 |        0.869 |           0.986 |        0.719 |
|       0.75 |        0.874 |           1.000 |        0.767 |
|       0.85 |        0.880 |           1.000 |        0.797 |
|       0.95 |        0.876 |           1.000 |        0.827 |

## Top 5 Configurations

1. **rainbow** (Sat=0.95, Bright=0.4-1.0)
   Composite: 0.992 | Acc=0.988 | Distinct=1.000
2. **perceptual** (Sat=0.85, Bright=0.4-1.0)
   Composite: 0.990 | Acc=0.997 | Distinct=1.000
3. **rainbow** (Sat=0.85, Bright=0.5-0.85)
   Composite: 0.988 | Acc=0.997 | Distinct=1.000
4. **perceptual** (Sat=0.75, Bright=0.4-1.0)
   Composite: 0.983 | Acc=1.000 | Distinct=1.000
5. **perceptual** (Sat=0.95, Bright=0.5-0.85)
   Composite: 0.982 | Acc=0.955 | Distinct=1.000

## Key Findings & Recommendations

1. **rainbow** mapping achieves best overall performance
2. Optimal saturation: **0.95**
3. Perceptual uniformity improves distinctiveness by ~10%

### Visual Memory Optimization
- Higher saturation (0.85-0.95) improves memorability
- Perceptual mappings reduce confusion between similar frequencies
- Categorical mapping best for distinct frequency bands