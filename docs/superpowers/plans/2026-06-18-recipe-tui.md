# Recipe TUI Implementation Plan (Plan 2 of 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the interactive Textual TUI front-end (Version A) on top of the Plan 1 CLI core — a phosphor launch banner, a recipe browser, an auto-generated parameter form, and a render pane with progress + a Sparkline.

**Architecture:** A `pyreeler/tui/` package: `banner.py` plays the launch spectacle (TerminalTextEffects with a guaranteed static fallback); `app.py` is a Textual `App` with three panes (recipe list │ param form │ render pane) that calls the existing `pyreeler.engine.render_film` in a worker thread; `styles.tcss` themes it phosphor. `app.run()` is the entry point the CLI's existing `_launch_tui()` seam already imports.

**Tech Stack:** Python 3.10+, Textual (`>=0.60`), Rich, TerminalTextEffects — all **optional** (`requirements-tui.txt`). Reuses the Plan 1 recipe registry + engine unchanged.

**Spec:** `docs/superpowers/specs/2026-06-18-recipe-cli-and-tui-design.md` (the "TUI (Version A — Textual)" section).

---

## Pre-flight (read before starting)

- The TUI deps are **not** installed in CI, and the existing CI suite must stay green. Every test file in this plan begins with a `pytest.importorskip("textual")` (or `terminaltexteffects`) guard so it **skips** when the dep is absent. CI (numpy+pillow only) therefore skips all TUI tests; a developer who runs `pip install -r requirements-tui.txt` gets them.
- **Install the deps first** (Task 1 Step 1). You cannot develop or test the Textual app without them.
- **Textual API note:** this plan targets Textual's stable core API (`App`, `compose()`, `ComposeResult`, `query_one`, `@work`, `run_test`). If the installed Textual version names a method or argument slightly differently, **the TDD test is the contract** — adjust the widget call to the installed version while keeping the test green. Do not change what the test asserts.
- The CLI already contains the seam this plan fills:
  ```python
  # pyreeler/cli.py
  def _launch_tui() -> int:
      try:
          from .tui.app import run as run_tui
      except ImportError:
          print("The PyReeler TUI needs extra packages...", file=sys.stderr)
          return 1
      return run_tui()
  ```
  So `pyreeler/tui/app.py` must expose `run() -> int`.
- `pyreeler/tui/__init__.py` already exists as a placeholder docstring — leave it.

---

## File Structure

- Create `pyreeler/tui/banner.py` — `render_banner()`: TTE animated reveal + static phosphor fallback.
- Create `pyreeler/tui/styles.tcss` — phosphor Textual theme.
- Create `pyreeler/tui/app.py` — `PyReelerApp(App)` + `run()`.
- Create `tests/test_tui_banner.py`, `tests/test_tui_app.py`.
- Modify `README.md` — replace the "TUI front-end is on the way" line with real usage.

---

## Task 1: Install deps + the launch banner

**Files:**
- Create: `pyreeler/tui/banner.py`
- Test: `tests/test_tui_banner.py`

- [ ] **Step 1: Install the TUI dependencies**

Run: `python3 -m pip install -r requirements-tui.txt`
Expected: textual, rich, terminaltexteffects install successfully. Verify:
`python3 -c "import textual, terminaltexteffects; print('tui deps ok')"`

- [ ] **Step 2: Write the failing test**

Create `tests/test_tui_banner.py`:

```python
"""Tests for the TUI launch banner. The animated path needs a real TTY, so these
exercise the deterministic static fallback (what runs under pytest's captured IO)."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from pyreeler.tui import banner  # noqa: E402


def test_render_banner_returns_multiline_logo(capsys):
    out = banner.render_banner(animate=False)
    assert out.count("\n") >= 5          # a multi-line ASCII logo
    assert capsys.readouterr().out.strip()  # it printed something


def test_render_banner_animate_is_safe_without_tty(capsys):
    # Under pytest stdout is not a TTY, so animate=True must fall back, never raise,
    # and must not blow up even if TerminalTextEffects' API differs.
    out = banner.render_banner(animate=True)
    assert out.count("\n") >= 5
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python3 -m pytest tests/test_tui_banner.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'pyreeler.tui.banner'`.

- [ ] **Step 4: Write minimal implementation**

Create `pyreeler/tui/banner.py`:

```python
"""Phosphor PYREELER launch banner for the TUI.

Tries TerminalTextEffects for an animated reveal when attached to a real terminal;
always falls back to a static phosphor ASCII logo so it works (and tests) anywhere.
"""
from __future__ import annotations

import sys

PHOSPHOR = "\x1b[38;2;57;255;20m"
RESET = "\x1b[0m"

ASCII_LOGO = r"""
 ____  _   _ ____  _____ _____ _     _____ ____
|  _ \| | | |  _ \| ____| ____| |   | ____|  _ \
| |_) | | | | |_) |  _| |  _| | |   |  _| | |_) |
|  __/| |_| |  _ <| |___| |___| |___| |___|  _ <
|_|    \___/|_| \_\_____|_____|_____|_____|_| \_\
         code-generated cinema, conjured from math
"""


def _tint(text: str) -> str:
    """Phosphor-green truecolor if writing to a terminal, else plain."""
    if sys.stdout.isatty():
        return f"{PHOSPHOR}{text}{RESET}"
    return text


def render_banner(text: str = "PYREELER", *, animate: bool = True) -> str:
    """Play the launch banner; return the static ASCII logo string.

    Animated reveal (TerminalTextEffects) only runs on a real TTY; any version
    mismatch or absence falls back to the static phosphor logo. Always safe.
    """
    if animate and sys.stdout.isatty():
        try:
            from terminaltexteffects.effects.effect_beams import Beams

            effect = Beams(ASCII_LOGO)
            with effect.terminal_output() as terminal:
                for frame in effect:
                    terminal.print(frame)
            return ASCII_LOGO
        except Exception:
            pass  # any TTE/version problem -> fall through to the static logo
    sys.stdout.write(_tint(ASCII_LOGO) + "\n")
    sys.stdout.flush()
    return ASCII_LOGO
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python3 -m pytest tests/test_tui_banner.py -q`
Expected: PASS (2 passed).

- [ ] **Step 6: Commit**

```bash
git add pyreeler/tui/banner.py tests/test_tui_banner.py
git commit -m "feat(tui): phosphor launch banner (TTE reveal + static fallback)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: App skeleton — recipe list pane + run()

**Files:**
- Create: `pyreeler/tui/styles.tcss`, `pyreeler/tui/app.py`
- Test: `tests/test_tui_app.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_tui_app.py`:

```python
"""Tests for the Textual TUI app. Skipped entirely when textual is not installed
(so the numpy+pillow CI stays green). Async pilots are driven via asyncio.run."""
import asyncio
import sys
from pathlib import Path

import pytest

pytest.importorskip("textual")

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from pyreeler.tui.app import PyReelerApp  # noqa: E402


def test_app_mounts_and_lists_recipes():
    async def body():
        app = PyReelerApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            from textual.widgets import ListView
            lst = app.query_one("#recipe-list", ListView)
            # one ListItem per registered recipe; lorenz + rossler present
            ids = [item.id for item in lst.query("ListItem")]
            assert "recipe-lorenz" in ids
            assert "recipe-rossler" in ids
    asyncio.run(body())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_tui_app.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'pyreeler.tui.app'`.

- [ ] **Step 3: Write minimal implementation**

Create `pyreeler/tui/styles.tcss`:

```css
Screen {
    background: #0d1117;
    color: #39ff14;
}

#sidebar {
    width: 28;
    border: round #1f8f3a;
}

#detail {
    border: round #1f8f3a;
    padding: 1 2;
}

.heading {
    color: #d6ffcc;
    text-style: bold;
}

ListView {
    background: #0d1117;
}

ListView > ListItem.--highlight {
    background: #15311c;
}

Input {
    border: tall #1f8f3a;
}

Button {
    background: #1f8f3a;
    color: #d6ffcc;
}
```

Create `pyreeler/tui/app.py`:

```python
"""Textual TUI: browse recipes, tune parameters, render — the phosphor front-end."""
from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Button, Footer, Header, Input, Label, ListItem, ListView, ProgressBar, Static,
)

from ..recipes import get, list_recipes, merged_params, resolve_params, ParamError

RECIPE_PREFIX = "recipe-"


class PyReelerApp(App):
    """The PyReeler recipe browser + renderer."""

    CSS_PATH = "styles.tcss"
    TITLE = "PyReeler"

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main"):
            with Vertical(id="sidebar"):
                yield Label("RECIPES", classes="heading")
                yield ListView(
                    *[
                        ListItem(Label(r.name), id=f"{RECIPE_PREFIX}{r.name}")
                        for r in list_recipes()
                    ],
                    id="recipe-list",
                )
            with Vertical(id="detail"):
                yield Static("", id="summary")
                yield Vertical(id="form")
                yield Button("Render", id="render-btn", variant="success")
                yield ProgressBar(id="progress", total=100, show_eta=False)
                yield Static("", id="status")
        yield Footer()


def run() -> int:
    """Entry point used by the CLI's no-arg path."""
    PyReelerApp().run()
    return 0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_tui_app.py -q`
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add pyreeler/tui/styles.tcss pyreeler/tui/app.py tests/test_tui_app.py
git commit -m "feat(tui): Textual app skeleton with recipe list + run()

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Recipe selection → summary + parameter form

**Files:**
- Modify: `pyreeler/tui/app.py`
- Modify: `tests/test_tui_app.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_tui_app.py`:

```python
def test_selecting_recipe_populates_summary_and_form():
    async def body():
        app = PyReelerApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            from textual.widgets import Input, Static
            # on_mount loads the first recipe; summary is non-empty
            assert app.query_one("#summary", Static).renderable
            # the form has one Input per merged param of the selected recipe
            from pyreeler.recipes import get, merged_params
            recipe = get(app._current_name)
            inputs = app.query("#form Input")
            assert len(inputs) == len(merged_params(recipe))
            # a known recipe-specific field is present and prefilled with its default
            rho = app.query_one("#param-rho", Input)
            assert rho.value == "28.0"
    asyncio.run(body())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_tui_app.py -q`
Expected: FAIL — `app._current_name` / `#param-rho` do not exist yet.

- [ ] **Step 3: Write minimal implementation**

In `pyreeler/tui/app.py`, add an `on_mount` and recipe-loading logic to `PyReelerApp`. Insert these methods into the class (after `compose`):

```python
    def on_mount(self) -> None:
        first = list_recipes()[0].name
        self.query_one("#recipe-list", ListView).index = 0
        self._load_recipe(first)

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        item = event.item
        if item is not None and item.id and item.id.startswith(RECIPE_PREFIX):
            self._load_recipe(item.id[len(RECIPE_PREFIX):])

    def _load_recipe(self, name: str) -> None:
        recipe = get(name)
        self._current_name = name
        self.query_one("#summary", Static).update(recipe.summary)
        form = self.query_one("#form", Vertical)
        form.remove_children()
        for p in merged_params(recipe):
            form.mount(Label(p.name, classes="param-label"))
            form.mount(Input(value=str(p.default), id=f"param-{p.name}"))
```

Also add a class attribute near the top of the class body (right under `TITLE = "PyReeler"`):

```python
    _current_name: str = ""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_tui_app.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add pyreeler/tui/app.py tests/test_tui_app.py
git commit -m "feat(tui): recipe selection drives summary + generated param form

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: Param collection, render worker, progress + Sparkline

**Files:**
- Modify: `pyreeler/tui/app.py`
- Modify: `tests/test_tui_app.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_tui_app.py`:

```python
def test_collect_params_reads_form_values():
    async def body():
        app = PyReelerApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            from textual.widgets import Input
            app.query_one("#param-rho", Input).value = "30"
            app.query_one("#param-duration", Input).value = "2"
            params = app._collect_params()
            assert params["rho"] == 30.0
            assert params["duration"] == 2.0
    asyncio.run(body())


def test_bad_param_shows_error_in_status():
    async def body():
        app = PyReelerApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            from textual.widgets import Input, Static
            app.query_one("#param-palette", Input).value = "chartreuse"
            app._start_render()  # invalid -> should set status, not raise
            await pilot.pause()
            status = str(app.query_one("#status", Static).renderable)
            assert "palette" in status
    asyncio.run(body())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_tui_app.py -q`
Expected: FAIL — `app._collect_params` / `app._start_render` do not exist.

- [ ] **Step 3: Write minimal implementation**

In `pyreeler/tui/app.py`, add the imports at the top (extend the existing imports):

```python
from textual import work
from textual.widgets import Sparkline
```

Add a `Sparkline` to `compose`, immediately after the `ProgressBar` line:

```python
                yield Sparkline([], id="spark")
```

Add the render methods to `PyReelerApp` (after `_load_recipe`):

```python
    def _collect_params(self) -> dict:
        """Read the form inputs into a validated params dict (raises ParamError)."""
        recipe = get(self._current_name)
        overrides = {}
        for p in merged_params(recipe):
            value = self.query_one(f"#param-{p.name}", Input).value.strip()
            if value:
                overrides[p.name] = value
        return resolve_params(recipe, overrides)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "render-btn":
            self._start_render()

    def _start_render(self) -> None:
        try:
            params = self._collect_params()
        except ParamError as exc:
            self.query_one("#status", Static).update(f"error: {exc}")
            return
        recipe = get(self._current_name)
        total = max(1, round(params["duration"] * params["fps"]))
        self.query_one("#progress", ProgressBar).update(total=total, progress=0)
        self.query_one("#status", Static).update("rendering...")
        out = Path(f"{recipe.name}.mp4")
        self._render_worker(recipe, params, out)

    @work(thread=True, exclusive=True)
    def _render_worker(self, recipe, params, out) -> None:
        from ..engine import render_film

        def progress(done, total):
            self.call_from_thread(self._on_progress, done)

        try:
            render_film(recipe, params, out, on_progress=progress)
            self.call_from_thread(self._on_done, out)
        except Exception as exc:  # surface any render failure into the UI
            self.call_from_thread(self._on_error, exc)

    def _on_progress(self, done: int) -> None:
        self.query_one("#progress", ProgressBar).update(progress=done)
        spark = self.query_one("#spark", Sparkline)
        spark.data = list(spark.data or []) + [done]

    def _on_done(self, out) -> None:
        self.query_one("#status", Static).update(f"wrote {out}")

    def _on_error(self, exc) -> None:
        self.query_one("#status", Static).update(f"error: {exc}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_tui_app.py -q`
Expected: PASS (4 passed). (The render *worker* happy-path is deliberately not
asserted in tests — worker threads are flaky to assert; `_collect_params` and the
error path cover the logic. The worker is exercised manually in Task 5.)

- [ ] **Step 5: Commit**

```bash
git add pyreeler/tui/app.py tests/test_tui_app.py
git commit -m "feat(tui): param collection, threaded render worker, progress + sparkline

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Wire the banner into launch, manual smoke, docs

**Files:**
- Modify: `pyreeler/tui/app.py`
- Modify: `README.md`

- [ ] **Step 1: Play the banner before the app mounts**

In `pyreeler/tui/app.py`, update `run()` to show the banner first:

```python
def run() -> int:
    """Entry point used by the CLI's no-arg path: banner, then the app."""
    from .banner import render_banner

    render_banner()
    PyReelerApp().run()
    return 0
```

- [ ] **Step 2: Manual smoke test (real terminal)**

These require an interactive terminal (pilot tests can't cover the live app). Run and confirm by eye:
```bash
python3 -m pyreeler            # banner plays, then the TUI opens
```
Confirm: the phosphor PYREELER banner appears; the recipe list shows `lorenz`/`rossler`;
arrow keys change the highlighted recipe and the form repopulates; editing params and
pressing the Render button shows progress filling and ends with `wrote lorenz.mp4`;
`q` quits. Delete any `lorenz.mp4`/`rossler.mp4` produced by the smoke test.

- [ ] **Step 3: Confirm CI-safe collection (deps-absent simulation)**

Run the full suite the way CI does and confirm the TUI tests are collected when deps
are present and that nothing errors:
```bash
python3 -m pytest -q
```
Expected: all pass (the TUI tests run here because Task 1 installed the deps). To prove
the CI-skip path, `pytest tests/test_tui_app.py -q` in an env without textual would
report "skipped" — not required to run, but that's the guard's purpose.

- [ ] **Step 4: Update the README**

In `README.md`, find this line in the "Use It Without an AI (CLI)" section:

```markdown
is on the way.
```

Replace the sentence ending in "An interactive TUI front-end (phosphor banner and all)
is on the way." with:

```markdown
Prefer it interactive? `pip install -r requirements-tui.txt` then run **`pyreeler`**
with no arguments for the full TUI — a phosphor PYREELER banner, a recipe browser, a
live parameter form, and a render progress bar with a Sparkline.
```

- [ ] **Step 5: Commit**

```bash
git add pyreeler/tui/app.py README.md
git commit -m "feat(tui): play banner on launch; document the TUI

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review Notes

**Spec coverage (TUI section):**
- Launch banner via TerminalTextEffects with fallback → Task 1.
- Layout: recipe ListView │ auto-generated param form │ render pane → Tasks 2-4.
- Phosphor theme `#39ff14` on `#0d1117` → Task 2 (`styles.tcss`).
- Render in a worker thread, progress callback drives bar + Sparkline → Task 4.
- ParamError surfaced cleanly (no crash) → Task 4 (`_start_render` error path).
- Optional deps; CI stays green via `importorskip` → Pre-flight + every test file.
- `run()` matches the CLI's existing `_launch_tui` import seam → Tasks 2, 5.
- README documents the TUI → Task 5.

**Deferred (Plan 2 is Version A; these are future, per spec):** live in-terminal frame
preview (Version B), guided multi-screen flow (Version C), TTE motion-path/particle
banner variants beyond the default reveal.

**API-risk note:** Textual/TTE are not installed in CI, so this plan's widget calls
target the stable Textual core API. The TDD tests are the contract; if the installed
Textual version differs on a method name/argument, adjust the call to keep the test
green (do not change the assertions). The banner's TTE path is fully wrapped in
try/except so any TTE API drift degrades to the static logo rather than breaking.

**No placeholders:** every code step contains complete code; every run step lists the
exact command and expected result.
