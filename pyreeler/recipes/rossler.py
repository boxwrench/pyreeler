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
