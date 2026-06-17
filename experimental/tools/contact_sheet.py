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
