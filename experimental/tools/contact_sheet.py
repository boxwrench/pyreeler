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
