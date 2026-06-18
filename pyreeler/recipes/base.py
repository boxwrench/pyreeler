"""Recipe registry primitives: Param, Recipe, the registry, and lookups."""
from __future__ import annotations

import difflib
from dataclasses import dataclass
from typing import Any, Callable


class UnknownRecipeError(LookupError):
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
    params: tuple[Param, ...]
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
