# CLAUDE.md - Synesthesia 2.0

AI-Enhanced Psychoacoustic Audio Visualization system. Transforms audio into cochlear spiral visualizations with deep learning classification overlays.

**Owner:** Niv Dvir | **YouTube:** [@NivDvir-ND](https://youtube.com/@NivDvir-ND) (1M+ views)

Detailed component instructions are in `.claude/rules/` at the project root (visualization, evaluation, web-labeler, classifier).

---

## Visualization Versions

| Version | File | Description |
|---------|------|-------------|
| 3.0 "Enhanced" | `experiments/generators/generate_enhanced.py` | Circles with glow, white-hot cores |
| 3.5 "Radial Seismograph" | `experiments/generators/generate_hybrid_trails.py` | Trails expand outward |
| 3.5-sharp/sharper | — | Crisp trails (`order=0`, high `fade_rate`, low `accumulation_strength`) |
| Harmonic Forces (NEW) | `harmonic_connections.py` | Physics-based consonance/dissonance lines |

---

## Key Files

| File | Description |
|------|-------------|
| `audio_analyzer.py` | FFT analysis (381 logarithmic bins, 20Hz-8kHz) |
| `spiral_renderer_2d.py` | 2D spiral renderer (PIL) — primary renderer |
| `video_generator.py` | Full pipeline with FFmpeg |
| `video_generator_temporal.py` | Temporal intelligence pipeline |
| `ai_overlay.py` | ViT classification overlay |
| `synesthesia_cli.py` | CLI (v2.0), `synesthesia3_cli.py` (v3.0) |
| `harmonic_connections.py` | Harmonic forces visualization |
| `experiments/` | Generators, renderers, merkabah, legacy experiments |
| `outputs/` | Generated media files (.mp4, .png, .gif) |

---

## Development Environment

```bash
# Main venv
cd /Users/guydvir/Project/04_Code/synesthesia2
source .venv/bin/activate   # Python 3.14

# synesthesia_eval has its own venv
cd synesthesia_eval
source .venv/bin/activate
```

### Dependencies
Core: torch, torchvision, librosa, numpy, scipy, Pillow, FFmpeg, PyVista, CuPy (optional)

---

## Notes for Claude

1. Use the correct venv: `.venv/bin/python` or `synesthesia_eval/.venv/bin/python`
2. Auto-labeler needs `GEMINI_API_KEY` environment variable
3. Keep `order=0` for sharp visuals (no blurring)
4. The 123 clips in `data/clips/` are ready for labeling

---

## Current TODO

### High Priority
- [ ] Run auto_labeler on all 123 clips (needs GEMINI_API_KEY)
- [ ] Expand dataset to 50+ clips for scoring model
- [ ] Train initial ScoringModel with labeled data
- [ ] Move Google OAuth to production mode

### Medium Priority
- [ ] Add more visualization variations to dataset
- [ ] Implement inter-rater reliability (multiple labelers)
- [ ] Integrate harmonic forces into main pipeline
- [ ] Export best clips for YouTube

### Done
- [x] Web labeler deployed to production (Render.com)
- [x] Google OAuth authentication
- [x] HuggingFace integration (video streaming + label sync)
- [x] Rate limiting middleware
- [x] Jest tests (auth, labels)
- [x] Leaderboard + gamification (badges, streaks)
- [x] Auto-labeler with Gemini AI (29 clips labeled)
- [x] HuggingFace bridge (auto_labeler --push-hf, fetch_labels.py, HF dataset loader)
- [x] Organized experiments into subdirectories (experiments/)
- [x] Schema aligned: GroundTruth now uses 4 dimensions on 1-5 scale

### Low Priority
- [ ] Real-time preview feature
- [ ] YouTube auto-upload integration
- [ ] Learnable visualization parameters

---

## History

- **2026-03-09:** Fixed eval pipeline gaps (schema, HF loader, label bridge), organized 54→15 files at root
- **2026-03-09:** Reorganized CLAUDE.md, added .claude/rules/ for component-specific docs
- **2026-03-01:** Deployed web-labeler to Render.com with Google OAuth, HuggingFace integration
- **2026-03-01:** Uploaded eval dataset to HuggingFace Hub (29 clips)
- **2026-02-17:** Created auto_labeler.py with Gemini integration
- **2026-02-13:** Set up synesthesia_eval module structure
- **2026-02-06:** Version 3.5 (radial seismograph) completed
- **2026-01-28:** Version 3.0 (enhanced circles) completed

---

*Last updated: 2026-03-09*
