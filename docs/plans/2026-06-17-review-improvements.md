# Project Review — Improvements, Merges & Future Directions

**Date:** 2026-06-17
**Status:** Current through commit `9096383`. Five follow-up improvements are landed, committed, and passing the full gate.
**Purpose:** Pickup/handoff doc. Safe to clear context and resume from here.

---

## How to resume

```bash
cd ~/Desktop/github/pyreeler
git status                 # should be clean after the latest committed task
python3 sync.py --check    # should print "in sync"
python3 graduation_check.py
python3 -m pytest -q       # should be 52 passed
```

Current worktree expectation: clean. The implementation history is commit-backed;
use the roadmap below to choose the next task.

---

## DONE (earlier review cleanup)

### 1. Template de-duplication + sync guard ✅
**Problem:** `templates/`, `skills/claude/templates/`, `skills/codex/templates/` held
byte-identical copies with no sync mechanism — already drifting.
**Done:**
- `sync.py` (new) — `templates/` (root) is canonical; copies into both skill folders.
  Also syncs the 3 byte-identical reference docs (`three-d-and-lensing.md`,
  `creative-lenses.md`, `audio-pipeline.md`). Leaves `workflow.md` /
  `vocabulary-map.md` alone — those legitimately differ per platform.
  - `python3 sync.py` to distribute; `python3 sync.py --check` for CI drift guard.
- `tests/test_sync.py` (new) — verifies faithful copy + that divergent files are excluded.

### 2. Untracked scratch artifacts ✅
- `git rm --cached` on `experimental/_b64_part*.txt`, `_mobile_b64.txt`,
  `_*_debug.png`, `cosmic_collapse_smoke*.png` (files kept on disk, just untracked).
- `experimental/.gitignore` extended with `_*.txt`, `*_debug.png`, `*_smoke*.png`.

### 3. README + DEVLOG contradictions fixed ✅
- README "videos not stored" line corrected — small showcase clips *are* committed
  for the gallery; finals/previews are gitignored and go to `~/Videos`.
- README: new **Development** section (sync.py / pytest) + structure tree updated.
- DEVLOG: header + benchmark section flagged as historical (Windows paths and the
  `narrative_preview_smoke.py` harness are not in this repo / not reproducible).

### 4. Tests + CI ✅
- `pytest.ini` — testpaths = `tests/` + `experimental/experiments/test_cosmic_collapse.py`
  (sampler-film tests excluded by default: hardcoded relative paths + perf monitors).
- `.github/workflows/ci.yml` — on push/PR: `sync.py --check` then `pytest -q`.
- Superseded by the current full gate below.

---

## DONE (follow-up implementation run)

### 1. Contact-sheet sweep tool ✅
**Commits:** `53216e3` through `eb6fa94`, plus docs in `04b3eed` and roadmap refresh in `2ae06ec`.
**Delivered:** `experimental/tools/contact_sheet.py`, co-located tests, runnable demo,
pytest wiring, optional contact-sheet and individual frame outputs.

### 2. Template graduation gate ✅
**Commits:** `c0287ec`, `21ae885`, `b807842`, `20b4a14`.
**Delivered:** `template_graduation.toml`, `graduation_check.py`, tests, README docs,
and CI enforcement after `sync.py --check`.

### 3. Audio-reactive parameter mapping ✅
**Commits:** `09f85d3`, `e894a0a`.
**Delivered:** `templates/audio/audio_reactive.py`, synced provider copies, tests,
README docs, and graduation manifest entry.

### 4. Local GPU frame synthesis runtime hardening ✅
**Commits:** `f71bff5`, `12d2644`, `f245aaa`, `5025e3d`.
**Delivered:** import-safe optional `wgpu`, fake-adapter tests, local FFmpeg candidate
resolution, docs distinguishing GPU encoding from GPU frame synthesis.

### 5. Provider-agnostic shared skill core ✅
**Commits:** `38c7e1b`, `d24fe6c`, `9096383`.
**Delivered:** `skills/_shared/references/` as the canonical shared-reference source,
`sync.py` updates, sync tests, and README/docs updates.

### Current verification ✅

```bash
python3 sync.py --check
python3 graduation_check.py
python3 -m pytest -q
```

Latest result: **52 passed**.

---

## RESOLVED

### A. Stale `experimental/skills/codex/` copy ✅ (2026-06-17)
**Resolution: deleted (option c).** The copy was documentation-only (no code imported
it — verified) and meaningfully stale (missing the 4 newer video templates,
`three-d-and-lensing.md`, `agents/`). Keeping a 4th drifting copy contradicted the
single-source `sync.py` model. Removed it and repointed the three doc references in
`experimental/README.md` and `experimental/GUIDE.md` to the canonical top-level
`skills/codex/` (and repo-root `templates/`). `main-skill-demo`'s references already
point at the canonical skill, so they stayed valid.

## RESOLVED (cont.)

### B. Committed showcase media ✅ (2026-06-17)
**Resolution: re-encoded in place, kept in main.** Git LFS was rejected because
GitHub Pages does not serve LFS objects — `index.html` loads the 9 clips directly,
so LFS would serve pointer text and break the gallery. Instead re-encoded all clips
with `libx264 -crf 28 -preset slow -movflags +faststart` (no resolution change; they
were already ≤720p). **Result: 76 MB → 29 MB (~62% smaller)**, faststart added for
better web streaming, durations/resolutions preserved, all decode cleanly, terminal
text and detail spot-checked. No force-push / history rewrite (full-clone history
still holds the old blobs; only the checkout shrinks — acceptable per the chosen
low-risk path).

---

## CURRENT ROADMAP STATUS (prioritized)

1. **Formalize template "graduation"** (ROADMAP Option 4). Graduation currently = manual
   copy. Make it: passing tests + an example film + `sync.py`. Turns a copy-paste ritual
   into a verifiable gate. Implemented via `template_graduation.toml`,
   `graduation_check.py`, and CI enforcement. Spec/plan:
   `docs/superpowers/specs/2026-06-17-template-graduation-design.md` and
   `docs/superpowers/plans/2026-06-17-template-graduation.md`.
2. **ParameterSequence-driven batch render + comparison/contact-sheet tool.** Contact-sheet
   comparison is delivered as `experimental/tools/contact_sheet.py` for single-axis
   sweeps. 2D grids and parallel variant rendering remain future work.
3. **Audio-reactive parameter mapping** — let audio envelopes drive visual params via the
   existing shared `arc_state(t)` timeline. Portable v1 delivered as
   `templates/audio/audio_reactive.py` with per-frame RMS envelopes and scalar
   mapping helpers; band-specific envelopes and beat detection remain future work.
   Spec/plan:
   `docs/superpowers/specs/2026-06-17-audio-reactive-parameter-mapping-design.md`
   and `docs/superpowers/plans/2026-06-17-audio-reactive-parameter-mapping.md`.
4. **GPU frame *synthesis*** (not just encoding). Seed: `docs/hardware-experiments/wgpu_runtime.py`.
   Keep in `experimental/` until portable. DEVLOG is honest that "GPU mode" today = encode only.
   Local runtime is now import-safe without `wgpu` and CI-covered for adapter/FFmpeg
   selection behavior; actual shader rendering remains local-only. Spec/plan:
   `docs/superpowers/specs/2026-06-17-gpu-frame-synthesis-runtime-design.md` and
   `docs/superpowers/plans/2026-06-17-gpu-frame-synthesis-runtime.md`.
5. **Provider-agnostic skill core** — a `skills/_shared/` consumed by thin per-provider
   wrappers, so adding a 3rd AI provider is trivial. `skills/_shared/references/`
   now provides the canonical source for byte-identical references, and `sync.py`
   copies those into each provider skill. Generated provider wrappers remain future work.
   Spec/plan:
   `docs/superpowers/specs/2026-06-17-provider-agnostic-skill-core-design.md` and
   `docs/superpowers/plans/2026-06-17-provider-agnostic-skill-core.md`.

## NEXT TASK CANDIDATES

Detailed backlog:
`docs/plans/2026-06-17-remaining-roadmap-implementation.md`.

1. **Contact-sheet v2:** add 2D parameter grids and/or parallel variant rendering.
2. **Audio-reactive v2:** add band-specific envelopes and beat/onset helpers.
3. **GPU synthesis v2:** add a shader render base class, benchmark output, or CPU
   fallback contract while keeping CI GPU-free.
4. **Provider core v2:** generate provider wrappers/shared SKILL fragments instead
   of maintaining duplicated prose manually.
5. **Experimental roadmap:** implement `ParameterSequence` batch rendering or visual
   regression testing.

---

## Notes on conventions observed
- Skills must ship self-contained → templates are physical copies, hence `sync.py`.
- `experimental/` is a permanent "habitat," not a staging area (per its README).
- References differ per platform only for tool naming / invocation syntax.
