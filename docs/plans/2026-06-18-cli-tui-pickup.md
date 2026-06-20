# PyReeler CLI + TUI — Pickup / Resume Doc

**Updated:** 2026-06-18
**Purpose:** Resume cleanly after clearing context. Everything needed to continue is here or linked.

---

## TL;DR state

- **Plan 1 (non-AI CLI core): DONE and merged to `main`** (merge commit on `origin/main`,
  branch `feat/recipe-cli` deleted). `pyreeler list` / `pyreeler render` work and produce
  real mp4s. 76 tests pass; all three CI gates green.
- **Plan 2 (Textual TUI): IN PROGRESS on branch `feat/recipe-tui`.** Tasks 1-2 of 5 done,
  fully reviewed (spec + code quality), committed. Tasks 3-5 remain. See
  "Plan 2 progress" below for exact resume state.

## How to resume (commands)

```bash
cd /path/to/pyreeler
git status                       # expect clean, on main
python3 -m pytest -q             # expect all pass (76+)
python3 sync.py --check && python3 graduation_check.py   # both clean
python3 -m pyreeler list         # prints lorenz + rossler  (proves CLI works)
python3 -m pyreeler render lorenz --duration 5 --fps 12 -o /tmp/demo.mp4  # real render
```

To **implement Plan 2**, tell Claude:
> "Execute Plan 2 (the TUI) with subagent-driven development."

Claude should then:
1. Create a branch: `git checkout -b feat/recipe-tui`.
2. `pip install -r requirements-tui.txt` (textual, rich, terminaltexteffects — needed to
   develop/test the TUI; CI stays green without them via `importorskip`).
3. Work through `docs/superpowers/plans/2026-06-18-recipe-tui.md` task by task.

## Plan 2 progress (resume here)

**Branch:** `feat/recipe-tui` (3 commits ahead of `main`, working tree clean).
**Execution method:** subagent-driven-development (fresh implementer per task, then a
spec-compliance review and a code-quality review before marking each task done).

**Resume commands:**
```bash
cd /path/to/pyreeler
git checkout feat/recipe-tui
git log --oneline main..HEAD     # expect the 3 commits below
python3 -m pytest -q             # expect 79 passed (76 core + 3 TUI; deps are installed)
```

**Environment note (important):** this machine's `/usr/bin/python3` is Debian
externally-managed (PEP 668), so plain `pip install -r requirements-tui.txt` is REFUSED.
The TUI deps are already installed for the current user via:
```bash
python3 -m pip install --user --break-system-packages -r requirements-tui.txt
```
Installed versions: **textual 8.2.7, terminaltexteffects 0.15.0, rich**. If a fresh
machine needs them, rerun that exact command (or use a venv with `--system-site-packages`
so it keeps the system numpy/pillow). The 3 TUI tests run only when these deps are present;
CI (numpy+pillow only) skips them via `pytest.importorskip`.

**Done (committed + reviewed):**
- Task 1 — `pyreeler/tui/banner.py` + `tests/test_tui_banner.py`. Commits `3680117`,
  `84e2bc2` (trailing-newline polish from code review).
- Task 2 — `pyreeler/tui/app.py` + `pyreeler/tui/styles.tcss` + `tests/test_tui_app.py`
  (`PyReelerApp` skeleton: recipe ListView + `run()`). Commit `96cfa0c`.

**Key learning for the remaining tasks:** the plan was written blind against textual
`>=0.60`, but **textual 8.2.7 accepted every plan API call verbatim** in Task 2 (`App`,
`compose`, `ComposeResult`, `Horizontal/Vertical`, `ListView/ListItem`, `ProgressBar(...,
show_eta=False)`, `Button(variant="success")`, `run_test()`/`pilot.pause()`). So Tasks 3-4
can likely use the plan's code as-is; if any call drifts, **adjust the call, keep the test
assertions** (the test is the contract).

**Remaining (do these next, in order — full code is in the Plan 2 doc):**
- Task 3 — recipe selection drives summary + generated param form (`on_mount`,
  `on_list_view_highlighted`, `_load_recipe`, `_current_name`). Extends `tests/test_tui_app.py`.
- Task 4 — `_collect_params`, threaded `@work` render worker, progress bar + `Sparkline`,
  `ParamError` surfaced to `#status`. Extends `tests/test_tui_app.py`.
- Task 5 — play banner in `run()` before mount; manual smoke test in a real terminal
  (`python3 -m pyreeler`); update `README.md` TUI section. Then final whole-branch review
  + `superpowers:finishing-a-development-branch`.

**Carry-forward notes from the Task 1-2 reviews (non-blocking, address while doing 3-5):**
- Task 4: consider hiding `ProgressBar` (`display: none` in `styles.tcss`) until a render
  starts, so it isn't sitting at 0% the whole time.
- `run()` hard-codes `return 0` and ignores `App.run()`'s return — fine, but Task 5 rewrites
  `run()` anyway; a one-line "intentionally ignored" comment there would be clearer.

To continue, tell Claude:
> "Resume Plan 2 on branch feat/recipe-tui — continue from Task 3 with subagent-driven development."

## Key documents

- **Spec (covers BOTH CLI + TUI):** `docs/superpowers/specs/2026-06-18-recipe-cli-and-tui-design.md`
- **Plan 1 (done):** `docs/superpowers/plans/2026-06-18-recipe-cli-core.md`
- **Plan 2 (next):** `docs/superpowers/plans/2026-06-18-recipe-tui.md`

## What Plan 1 delivered (so you don't re-derive it)

New `pyreeler/` package:
- `recipes/` — `Param`/`Recipe` registry, param validation, a palette-aware attractor
  plotter (`_plot.scatter_trail`), and `lorenz` + `rossler` recipes (auto-registered).
- `engine.py` — `render_film(recipe, params, out, on_progress)`: precompute trajectory →
  parallel frame map (`templates.video.parallel_render`) → pipe to FFmpeg. Picklable
  `_FrameJob` for multiprocessing; `_encode_frames` reaps FFmpeg + surfaces its stderr.
- `cli.py` + `__main__.py` — `list` / `render` with per-recipe generated typed flags;
  no-arg launches the TUI via the `_launch_tui()` seam (Plan 2 fills `pyreeler/tui/app.py:run`).
- `pyproject.toml` (`tui` extra), `requirements-tui.txt`, `pyreeler/tui/__init__.py`.
  (The original `pyreeler` console-script entry was later removed in favor of the
  canonical `python3 -m pyreeler`; the TUI package is now built, not a placeholder.)

**Recipe rendering note:** the plotter uses rotation-invariant centered framing + a gamma
glow lift; default `trail` shows the full attractor. A `render lorenz` produces a centered,
glowing phosphor butterfly (verified by eye). If you change the plotter, **render a frame
and look at it** — visual regressions don't show up in unit tests.

## Deferred Plan-1 polish (non-blocking — none affect correctness at defaults)

From the final whole-branch review; pick up anytime:
1. Sub-frame off-by-one in the trail-window center (`_plot.py`: `frame_idx/total` vs
   `/(total-1)`) — imperceptible at 24fps.
2. Guard hyphenated param names in the CLI (`dest=p.name.replace('-','_')`) — no current
   param has a hyphen; purely defensive.
3. `pyreeler render --help` (no recipe) prints a terse argparse error — could short-circuit
   to show recipes.
4. `_plot.scatter_trail` recomputes the trajectory min/max every frame; move bounds into
   `recipe.prepare()` (negligible perf today).
5. Dedup the per-file `sys.path.insert` test boilerplate into a `conftest.py`.

## After Plan 2

The spec lists future directions beyond Version A: **Version B** (live in-terminal frame
preview — the image-to-ANSI playground) and **Version C** (guided browse → play flow), plus
more recipes (reaction-diffusion, pixel-sort) and a `film.toml` declarative format.
