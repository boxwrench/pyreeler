# PyReeler CLI + TUI — Pickup / Resume Doc

**Updated:** 2026-06-18
**Purpose:** Resume cleanly after clearing context. Everything needed to continue is here or linked.

---

## TL;DR state

- **Plan 1 (non-AI CLI core): DONE and merged to `main`** (merge commit on `origin/main`,
  branch `feat/recipe-cli` deleted). `pyreeler list` / `pyreeler render` work and produce
  real mp4s. 76 tests pass; all three CI gates green.
- **Plan 2 (Textual TUI): WRITTEN, NOT STARTED.** Ready to implement.

## How to resume (commands)

```bash
cd ~/Desktop/github/pyreeler
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
- `pyproject.toml` (console entry `pyreeler` + `tui` extra), `requirements-tui.txt`,
  `pyreeler/tui/__init__.py` placeholder.

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
