# SYNESTHESIA Visualization Laws Report

## Law 1: Cochlear Logarithmic Mapping

**Category:** geometry

**Description:** Frequency maps to position logarithmically, matching cochlear tonotopy

**Formula:** `position = log(freq / f_min) / log(f_max / f_min)`

**Parameters:**
- f_min: 20
- f_max: 20000

**Evidence:**
- Experiments tested: 0
- Mean accuracy improvement: 0.00%
- Confidence: 90%

**Conditions:** biologically inspired

---

## Law 2: Scriabin Chromesthesia

**Category:** color

**Description:** Pitch class maps to color following Scriabin's synesthetic associations

**Formula:** `color = scriabin_map[pitch_class % 12]`

**Parameters:**
- base_note: C

**Evidence:**
- Experiments tested: 0
- Mean accuracy improvement: 0.00%
- Confidence: 70%

**Conditions:** pitch-based classification

---

## Law 3: Logarithmic Amplitude Compression

**Category:** amplitude

**Description:** Amplitude maps to size logarithmically to compress dynamic range

**Formula:** `size = min_size + log(amp/threshold) / log(1/threshold) * (max_size - min_size)`

**Parameters:**
- threshold: 0.01
- min_size: 2
- max_size: 12

**Evidence:**
- Experiments tested: 0
- Mean accuracy improvement: 0.00%
- Confidence: 80%

**Conditions:** audio with >40dB dynamic range

---

## Law 4: Hierarchical Temporal Pyramid

**Category:** temporal

**Description:** Multi-scale temporal analysis from frames to atmosphere

**Formula:** `features[scale] = pool(extract(audio, windows[scale]))`

**Parameters:**
- frame_ms: 30
- note_ms: 200
- phrase_s: 4
- atmosphere_s: 60

**Evidence:**
- Experiments tested: 0
- Mean accuracy improvement: 0.00%
- Confidence: 85%

**Conditions:** temporal pattern recognition

---

