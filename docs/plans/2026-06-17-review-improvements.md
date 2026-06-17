# Project Review — Improvements, Merges & Future Directions

**Date:** 2026-06-17
**Status:** In progress — 4 improvements landed in working tree (uncommitted), several proposed items pending your call.
**Purpose:** Pickup/handoff doc. Safe to clear context and resume from here.

---

## How to resume

```bash
cd ~/Desktop/github/pyreeler
git status                 # see the uncommitted work described below
python3 sync.py --check    # should print "in sync"
pytest -q                  # should be 8 passed
```

Nothing has been committed yet. The changes below live in the working tree.

---

## DONE (this session, uncommitted)

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
- Current: **8 passed**.

**Suggested commit grouping** (when you're ready — not yet committed):
1. `chore: untrack scratch artifacts + extend experimental gitignore`
2. `feat(build): add sync.py to dedupe templates across skill folders + tests`
3. `ci: add pytest config and GitHub Actions workflow`
4. `docs: reconcile README/DEVLOG with committed media and add dev workflow`

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

## FUTURE DIRECTIONS (prioritized — beyond ROADMAP.md)

1. **Formalize template "graduation"** (ROADMAP Option 4). Graduation currently = manual
   copy. Make it: passing tests + an example film + `sync.py`. Turns a copy-paste ritual
   into a verifiable gate. Spec/plan drafted in
   `docs/superpowers/specs/2026-06-17-template-graduation-design.md` and
   `docs/superpowers/plans/2026-06-17-template-graduation.md`.
2. **ParameterSequence-driven batch render + comparison/contact-sheet tool.** Contact-sheet
   comparison is delivered as `experimental/tools/contact_sheet.py` for single-axis
   sweeps. 2D grids and parallel variant rendering remain future work.
3. **Audio-reactive parameter mapping** — let audio envelopes drive visual params via the
   existing shared `arc_state(t)` timeline. Builds on existing infra, no new deps.
4. **GPU frame *synthesis*** (not just encoding). Seed: `docs/hardware-experiments/wgpu_runtime.py`.
   Keep in `experimental/` until portable. DEVLOG is honest that "GPU mode" today = encode only.
5. **Provider-agnostic skill core** — a `skills/_shared/` consumed by thin per-provider
   wrappers, so adding a 3rd AI provider is trivial. `sync.py` is the first step toward this.

---

## Notes on conventions observed
- Skills must ship self-contained → templates are physical copies, hence `sync.py`.
- `experimental/` is a permanent "habitat," not a staging area (per its README).
- References differ per platform only for tool naming / invocation syntax.
