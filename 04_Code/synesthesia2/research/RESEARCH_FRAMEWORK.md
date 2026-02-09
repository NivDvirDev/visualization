# SYNESTHESIA Research Framework
## Systematic Investigation of Visualization-Classification Optimization

### 🎯 Research Goal
Discover optimal visualization rules/laws that maximize classification accuracy through iterative cycles of:
**Visualization → Classification → Analysis → Retune → Repeat**

---

## 1. Core Research Questions

### 1.1 Visualization Parameter Space
- **Spiral Geometry**: How do spiral turns, radius scaling, and point density affect feature extraction?
- **Color Mapping**: Which chromesthesia mappings (frequency→color) produce most discriminative features?
- **Temporal Integration**: What time windows for melody/rhythm/harmony/atmosphere optimize classification?
- **Amplitude Encoding**: Linear vs. logarithmic vs. learned amplitude-to-size mappings?

### 1.2 Classification Feedback
- Which visual regions contain most discriminative information?
- How does attention distribution correlate with classification accuracy?
- Can we learn visualization parameters end-to-end with classification?

---

## 2. Experimental Design

### 2.1 Dataset Requirements
We need diverse, labeled audio data across multiple dimensions:

| Dimension | Classes | Purpose |
|-----------|---------|---------|
| Instrument | Piano, Guitar, Violin, Drums, Voice, etc. | Primary classification task |
| Genre | Classical, Jazz, Rock, Electronic, World | Cross-domain generalization |
| Emotion | Happy, Sad, Energetic, Calm, Tense | Perceptual validation |
| Pitch Range | Low, Mid, High | Spiral mapping validation |
| Tempo | Slow (<80), Medium (80-120), Fast (>120) | Temporal feature validation |

### 2.2 Visualization Parameters to Investigate

```
SPIRAL_PARAMS = {
    'turns': [1.5, 2.0, 2.5, 3.0, 3.5],
    'inner_radius': [0.1, 0.15, 0.2, 0.25],
    'outer_radius': [0.4, 0.45, 0.5],
    'point_density': [1.0, 1.5, 2.0],
}

COLOR_PARAMS = {
    'mapping': ['chromesthesia_classic', 'mel_rainbow', 'perceptual_uniform', 'learned'],
    'saturation_curve': ['linear', 'log', 'sqrt'],
    'brightness_range': [(0.3, 1.0), (0.5, 1.0), (0.2, 0.9)],
}

TEMPORAL_PARAMS = {
    'melody_trail_length': [10, 20, 30, 50],
    'rhythm_pulse_decay': [0.1, 0.2, 0.3],
    'harmony_blend_time': [0.5, 1.0, 2.0],
    'atmosphere_window': [30, 60, 120],
}

AMPLITUDE_PARAMS = {
    'scaling': ['linear', 'log', 'sqrt', 'learned'],
    'min_size': [1, 2, 3],
    'max_size': [8, 12, 16, 20],
    'threshold': [0.01, 0.05, 0.1],
}
```

### 2.3 Evaluation Metrics

1. **Classification Accuracy**: Primary metric across instrument/genre/emotion tasks
2. **Attention Consistency**: Do attention maps focus on musically meaningful regions?
3. **Feature Discriminability**: t-SNE/UMAP clustering quality of learned features
4. **Perceptual Validity**: Human evaluation of visualization meaningfulness
5. **Generalization**: Cross-dataset transfer performance

---

## 3. Implementation Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    RESEARCH PIPELINE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │  AUDIO   │───▶│ VISUALIZATION │───▶│ CLASSIFIER   │          │
│  │ DATASET  │    │   RENDERER    │    │   (CNN/ViT)  │          │
│  └──────────┘    └──────────────┘    └──────────────┘          │
│       │                │                    │                   │
│       │                │                    │                   │
│       ▼                ▼                    ▼                   │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │ METADATA │    │  ATTENTION   │    │  ACCURACY    │          │
│  │  LABELS  │    │    MAPS      │    │  METRICS     │          │
│  └──────────┘    └──────────────┘    └──────────────┘          │
│       │                │                    │                   │
│       └────────────────┼────────────────────┘                   │
│                        │                                        │
│                        ▼                                        │
│              ┌──────────────────┐                               │
│              │    ANALYZER      │                               │
│              │  - Correlation   │                               │
│              │  - Attribution   │                               │
│              │  - Suggestions   │                               │
│              └──────────────────┘                               │
│                        │                                        │
│                        ▼                                        │
│              ┌──────────────────┐                               │
│              │ PARAMETER TUNER  │                               │
│              │  - Grid Search   │                               │
│              │  - Bayesian Opt  │                               │
│              │  - Evolutionary  │                               │
│              └──────────────────┘                               │
│                        │                                        │
│                        ▼                                        │
│              ┌──────────────────┐                               │
│              │  EXPERIMENT LOG  │                               │
│              │  - Parameters    │                               │
│              │  - Results       │                               │
│              │  - Insights      │                               │
│              └──────────────────┘                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Dataset Strategy

### 4.1 Public Datasets to Integrate
- **NSynth** (Google Magenta): 300K+ instrument samples with labels
- **GTZAN**: 1000 audio tracks across 10 genres
- **MedleyDB**: Multi-track recordings with instrument annotations
- **Free Music Archive (FMA)**: Large-scale genre-labeled dataset
- **RAVDESS**: Emotional speech/song dataset

### 4.2 Custom Dataset Generation
- Synthesize controlled samples with known parameters
- Record isolated instrument samples
- Create audio with controlled melody/rhythm/harmony variations

### 4.3 Augmentation Pipeline
- Pitch shifting (±2 semitones)
- Time stretching (0.8x - 1.2x)
- Adding noise/reverb
- Mixing instruments

---

## 5. Experiment Tracking

Each experiment records:
```json
{
    "experiment_id": "exp_001",
    "timestamp": "2026-01-29T10:00:00Z",
    "visualization_params": { ... },
    "dataset": "nsynth_train",
    "model": "SimpleCNN",
    "results": {
        "accuracy": 0.87,
        "per_class_accuracy": { ... },
        "confusion_matrix": [ ... ],
        "attention_stats": { ... }
    },
    "insights": "High attention on spiral center suggests low-freq importance"
}
```

---

## 6. Key Hypotheses to Test

1. **H1**: Logarithmic spiral radius scaling improves low-frequency discrimination
2. **H2**: Longer melody trails improve pitch-based classification
3. **H3**: Rhythm pulse intensity correlates with tempo classification accuracy
4. **H4**: Perceptually uniform color spaces outperform raw chromesthesia
5. **H5**: Attention-guided rendering creates self-reinforcing improvement cycles

---

## 7. Success Criteria

| Metric | Baseline | Target |
|--------|----------|--------|
| Instrument Classification | 87% | 95%+ |
| Genre Classification | 75% | 88%+ |
| Emotion Recognition | 65% | 80%+ |
| Cross-dataset Transfer | 60% | 75%+ |
| Human Perceptual Rating | 3.5/5 | 4.5/5 |

