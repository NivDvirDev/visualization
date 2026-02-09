# Melody Trail Parameter Investigation Report

Generated: 2026-01-29T11:11:11.931270

Total Experiments: 90

## Summary by Trail Length

| Trail Length | Avg Accuracy | Avg Coherence | Avg Contour |
|--------------|--------------|---------------|-------------|
|           10 |        0.839 |         0.836 |       1.000 |
|           20 |        0.826 |         0.810 |       1.000 |
|           30 |        0.818 |         0.808 |       1.000 |
|           50 |        0.851 |         0.809 |       1.000 |
|           80 |        0.819 |         0.810 |       1.000 |
|          120 |        0.834 |         0.810 |       1.000 |

**Optimal Trail Length:** 10 frames

## Summary by Decay Rate

| Decay Rate | Avg Accuracy | Avg Coherence | Avg Contour |
|------------|--------------|---------------|-------------|
|       0.70 |        0.868 |         0.837 |       1.000 |
|       0.80 |        0.831 |         0.832 |       1.000 |
|       0.85 |        0.832 |         0.822 |       1.000 |
|       0.90 |        0.829 |         0.803 |       1.000 |
|       0.95 |        0.796 |         0.774 |       1.000 |

## Top 5 Configurations

1. L=50, D=0.7, Style=glow
   Score: 0.924 (Acc=0.931, Coh=0.838, Con=1.000)
2. L=120, D=0.8, Style=gradient
   Score: 0.923 (Acc=0.933, Coh=0.833, Con=1.000)
3. L=120, D=0.7, Style=gradient
   Score: 0.918 (Acc=0.915, Coh=0.839, Con=1.000)
4. L=30, D=0.7, Style=solid
   Score: 0.918 (Acc=0.916, Coh=0.837, Con=1.000)
5. L=50, D=0.85, Style=glow
   Score: 0.917 (Acc=0.928, Coh=0.819, Con=1.000)

## Key Findings

1. **Optimal trail length:** 50 frames (accuracy: 0.851)
2. **Best decay rate for coherence:** 0.70 (score: 0.837)

## Recommendations

Based on this analysis:
- Use trail length of **10** frames for optimal balance
- Decay rate of **0.70** provides best visual coherence
- Consider adaptive trail length based on note density