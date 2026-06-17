# Contact-Sheet Sweep Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Add `experimental/tools/contact_sheet.py` — a `sweep()` function that renders one frame per parameter value and tiles them into a single contact-sheet image for side-by-side comparison.

**Status:** Completed through commit `eb6fa94`; follow-up docs landed in `04b3eed`.

**Architecture:** A pure library (import-and-use, like the other `experimental/tools/` modules). `sweep(render, param, values, ...)` calls a user-supplied `render(value)` callable for each value, normalizes each result (PIL image or `HxWx3 uint8` numpy array) to a PIL image, then composes a grid with optional per-cell captions and a title. Sequential only (no multiprocessing — render callables are usually unpicklable closures).

**Tech Stack:** Python 3.10+, NumPy, Pillow, pytest. No new dependencies (all already CI deps).

**Spec:** `docs/superpowers/specs/2026-06-17-contact-sheet-tool-design.md`

---

## File Structure

- Create: `experimental/tools/contact_sheet.py` — the `sweep()` function + `_to_image`/`_paste_centered` helpers + a `__main__` demo.
- Create: `experimental/tools/test_contact_sheet.py` — co-located pytest tests.
- Modify: `pytest.ini` — add the new test file to `testpaths` so CI runs it.

All three files follow existing repo conventions: tool docstring-with-Usage header (like `fm_synth.py`), co-located test importing via `sys.path.insert` (like `tests/test_sync.py`).

---

## Task 1: Module scaffold + image normalization helper

**Files:**
- Create: `experimental/tools/contact_sheet.py`
- Create: `experimental/tools/test_contact_sheet.py`

- [x] **Step 1: Write the failing test**

Create `experimental/tools/test_contact_sheet.py`:

```python
"""Tests for contact_sheet.py — the parameter-sweep contact-sheet tool.

Tests use tiny synthetic render functions returning solid-color tiles, so they
are deterministic and need only Pillow/NumPy (already CI deps).
"""
import os
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

from contact_sheet import _to_image  # noqa: E402


def test_to_image_accepts_numpy_uint8():
    arr = np.zeros((4, 6, 3), dtype=np.uint8)
    img = _to_image(arr, value=1)
    assert isinstance(img, Image.Image)
    assert img.size == (6, 4)  # PIL size is (width, height)


def test_to_image_accepts_pil():
    src = Image.new("RGB", (6, 4), (10, 20, 30))
    img = _to_image(src, value=1)
    assert isinstance(img, Image.Image)
    assert img.size == (6, 4)


def test_to_image_rejects_wrong_array_shape():
    arr = np.zeros((4, 6), dtype=np.uint8)  # missing channel axis
    with pytest.raises(TypeError):
        _to_image(arr, value=7)


def test_to_image_rejects_wrong_type():
    with pytest.raises(TypeError):
        _to_image("not an image", value=7)
```

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest experimental/tools/test_contact_sheet.py -q`
Expected: FAIL — `ImportError: cannot import name '_to_image'` (module/file does not exist yet).

- [x] **Step 3: Write minimal implementation**

Create `experimental/tools/contact_sheet.py`:

```python
"""Contact-sheet sweep tool for PyReeler experimental.

Render one frame per parameter value and tile them into a single image for
side-by-side visual comparison — turning "which value looks best?" into one call.

Usage:
    from experimental.tools.contact_sheet import sweep

    def render(threshold):
        return my_pixel_sort(img, threshold)   # PIL.Image or HxWx3 uint8 array

    sweep(render, "threshold", [50, 100, 150, 200], out="sheet.png")
"""
from __future__ import annotations

import math
import os
from typing import Any, Callable, Sequence

import numpy as np
from PIL import Image, ImageDraw


def _to_image(obj: Any, value: Any) -> Image.Image:
    """Normalize a render result to an RGB PIL image.

    Accepts a PIL.Image or an HxWx3 uint8 numpy array. Raises TypeError with a
    message naming the offending value otherwise.
    """
    if isinstance(obj, Image.Image):
        return obj.convert("RGB")
    if isinstance(obj, np.ndarray):
        if obj.ndim == 3 and obj.shape[2] == 3 and obj.dtype == np.uint8:
            return Image.fromarray(obj, mode="RGB")
        raise TypeError(
            f"render({value!r}) returned a numpy array of shape {obj.shape} "
            f"dtype {obj.dtype}; expected HxWx3 uint8"
        )
    raise TypeError(
        f"render({value!r}) returned {type(obj).__name__}; "
        f"expected PIL.Image or HxWx3 uint8 numpy array"
    )
```

- [x] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest experimental/tools/test_contact_sheet.py -q`
Expected: PASS (4 passed).

- [x] **Step 5: Commit**

```bash
git add experimental/tools/contact_sheet.py experimental/tools/test_contact_sheet.py
git commit -m "feat(contact-sheet): add render-result normalization helper

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: `sweep()` core — grid layout, value→cell mapping, errors

**Files:**
- Modify: `experimental/tools/contact_sheet.py`
- Modify: `experimental/tools/test_contact_sheet.py`

This task builds the grid composition (no labels/title/file-writing yet — those land in Tasks 3–4). All tests here pass `labels=False` so they stay valid after Task 3 adds caption height.

- [x] **Step 1: Write the failing tests**

Append to `experimental/tools/test_contact_sheet.py`:

```python
from contact_sheet import sweep  # noqa: E402


def _solid(width=20, height=20):
    """Render factory: returns a render fn producing solid tiles colored by value.

    The value is expected to be an (r, g, b) tuple so each cell is distinct.
    """
    def render(value):
        arr = np.zeros((height, width, 3), dtype=np.uint8)
        arr[:, :] = value
        return arr
    return render


def test_default_grid_is_square_ish():
    render = lambda v: np.zeros((20, 30, 3), dtype=np.uint8)  # 30 wide, 20 tall
    sheet = sweep(render, "v", [1, 2, 3, 4], labels=False, pad=0)
    # n=4 -> cols=ceil(sqrt(4))=2, rows=2; cell 30x20 -> 60x40
    assert sheet.size == (60, 40)


def test_cols_override_changes_layout():
    render = lambda v: np.zeros((20, 30, 3), dtype=np.uint8)
    sheet = sweep(render, "v", [1, 2, 3, 4], cols=4, labels=False, pad=0)
    # cols=4, rows=1 -> 120x20
    assert sheet.size == (120, 20)


def test_each_value_lands_in_its_cell():
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
    sheet = sweep(_solid(20, 20), "rgb", colors, cols=2, labels=False, pad=0)
    for i, color in enumerate(colors):
        r, c = divmod(i, 2)
        px = sheet.getpixel((c * 20 + 10, r * 20 + 10))  # cell center
        assert px == color


def test_accepts_pil_and_numpy_renders():
    arr_render = lambda v: np.full((20, 20, 3), 128, dtype=np.uint8)
    pil_render = lambda v: Image.new("RGB", (20, 20), (128, 128, 128))
    a = sweep(arr_render, "v", [1, 2], labels=False, pad=0)
    b = sweep(pil_render, "v", [1, 2], labels=False, pad=0)
    assert a.size == b.size


def test_empty_values_raises():
    with pytest.raises(ValueError):
        sweep(lambda v: np.zeros((2, 2, 3), np.uint8), "v", [])


def test_bad_cols_raises():
    with pytest.raises(ValueError):
        sweep(lambda v: np.zeros((2, 2, 3), np.uint8), "v", [1], cols=0)
```

- [x] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest experimental/tools/test_contact_sheet.py -q`
Expected: FAIL — `ImportError: cannot import name 'sweep'`.

- [x] **Step 3: Write minimal implementation**

Append to `experimental/tools/contact_sheet.py`:

```python
def _paste_centered(canvas: Image.Image, img: Image.Image,
                    box_x: int, box_y: int, box_w: int, box_h: int) -> None:
    """Paste img centered inside the (box_x, box_y, box_w, box_h) cell.

    Centering (rather than resizing) avoids distorting images whose size differs
    from the cell — the comparison stays honest.
    """
    off_x = box_x + (box_w - img.width) // 2
    off_y = box_y + (box_h - img.height) // 2
    canvas.paste(img, (off_x, off_y))


def sweep(
    render: Callable[[Any], Any],
    param: str,
    values: Sequence[Any],
    out: str | None = None,
    *,
    cols: int | None = None,
    labels: bool = True,
    label_fmt: str = "{param}={value}",
    frames_dir: str | None = None,
    title: str | None = None,
    pad: int = 8,
    bg: tuple[int, int, int] = (0, 0, 0),
) -> Image.Image:
    """Render one frame per value and tile them into a contact sheet.

    Args:
        render: Callable taking a value, returning a PIL.Image or HxWx3 uint8 array.
        param: Parameter name (used in captions).
        values: Candidate values to sweep.
        out: If given, write the assembled sheet PNG to this path.
        cols: Grid columns; defaults to ceil(sqrt(n)) for a square-ish grid.
        labels: Draw a "param=value" caption under each cell.
        label_fmt: Caption format string; receives param= and value=.
        frames_dir: If given, also write each individual frame here.
        title: Optional title strip across the top.
        pad: Pixels of padding around and between cells.
        bg: Background RGB color.

    Returns:
        The assembled PIL.Image (also written to `out` if provided).
    """
    values = list(values)
    if not values:
        raise ValueError("values must be non-empty")
    if cols is not None and cols < 1:
        raise ValueError("cols must be >= 1")

    frames = [_to_image(render(v), v) for v in values]

    n = len(frames)
    if cols is None:
        cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)

    cell_w = max(img.width for img in frames)
    cell_h = max(img.height for img in frames)

    sheet_w = pad + cols * (cell_w + pad)
    sheet_h = pad + rows * (cell_h + pad)

    sheet = Image.new("RGB", (sheet_w, sheet_h), bg)

    for i, img in enumerate(frames):
        r = i // cols
        c = i % cols
        box_x = pad + c * (cell_w + pad)
        box_y = pad + r * (cell_h + pad)
        _paste_centered(sheet, img, box_x, box_y, cell_w, cell_h)

    if out is not None:
        sheet.save(out)

    return sheet
```

- [x] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest experimental/tools/test_contact_sheet.py -q`
Expected: PASS (10 passed total).

- [x] **Step 5: Commit**

```bash
git add experimental/tools/contact_sheet.py experimental/tools/test_contact_sheet.py
git commit -m "feat(contact-sheet): add sweep() grid composition

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Captions and title

**Files:**
- Modify: `experimental/tools/contact_sheet.py`
- Modify: `experimental/tools/test_contact_sheet.py`

- [x] **Step 1: Write the failing tests**

Append to `experimental/tools/test_contact_sheet.py`:

```python
def test_labels_increase_height():
    render = lambda v: np.zeros((20, 20, 3), dtype=np.uint8)
    no_labels = sweep(render, "v", [1, 2], labels=False, pad=0)
    with_labels = sweep(render, "v", [1, 2], labels=True, pad=0)
    assert with_labels.height > no_labels.height


def test_title_increases_height():
    render = lambda v: np.zeros((20, 20, 3), dtype=np.uint8)
    without = sweep(render, "v", [1, 2], labels=False, pad=0)
    withtitle = sweep(render, "v", [1, 2], labels=False, pad=0, title="sweep")
    assert withtitle.height > without.height
```

- [x] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest experimental/tools/test_contact_sheet.py -q`
Expected: FAIL — `test_labels_increase_height` and `test_title_increases_height` fail (heights equal: caption/title not yet reserved).

- [x] **Step 3: Write minimal implementation**

In `experimental/tools/contact_sheet.py`, replace the body of `sweep()` from the
`cell_w = ...` line through the `return sheet` line with this version (adds caption
and title height + drawing):

```python
    cell_w = max(img.width for img in frames)
    cell_h = max(img.height for img in frames)

    caption_h = 16 if labels else 0
    full_cell_h = cell_h + caption_h
    title_h = 20 if title else 0

    sheet_w = pad + cols * (cell_w + pad)
    sheet_h = pad + title_h + rows * (full_cell_h + pad)

    sheet = Image.new("RGB", (sheet_w, sheet_h), bg)
    draw = ImageDraw.Draw(sheet)

    if title:
        draw.text((pad, pad // 2), title, fill=(255, 255, 255))

    for i, (value, img) in enumerate(zip(values, frames)):
        r = i // cols
        c = i % cols
        box_x = pad + c * (cell_w + pad)
        box_y = pad + title_h + r * (full_cell_h + pad)
        _paste_centered(sheet, img, box_x, box_y, cell_w, cell_h)
        if labels:
            caption = label_fmt.format(param=param, value=value)
            draw.text((box_x, box_y + cell_h + 2), caption, fill=(255, 255, 255))

    if out is not None:
        sheet.save(out)

    return sheet
```

- [x] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest experimental/tools/test_contact_sheet.py -q`
Expected: PASS (12 passed). The Task 2 layout tests still pass because they use
`labels=False` and no `title`, so `caption_h` and `title_h` are both 0.

- [x] **Step 5: Commit**

```bash
git add experimental/tools/contact_sheet.py experimental/tools/test_contact_sheet.py
git commit -m "feat(contact-sheet): draw per-cell captions and optional title

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: File outputs — `out` and `frames_dir`

**Files:**
- Modify: `experimental/tools/contact_sheet.py`
- Modify: `experimental/tools/test_contact_sheet.py`

`out` writing already exists from Task 2. This task adds `frames_dir` dumping and
verifies both output paths.

- [x] **Step 1: Write the failing tests**

Append to `experimental/tools/test_contact_sheet.py`:

```python
def test_writes_out_png(tmp_path):
    render = lambda v: np.zeros((20, 20, 3), dtype=np.uint8)
    out = tmp_path / "sheet.png"
    sweep(render, "thr", [10, 20, 30], out=str(out))
    assert out.exists()
    Image.open(out).verify()  # raises if not a valid image


def test_writes_individual_frames(tmp_path):
    render = lambda v: np.zeros((20, 20, 3), dtype=np.uint8)
    frames = tmp_path / "frames"
    sweep(render, "thr", [10, 20, 30], frames_dir=str(frames))
    written = sorted(os.listdir(frames))
    assert written == ["thr_000.png", "thr_001.png", "thr_002.png"]
```

- [x] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest experimental/tools/test_contact_sheet.py -q`
Expected: `test_writes_out_png` PASSES already (out implemented in Task 2);
`test_writes_individual_frames` FAILS — `frames_dir` directory is never created.

- [x] **Step 3: Write minimal implementation**

In `experimental/tools/contact_sheet.py`, immediately after the
`frames = [_to_image(render(v), v) for v in values]` line, insert the frame-dump block:

```python
    frames = [_to_image(render(v), v) for v in values]

    if frames_dir is not None:
        os.makedirs(frames_dir, exist_ok=True)
        for i, img in enumerate(frames):
            img.save(os.path.join(frames_dir, f"{param}_{i:03d}.png"))

```

- [x] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest experimental/tools/test_contact_sheet.py -q`
Expected: PASS (14 passed).

- [x] **Step 5: Commit**

```bash
git add experimental/tools/contact_sheet.py experimental/tools/test_contact_sheet.py
git commit -m "feat(contact-sheet): optionally dump individual frame PNGs

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: `__main__` demo, CI wiring, full-suite verification

**Files:**
- Modify: `experimental/tools/contact_sheet.py`
- Modify: `pytest.ini`

- [x] **Step 1: Add the runnable demo**

Append to `experimental/tools/contact_sheet.py`:

```python
if __name__ == "__main__":
    # Demo: sweep a brightness ramp and write a sample contact sheet.
    def _demo_render(brightness):
        return np.full((80, 120, 3), brightness, dtype=np.uint8)

    sheet = sweep(
        _demo_render,
        "brightness",
        [0, 64, 128, 192, 255],
        out="contact_sheet_demo.png",
        title="brightness sweep",
    )
    print(f"Wrote contact_sheet_demo.png ({sheet.width}x{sheet.height})")
```

- [x] **Step 2: Verify the demo runs**

Run: `cd experimental/tools && python3 contact_sheet.py && rm -f contact_sheet_demo.png && cd -`
Expected: prints `Wrote contact_sheet_demo.png (NNNxNNN)` with no traceback.

- [x] **Step 3: Wire the test into pytest testpaths**

In `pytest.ini`, change:

```
testpaths =
    tests
    experimental/experiments/test_cosmic_collapse.py
```

to:

```
testpaths =
    tests
    experimental/experiments/test_cosmic_collapse.py
    experimental/tools/test_contact_sheet.py
```

- [x] **Step 4: Run the full default suite + sync drift guard**

Run: `python3 sync.py --check && python3 -m pytest -q`
Expected: sync prints in-sync; pytest collects the existing suite **plus** the 14
new contact-sheet tests, all passing.

- [x] **Step 5: Commit**

```bash
git add experimental/tools/contact_sheet.py pytest.ini
git commit -m "feat(contact-sheet): add demo and wire tests into CI

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: Documentation

**Files:**
- Modify: `experimental/README.md`
- Modify: `docs/plans/2026-06-17-review-improvements.md`

- [x] **Step 1: Document the tool in the experimental README**

In `experimental/README.md`, under the `### Visual` techniques table area or the
tools listing, add a short entry describing `contact_sheet.sweep` (parameter sweep →
tiled comparison image). Match the surrounding table/prose style. Example row to add
under a "Tools" mention:

```markdown
- `contact_sheet.py` — `sweep(render, param, values)` renders one frame per value
  and tiles them into a single comparison image. Fast "which value looks best?" loop.
```

- [x] **Step 2: Mark the future direction as delivered**

In `docs/plans/2026-06-17-review-improvements.md`, in the FUTURE DIRECTIONS list,
update item 2 (ParameterSequence-driven batch render / contact-sheet tool) to note
it is delivered as `experimental/tools/contact_sheet.py` (single-axis sweep; 2D
grids and parallel variants remain future work).

- [x] **Step 3: Commit**

```bash
git add experimental/README.md docs/plans/2026-06-17-review-improvements.md
git commit -m "docs: document contact-sheet sweep tool

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review Notes

**Spec coverage:** every spec section maps to a task —
- `sweep` signature + contract → Tasks 2–4
- numpy/PIL normalization + TypeErrors → Task 1
- grid/`cols` default `ceil(sqrt(n))` → Task 2
- pad-center cell policy → Task 2 (`_paste_centered`)
- labels + title → Task 3
- `out` + `frames_dir` (`{param}_{index:03d}.png`) → Tasks 2 & 4
- error handling (empty values, bad cols, bad render return) → Tasks 1–2
- testing matrix (7 spec items) → covered across Tasks 1–4 (14 tests)
- `__main__` demo → Task 5
- CI wiring → Task 5

**Type/name consistency:** `sweep`, `_to_image`, `_paste_centered` used identically
across all tasks. Signature in Task 2 is the final signature; Tasks 3–4 only fill in
behavior for already-declared kwargs (`labels`, `title`, `frames_dir`).

**No placeholders:** every code step shows complete code; every run step shows the
exact command and expected result.
