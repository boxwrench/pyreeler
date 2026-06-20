# TUI Richer Interaction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add stepper/cycler param controls, recipe search, and open-in-player to the PyReeler Textual TUI, without changing its layout or phosphor aesthetic.

**Architecture:** A new `pyreeler/tui/fields.py` provides per-param-kind control widgets (`NumberField`, `ChoiceField`, `TextField`) behind a uniform `ParamField.param_value` interface and a `make_field` factory; a new `pyreeler/tui/player.py` opens files in the OS player. `app.py` builds its form via `make_field`, gains a search box, and a Play button. One schema field (`Param.step`) is added as a TUI-only hint.

**Tech Stack:** Python 3.10+, Textual (`textual>=0.60`), pytest. Pure stdlib for the player.

## Global Constraints

- Python 3.10+; core deps numpy + pillow only — TUI deps (`textual`, `rich`, `terminaltexteffects`) are an optional extra. TUI tests use `pytest.importorskip("textual")` so core CI stays green.
- `Param.step` must be ignored by the CLI and by `resolve_params` — it is a TUI hint only.
- `resolve_params` (in `pyreeler/recipes/params.py`) is the single validation path; do not duplicate coercion/bounds logic. Steppers may produce out-of-range typed text; `resolve_params` remains the gate.
- Keep the inner numeric Input's id as `param-{name}` so existing query patterns hold.
- Render runs on a `@work(thread=True)` worker; only touch widgets from the UI thread via `call_from_thread` (already established in `app.py`).
- Gates that must stay green after every task: `python3 -m pytest -q`, `python3 sync.py --check`, `python3 graduation_check.py`.
- Commit message trailer: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.

## File Structure

- `pyreeler/recipes/base.py` — **modify**: add `Param.step`; set explicit steps on `duration`/`fps`.
- `pyreeler/tui/fields.py` — **create**: `effective_step`, `stepped_value`, `_format`, `ParamField`, `TextField`, `ChoiceField`, `NumberField`, `make_field`.
- `pyreeler/tui/player.py` — **create**: `open_in_player`.
- `pyreeler/tui/app.py` — **modify**: form via `make_field`, `_collect_params` via `param_value`, search box + filter, Play button + `_last_output`, `p`/`/` bindings.
- `pyreeler/tui/styles.tcss` — **modify**: rows for fields/steppers/cycler/search.
- `tests/test_tui_fields.py` — **create**.
- `tests/test_tui_player.py` — **create**.
- `tests/test_tui_app.py` — **modify**: update field-API assertions; add search + play tests.

---

### Task 1: `Param.step` schema + `effective_step`

**Files:**
- Modify: `pyreeler/recipes/base.py`
- Create: `pyreeler/tui/fields.py`
- Test: `tests/test_tui_fields.py`

**Interfaces:**
- Consumes: `Param` from `pyreeler.recipes.base`.
- Produces: `Param.step` field (default `None`); `effective_step(param) -> int | float`; `_round_1sf(x) -> float` (module-private).

- [ ] **Step 1: Write the failing test**

Create `tests/test_tui_fields.py`:

```python
"""Unit tests for the TUI param-control helpers and widgets."""
import sys
from pathlib import Path

import pytest

pytest.importorskip("textual")

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from pyreeler.recipes.base import Param  # noqa: E402
from pyreeler.tui import fields  # noqa: E402


def test_effective_step_uses_explicit_step_when_set():
    p = Param("fps", int, 24, step=1)
    assert fields.effective_step(p) == 1


def test_effective_step_is_magnitude_aware_for_ints():
    assert fields.effective_step(Param("points", int, 10000)) == 500
    assert fields.effective_step(Param("width", int, 854)) == 40


def test_effective_step_is_magnitude_aware_for_floats():
    assert fields.effective_step(Param("rho", float, 28.0)) == pytest.approx(1.0)
    assert fields.effective_step(Param("a", float, 0.2)) == pytest.approx(0.01)


def test_effective_step_zero_default_falls_back():
    assert fields.effective_step(Param("z", int, 0)) == 1
    assert fields.effective_step(Param("z", float, 0.0)) == pytest.approx(0.1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_tui_fields.py -q`
Expected: FAIL — `Param.__init__` has no `step`, and `pyreeler.tui.fields` does not exist (ImportError/TypeError).

- [ ] **Step 3: Add `Param.step` and explicit steps**

In `pyreeler/recipes/base.py`, add the field to the `Param` dataclass (after `choices`, before `help` is fine; keep `help` last for call-site compatibility):

```python
@dataclass(frozen=True)
class Param:
    """One tunable parameter: its type, default, and optional bounds/choices."""

    name: str
    type: type
    default: Any
    min: Any = None
    max: Any = None
    choices: tuple = ()
    help: str = ""
    step: Any = None  # TUI stepper increment hint; ignored by CLI and validation
```

Set explicit steps in `STANDARD_PARAMS` where 1 is obviously right:

```python
STANDARD_PARAMS = (
    Param("duration", float, 30.0, min=1, help="film length in seconds", step=1.0),
    Param("fps", int, 24, min=1, help="frames per second", step=1),
    Param("width", int, 854, min=16, help="frame width in pixels"),
    Param("height", int, 480, min=16, help="frame height in pixels"),
    Param("palette", str, "phosphor", choices=tuple(PALETTES), help="color palette"),
)
```

- [ ] **Step 4: Create `fields.py` with the step helpers**

Create `pyreeler/tui/fields.py`:

```python
"""Param-control widgets for the TUI form, plus the pure stepper helpers.

Each Param renders as a ParamField exposing a uniform `param_value` string that
feeds the existing `resolve_params` validation. Numeric params get +/- steppers,
enum params get a cycler, free strings keep a plain Input.
"""
from __future__ import annotations

import math

from ..recipes.base import Param


def _round_1sf(x: float) -> float:
    """Round to one significant figure (1.4 -> 1, 0.014 -> 0.01, 530 -> 500)."""
    if x == 0:
        return 0.0
    exp = math.floor(math.log10(abs(x)))
    factor = 10 ** exp
    return round(x / factor) * factor


def effective_step(param: Param):
    """The stepper increment for `param`: its explicit `step`, else a
    magnitude-aware ~5%-of-default value rounded to one significant figure."""
    if param.step is not None:
        return param.step
    default = param.default
    is_int = param.type is int
    if not default:  # 0, 0.0, or None
        return 1 if is_int else 0.1
    nice = _round_1sf(0.05 * abs(default))
    if is_int:
        return max(1, int(round(nice)))
    return max(nice, 1e-9)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python3 -m pytest tests/test_tui_fields.py -q`
Expected: PASS (4 passed).

- [ ] **Step 6: Verify gates**

Run: `python3 -m pytest -q && python3 sync.py --check && python3 graduation_check.py`
Expected: all pass; existing CLI/recipe tests unaffected (the new `step` field is keyword-only with a default).

- [ ] **Step 7: Commit**

```bash
git add pyreeler/recipes/base.py pyreeler/tui/fields.py tests/test_tui_fields.py
git commit -m "$(cat <<'EOF'
feat(tui): Param.step hint + magnitude-aware effective_step

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: `stepped_value` + `_format`

**Files:**
- Modify: `pyreeler/tui/fields.py`
- Test: `tests/test_tui_fields.py`

**Interfaces:**
- Consumes: `effective_step`, `Param`.
- Produces: `stepped_value(current: str, param: Param, delta: int) -> str`; `_format(value) -> str`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_tui_fields.py`:

```python
def test_format_trims_float_noise():
    assert fields._format(28.0) == "28"
    assert fields._format(0.01) == "0.01"
    assert fields._format(10) == "10"


def test_stepped_value_increments_by_effective_step():
    p = Param("rho", float, 28.0)
    assert fields.stepped_value("28", p, +1) == "29"
    assert fields.stepped_value("28", p, -1) == "27"


def test_stepped_value_clamps_to_bounds():
    p = Param("duration", float, 30.0, min=1, step=1.0)
    assert fields.stepped_value("1", p, -1) == "1"  # min clamp


def test_stepped_value_recovers_from_unparseable_current():
    p = Param("fps", int, 24, min=1, step=1)
    # garbage current resets to default (24) then steps up
    assert fields.stepped_value("abc", p, +1) == "25"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_tui_fields.py -k "stepped_value or format" -q`
Expected: FAIL — `_format`/`stepped_value` not defined.

- [ ] **Step 3: Implement the helpers**

Append to `pyreeler/tui/fields.py` (after `effective_step`):

```python
def _format(value) -> str:
    """Render a number without trailing-zero noise (28.0 -> '28')."""
    if isinstance(value, float):
        return f"{value:.6f}".rstrip("0").rstrip(".") or "0"
    return str(value)


def stepped_value(current: str, param: Param, delta: int) -> str:
    """Apply `delta * effective_step` to `current`, clamp to bounds, format.

    `delta` is +1 or -1. An unparseable `current` resets to the param default
    before stepping, so the control can never get wedged.
    """
    step = effective_step(param)
    try:
        value = param.type(current)
    except (TypeError, ValueError):
        value = param.default
    value = value + delta * step
    if param.min is not None and value < param.min:
        value = param.min
    if param.max is not None and value > param.max:
        value = param.max
    return _format(param.type(value))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_tui_fields.py -q`
Expected: PASS (all fields tests green).

- [ ] **Step 5: Commit**

```bash
git add pyreeler/tui/fields.py tests/test_tui_fields.py
git commit -m "$(cat <<'EOF'
feat(tui): stepped_value clamp/format helper for number controls

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: `ParamField` widgets + `make_field`

**Files:**
- Modify: `pyreeler/tui/fields.py`
- Test: `tests/test_tui_fields.py`

**Interfaces:**
- Consumes: `stepped_value`, `_format`, `effective_step`, `Param`; Textual `Horizontal`, `Button`, `Input`, `Label`, `Static`.
- Produces: `ParamField(Horizontal)` with `.param_value -> str` and id `field-{name}`; `TextField`, `ChoiceField` (with `.cycle(delta)`), `NumberField` (with `._bump(delta)`); `make_field(param) -> ParamField`. `NumberField`/`TextField` keep an inner `Input` with id `param-{name}`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_tui_fields.py`:

```python
def test_make_field_picks_the_right_widget():
    assert isinstance(fields.make_field(Param("palette", str, "phosphor",
                                              choices=("phosphor", "amber"))),
                      fields.ChoiceField)
    assert isinstance(fields.make_field(Param("rho", float, 28.0)),
                      fields.NumberField)
    assert isinstance(fields.make_field(Param("label", str, "hi")),
                      fields.TextField)


def test_choice_field_cycles_and_never_leaves_choices():
    p = Param("palette", str, "amber", choices=("phosphor", "amber", "ice"))
    f = fields.ChoiceField(p)
    assert f.param_value == "amber"
    f.cycle(1)
    assert f.param_value == "ice"
    f.cycle(1)  # wraps
    assert f.param_value == "phosphor"
    f.cycle(-1)  # wraps backward
    assert f.param_value == "ice"
    assert f.param_value in p.choices


def test_number_field_bump_steps_and_clamps():
    # Textual's Input cannot exist outside an app, so mount one NumberField in a
    # tiny harness app and drive it through a pilot.
    import asyncio
    from textual.app import App, ComposeResult
    from textual.widgets import Input

    class _Harness(App):
        def compose(self) -> ComposeResult:
            yield fields.NumberField(Param("duration", float, 30.0, min=1, step=1.0))

    async def body():
        app = _Harness()
        async with app.run_test() as pilot:
            await pilot.pause()
            field = app.query_one(fields.NumberField)
            assert field.param_value == "30"
            field._bump(-1)
            assert field.param_value == "29"
            app.query_one(Input).value = "1"
            field._bump(-1)  # clamped at min
            assert field.param_value == "1"

    asyncio.run(body())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_tui_fields.py -k "make_field or choice_field or number_field" -q`
Expected: FAIL — `ParamField`/`NumberField`/`ChoiceField`/`make_field` not defined.

- [ ] **Step 3: Implement the widgets**

Add imports at the top of `pyreeler/tui/fields.py` (below `import math`):

```python
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Input, Label, Static
```

Append the widget classes and factory to `pyreeler/tui/fields.py`:

```python
class ParamField(Horizontal):
    """One param row. Subclasses expose the current value as a string."""

    def __init__(self, param: Param) -> None:
        super().__init__(id=f"field-{param.name}", classes="param-field")
        self.param = param

    @property
    def param_value(self) -> str:
        raise NotImplementedError


class TextField(ParamField):
    """Free-text / optional param: a plain Input (today's behavior).

    Note: Textual's Input cannot be constructed outside an app, so it is created
    in compose() and read through `query_one(Input)` rather than cached.
    """

    def __init__(self, param: Param) -> None:
        super().__init__(param)
        self._default = "" if param.default is None else str(param.default)

    def compose(self) -> ComposeResult:
        yield Label(self.param.name, classes="param-label")
        yield Input(value=self._default, id=f"param-{self.param.name}")

    @property
    def param_value(self) -> str:
        return self.query_one(Input).value


class ChoiceField(ParamField):
    """Enum param: a `< value >` cycler that can never hold an invalid value."""

    def __init__(self, param: Param) -> None:
        super().__init__(param)
        self._choices = list(param.choices)
        try:
            self._index = self._choices.index(param.default)
        except ValueError:
            self._index = 0
        self._value = Static(self.param_value, id=f"choice-{param.name}",
                             classes="choice-value")

    @property
    def param_value(self) -> str:
        return str(self._choices[self._index])

    def cycle(self, delta: int) -> None:
        self._index = (self._index + delta) % len(self._choices)
        if self.is_mounted:
            self._value.update(self.param_value)

    def compose(self) -> ComposeResult:
        yield Label(self.param.name, classes="param-label")
        yield Button("‹", id=f"prev-{self.param.name}", classes="cycle-btn")
        yield self._value
        yield Button("›", id=f"next-{self.param.name}", classes="cycle-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == f"prev-{self.param.name}":
            self.cycle(-1)
            event.stop()
        elif event.button.id == f"next-{self.param.name}":
            self.cycle(1)
            event.stop()


class NumberField(ParamField):
    """Numeric param: [-] Input [+]. Typing is still allowed.

    Input is created in compose() (Textual forbids it outside an app) and read
    through `query_one(Input)`, so the displayed value is always the source of
    truth — no cached copy to drift.
    """

    def __init__(self, param: Param) -> None:
        super().__init__(param)
        self._default = _format(param.default)

    def compose(self) -> ComposeResult:
        yield Label(self.param.name, classes="param-label")
        yield Button("-", id=f"dec-{self.param.name}", classes="step-btn")
        yield Input(value=self._default, id=f"param-{self.param.name}")
        yield Button("+", id=f"inc-{self.param.name}", classes="step-btn")

    @property
    def param_value(self) -> str:
        return self.query_one(Input).value

    def _bump(self, delta: int) -> None:
        inp = self.query_one(Input)
        inp.value = stepped_value(inp.value, self.param, delta)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == f"dec-{self.param.name}":
            self._bump(-1)
            event.stop()
        elif event.button.id == f"inc-{self.param.name}":
            self._bump(1)
            event.stop()


def make_field(param: Param) -> ParamField:
    """Pick the control widget for a param: cycler for enums, stepper for
    numbers, plain input otherwise."""
    if param.choices:
        return ChoiceField(param)
    if param.type in (int, float) and param.default is not None:
        return NumberField(param)
    return TextField(param)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_tui_fields.py -q`
Expected: PASS (all fields tests green).

- [ ] **Step 5: Verify gates**

Run: `python3 -m pytest -q && python3 sync.py --check && python3 graduation_check.py`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add pyreeler/tui/fields.py tests/test_tui_fields.py
git commit -m "$(cat <<'EOF'
feat(tui): ParamField widgets (number stepper, choice cycler, text) + make_field

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: `open_in_player`

**Files:**
- Create: `pyreeler/tui/player.py`
- Test: `tests/test_tui_player.py`

**Interfaces:**
- Consumes: stdlib `os`, `subprocess`, `sys`, `pathlib.Path`.
- Produces: `open_in_player(path: Path) -> None` (raises `OSError` if no opener works). No Textual dependency.

- [ ] **Step 1: Write the failing test**

Create `tests/test_tui_player.py`:

```python
"""Tests for opening a rendered file in the OS player (no Textual needed)."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from pyreeler.tui import player  # noqa: E402


def test_linux_uses_xdg_open(monkeypatch):
    calls = {}
    monkeypatch.setattr(player.sys, "platform", "linux")
    monkeypatch.setattr(player.subprocess, "Popen",
                        lambda args, **kw: calls.update(args=args))
    player.open_in_player(Path("/tmp/x.mp4"))
    assert calls["args"][0] == "xdg-open"
    assert calls["args"][1] == "/tmp/x.mp4"


def test_macos_uses_open(monkeypatch):
    calls = {}
    monkeypatch.setattr(player.sys, "platform", "darwin")
    monkeypatch.setattr(player.subprocess, "Popen",
                        lambda args, **kw: calls.update(args=args))
    player.open_in_player(Path("/tmp/x.mp4"))
    assert calls["args"][0] == "open"


def test_windows_uses_startfile(monkeypatch):
    calls = {}
    monkeypatch.setattr(player.sys, "platform", "win32")
    monkeypatch.setattr(player.os, "startfile",
                        lambda p: calls.update(path=p), raising=False)
    player.open_in_player(Path("C:/tmp/x.mp4"))
    assert "x.mp4" in calls["path"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_tui_player.py -q`
Expected: FAIL — `pyreeler.tui.player` does not exist.

- [ ] **Step 3: Implement the player**

Create `pyreeler/tui/player.py`:

```python
"""Open a rendered file in the OS default player. Pure stdlib, no Textual."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def open_in_player(path: Path) -> None:
    """Open `path` in the system default player.

    Uses `os.startfile` on Windows, `open` on macOS, `xdg-open` elsewhere.
    Launches detached so it never blocks the UI thread. Raises `OSError` if the
    opener is missing or fails.
    """
    path = Path(path)
    if sys.platform == "win32":
        os.startfile(str(path))  # type: ignore[attr-defined]  # noqa: S606
        return
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.Popen([opener, str(path)],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_tui_player.py -q`
Expected: PASS (3 passed). Note: this file does NOT importorskip textual — it runs in core CI.

- [ ] **Step 5: Commit**

```bash
git add pyreeler/tui/player.py tests/test_tui_player.py
git commit -m "$(cat <<'EOF'
feat(tui): open_in_player — cross-platform open of a rendered file

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: Wire fields into the app form

**Files:**
- Modify: `pyreeler/tui/app.py`
- Modify: `pyreeler/tui/styles.tcss`
- Test: `tests/test_tui_app.py`

**Interfaces:**
- Consumes: `make_field`, `ParamField` from `pyreeler.tui.fields`.
- Produces: form built from `ParamField`s; `_collect_params` reads each `#field-{name}` `ParamField.param_value`.

- [ ] **Step 1: Update existing app tests to the field API**

In `tests/test_tui_app.py`, replace the body of `test_selecting_recipe_populates_summary_and_form` with a field-count + field-type check (palette is no longer an `Input`; rho default now formats as `"28"`):

```python
def test_selecting_recipe_populates_summary_and_form():
    async def body():
        app = PyReelerApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            from textual.widgets import Input, Static
            from pyreeler.tui.fields import ParamField, ChoiceField
            assert app.query_one("#summary", Static).content
            assert "output:" in str(app.query_one("#status", Static).content)
            from pyreeler.recipes import get, merged_params
            recipe = get(app._current_name)
            # one ParamField per merged param
            assert len(app.query(ParamField)) == len(merged_params(recipe))
            # rho is a numeric field whose inner Input keeps id param-rho
            rho = app.query_one("#param-rho", Input)
            assert rho.value == "28"
            # palette is a cycler, not an Input
            assert isinstance(app.query_one("#field-palette", ParamField), ChoiceField)
    asyncio.run(body())
```

Replace `test_bad_param_shows_error_in_status` (palette can no longer be set to an invalid string — use a bad numeric instead):

```python
def test_bad_numeric_param_shows_error_in_status():
    async def body():
        app = PyReelerApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            from textual.widgets import Input, Static
            app.query_one("#param-rho", Input).value = "not-a-number"
            app._start_render()  # invalid -> should set status, not raise
            await pilot.pause()
            status = str(app.query_one("#status", Static).content)
            assert "rho" in status
    asyncio.run(body())
```

`test_collect_params_reads_form_values` is unchanged — it sets `#param-rho`/`#param-duration` Inputs, which still exist inside `NumberField`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_tui_app.py -q`
Expected: FAIL — form still mounts raw `Label`+`Input`; `#field-palette`/`ParamField` not present; rho value is `"28.0"`.

- [ ] **Step 3: Build the form from fields**

In `pyreeler/tui/app.py`, add the import near the other local imports:

```python
from ..output import next_output_path
from ..recipes import get, list_recipes, merged_params, resolve_params, ParamError
from .fields import ParamField, make_field
```

Replace the form-building block in `_load_recipe` (the `widgets`/mount loop) with:

```python
        form = self.query_one("#form", Vertical)
        await form.remove_children()
        fields = [make_field(p) for p in merged_params(recipe)]
        if fields:
            await form.mount(*fields)
        self.query_one("#status", Static).update(
            f"output: {self._output_path(recipe.name)}"
        )
```

Replace `_collect_params` to read `param_value`:

```python
    def _collect_params(self) -> dict:
        """Read the form fields into a validated params dict."""
        recipe = get(self._current_name)
        overrides = {}
        for p in merged_params(recipe):
            value = self.query_one(f"#field-{p.name}", ParamField).param_value.strip()
            if value:
                overrides[p.name] = value
        return resolve_params(recipe, overrides)
```

- [ ] **Step 4: Add field styles**

Append to `pyreeler/tui/styles.tcss`:

```css
.param-field {
    height: auto;
    align: left middle;
}

.param-label {
    width: 10;
    color: #d6ffcc;
}

.step-btn, .cycle-btn {
    width: 3;
    min-width: 3;
    background: #1f8f3a;
    color: #d6ffcc;
}

.choice-value {
    width: 1fr;
    color: #d6ffcc;
}

.param-field Input {
    width: 1fr;
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_tui_app.py tests/test_tui_fields.py -q`
Expected: PASS.

- [ ] **Step 6: Verify gates**

Run: `python3 -m pytest -q && python3 sync.py --check && python3 graduation_check.py`
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add pyreeler/tui/app.py pyreeler/tui/styles.tcss tests/test_tui_app.py
git commit -m "$(cat <<'EOF'
feat(tui): build the param form from stepper/cycler fields

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: Recipe search/filter

**Files:**
- Modify: `pyreeler/tui/app.py`
- Modify: `pyreeler/tui/styles.tcss`
- Test: `tests/test_tui_app.py`

**Interfaces:**
- Consumes: `list_recipes`, `RECIPE_PREFIX`.
- Produces: `#recipe-search` Input; `async _apply_filter(query: str)`; `action_search()`; `/` binding.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_tui_app.py`:

```python
def test_search_filters_recipe_list():
    async def body():
        app = PyReelerApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            from textual.widgets import ListView
            await app._apply_filter("ross")
            ids = [item.id for item in app.query_one("#recipe-list", ListView).query("ListItem")]
            assert ids == ["recipe-rossler"]
            await app._apply_filter("")  # cleared -> all back
            ids = [item.id for item in app.query_one("#recipe-list", ListView).query("ListItem")]
            assert "recipe-lorenz" in ids and "recipe-rossler" in ids
    asyncio.run(body())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_tui_app.py::test_search_filters_recipe_list -q`
Expected: FAIL — `_apply_filter` not defined.

- [ ] **Step 3: Add the search box, binding, and handlers**

In `pyreeler/tui/app.py`, add the `/` binding:

```python
    BINDINGS = [
        Binding("escape", "quit", "Back", priority=True),
        Binding("slash", "search", "Search"),
    ]
```

Add the search Input to the sidebar in `compose` (between the heading and the ListView):

```python
            with Vertical(id="sidebar"):
                yield Label("RECIPES", classes="heading")
                yield Input(placeholder="filter…", id="recipe-search")
                yield ListView(
                    *[
                        ListItem(Label(r.name), id=f"{RECIPE_PREFIX}{r.name}")
                        for r in list_recipes()
                    ],
                    id="recipe-list",
                )
```

Add the change handler and filter method (place after `on_list_view_highlighted`):

```python
    async def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "recipe-search":
            await self._apply_filter(event.value)

    async def _apply_filter(self, query: str) -> None:
        q = query.strip().lower()
        matches = [r for r in list_recipes()
                   if q in r.name.lower() or q in r.summary.lower()]
        lst = self.query_one("#recipe-list", ListView)
        await lst.clear()
        for r in matches:
            await lst.append(
                ListItem(Label(r.name), id=f"{RECIPE_PREFIX}{r.name}"))
        if matches:
            names = [r.name for r in matches]
            target = self._current_name if self._current_name in names else names[0]
            if target != self._current_name:
                await self._load_recipe(target)
            lst.index = names.index(target)

    def action_search(self) -> None:
        self.set_focus(self.query_one("#recipe-search", Input))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_tui_app.py::test_search_filters_recipe_list -q`
Expected: PASS.

- [ ] **Step 5: Add search styling**

Append to `pyreeler/tui/styles.tcss`:

```css
#recipe-search {
    border: tall #1f8f3a;
    margin: 0 0 1 0;
}
```

- [ ] **Step 6: Verify gates**

Run: `python3 -m pytest -q && python3 sync.py --check && python3 graduation_check.py`
Expected: all pass. (Note: `on_input_changed` guards on `id == "recipe-search"`, so NumberField/TextField inner inputs are unaffected.)

- [ ] **Step 7: Commit**

```bash
git add pyreeler/tui/app.py pyreeler/tui/styles.tcss tests/test_tui_app.py
git commit -m "$(cat <<'EOF'
feat(tui): recipe search box filters the list as you type

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: Play/open the rendered result

**Files:**
- Modify: `pyreeler/tui/app.py`
- Test: `tests/test_tui_app.py`

**Interfaces:**
- Consumes: `open_in_player` from `pyreeler.tui.player`.
- Produces: `#play-btn` Button (starts disabled, enabled in `_on_done`); `self._last_output: Path | None`; `action_play()`; `p` binding.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_tui_app.py`:

```python
def test_play_enables_after_render_and_opens_file(monkeypatch, tmp_path):
    async def body():
        app = PyReelerApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            from textual.widgets import Button
            # play disabled until a render completes
            assert app.query_one("#play-btn", Button).disabled is True
            out = tmp_path / "lorenz.mp4"
            out.write_bytes(b"x")
            app._on_done(out)  # simulate a finished render
            await pilot.pause()
            assert app.query_one("#play-btn", Button).disabled is False
            opened = {}
            import pyreeler.tui.app as appmod
            monkeypatch.setattr(appmod, "open_in_player",
                                lambda p: opened.update(path=p))
            app.action_play()
            assert opened["path"] == out
    asyncio.run(body())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_tui_app.py::test_play_enables_after_render_and_opens_file -q`
Expected: FAIL — no `#play-btn`, no `action_play`, `open_in_player` not imported into app.

- [ ] **Step 3: Add the Play button, binding, and action**

In `pyreeler/tui/app.py`, add the import:

```python
from .fields import ParamField, make_field
from .player import open_in_player
```

Add the `p` binding to `BINDINGS`:

```python
    BINDINGS = [
        Binding("escape", "quit", "Back", priority=True),
        Binding("slash", "search", "Search"),
        Binding("p", "play", "Play"),
    ]
    _current_name: str = ""
    _last_output: "Path | None" = None
```

Add the Play button to the detail pane in `compose`, right after the Render button:

```python
                yield Button("Render", id="render-btn", variant="success")
                yield Button("Play", id="play-btn", disabled=True)
```

Extend `on_button_pressed` to handle the Play button:

```python
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "render-btn":
            self._start_render()
        elif event.button.id == "play-btn":
            self.action_play()
```

Update `_on_done` to record the output and enable Play:

```python
    def _on_done(self, out) -> None:
        self._last_output = out
        self.query_one("#play-btn", Button).disabled = False
        self.query_one("#status", Static).update(f"wrote {out}")
```

Add `action_play`:

```python
    def action_play(self) -> None:
        if not self._last_output or not Path(self._last_output).exists():
            self.query_one("#status", Static).update("nothing to play yet")
            return
        try:
            open_in_player(Path(self._last_output))
        except OSError as exc:
            self.query_one("#status", Static).update(
                f"cannot open {self._last_output}: {exc}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_tui_app.py::test_play_enables_after_render_and_opens_file -q`
Expected: PASS.

- [ ] **Step 5: Verify gates**

Run: `python3 -m pytest -q && python3 sync.py --check && python3 graduation_check.py`
Expected: all pass.

- [ ] **Step 6: Manual smoke (optional, needs a TTY)**

Run: `python3 -m pyreeler` → pick a recipe → nudge a param with `+`/`-` → cycle `palette` with `‹`/`›` → type in the filter box → Render → press `p` to open the result. (Skip if not on an interactive terminal.)

- [ ] **Step 7: Commit**

```bash
git add pyreeler/tui/app.py tests/test_tui_app.py
git commit -m "$(cat <<'EOF'
feat(tui): Play button + p key open the rendered film

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

### Task 8: README note for the new TUI controls

**Files:**
- Modify: `README.md`

**Interfaces:** none (docs only).

- [ ] **Step 1: Update the TUI blurb**

In `README.md`, extend the interactive-TUI paragraph (the one that begins "Prefer it interactive?") to mention the new controls. Find:

```text
live parameter form, and a render progress bar with a Sparkline. Renders land in
```

Replace "live parameter form" with:

```text
live parameter form (with `[-]`/`[+]` steppers, a `‹ ›` palette cycler, and a
recipe filter box — press `p` to play the finished render), and a render progress
bar with a Sparkline. Renders land in
```

- [ ] **Step 2: Verify gates**

Run: `python3 -m pytest -q && python3 sync.py --check && python3 graduation_check.py`
Expected: all pass (docs-only change).

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "$(cat <<'EOF'
docs: note TUI steppers, palette cycler, filter, and play key

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

## Self-Review

**Spec coverage:**
- Stepper/cycler controls → Tasks 1–3, 5. ✓
- `Param.step` schema + magnitude-aware derive → Task 1. ✓
- Recipe search → Task 6. ✓
- Play/open → Tasks 4, 7. ✓
- Keybindings (`p`, `/`) → Tasks 6, 7. ✓
- Error handling (bad numeric → resolve_params; open failure → status; empty search) → Tasks 2, 5 (bad-numeric test), 6, 7. ✓
- Testing matrix (effective_step, ChoiceField, NumberField, open_in_player, app build, collect round-trip, search, play) → Tasks 1–7. ✓
- Existing-test updates → Task 5. ✓
- Out-of-scope items (preview, theming, reset) → not present. ✓

**Type consistency:** `effective_step`/`stepped_value`/`_format` signatures match across Tasks 1–3. `ParamField.param_value` (str) used by `_collect_params` in Task 5. `make_field` precedence (choices → numeric → text) consistent with the bad-numeric test (palette is a cycler). `#field-{name}`, `#param-{name}`, `#play-btn`, `#recipe-search` ids consistent across tasks. `open_in_player` imported into `app` (Task 7) matches the module from Task 4.

**Placeholder scan:** No TBD/TODO; every code step shows full code; tests include real assertions.
