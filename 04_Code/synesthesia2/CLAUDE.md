# CLAUDE.md - Synesthesia 2.0

AI-Enhanced Psychoacoustic Audio Visualization system. Transforms audio into cochlear spiral visualizations with deep learning classification overlays.

**Owner:** Niv Dvir | **YouTube:** [@NivDvir-ND](https://youtube.com/@NivDvir-ND) (1M+ views)

Detailed component instructions are in `.claude/rules/` at the project root (visualization, evaluation, web-labeler, classifier).

---

## Visualization Versions

| Version | File | Description |
|---------|------|-------------|
| **Mesh3D (NEW)** | `Mesh3_remake1/mesh_renderer.py` | ModernGL 3D wireframe double-helix — reproduces MATLAB YouTube look |
| 2D Spiral | `spiral_renderer_2d.py` | PIL 2D circles with glow — default renderer |
| Harmonic Forces | `harmonic_connections.py` | Physics-based consonance/dissonance lines |
| 3.0-3.5 experiments | `archive/experiments/` | Archived: enhanced circles, seismograph, merkabah, etc. |

---

## Key Files

| File | Description |
|------|-------------|
| `audio_analyzer.py` | FFT analysis (381 logarithmic bins, 20Hz-8kHz) |
| `Mesh3_remake1/` | **3D wireframe renderer package** — Python port of MATLAB Mesh3 |
| `Mesh3_remake1/mesh_renderer.py` | ModernGL 3D wireframe renderer — port of piperecord11 |
| `Mesh3_remake1/mesh_colormap.py` | Per-octave HSV rainbow colormap (myjet port) |
| `Mesh3_remake1/flow_amp.py` | Energy envelope for wave speed modulation (flowAMP port) |
| `Mesh3_remake1/outputs/` | Generated mesh3d demo videos and frame captures |
| `spiral_renderer_2d.py` | 2D spiral renderer (PIL) — default renderer |
| `video_generator.py` | Full 2D pipeline with FFmpeg |
| `synesthesia_cli.py` | CLI — use `--renderer mesh3d` for 3D wireframe |
| `harmonic_connections.py` | Harmonic forces visualization |
| `archive/` | Archived experiments (merkabah, seismograph, PyVista, etc.) |
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

## CRITICAL: Web-Labeler Deployment (Dual-Repo)

The web-labeler has a **nested git repo** inside the monorepo. Render deploys from the nested repo, NOT this one.

| Repo | Path | Remote | Deploys? |
|------|------|--------|----------|
| **Monorepo** | `/Users/guydvir/Project/04_Code/synesthesia2/` | `NivDvirDev/visualization` | NO |
| **Nested (Render)** | `synesthesia_eval/web-labeler/` | `NivDvirDev/synesthesia-labeler` | **YES** |

**When changing web-labeler files, ALWAYS push to BOTH repos:**
```bash
# 1. Push to nested repo FIRST (this triggers Render deploy)
cd synesthesia_eval/web-labeler && git add <files> && git commit -m "msg" && git push

# 2. Then push to monorepo (keeps history in sync)
cd ../.. && git add <files> && git commit -m "msg" && git push
```

Pushing only to the monorepo will NOT deploy. This caused a critical incident on 2026-03-20 where fixes were committed but never reached production.

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
