# Recipe CLI Core Implementation Plan (Plan 1 of 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the non-AI core of PyReeler — a recipe registry, two attractor recipes (lorenz, rossler), a render engine, and a scriptable CLI (`pyreeler list` / `pyreeler render`) — so films can be made from the command line with no AI.

**Architecture:** A new top-level `pyreeler/` package. Recipes declare a param schema + a two-phase render (`prepare` precomputes the trajectory once; `make_frame` plots one frame). The engine wraps the existing `templates/video` runtime + parallel-frame map and pipes frames to FFmpeg. The CLI generates typed flags from each recipe's merged schema. The TUI is **Plan 2** — this plan leaves a clean `_launch_tui()` seam.

**Tech Stack:** Python 3.10+, NumPy, Pillow, argparse (stdlib), FFmpeg (external). No new runtime deps. Reuses `experimental/tools/attractors.py` and `templates/video/{render_runtime,parallel_render,ffmpeg_utils}.py` via PEP 420 namespace imports.

**Spec:** `docs/superpowers/specs/2026-06-18-recipe-cli-and-tui-design.md`

---

## File Structure

- Create `pyreeler/__init__.py` — package docstring + repo-root `sys.path` shim (so `experimental.*` / `templates.*` resolve from anywhere).
- Create `pyreeler/recipes/base.py` — `Param`, `Recipe`, `PALETTES`, `STANDARD_PARAMS`, `REGISTRY`, `register`, `get`, `list_recipes`, `UnknownRecipeError`.
- Create `pyreeler/recipes/params.py` — `merged_params`, `resolve_params`, `ParamError`.
- Create `pyreeler/recipes/_plot.py` — `scatter_trail` (palette-aware attractor plotter).
- Create `pyreeler/recipes/lorenz.py`, `pyreeler/recipes/rossler.py` — the two v1 recipes.
- Create `pyreeler/recipes/__init__.py` — re-exports + triggers recipe registration.
- Create `pyreeler/engine.py` — `render_film`, `_FrameJob`, `_encode_frames`.
- Create `pyreeler/cli.py` — argparse CLI (`list`, `render`, no-arg → TUI seam).
- Create `pyreeler/__main__.py` — `python -m pyreeler` entry.
- Create `pyproject.toml` — `pyreeler` console-script + deps + `tui` extra.
- Create `requirements-tui.txt` — placeholder dep list for Plan 2.
- Create tests under `tests/` (one file per area).
- Modify `pytest.ini` — add the new test files to `testpaths`.
- Modify `README.md` — add a "Use it without an AI (CLI)" section.

---

## Task 1: Package scaffold + recipe registry

**Files:**
- Create: `pyreeler/__init__.py`, `pyreeler/recipes/base.py`
- Test: `tests/test_recipe_registry.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_recipe_registry.py`:

```python
"""Tests for the recipe registry core (pyreeler.recipes.base)."""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from pyreeler.recipes import base  # noqa: E402


def _dummy_recipe(name="dummy"):
    return base.Recipe(
        name=name, summary="a test recipe", params=(),
        prepare=lambda params: None,
        make_frame=lambda prepared, params, i, total: None,
    )


def test_register_and_get_round_trip():
    base.REGISTRY.clear()
    r = _dummy_recipe("alpha")
    base.register(r)
    assert base.get("alpha") is r


def test_list_recipes_is_sorted_by_name():
    base.REGISTRY.clear()
    base.register(_dummy_recipe("zed"))
    base.register(_dummy_recipe("abe"))
    assert [r.name for r in base.list_recipes()] == ["abe", "zed"]


def test_get_unknown_raises_with_suggestion():
    base.REGISTRY.clear()
    base.register(_dummy_recipe("lorenz"))
    with pytest.raises(base.UnknownRecipeError) as exc:
        base.get("loranz")
    assert "lorenz" in str(exc.value)  # close-match suggestion


def test_standard_params_define_core_film_knobs():
    names = {p.name for p in base.STANDARD_PARAMS}
    assert {"duration", "fps", "width", "height", "palette"} <= names
    palette = next(p for p in base.STANDARD_PARAMS if p.name == "palette")
    assert set(palette.choices) == set(base.PALETTES)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_recipe_registry.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'pyreeler'`.

- [ ] **Step 3: Write minimal implementation**

Create `pyreeler/__init__.py`:

```python
"""PyReeler CLI/TUI package — make code-generated films without an AI.

Ensures the repository root is importable so the sibling namespace packages
`experimental.tools.*` and `templates.video.*` resolve regardless of the current
working directory (they have no __init__.py; PEP 420 namespace import covers them).
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
```

Create `pyreeler/recipes/base.py`:

```python
"""Recipe registry primitives: Param, Recipe, the registry, and lookups."""
from __future__ import annotations

import difflib
from dataclasses import dataclass
from typing import Any, Callable


class UnknownRecipeError(KeyError):
    """Raised when a recipe name is not in the registry."""


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


@dataclass(frozen=True)
class Recipe:
    """A named, parameterized film effect.

    prepare(params) -> shared precomputed data (e.g. a trajectory), run once.
    make_frame(prepared, params, frame_idx, total) -> PIL.Image for one frame.
    """

    name: str
    summary: str
    params: tuple
    prepare: Callable
    make_frame: Callable


# Palette name -> RGB. Phosphor matches the site/README (#39ff14).
PALETTES = {
    "phosphor": (57, 255, 20),
    "amber": (255, 176, 0),
    "ice": (120, 200, 255),
    "mono": (235, 235, 235),
}

# Standard knobs every recipe inherits, prepended to its specific params.
STANDARD_PARAMS = (
    Param("duration", float, 30.0, min=1, help="film length in seconds"),
    Param("fps", int, 24, min=1, help="frames per second"),
    Param("width", int, 854, min=16, help="frame width in pixels"),
    Param("height", int, 480, min=16, help="frame height in pixels"),
    Param("palette", str, "phosphor", choices=tuple(PALETTES), help="color palette"),
)

REGISTRY: dict[str, Recipe] = {}


def register(recipe: Recipe) -> Recipe:
    """Add a recipe to the registry and return it (usable as an expression)."""
    REGISTRY[recipe.name] = recipe
    return recipe


def list_recipes() -> list[Recipe]:
    """All registered recipes, sorted by name."""
    return [REGISTRY[name] for name in sorted(REGISTRY)]


def get(name: str) -> Recipe:
    """Look up a recipe, raising UnknownRecipeError with a suggestion on miss."""
    try:
        return REGISTRY[name]
    except KeyError:
        close = difflib.get_close_matches(name, list(REGISTRY), n=3)
        hint = f" Did you mean: {', '.join(close)}?" if close else ""
        raise UnknownRecipeError(f"unknown recipe '{name}'.{hint}") from None
```

Also create an empty `pyreeler/recipes/__init__.py` for now so the import resolves:

```python
from .base import (  # noqa: F401
    Param, Recipe, PALETTES, STANDARD_PARAMS, REGISTRY,
    register, get, list_recipes, UnknownRecipeError,
)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_recipe_registry.py -q`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add pyreeler/__init__.py pyreeler/recipes/__init__.py pyreeler/recipes/base.py tests/test_recipe_registry.py
git commit -m "feat(cli): recipe registry primitives (Param, Recipe, lookups)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Parameter resolution + validation

**Files:**
- Create: `pyreeler/recipes/params.py`
- Modify: `pyreeler/recipes/__init__.py`
- Test: `tests/test_recipe_params.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_recipe_params.py`:

```python
"""Tests for parameter merging, coercion, and validation."""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from pyreeler.recipes import base  # noqa: E402
from pyreeler.recipes import params as P  # noqa: E402


def _recipe():
    return base.Recipe(
        name="t", summary="", params=(base.Param("rho", float, 28.0, min=0, max=100),),
        prepare=lambda p: None, make_frame=lambda pr, p, i, n: None,
    )


def test_merged_params_prepends_standard():
    names = [p.name for p in P.merged_params(_recipe())]
    assert names[:5] == ["duration", "fps", "width", "height", "palette"]
    assert names[-1] == "rho"


def test_resolve_applies_defaults_and_coerces_types():
    out = P.resolve_params(_recipe(), {"rho": "30", "fps": "12"})
    assert out["rho"] == 30.0 and isinstance(out["rho"], float)
    assert out["fps"] == 12 and isinstance(out["fps"], int)
    assert out["duration"] == 30.0  # default applied


def test_resolve_rejects_out_of_range():
    with pytest.raises(P.ParamError):
        P.resolve_params(_recipe(), {"rho": 250})


def test_resolve_rejects_bad_choice():
    with pytest.raises(P.ParamError):
        P.resolve_params(_recipe(), {"palette": "chartreuse"})


def test_resolve_rejects_unknown_param():
    with pytest.raises(P.ParamError):
        P.resolve_params(_recipe(), {"nope": 1})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_recipe_params.py -q`
Expected: FAIL — `ImportError: cannot import name 'params'` / `ParamError`.

- [ ] **Step 3: Write minimal implementation**

Create `pyreeler/recipes/params.py`:

```python
"""Merge, coerce, and validate recipe parameters."""
from __future__ import annotations

from typing import Any

from .base import Param, Recipe, STANDARD_PARAMS


class ParamError(ValueError):
    """Raised when a parameter value is missing-typed, out of range, or unknown."""


def merged_params(recipe: Recipe) -> tuple:
    """Standard params followed by the recipe's specific params."""
    return STANDARD_PARAMS + tuple(recipe.params)


def resolve_params(recipe: Recipe, overrides: dict[str, Any]) -> dict[str, Any]:
    """Return a fully-resolved param dict: defaults + overrides, coerced + validated."""
    schema = {p.name: p for p in merged_params(recipe)}

    unknown = set(overrides) - set(schema)
    if unknown:
        raise ParamError(f"unknown parameter(s): {', '.join(sorted(unknown))}")

    resolved: dict[str, Any] = {}
    for name, p in schema.items():
        raw = overrides.get(name, p.default)
        try:
            value = p.type(raw)
        except (TypeError, ValueError):
            raise ParamError(f"{name} must be {p.type.__name__}, got {raw!r}") from None
        if p.choices and value not in p.choices:
            raise ParamError(f"{name} must be one of {p.choices}, got {value!r}")
        if p.min is not None and value < p.min:
            raise ParamError(f"{name} must be >= {p.min}, got {value}")
        if p.max is not None and value > p.max:
            raise ParamError(f"{name} must be <= {p.max}, got {value}")
        resolved[name] = value
    return resolved
```

Update `pyreeler/recipes/__init__.py` to re-export the new names:

```python
from .base import (  # noqa: F401
    Param, Recipe, PALETTES, STANDARD_PARAMS, REGISTRY,
    register, get, list_recipes, UnknownRecipeError,
)
from .params import merged_params, resolve_params, ParamError  # noqa: F401
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_recipe_params.py -q`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add pyreeler/recipes/params.py pyreeler/recipes/__init__.py tests/test_recipe_params.py
git commit -m "feat(cli): parameter merge, coercion, and validation

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Palette-aware attractor plotter

**Files:**
- Create: `pyreeler/recipes/_plot.py`
- Test: `tests/test_recipe_plot.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_recipe_plot.py`:

```python
"""Tests for the shared attractor plotter."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from pyreeler.recipes._plot import scatter_trail  # noqa: E402


def _spiral(n=2000):
    """A simple non-degenerate trajectory of shape (n, 1, 3)."""
    t = np.linspace(0, 8 * np.pi, n)
    xyz = np.stack([np.cos(t) * t, np.sin(t) * t, t], axis=1)
    return xyz[:, None, :]  # (n, 1, 3)


def test_returns_image_of_requested_size():
    img = scatter_trail(_spiral(), 5, 10, 200, 150, trail=400, color=(57, 255, 20))
    assert isinstance(img, Image.Image)
    assert img.size == (200, 150)  # (width, height)


def test_distinct_frames_differ():
    traj = _spiral()
    a = scatter_trail(traj, 1, 10, 200, 200, trail=400, color=(57, 255, 20))
    b = scatter_trail(traj, 6, 10, 200, 200, trail=400, color=(57, 255, 20))
    assert np.asarray(a).tobytes() != np.asarray(b).tobytes()


def test_color_channels_follow_palette():
    # A green palette must not paint blue.
    img = scatter_trail(_spiral(), 6, 10, 200, 200, trail=400, color=(57, 255, 20))
    arr = np.asarray(img)
    assert arr[..., 2].max() <= arr[..., 1].max()  # blue <= green
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_recipe_plot.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'pyreeler.recipes._plot'`.

- [ ] **Step 3: Write minimal implementation**

Create `pyreeler/recipes/_plot.py`:

```python
"""Render a rotating, fading attractor trail into a single-color frame."""
from __future__ import annotations

import numpy as np
from PIL import Image

from experimental.tools.attractors import rotate_points


def scatter_trail(trajectory, frame_idx, total, width, height, trail, color):
    """Plot the trail window ending at this frame, rotated and color-tinted.

    Args:
        trajectory: array of shape (n_points, n_particles, 3).
        frame_idx, total: position in the animation (drives window + rotation).
        width, height: output size in pixels.
        trail: number of trailing points to draw.
        color: (r, g, b) tint for the accumulated intensity.

    Returns:
        An (width x height) RGB PIL.Image.
    """
    n_points, n_particles, _ = trajectory.shape
    total = max(1, total)
    angle = 2 * np.pi * frame_idx / total

    mins = trajectory.min(axis=(0, 1))
    maxs = trajectory.max(axis=(0, 1))
    ranges = maxs - mins
    ranges[ranges == 0] = 1.0

    center = int(frame_idx / total * (n_points - 1))
    start = max(0, center - trail)
    end = min(n_points, center + 1)

    buf = np.zeros((height, width), dtype=np.float32)
    for p in range(n_particles):
        pts = trajectory[start:end, p, :].copy()
        if pts.shape[0] == 0:
            continue
        pts = rotate_points(pts, angle_y=angle)
        pts = (pts - mins) / ranges
        x = (pts[:, 0] * (width - 100) + 50).astype(int)
        y = (pts[:, 1] * (height - 100) + 50).astype(int)
        weight = np.linspace(0.15, 1.0, pts.shape[0]).astype(np.float32)
        inside = (x >= 0) & (x < width) & (y >= 0) & (y < height)
        np.add.at(buf, (y[inside], x[inside]), weight[inside])

    peak = float(buf.max())
    if peak > 0:
        buf /= peak
    rgb = (buf[..., None] * np.array(color, dtype=np.float32)).clip(0, 255).astype(np.uint8)
    return Image.fromarray(rgb, "RGB")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_recipe_plot.py -q`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add pyreeler/recipes/_plot.py tests/test_recipe_plot.py
git commit -m "feat(cli): palette-aware attractor trail plotter

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: The lorenz + rossler recipes (auto-registered)

**Files:**
- Create: `pyreeler/recipes/lorenz.py`, `pyreeler/recipes/rossler.py`
- Modify: `pyreeler/recipes/__init__.py`
- Test: `tests/test_recipes_builtin.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_recipes_builtin.py`:

```python
"""Tests for the built-in lorenz and rossler recipes."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import pyreeler.recipes as recipes  # noqa: E402


def test_both_recipes_registered():
    names = {r.name for r in recipes.list_recipes()}
    assert {"lorenz", "rossler"} <= names


def test_lorenz_make_frame_is_correct_size_and_moves():
    r = recipes.get("lorenz")
    params = recipes.resolve_params(r, {"points": 1500, "width": 200, "height": 200})
    prepared = r.prepare(params)
    f0 = r.make_frame(prepared, params, 0, 10)
    f5 = r.make_frame(prepared, params, 5, 10)
    assert isinstance(f0, Image.Image) and f0.size == (200, 200)
    assert np.asarray(f0).tobytes() != np.asarray(f5).tobytes()


def test_rossler_prepare_returns_trajectory():
    r = recipes.get("rossler")
    params = recipes.resolve_params(r, {"points": 1200})
    prepared = r.prepare(params)
    assert prepared.shape[0] == 1200 and prepared.shape[2] == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_recipes_builtin.py -q`
Expected: FAIL — `lorenz`/`rossler` not registered (KeyError/UnknownRecipeError).

- [ ] **Step 3: Write minimal implementation**

Create `pyreeler/recipes/lorenz.py`:

```python
"""Lorenz strange attractor recipe."""
from __future__ import annotations

from experimental.tools.attractors import generate_lorenz

from .base import Param, Recipe, PALETTES, register
from ._plot import scatter_trail

PARAMS = (
    Param("sigma", float, 10.0, help="Lorenz sigma"),
    Param("rho", float, 28.0, help="Lorenz rho"),
    Param("beta", float, 8 / 3, help="Lorenz beta"),
    Param("points", int, 10000, min=100, help="trajectory integration steps"),
    Param("trail", int, 400, min=1, help="trail length in points"),
)


def _prepare(params):
    return generate_lorenz(
        n_points=params["points"], n_particles=1,
        sigma=params["sigma"], rho=params["rho"], beta=params["beta"],
    )


def _make_frame(prepared, params, frame_idx, total):
    return scatter_trail(
        prepared, frame_idx, total,
        params["width"], params["height"], params["trail"],
        PALETTES[params["palette"]],
    )


RECIPE = register(Recipe(
    name="lorenz",
    summary="Lorenz strange attractor — the iconic butterfly.",
    params=PARAMS, prepare=_prepare, make_frame=_make_frame,
))
```

Create `pyreeler/recipes/rossler.py`:

```python
"""Rossler strange attractor recipe."""
from __future__ import annotations

from experimental.tools.attractors import generate_rossler

from .base import Param, Recipe, PALETTES, register
from ._plot import scatter_trail

PARAMS = (
    Param("a", float, 0.2, help="Rossler a"),
    Param("b", float, 0.2, help="Rossler b"),
    Param("c", float, 5.7, help="Rossler c"),
    Param("points", int, 10000, min=100, help="trajectory integration steps"),
    Param("trail", int, 400, min=1, help="trail length in points"),
)


def _prepare(params):
    return generate_rossler(
        n_points=params["points"], n_particles=1,
        a=params["a"], b=params["b"], c=params["c"],
    )


def _make_frame(prepared, params, frame_idx, total):
    return scatter_trail(
        prepared, frame_idx, total,
        params["width"], params["height"], params["trail"],
        PALETTES[params["palette"]],
    )


RECIPE = register(Recipe(
    name="rossler",
    summary="Rossler strange attractor — a single smooth scroll.",
    params=PARAMS, prepare=_prepare, make_frame=_make_frame,
))
```

Append the registration side-effect import to `pyreeler/recipes/__init__.py` (after the existing imports):

```python
from . import lorenz, rossler  # noqa: F401,E402  (import-time registration)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_recipes_builtin.py -q`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add pyreeler/recipes/lorenz.py pyreeler/recipes/rossler.py pyreeler/recipes/__init__.py tests/test_recipes_builtin.py
git commit -m "feat(cli): lorenz + rossler recipes, auto-registered

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Render engine

**Files:**
- Create: `pyreeler/engine.py`
- Test: `tests/test_engine.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_engine.py`:

```python
"""Tests for the render engine (frame pipeline; encoder is stubbed)."""
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from pyreeler import engine  # noqa: E402
from pyreeler.recipes.base import Recipe  # noqa: E402


class _FakeRuntime:
    ffmpeg_path = "ffmpeg"
    video_args = ("-c:v", "libx264")
    workers = 1


def _solid_recipe():
    return Recipe(
        name="solid", summary="", params=(),
        prepare=lambda params: None,
        make_frame=lambda prepared, params, i, total: Image.fromarray(
            np.full((params["height"], params["width"], 3), i, dtype=np.uint8), "RGB"
        ),
    )


def test_render_film_iterates_all_frames_and_reports_progress(tmp_path, monkeypatch):
    monkeypatch.setattr(engine, "detect_render_runtime", lambda: _FakeRuntime())
    captured = {}
    monkeypatch.setattr(engine, "_encode_frames",
                        lambda frames, out, runtime, fps: captured.update(
                            n=len(frames), size=frames[0].size))
    seen = []
    params = {"duration": 1.0, "fps": 5, "width": 32, "height": 24, "palette": "phosphor"}
    out = engine.render_film(_solid_recipe(), params, tmp_path / "x.mp4",
                             on_progress=lambda d, t: seen.append((d, t)))
    assert captured["n"] == 5            # duration*fps frames
    assert captured["size"] == (32, 24)  # (width, height)
    assert seen[-1] == (5, 5)            # progress reached the end
    assert out == tmp_path / "x.mp4"


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_render_film_writes_real_mp4(tmp_path):
    import pyreeler.recipes as recipes
    r = recipes.get("lorenz")
    params = recipes.resolve_params(r, {"duration": 0.5, "fps": 4, "points": 800,
                                        "width": 160, "height": 120})
    out = engine.render_film(r, params, tmp_path / "lorenz.mp4")
    assert out.exists() and out.stat().st_size > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_engine.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'pyreeler.engine'`.

- [ ] **Step 3: Write minimal implementation**

Create `pyreeler/engine.py`:

```python
"""Render a recipe to an mp4: precompute, map frames (optionally parallel), encode."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Callable

from templates.video.render_runtime import detect_render_runtime
from templates.video.parallel_render import ordered_frame_map


class _FrameJob:
    """A picklable per-frame callable (needed for multiprocessing workers)."""

    def __init__(self, recipe, params, prepared, total):
        self.recipe = recipe
        self.params = params
        self.prepared = prepared
        self.total = total

    def __call__(self, frame_idx):
        return self.recipe.make_frame(self.prepared, self.params, frame_idx, self.total)


def render_film(recipe, params: dict[str, Any], out_path,
                on_progress: Callable[[int, int], None] | None = None) -> Path:
    """Render `recipe` with resolved `params` to `out_path` (mp4); return the path."""
    out_path = Path(out_path)
    total = max(1, round(params["duration"] * params["fps"]))
    prepared = recipe.prepare(params)
    runtime = detect_render_runtime()
    job = _FrameJob(recipe, params, prepared, total)

    frames = []
    for done, image in enumerate(
        ordered_frame_map(range(total), job, runtime.workers), start=1
    ):
        frames.append(image)
        if on_progress is not None:
            on_progress(done, total)

    _encode_frames(frames, out_path, runtime, int(params["fps"]))
    return out_path


def _encode_frames(frames, out_path, runtime, fps: int) -> None:
    """Pipe RGB frames to FFmpeg and write out_path. Stubbed in unit tests."""
    if not frames:
        raise ValueError("no frames to encode")
    width, height = frames[0].size
    ffmpeg = runtime.ffmpeg_path or "ffmpeg"
    cmd = [
        ffmpeg, "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{width}x{height}", "-r", str(fps),
        "-i", "-",
        *runtime.video_args,
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(out_path),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None
    for image in frames:
        proc.stdin.write(image.convert("RGB").tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError(f"ffmpeg exited with code {proc.returncode}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_engine.py -q`
Expected: PASS (2 passed — or 1 passed + 1 skipped if FFmpeg is absent).

- [ ] **Step 5: Commit**

```bash
git add pyreeler/engine.py tests/test_engine.py
git commit -m "feat(cli): render engine (frame map + ffmpeg pipe, picklable job)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: CLI (`list`, `render`, TUI seam) + `__main__`

**Files:**
- Create: `pyreeler/cli.py`, `pyreeler/__main__.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_cli.py`:

```python
"""Tests for the pyreeler CLI argument handling and dispatch."""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from pyreeler import cli  # noqa: E402


def test_list_prints_both_recipes(capsys):
    rc = cli.main(["list"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "lorenz" in out and "rossler" in out


def test_render_maps_flags_to_resolved_params(monkeypatch, tmp_path):
    captured = {}
    monkeypatch.setattr(cli, "render_film",
                        lambda recipe, params, out, on_progress=None: captured.update(
                            recipe=recipe.name, params=params, out=out) or out)
    rc = cli.main(["render", "lorenz", "--rho", "30", "--duration", "1",
                   "--fps", "2", "-o", str(tmp_path / "f.mp4")])
    assert rc == 0
    assert captured["recipe"] == "lorenz"
    assert captured["params"]["rho"] == 30.0
    assert captured["params"]["fps"] == 2
    assert captured["out"] == tmp_path / "f.mp4"


def test_render_unknown_recipe_exits_nonzero(capsys):
    rc = cli.main(["render", "loranz"])
    assert rc != 0
    assert "unknown recipe" in capsys.readouterr().err


def test_render_bad_param_exits_nonzero(capsys, monkeypatch):
    monkeypatch.setattr(cli, "render_film", lambda *a, **k: None)
    rc = cli.main(["render", "lorenz", "--palette", "chartreuse"])
    assert rc != 0
    assert "palette" in capsys.readouterr().err
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_cli.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'pyreeler.cli'`.

- [ ] **Step 3: Write minimal implementation**

Create `pyreeler/cli.py`:

```python
"""Command-line interface: `pyreeler list` / `pyreeler render` / (no args -> TUI)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .recipes import (
    get, list_recipes, merged_params, resolve_params,
    UnknownRecipeError, ParamError,
)
from .engine import render_film


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        return _launch_tui()
    command = argv[0]
    if command == "list":
        return _cmd_list()
    if command == "render":
        return _cmd_render(argv[1:])
    # Unknown command: let argparse produce a helpful usage/error.
    _build_parser().parse_args(argv)
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pyreeler", description="Make code-generated films from recipes.")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("list", help="list available recipes")
    render = sub.add_parser("render", help="render a recipe to an mp4")
    render.add_argument("recipe", help="recipe name (see `pyreeler list`)")
    render.add_argument("-o", "--out", default=None, help="output path")
    return parser


def _cmd_list() -> int:
    for recipe in list_recipes():
        print(f"{recipe.name:12} {recipe.summary}")
    return 0


def _cmd_render(args: list[str]) -> int:
    # Stage 1: pull out the recipe name (and -o) so we know which flags exist.
    pre = argparse.ArgumentParser(prog="pyreeler render", add_help=False)
    pre.add_argument("recipe")
    pre.add_argument("-o", "--out", default=None)
    known, _ = pre.parse_known_args(args)
    try:
        recipe = get(known.recipe)
    except UnknownRecipeError as exc:
        print(exc, file=sys.stderr)
        return 2

    # Stage 2: build the real parser with this recipe's generated flags.
    parser = argparse.ArgumentParser(prog=f"pyreeler render {recipe.name}")
    parser.add_argument("recipe")
    parser.add_argument("-o", "--out", default=None)
    for p in merged_params(recipe):
        parser.add_argument(f"--{p.name}", default=None,
                            help=f"{p.help} (default {p.default})")
    namespace = parser.parse_args(args)

    overrides = {p.name: getattr(namespace, p.name)
                 for p in merged_params(recipe)
                 if getattr(namespace, p.name) is not None}
    try:
        params = resolve_params(recipe, overrides)
    except ParamError as exc:
        print(exc, file=sys.stderr)
        return 2

    out = Path(namespace.out) if namespace.out else Path(f"{recipe.name}.mp4")

    def progress(done, total):
        print(f"\rframe {done}/{total}", end="", file=sys.stderr, flush=True)

    render_film(recipe, params, out, on_progress=progress)
    print(f"\nwrote {out}", file=sys.stderr)
    return 0


def _launch_tui() -> int:
    try:
        from .tui.app import run as run_tui
    except ImportError:
        print("The PyReeler TUI needs extra packages. Install them with:\n"
              "    pip install -r requirements-tui.txt", file=sys.stderr)
        return 0
    return run_tui()
```

Create `pyreeler/__main__.py`:

```python
"""Enable `python -m pyreeler`."""
import sys

from .cli import main

sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_cli.py -q`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add pyreeler/cli.py pyreeler/__main__.py tests/test_cli.py
git commit -m "feat(cli): list/render commands with generated per-recipe flags

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 7: Packaging, CI wiring, end-to-end smoke

**Files:**
- Create: `pyproject.toml`, `requirements-tui.txt`
- Modify: `pytest.ini`

- [ ] **Step 1: Create the packaging files**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "pyreeler"
version = "0.1.0"
description = "Make short code-generated films from recipes — CLI + TUI."
requires-python = ">=3.10"
dependencies = ["numpy>=1.21", "pillow>=9.0"]

[project.optional-dependencies]
tui = ["textual>=0.60", "rich>=13.0", "terminaltexteffects>=0.10"]

[project.scripts]
pyreeler = "pyreeler.cli:main"

[tool.setuptools]
packages = ["pyreeler", "pyreeler.recipes", "pyreeler.tui"]
```

Create `requirements-tui.txt`:

```
# PyReeler TUI extras (Plan 2). Install with: pip install -r requirements-tui.txt
textual>=0.60
rich>=13.0
terminaltexteffects>=0.10
```

Note: `pyreeler/tui/` does not exist yet (Plan 2). Create a placeholder so the
declared package imports cleanly — create `pyreeler/tui/__init__.py`:

```python
"""PyReeler TUI front-end (built in Plan 2)."""
```

- [ ] **Step 2: Wire the new tests into pytest**

In `pytest.ini`, extend `testpaths` with the five new files. The block becomes:

```
testpaths =
    tests
    experimental/experiments/test_cosmic_collapse.py
    experimental/tools/test_contact_sheet.py
```

Because `tests` is already a testpath and all new tests live under `tests/`, **no
change to `pytest.ini` is required** — confirm by listing collection in the next step.
(If a future test lands outside `tests/`, add it explicitly.)

- [ ] **Step 3: Verify the whole package imports and the CLI runs**

Run:
```bash
python3 -c "import pyreeler, pyreeler.cli, pyreeler.engine, pyreeler.recipes"
python3 -m pyreeler list
```
Expected: no import error; `python3 -m pyreeler list` prints the `lorenz` and
`rossler` rows.

- [ ] **Step 4: Run all three CI gates + the full suite**

Run: `python3 sync.py --check && python3 graduation_check.py && python3 -m pytest -q`
Expected: sync in-sync; graduation valid; pytest collects the existing suite **plus**
the new recipe/engine/CLI tests, all passing (FFmpeg e2e test passes or skips).

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml requirements-tui.txt pyreeler/tui/__init__.py
git commit -m "build(cli): pyproject console entry, tui extras, package scaffolding

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 8: Document the no-AI CLI path

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add a CLI section to the README**

In `README.md`, immediately after the "Quick Start" section (before "The Beauty of
Math, Rendered" or wherever it reads naturally near the top), add:

```markdown
## Use It Without an AI (CLI)

PyReeler also ships a deterministic command-line renderer — no AI, no API cost,
fully offline. Pick a recipe, turn the knobs, render:

```bash
python3 -m pyreeler list                              # see available recipes
python3 -m pyreeler render lorenz --duration 30 -o butterfly.mp4
python3 -m pyreeler render rossler --c 5.7 --palette amber -o scroll.mp4
```

Every recipe exposes typed, range-checked flags (`--rho`, `--fps`, `--palette`, …);
run `python3 -m pyreeler render <recipe> -h` to see them. Core deps are just
`numpy` + `pillow` + FFmpeg. An interactive TUI front-end is on the way.
```

- [ ] **Step 2: Verify the documented commands actually work**

Run:
```bash
python3 -m pyreeler list
python3 -m pyreeler render lorenz -h
```
Expected: `list` shows both recipes; `-h` shows generated flags including `--rho`,
`--duration`, `--palette`.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: document the no-AI CLI render path

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review Notes

**Spec coverage (Plan 1 portion):**
- Package layout (`pyreeler/`, recipes, engine, cli, `__main__`) → Tasks 1–7.
- Recipe contract (`Param`, `Recipe`, `prepare`/`make_frame`, `STANDARD_PARAMS`,
  `PALETTES`, registry, `UnknownRecipeError`) → Tasks 1, 4.
- Param resolution/validation (`merged_params`, `resolve_params`, `ParamError`) → Task 2.
- v1 recipes lorenz + rossler reusing `attractors` + `rotate_points` → Tasks 3, 4.
- Engine (`render_film`, `_encode_frames` seam, `detect_render_runtime`,
  `ordered_frame_map`, parallel-safe `_FrameJob`) → Task 5.
- CLI (`list`, `render` with generated typed flags, no-arg TUI seam, error exits) → Task 6.
- Packaging (`pyproject.toml` console entry + `tui` extra, `requirements-tui.txt`) → Task 7.
- Testing matrix (registry, params, recipes, engine w/ stubbed encoder + skip-if-no-
  ffmpeg, CLI) and CI-gate compatibility → Tasks 1–7.
- Docs (no-AI CLI path) → Task 8.

**Deferred to Plan 2 (TUI), per spec scope:** `tui/app.py`, `tui/banner.py`
(TerminalTextEffects), `tui/styles.tcss`, the live launch, Sparkline/progress UI.
This plan only leaves the `_launch_tui()` seam + a `tui/__init__.py` placeholder.

**Type/name consistency:** `Param`/`Recipe`/`register`/`get`/`list_recipes`/
`merged_params`/`resolve_params`/`scatter_trail`/`render_film`/`_encode_frames`/
`_FrameJob` are used identically across tasks. `make_frame(prepared, params, idx,
total)` and `prepare(params)` signatures match the spec refinement everywhere.

**No placeholders:** every code step contains complete code; every run step lists the
exact command and expected result.
