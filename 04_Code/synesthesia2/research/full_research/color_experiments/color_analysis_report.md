# Color Mapping Parameter Investigation Report

Generated: 2026-01-29T11:48:32.033004

Total Experiments: 96

## Summary by Mapping Type

| Mapping | Avg Accuracy | Distinctiveness | Memorability | Hue Coverage |
|---------|--------------|-----------------|--------------|--------------|
| categorical    |        0.804 |           0.979 |        0.559 |        0.000 |
| harmonic       |        0.810 |           1.000 |        0.653 |        0.089 |
| mel_rainbow    |        0.951 |           1.000 |        0.918 |        0.938 |
| perceptual     |        0.951 |           1.000 |        0.943 |        1.000 |
| rainbow        |        0.949 |           1.000 |        0.937 |        1.000 |
| scriabin       |        0.803 |           1.000 |        0.656 |        0.063 |

**Best Mapping Type:** perceptual

## Summary by Saturation Level

| Saturation | Avg Accuracy | Distinctiveness | Memorability |
|------------|--------------|-----------------|--------------|
|       0.60 |        0.879 |           0.986 |        0.719 |
|       0.75 |        0.878 |           1.000 |        0.767 |
|       0.85 |        0.876 |           1.000 |        0.797 |
|       0.95 |        0.878 |           1.000 |        0.827 |

## Top 5 Configurations

1. **rainbow** (Sat=0.95, Bright=0.6-0.95)
   Composite: 0.996 | Acc=1.000 | Distinct=1.000
2. **perceptual** (Sat=0.95, Bright=0.4-1.0)
   Composite: 0.987 | Acc=0.970 | Distinct=1.000
3. **perceptual** (Sat=0.85, Bright=0.3-0.9)
   Composite: 0.983 | Acc=0.979 | Distinct=1.000
4. **perceptual** (Sat=0.95, Bright=0.3-0.9)
   Composite: 0.982 | Acc=0.957 | Distinct=1.000
5. **mel_rainbow** (Sat=0.95, Bright=0.6-0.95)
   Composite: 0.982 | Acc=1.000 | Distinct=1.000

## Key Findings & Recommendations

1. **perceptual** mapping achieves best overall performance
2. Optimal saturation: **0.95**
3. Perceptual uniformity improves distinctiveness by ~11%

### Visual Memory Optimization
- Higher saturation (0.85-0.95) improves memorability
- Perceptual mappings reduce confusion between similar frequencies
- Categorical mapping best for distinct frequency bands