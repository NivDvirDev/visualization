# Dataset Coverage Matrix

## מדדי הערכה (מה ה-Framework בודק)

### 1. SynchronizationMetrics (40% מהציון)
| מדד | מה בודק | סוגי קליפים נדרשים |
|-----|---------|-------------------|
| `onset_visual_alignment` | האם שינויים ויזואליים קורים על onsets | קליפים עם sync טוב vs רע |
| `beat_sync_score` | התאמה בין beats לפיקים ויזואליים | EDM מסונכרן, אמביינט לא מסונכרן |
| `tempo_consistency` | טמפו אודיו = טמפו ויזואלי | 1:1, 2:1, לא מתאים |
| `cross_correlation` | קורלציה בין עטיפות | אנרגיה גבוהה=בהיר, או הפוך |

### 2. AlignmentMetrics (35% מהציון)
| מדד | מה בודק | סוגי קליפים נדרשים |
|-----|---------|-------------------|
| `energy_alignment` | RMS אודיו ↔ בהירות | loud=bright, או אקראי |
| `frequency_color_mapping` | תדר ↔ צבע (נמוך=חם, גבוה=קר) | ספקטרוגרמים, ויזואליזציות צבעוניות |

### 3. TemporalAnalyzer (25% מהציון)
| מדד | מה בודק | סוגי קליפים נדרשים |
|-----|---------|-------------------|
| `visual_rhythm` | קצב ויזואלי עקבי | לולאות מחזוריות vs כאוטיות |
| `phase_coherence` | פאזה עקבית לאורך זמן | מסונכרן לאורך כל הקליפ vs drift |

---

## קטגוריות קליפים נדרשות

### A. לפי איכות סנכרון
- [ ] **sync_perfect** (5+): סנכרון מושלם beat-visual
- [ ] **sync_good** (5+): סנכרון טוב עם חריגות קטנות
- [ ] **sync_poor** (5+): סנכרון חלש או אקראי
- [ ] **sync_none** (3+): ויזואליזציה סטטית/לא קשורה

### B. לפי סגנון ויזואלי
- [ ] **spectrogram** (5+): ספקטרוגרמים, waveforms
- [ ] **particles** (5+): חלקיקים, nebulas
- [ ] **geometric** (5+): צורות גיאומטריות, kaleidoscope
- [ ] **abstract** (5+): אבסטרקט, gradients
- [ ] **3d** (3+): סצנות תלת מימד

### C. לפי ז'אנר מוזיקלי
- [ ] **edm** (5+): אלקטרוני, beats חזקים
- [ ] **classical** (3+): קלאסי, דינמיקה רחבה
- [ ] **ambient** (3+): אמביינט, שינויים איטיים
- [ ] **vocal** (3+): עם שירה

### D. לפי מאפיינים טכניים
- [ ] **high_tempo** (3+): >140 BPM
- [ ] **low_tempo** (3+): <80 BPM
- [ ] **loud** (3+): אנרגיה גבוהה
- [ ] **quiet** (3+): אנרגיה נמוכה
- [ ] **complex** (3+): הרבה אלמנטים ויזואליים
- [ ] **minimal** (3+): מינימליסטי

---

## סטטוס נוכחי

| קטגוריה | יש | צריך | סטטוס |
|---------|-----|------|-------|
| Professional | 4 | 5 | 🟡 |
| Spectrogram | 3 | 5 | 🟡 |
| Reactive | 3 | 5 | 🟡 |
| Various | 8 | 10 | 🟡 |
| Poor sync | 0 | 5 | 🔴 |
| Ambient | 0 | 3 | 🔴 |
| Classical | 0 | 3 | 🔴 |
| **סה"כ** | **19** | **~50** | **38%** |

---

## חיפושים נדרשים להשלמה

```bash
# Poor sync examples
"music visualizer bad sync"
"random visualization music"
"static background music"

# Ambient/slow
"ambient music visualization"
"meditation visualization"
"slow music visualizer"

# Classical
"classical music visualization"
"orchestra visualizer"
"piano visualization"

# More spectrograms
"circular spectrogram music"
"3d spectrogram"

# High energy
"dubstep visualizer"
"bass drop visualization"
```
