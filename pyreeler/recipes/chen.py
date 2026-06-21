"""Chen attractor recipe."""
from __future__ import annotations

from experimental.tools.attractors import generate_chen

from .base import Param, Recipe, PALETTES, register
from ._plot import scatter_trail

PARAMS = (
    Param("a", float, 40.0, help="Chen a parameter"),
    Param("b", float, 3.0, help="Chen b parameter"),
    Param("c", float, 28.0, help="Chen c parameter"),
    Param("points", int, 10000, min=100, help="trajectory integration steps"),
    Param("trail", int, 10000, min=1, help="trail length in points (>=points shows the whole attractor)"),
)


def _prepare(params):
    return generate_chen(
        n_points=params["points"], n_particles=1,
        a=params["a"], b=params["b"], c=params["c"],
    )


def _make_frame(prepared, params, frame_idx, total):
    return scatter_trail(
        prepared, frame_idx, total,
        params["width"], params["height"], params["trail"],
        PALETTES[params["palette"]],
        thickness=params["thickness"],
    )


RECIPE = register(Recipe(
    name="chen",
    summary="Chen strange attractor.",
    description=(
        "The Chen attractor is similar to the Lorenz attractor but has more complex "
        "topological structures. It was discovered by Guanrong Chen and represents a "
        "system connecting the Lorenz and Rössler attractors in the chaotic parameter space."
    ),
    params=PARAMS, prepare=_prepare, make_frame=_make_frame,
))
