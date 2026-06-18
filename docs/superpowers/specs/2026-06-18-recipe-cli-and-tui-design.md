# Recipe CLI + TUI (Version A) — Design

**Date:** 2026-06-18
**Status:** Approved (design) — ready for implementation plan
**Artifact:** a new top-level `pyreeler/` package (CLI + recipe registry + render engine + Textual TUI)

---

## Purpose

Give PyReeler a **non-AI** way to make films. Today the only author is an AI that
writes bespoke render code from an English brief. This adds a deterministic,
scriptable path: a CLI that renders parameterized "recipes," plus a polished Textual
TUI front-end for browsing recipes, tuning parameters, and watching a render.

It turns PyReeler from *"a director you talk to"* into *"an instrument you play"* —
and the CLI doubles as a tool the AI can also call.

## Scope: v1 = Core + Version A

Three TUI layers were considered (A: browse+launch, B: live preview playground,
C: guided). They share ~80% (recipe registry, render engine, CLI). **v1 builds the
shared core + Version A** (browse + launch) with full launch spectacle. Version B
(live image-to-ANSI preview) is a later upgrade that adds one pane to the TUI.

### Non-goals (YAGNI — explicitly out of v1)
- Live in-terminal frame preview (Version B) — the hard image-to-ANSI part.
- Guided multi-screen navigation (Version C).
- Wrapping the existing bespoke films (`interference`, `sentient-weather`, …) as
  recipes — those are large hand-tuned scripts, not clean parameterized effects.
- reaction-diffusion / pixel-sort recipes — drop in later as new registry entries.
- A declarative `film.toml` spec format (the possible "v2" config path).

## Architecture

A new top-level package, layered so the TUI is a front-end over a non-AI core:

```
pyreeler/
├── __init__.py
├── __main__.py        # enables `python -m pyreeler`
├── cli.py             # argparse: list · render · (no args -> launch TUI)
├── engine.py          # render_film(recipe, params, out, on_progress)
├── recipes/
│   ├── __init__.py    # Param + Recipe dataclasses, REGISTRY, register(), STANDARD_PARAMS
│   ├── lorenz.py      # wraps experimental.tools.attractors.generate_lorenz + render_frame_color
│   └── rossler.py     # wraps generate_rossler + render_frame_color
└── tui/
    ├── __init__.py
    ├── app.py         # Textual App: recipe ListView │ param form │ render pane
    ├── banner.py      # TerminalTextEffects phosphor "PYREELER" reveal
    └── styles.tcss    # phosphor theme (#39ff14 on #0d1117)
```

`recipes` + `engine` + `cli` are the non-AI core (numpy+pillow only). `tui/` is
optional and only imported when the TUI is launched.

## The recipe contract

```python
@dataclass(frozen=True)
class Param:
    name: str
    type: type                 # int | float | str
    default: Any
    min: Any = None            # numeric bound (inclusive), optional
    max: Any = None
    choices: tuple = ()        # for str enums (e.g. palette)
    help: str = ""

@dataclass(frozen=True)
class Recipe:
    name: str
    summary: str
    params: tuple[Param, ...]                              # recipe-specific knobs
    prepare: Callable[[dict], Any]                         # precompute shared data once (e.g. trajectory)
    make_frame: Callable[[Any, dict, int, int], "Image"]   # (prepared, params, frame_idx, total) -> PIL.Image
```

- **Standard params** (shared by every recipe, defined once as `STANDARD_PARAMS`):
  `duration` (float seconds, default 30, min 1), `fps` (int, default 24),
  `width` (int, default 854), `height` (int, default 480),
  `palette` (str choices: `phosphor`, `amber`, `ice`, `mono`; default `phosphor`).
- A recipe's full param set = `STANDARD_PARAMS + recipe.params`. The merged set
  drives both CLI flag generation and the TUI form.
- **Two-phase render so the expensive math runs once, not per frame:**
  - `prepare(params)` precomputes and returns shared, picklable data (the attractor
    trajectory array). Called once per render.
  - `make_frame(prepared, params, frame_idx, total)` is pure: given the precomputed
    data, resolved params, and the frame index, return one `PIL.Image` of size
    `(width, height)`. Time/rotation derives from `frame_idx / total`. Because it
    only reads `prepared` (a numpy array) + plain params, it is parallel-safe: the
    engine's worker closure pickles `prepared` cleanly.
- `REGISTRY: dict[str, Recipe]`; `register(recipe)` adds to it; `get(name)` raises
  `KeyError`-derived `UnknownRecipeError` (with close-match suggestions) on miss.

### v1 recipes
- **lorenz** — `prepare` calls `experimental.tools.attractors.generate_lorenz(...)`
  for the trajectory; `make_frame` plots the rotating trail with a palette-aware
  scatter (the recipe owns its plotting so it can honor `palette`, rather than using
  `render_frame_color`'s fixed velocity coloring). Params: `sigma` (default 10),
  `rho` (28), `beta` (2.667), `points` (10000), `trail` (400).
- **rossler** — same shape via `generate_rossler(...)`. Params: `a` (0.2),
  `b` (0.2), `c` (5.7), `points` (10000), `trail` (400).
Both need only numpy+pillow. The recipes reuse `attractors.rotate_points` for the
frame rotation.

## Render engine

```python
def render_film(recipe: Recipe, params: dict, out_path: Path,
                on_progress: Callable[[int, int], None] | None = None) -> Path:
    ...
```
- `total = round(params["duration"] * params["fps"])`.
- `prepared = recipe.prepare(params)` (precompute the trajectory once).
- `runtime = detect_render_runtime()` (from `templates/video/render_runtime.py`).
- Frames via `ordered_frame_map(range(total), frame_fn, runtime.workers)` where
  `frame_fn(i) = recipe.make_frame(prepared, params, i, total)`.
- Frames are encoded to `out_path` (mp4) via the existing `ffmpeg_utils` helpers /
  `runtime` encoder settings, piping frames to FFmpeg.
- `on_progress(done, total)` is invoked per completed frame (CLI: text/Rich bar;
  TUI: progress bar + Sparkline). When `on_progress` is None, render silently.
- **Encoder seam for testing:** the FFmpeg-writing step is a small internal function
  (`_encode_frames(frames, out_path, runtime, fps)`) so tests can stub it and verify
  the frame pipeline without FFmpeg installed.

## CLI

`python -m pyreeler` (and the `pyreeler` console entry, see Packaging):
- `pyreeler list` — table of recipes (name, summary). Plain text; uses Rich only if
  importable, else stdlib formatting.
- `pyreeler render <recipe> [--<param> <value> ...] [-o OUT]` — render headless.
  Flags are **generated from the merged param schema** (`--rho`, `--duration`, …),
  typed and range-checked. Default `OUT` = `<recipe>.mp4` in the current dir.
  Progress printed to stderr (Rich bar if available, else `frame i/total`).
- `pyreeler` (no subcommand) — launch the TUI (see below). If TUI deps are missing,
  print a friendly `pip install -r requirements-tui.txt` and exit 0.
- **Core CLI uses only the standard library** (`argparse`); Rich is an optional
  enhancement, never required for `list`/`render`.

## TUI (Version A — Textual)

1. **Launch spectacle:** `tui/banner.py` uses **TerminalTextEffects** to play the
   phosphor "PYREELER" reveal (scattered fragments assembling), then the Textual
   `App` mounts. Banner is skippable with `--no-banner` or any keypress.
2. **Layout** (`app.py`, themed by `styles.tcss`, phosphor `#39ff14` on `#0d1117`):
   - **Left:** recipe `ListView` (name + one-line summary).
   - **Right-top:** **param form** — `Input`/`Select` widgets auto-generated from the
     selected recipe's merged param schema, pre-filled with defaults.
   - **Right-bottom:** **render pane** — Rich/Textual `ProgressBar`, a braille
     spinner, an ETA label, and a **Sparkline** widget fed frames/sec.
3. **Render** runs in a Textual **worker thread**; `on_progress` updates the bar,
   ETA, and Sparkline so the UI stays responsive. On completion: show the output
   path and a brief "done" flourish.
4. **Keys:** arrows/tab to navigate, `enter`/`r` to render, `q` to quit.

## Dependencies

- **Core (unchanged):** numpy, pillow (`requirements.txt`). `list`/`render` work
  with these alone (plus FFmpeg on PATH for actual encoding).
- **TUI (new, optional):** `requirements-tui.txt` → `textual`, `rich`,
  `terminaltexteffects`. Imported lazily; absence yields an install hint, not a crash.

## Packaging / entry point

- Runnable immediately as `python -m pyreeler` (via `pyreeler/__main__.py`), needing
  no install.
- Add a minimal `pyproject.toml` declaring a `pyreeler` console-script entry point
  (`pyreeler = "pyreeler.cli:main"`) and the core dependencies, so
  `pip install -e .` yields the `pyreeler` command. The `[project.optional-
  dependencies]` table exposes a `tui` extra mirroring `requirements-tui.txt`.

## Error handling

- Unknown recipe → `UnknownRecipeError`; CLI prints it with close-match suggestions
  and exits non-zero.
- Param out of `min`/`max` or not in `choices` → clear validation message naming the
  param and allowed range/values; exit non-zero.
- TUI launched without its extras → friendly `pip install -r requirements-tui.txt`
  message; exit 0.
- FFmpeg missing → surfaced via the existing `render_runtime`/`ffmpeg_utils`
  detection message.

## Testing (TDD, red -> green)

New tests live in `tests/` and are wired into `pytest.ini`. All TUI- and
FFmpeg-dependent tests **skip gracefully** when those deps are absent, so the
existing CI (numpy+pillow+pytest, no FFmpeg, no Textual) stays green.

1. **Registry:** `register`/`get` round-trip; `STANDARD_PARAMS` merged into a
   recipe's full schema; unknown name raises `UnknownRecipeError` with suggestions.
2. **Recipes:** with `prepared = recipe.prepare(params)`, `make_frame(prepared,
   params, 0, total)` returns a `PIL.Image` of exactly `(width, height)`; two
   distinct frame indices produce different images (motion). No FFmpeg needed.
3. **Param validation:** out-of-range numeric and bad `choices` value raise the
   documented validation error; in-range passes.
4. **Engine:** with `_encode_frames` stubbed, `render_film` iterates the right number
   of frames (`duration*fps`), calls `on_progress` that many times, and passes
   correctly-sized frames. A separate end-to-end mp4 test is marked
   `skipif` no FFmpeg.
5. **CLI:** `render` arg parsing maps flags to a correct, type-coerced params dict
   (engine stubbed); `list` lists both recipes; unknown recipe exits non-zero.
6. **TUI (skip-if-no-textual):** Textual `run_test()` pilot — app mounts, recipe
   list populates with both recipes, selecting a recipe builds a form with the
   merged params. `banner.py` renders to a string without a TTY without error.

## Future directions (noted, not built)

- Version B: live image-to-ANSI preview pane (half-block/braille + truecolor).
- Version C: guided browse -> play screen flow (Textual screens).
- More recipes (reaction-diffusion, pixel-sort, interference) via the registry.
- `film.toml` declarative spec format feeding the same engine.
- `pyreeler sweep <recipe> --param a:b:n` → contact-sheet via the existing tool.
