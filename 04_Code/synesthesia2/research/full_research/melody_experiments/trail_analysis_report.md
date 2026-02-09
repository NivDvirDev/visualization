# Melody Trail Parameter Investigation Report

Generated: 2026-01-29T11:48:31.973495

Total Experiments: 90

## Summary by Trail Length

| Trail Length | Avg Accuracy | Avg Coherence | Avg Contour |
|--------------|--------------|---------------|-------------|
|           10 |        0.863 |         0.847 |       1.000 |
|           20 |        0.859 |         0.822 |       1.000 |
|           30 |        0.794 |         0.819 |       1.000 |
|           50 |        0.834 |         0.819 |       1.000 |
|           80 |        0.807 |         0.819 |       1.000 |
|          120 |        0.833 |         0.820 |       1.000 |

**Optimal Trail Length:** 10 frames

## Summary by Decay Rate

| Decay Rate | Avg Accuracy | Avg Coherence | Avg Contour |
|------------|--------------|---------------|-------------|
|       0.70 |        0.849 |         0.845 |       1.000 |
|       0.80 |        0.822 |         0.843 |       1.000 |
|       0.85 |        0.839 |         0.833 |       1.000 |
|       0.90 |        0.848 |         0.815 |       1.000 |
|       0.95 |        0.801 |         0.785 |       1.000 |

## Top 5 Configurations

1. L=10, D=0.7, Style=glow
   Score: 0.937 (Acc=0.962, Coh=0.842, Con=1.000)
2. L=10, D=0.9, Style=glow
   Score: 0.927 (Acc=0.931, Coh=0.850, Con=1.000)
3. L=20, D=0.7, Style=solid
   Score: 0.925 (Acc=0.930, Coh=0.844, Con=1.000)
4. L=50, D=0.7, Style=glow
   Score: 0.924 (Acc=0.924, Coh=0.847, Con=1.000)
5. L=120, D=0.7, Style=glow
   Score: 0.923 (Acc=0.922, Coh=0.848, Con=1.000)

## Key Findings

1. **Optimal trail length:** 10 frames (accuracy: 0.863)
2. **Best decay rate for coherence:** 0.70 (score: 0.845)

## Recommendations

Based on this analysis:
- Use trail length of **10** frames for optimal balance
- Decay rate of **0.70** provides best visual coherence
- Consider adaptive trail length based on note density