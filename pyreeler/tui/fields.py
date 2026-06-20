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
