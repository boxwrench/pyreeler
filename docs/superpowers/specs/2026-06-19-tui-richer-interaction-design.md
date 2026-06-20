# TUI Richer Interaction — Design

**Date:** 2026-06-19
**Status:** Approved, ready for implementation plan
**Component:** `pyreeler/tui/` (Textual app)

## Goal

Make the existing PyReeler TUI faster and more discoverable to operate, without
changing its phosphor-CRT character or its layout. Three additive features:

1. **Stepper / cycler param controls** — numeric params get `[-]`/`[+]` steppers
   (typing still allowed); enum params (e.g. `palette`) get a `‹ value ›` cycler
   that cannot hold an invalid value.
2. **Recipe search** — a filter box above the recipe list, narrowing it by
   case-insensitive substring as you type.
3. **Play/open result** — after a render completes, a `Play` button and `p` key
   open the rendered `.mp4` in the system player.

The current TUI is liked as-is, so this is strictly additive. Explicitly **out of
scope** (stays on the roadmap): live in-terminal frame preview, palette-matched
theming, and reset-to-defaults.

## Current baseline (what exists)

- `pyreeler/tui/app.py` — `PyReelerApp(App)`: sidebar `ListView` of recipes │
  detail pane (`#summary` Static, `#form` Vertical of Label+Input per param,
  `Render` Button, `ProgressBar`, `Sparkline`, `#status` Static). Render runs on
  a `@work(thread=True)` worker; progress marshaled back via `call_from_thread`.
  Output path comes from `pyreeler.output.next_output_path` (~/Videos, no clobber).
- `_load_recipe(name)` rebuilds the form (one Label + `Input#param-{name}` per
  merged param). `_collect_params()` reads each `Input#param-{name}` and calls
  `resolve_params`.
- `pyreeler/recipes/base.py` — `Param(name, type, default, min, max, choices, help)`
  (frozen). `STANDARD_PARAMS`: duration(float), fps(int), width(int), height(int),
  palette(str, choices=PALETTES). Recipe params span small floats (`a=0.2`,
  `rho=28.0`) to large ints (`points=10000`, `trail=10000`).
- `resolve_params` coerces via `p.type`, then enforces `choices`/`min`/`max`.

## Schema change: `Param.step`

Add one optional field to `Param`:

```python
step: Any = None   # TUI stepper increment hint; ignored by CLI and validation
```

Rationale: param magnitudes range from `0.2` to `10000`, so a single fixed
increment is useless. `step` lets a recipe declare an exact increment when it
matters; when `None`, the TUI derives a magnitude-aware "nice" step.

**Derived step (when `Param.step is None`)**, computed in the TUI, not the schema:

- Base = `0.05 * abs(default)` (5% of the default value).
- Round to 1 significant figure (so `1.4 → 1`, `0.014 → 0.01`, `530 → 500`).
- Floor: ints use `max(1, round(base_1sf))`; floats use `max(base_1sf, tiny)`
  where `tiny` is a small positive (e.g. `1e-9`) to avoid a zero step.
- If `default == 0`, fall back to `1` for ints and `0.1` for floats.

Explicit steps set in `STANDARD_PARAMS`: `duration` → `step=1.0`, `fps` →
`step=1`. `width`/`height` and all recipe params derive (gives `width` ≈ 40,
`points`/`trail` ≈ 500, `rho` ≈ 1, `a` ≈ 0.01).

The derived-step function lives in `pyreeler/tui/fields.py` (see below) as a pure,
unit-testable helper `effective_step(param) -> int | float`.

## Component design

### `pyreeler/tui/fields.py` (new) — the param controls

A small module of custom widgets, each a `ParamField` exposing a uniform
interface so `_collect_params` stays type-agnostic.

```python
class ParamField(Widget):
    """Base: renders one Param and exposes its current value as a string."""
    @property
    def param_value(self) -> str: ...   # raw string handed to resolve_params
```

Three concrete fields, chosen in a factory `make_field(param) -> ParamField`:

- **`NumberField`** — used when `param.type in (int, float)` and `not param.choices`.
  Layout: `Label(name)` · `Button("-")` · `Input(value=str(default),
  id=f"param-{name}")` · `Button("+")`. The `-`/`+` buttons read the current
  Input value, parse it (best-effort; on parse failure they reset to `default`),
  apply `±effective_step(param)`, clamp to `param.min`/`param.max` when set, and
  write it back. Float values are formatted without trailing-zero noise (e.g.
  `28` not `28.0000001`). `param_value` returns the Input's current text, so the
  user can also type freely (including out-of-range values that `resolve_params`
  will reject with the usual error path). Keeps `id=param-{name}` on the inner
  Input so existing query patterns and numeric tests continue to work.

- **`ChoiceField`** — used when `param.choices` is non-empty. Layout:
  `Label(name)` · `Button("‹")` · `Static(current, id=f"choice-{name}")` ·
  `Button("›")`. Buttons cycle through `param.choices` (wrapping). The current
  value starts at `param.default`. `param_value` returns the current choice. By
  construction it can never produce a value outside `choices`.

- **`TextField`** — fallback for free strings (`type is str`, no choices) and
  optional params (`default is None`). Just `Label(name)` + `Input(...,
  id=f"param-{name}")`, i.e. today's behavior. `param_value` returns the text.

Each field is given a stable widget id `field-{name}` on its container so the app
can query it generically.

### `pyreeler/tui/app.py` changes

- **Form build (`_load_recipe`).** Replace the Label+Input loop with
  `await form.mount(*[make_field(p) for p in merged_params(recipe)])`. The
  awaited single mount (already adopted) stays.
- **`_collect_params`.** Iterate `merged_params(recipe)`; for each, read
  `self.query_one(f"#field-{p.name}", ParamField).param_value` into `overrides`
  (skipping blanks as today), then `resolve_params(recipe, overrides)`. No change
  to validation or error surfacing.
- **Search.** Add `Input(id="recipe-search", placeholder="filter…")` above the
  `ListView` in `compose`. Handle `Input.Changed` for `#recipe-search`: recompute
  the visible recipes (`name`/`summary` case-insensitive substring) and rebuild
  the `ListView` children. Selection: if the current recipe is still visible keep
  it; else select the first visible (and load it); if none match, leave the detail
  pane on the last loaded recipe and show an empty list. `_load_recipe` must
  tolerate being called only when a match exists.
- **Play/open.** Track `self._last_output: Path | None`. Set it in `_on_done`,
  which also enables the `Play` button. Add `Button("Play", id="play-btn",
  disabled=True)` to the detail pane. `on_button_pressed` handles `play-btn` →
  `action_play()`. `action_play()` no-ops with a status hint when
  `_last_output` is unset or missing.
- **Bindings.** Add `Binding("p", "play", "Play")` and
  `Binding("slash", "search", "Search")` (focuses `#recipe-search`). Existing
  `escape → quit` stays.

### `pyreeler/tui/player.py` (new) — open in system player

```python
def open_in_player(path: Path) -> None:
    """Open `path` in the OS default player. Raises OSError if no opener works."""
```

Platform selection: Windows → `os.startfile(path)`; macOS (`sys.platform ==
"darwin"`) → `subprocess.Popen(["open", path])`; otherwise → `["xdg-open", path]`.
Launch detached; do not block the UI thread. Callers (the app) catch failures and
write a status message rather than crashing.

## Data flow

```
key/click ──▶ NumberField/ChoiceField mutate their own value
recipe-search Changed ──▶ rebuild ListView (filtered)
Render ──▶ _collect_params() reads each ParamField.param_value
        ──▶ resolve_params() (unchanged) ──▶ worker render ──▶ _on_done
_on_done ──▶ set _last_output, enable Play
p / Play ──▶ open_in_player(_last_output)  (errors ──▶ #status)
```

## Error handling

- Bad typed numeric value → caught by `resolve_params` → existing `#status`
  error message (unchanged path). Steppers themselves never raise: a parse
  failure resets the field to the param default.
- Stepper clamping respects `min`/`max`; params with no bound are unbounded in
  that direction.
- `open_in_player` failure (no opener, missing file) → `OSError` caught in
  `action_play` → `#status` shows `cannot open <path>: <reason>`; the app keeps
  running.
- Empty/`no-match` search → empty list, detail pane unchanged, no exception.

## Testing

Unit (no Textual event loop required where possible):

- `effective_step`: magnitude-aware results for representative params
  (`rho`→~1, `points`→~500, `a`→~0.01, `fps` explicit 1), zero-default fallback.
- `ChoiceField` cycling wraps and never yields a non-`choices` value.
- `NumberField` stepping increments by `effective_step`, clamps to bounds, and
  recovers from an unparseable current value.
- `open_in_player` selects the correct command per `sys.platform` (monkeypatched
  `subprocess.Popen`/`os.startfile`; assert args; never actually launches).

App-level (Textual `run_test` pilot, importorskip textual):

- Selecting a recipe builds the right field type per param (NumberField for
  `rho`, ChoiceField for `palette`, etc.).
- `_collect_params` round-trips values from all three field types into a valid
  resolved dict.
- A bad typed numeric still surfaces an error in `#status`.
- Typing in `#recipe-search` filters the `ListView`.
- After a (mocked) render, `_last_output` is set and the `Play` button enables;
  `action_play` calls `open_in_player` with that path (mocked).

Existing tests updated: the two that assumed `#param-palette` is an `Input`
move to the `ChoiceField` API; numeric `#param-rho` Input assertions are
preserved by keeping that id on `NumberField`'s inner Input.

Gates that must stay green: full `pytest`, `sync.py --check`,
`graduation_check.py`.

## Files touched

- `pyreeler/recipes/base.py` — add `Param.step` (+ explicit steps on
  `duration`/`fps`).
- `pyreeler/tui/fields.py` — **new**: `ParamField`, `NumberField`, `ChoiceField`,
  `TextField`, `make_field`, `effective_step`.
- `pyreeler/tui/player.py` — **new**: `open_in_player`.
- `pyreeler/tui/app.py` — form build via `make_field`, `_collect_params` via
  `param_value`, search box + filtering, Play button + `p`/`/` bindings,
  `_last_output` tracking.
- `pyreeler/tui/styles.tcss` — styles for the new field rows, stepper buttons,
  cycler, and the search input (keep the existing palette).
- `pyproject.toml` — no change (new modules live under the existing
  `pyreeler.tui` package).
- Tests — new `tests/test_tui_fields.py`, `tests/test_tui_player.py`; updates to
  `tests/test_tui_app.py`.

## Out of scope (roadmap, not now)

- Live in-terminal frame preview (image→ANSI) — roadmap "Version B".
- Palette-matched theming / scanline polish.
- Reset-to-defaults, render-history dashboard, ETA/fps telemetry.
