# Contact-Sheet Sweep Tool — Design

**Date:** 2026-06-17
**Status:** Approved (design) — ready for implementation plan
**Location of artifact:** `experimental/tools/contact_sheet.py` (+ co-located tests)

---

## Purpose

Turn parameter exploration from a manual edit → render → look loop into a single
call. Given a render function and a list of candidate values for one parameter,
render one representative frame per value and tile them into a single contact-sheet
image for side-by-side visual comparison.

This is the "highest exploration multiplier" item from the project review's future
directions. It answers the question *"which value looks best?"* in one shot.

## Non-goals (YAGNI — explicitly excluded from v1)

- 2D parameter grids (param A × param B). Single-axis sweep only.
- Video/animated cells. One still frame per cell.
- Parallel rendering across variants (closures are usually unpicklable; sequential
  is correct and confusion-free first).
- Animation over time — that is `ParameterSequence`'s job, a perpendicular axis.

Each of these is noted as possible future work, not built now.

## Relationship to existing tools

`ParameterSequence` (`experimental/tools/parameter_sequence.py`) maps **frame → value**:
it animates a parameter *over time within one render*. This tool maps **value → image**:
it varies a parameter *across many separate renders*. They are perpendicular axes
(time vs. variation-space) and do not overlap.

`parallel_render.ordered_frame_map` parallelizes *frames of one film*. A future
parallel version of this tool would parallelize *whole variants* — the same
multiprocessing idea one level up — but that is deferred.

The tool lives in `experimental/tools/` (not `templates/`) because it is an
exploration aid, consistent with the "experimental is a permanent habitat, not a
staging area" philosophy. It follows the import-and-use library convention of the
other tools in that folder (`parameter_sequence.py`, `fm_synth.py`).

## Public API

A single public function plus internal helpers.

```python
def sweep(
    render,                       # Callable[[Any], Image | np.ndarray]
    param: str,                   # parameter name, used in labels
    values: Sequence[Any],        # candidate values to sweep
    out: str | None = None,       # if given, write the contact sheet PNG here
    *,
    cols: int | None = None,      # grid columns; default ceil(sqrt(n))
    labels: bool = True,          # draw a "param=value" caption under each cell
    label_fmt: str = "{param}={value}",
    frames_dir: str | None = None,  # if given, also dump each frame PNG here
    title: str | None = None,     # optional title strip across the top
    pad: int = 8,                 # pixels of padding around/between cells
    bg: tuple[int, int, int] = (0, 0, 0),
) -> Image:
    """Render render(v) for each v in values and tile into a contact sheet.

    Returns the assembled PIL.Image (composable). Writes `out` if provided.
    """
```

### Contract details

- **`render(value)` return type:** accepts a `PIL.Image` **or** an `HxWx3` `uint8`
  numpy array. Normalized internally to a PIL image so the tool composes with the
  numpy-based renderers used across the repo.
- **Return value:** always returns the assembled `PIL.Image` so callers can post-
  process or embed it; writing `out` is a side effect, not the only output.
- **`cols` default:** `ceil(sqrt(n))` for a square-ish grid. Rows derive as
  `ceil(n / cols)`. A short final row is left-aligned; empty trailing cells are
  filled with `bg`.
- **Labels:** when `labels=True`, each cell gets a caption strip below it rendered
  via `PIL.ImageDraw` with the default font, text = `label_fmt.format(param=param,
  value=value)`. The caption strip increases per-cell height.
- **`frames_dir`:** when given, each individual frame is also written as
  `{param}_{index:03d}.png` (index in sweep order) so that once the winning value
  is identified, that exact frame already exists on disk.
- **`title`:** optional single-line title strip across the top of the whole sheet.

### Cell-size policy

Assume uniform cell size (the same render fn typically yields the same dimensions).
If a cell's image differs in size, **pad-center** it onto the max cell size rather
than resizing — resizing would distort the very thing being compared. This is a
one-line guard, not a feature.

## Data flow

```
values ──> for each v: render(v) ──> normalize to PIL ──> [frames]
                                                              │
                          (optional) write each to frames_dir │
                                                              ▼
        compute cols/rows ──> compose grid (+ labels, +title, +pad, bg) ──> sheet
                                                              │
                                       (optional) write sheet to `out`
                                                              ▼
                                                       return sheet
```

## Error handling

- Empty `values` → `ValueError("values must be non-empty")`.
- `render` returns something that is neither a PIL image nor an `HxWx3 uint8`
  array → `TypeError` naming the offending value and what was returned.
- `cols < 1` → `ValueError`.
- A non-uniform cell triggers pad-center (no error), so mixed sizes degrade
  gracefully rather than crashing.

## Testing (TDD, red → green)

Co-located at `experimental/tools/test_contact_sheet.py`, added to `pytest.ini`
`testpaths` so CI runs it. Tests use a tiny synthetic `render` returning solid-color
tiles — deterministic, no heavy deps beyond Pillow/NumPy (already CI deps).

1. **Grid dimensions:** n values with default `cols` → sheet has expected
   width/height (cells × cell size + padding).
2. **`cols` override:** explicit `cols` changes rows/columns as expected.
3. **Value→cell mapping:** sweeping distinct solid colors places each color in the
   correct cell position (sample a pixel from each cell).
4. **Return types:** `render` returning a numpy array and `render` returning a PIL
   image both work and produce identical layout.
5. **Labels:** `labels=True` increases cell height vs `labels=False` (caption strip
   present).
6. **File outputs:** `out` writes a readable PNG; `frames_dir` contains exactly N
   frame PNGs named in sweep order.
7. **Errors:** empty `values` and bad `render` return raise the documented
   exceptions.

## `__main__` demo

Like the other tools, a runnable demo under `if __name__ == "__main__":` that sweeps
a trivial built-in render (e.g. a brightness or hue ramp) and writes a sample sheet,
so the file is self-documenting when run directly.

## Future directions (noted, not built)

- Parallel variant rendering (pickle-safe render contract or process pool).
- 2D sweeps (param A × param B matrix).
- Short animated clip per cell (compose with `ParameterSequence`).
- Graduation into the portable skill if it proves broadly useful.
