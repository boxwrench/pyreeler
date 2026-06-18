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
