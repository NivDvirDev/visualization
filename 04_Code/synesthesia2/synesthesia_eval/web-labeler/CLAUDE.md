# Web Labeler — CLAUDE.md

Crowd-sourcing platform for rating synesthesia visualization clips on 4 quality dimensions.

**Live:** https://synesthesia-labeler.onrender.com
**Stack:** Node.js + Express | React 18 (TypeScript) | PostgreSQL | HuggingFace Hub

See `PLAN.md` for full architecture reference. See parent `../../CLAUDE.md` for broader project context.
Detailed rules also in `/Project/.claude/rules/web-labeler.md`.

---

## DEPLOYMENT — MUST READ

This directory is a **nested git repo** (`NivDvirDev/synesthesia-labeler`), separate from the parent monorepo (`NivDvirDev/visualization`). **Render deploys from THIS repo only.**

```bash
# To deploy: commit and push FROM THIS DIRECTORY
cd synesthesia_eval/web-labeler
git add <files> && git commit -m "msg" && git push origin main

# Pushing from the parent monorepo does NOT deploy to Render!
```

---

## ⚛️ Atoms Library — UI First Principle

> **MANDATORY RULE:** When building any new UI feature, **look in the Atoms library FIRST**.
> Compose from existing atoms before writing any new CSS or component from scratch.
> Only create custom styles when no existing atom covers the need.

### Atom Components (`client/src/components/atoms/`)

**Containers & Layout**
| Atom | Key Props |
|------|-----------|
| `GlassPanel` | variant: default\|strong\|overlay; padding |
| `Card` · `CardHeader` · `CardTitle` · `CardDescription` · `CardContent` · `CardFooter` | variant: default\|elevated\|glass\|outlined; hoverable; onClick |
| `Divider` | variant: subtle\|default\|strong; orientation; spacing |
| `Modal` | open; onClose; size: sm\|md\|lg\|full; title; footer |

**Actions & Feedback**
| Atom | Key Props |
|------|-----------|
| `Button` | variant: primary\|secondary\|ghost\|danger; size: sm\|md\|lg; loading |
| `Alert` | variant: info\|success\|warning\|error; dismissible; icon |
| `Toast` · `ToastContainer` · `useToast` | variant: default\|success\|warning\|error; duration (0=persistent) |

**Indicators & Labels**
| Atom | Key Props |
|------|-----------|
| `Badge` | variant: accent\|success\|error\|warning\|neutral\|bright; dot |
| `Tag` · `TagGroup` | variant: default\|accent\|teal\|success\|warning\|error\|outline; removable; active |
| `ScoreBar` | value; max; showLabel; size: sm\|md\|lg |
| `Avatar` · `AvatarGroup` | src; name (→initials); size: xs–xl; status: online\|offline\|away |
| `Skeleton` · `SkeletonText` · `SkeletonCard` | variant: text\|rect\|circle\|card; animated |

**Navigation & Selection**
| Atom | Key Props |
|------|-----------|
| `Tabs` · `TabPanel` | tabs[]; activeTab; onChange; variant: default\|pills\|underline |
| `Accordion` | items[]; allowMultiple; defaultOpen[]; variant: default\|flush\|glass |
| `Carousel` | children[]; autoPlay; showDots; showArrows; loop |
| `Select` | options[]; value; onChange; placeholder; size; error; label |

**Form Controls**
| Atom | Key Props |
|------|-----------|
| `Input` | label; error; hint + all HTML input attributes |
| `Checkbox` | checked; onChange; label; size; indeterminate; error |
| `Switch` | checked; onChange; label; size; variant: default\|accent |
| `Slider` | value; min; max; step; showValue; marks[]; variant: default\|accent |

**Contextual**
| Atom | Key Props |
|------|-----------|
| `Typography` | variant: display-xl/lg/md/sm, body-lg/md/sm, label, caption, mono |
| `Tooltip` | content; placement: top\|bottom\|left\|right; delay |

Import from barrel: `import { Button, Card, Modal, Select, Tabs, Avatar, Toast, useToast } from '../atoms';`

Browse all atoms in Storybook → **"Atoms"** section: `cd client && npm run storybook`

### Brand Atoms (`client/src/components/brand/`)
- `WellspringIcon` — animated SVG flame+water logo mark (`brand/WellspringLogo/WellspringIcon/`)
- `WellspringLogo` — full hero section (icon + headline + CTAs) (`brand/WellspringLogo/`)
- `FlameIcon` — compact cochlear flame icon (`brand/FlameIcon/`)

### Design Tokens (`client/src/styles/tokens.css`)
- **Colors:** `--color-accent` (flame #FF6B35), `--color-bg-primary` (parchment #F5F1E8), `--color-teal` (#2BA5A5), status colors
- **Fonts:** `--font-display` (Orbitron), `--font-body` (Inter), `--font-mono` (Space Mono)
- **Gradients:** `--gradient-accent`, `--gradient-brand`, `--gradient-elevated`
- **Glass:** `--color-glass-bg`, `--color-glass-bg-strong`
- **NEVER** use raw hex values — always reference a `--color-*` token
- **NEVER** use raw font-family strings — always use a `--font-*` token

---

## Quick Commands

```bash
# Development
cd server && npm run dev      # Backend on port 3001
cd client && npm start        # Frontend on port 3000 (proxied to 3001)

# Tests
cd server && npm test         # Jest (auth.test.js, labels.test.js)

# Production build
cd server && npm install && cd ../client && npm install --legacy-peer-deps && npm run build

# Start production
cd server && node src/index.js
```

## Key Directories

```
server/src/
├── routes/     auth.js, clips.js, labels.js, stats.js
├── models/     user.js, clip.js, label.js
├── middleware/  auth.js, rateLimiter.js, errorHandler.js
├── services/   huggingface.js
└── migrate/    001-004 SQL migrations (run on startup)

client/src/
├── App.tsx, api.ts, types.ts
└── components/  LoginPage, ClipList, VideoPlayer, LabelForm,
                 RatingsTable, Leaderboard, ProgressBar, StatsPanel
```

## Features

- JWT + Google OAuth authentication
- 4-dimension rating (sync, alignment, aesthetics, motion)
- Human vs AI label comparison (RatingsTable)
- Leaderboard, badges, streak tracking
- HuggingFace video streaming (no local storage in prod)
- Rate limiting (global, auth, label writes)
- Auto-migrations on startup

## Environment

Requires: `DATABASE_URL`, `JWT_SECRET`, `HF_TOKEN`
Optional: `USE_HUGGINGFACE`, `GOOGLE_CLIENT_ID`, `CLIPS_DIR`, `PORT`

## Figma Design System

The platform's visual design system is maintained in a **Figma Make** project:
- **Figma Make URL:** https://www.figma.com/make/YiCH6aAmkGOU3ShdPLKFbD/Web-platform-UI-UX-design
- **File Key:** `YiCH6aAmkGOU3ShdPLKFbD`
- **Integration:** `figma@claude-plugins-official` plugin (installed at user scope, provides MCP server + Agent Skills)

Key Figma Make components:
- `src/app/components/FlameIcon.tsx` — Small icon (cochlear flame spiral)
- `src/app/components/WellspringLogo.tsx` — Main logo (burning spiral)
- `src/app/components/DesignShowcase.tsx` — Full design system showcase
- `src/app/components/IconographyBreakdown.tsx` — Icon symbolism breakdown
- `src/app/components/SoundWaveVisualization.tsx` — Audio wave bars
- `src/styles/design-system.css` — Brand tokens (flame spectrum, codex palette)

Use Figma MCP tools (`get_design_context`, `ReadMcpResourceTool`) to read components.
Figma Make files are edited via Figma's own AI chat — the MCP server is read-only for Make projects.

---

*Last updated: 2026-03-11*
