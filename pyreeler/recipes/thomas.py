"""Thomas cyclically symmetric attractor recipe."""
from __future__ import annotations

from experimental.tools.attractors import generate_thomas

from .base import Param, Recipe, PALETTES, register
from ._plot import scatter_trail

PARAMS = (
    Param("b", float, 0.208186, help="Thomas dissipation parameter b"),
    Param("points", int, 10000, min=100, help="trajectory integration steps"),
    Param("trail", int, 10000, min=1, help="trail length in points (>=points shows the whole attractor)"),
)


def _prepare(params):
    return generate_thomas(
        n_points=params["points"], n_particles=1,
        b=params["b"],
    )


def _make_frame(prepared, params, frame_idx, total):
    return scatter_trail(
        prepared, frame_idx, total,
        params["width"], params["height"], params["trail"],
        PALETTES[params["palette"]],
        thickness=params["thickness"],
    )


RECIPE = register(Recipe(
    name="thomas",
    summary="Thomas cyclically symmetric attractor.",
    description=(
        "Thomas' cyclically symmetric attractor is a 3D strange attractor originally proposed "
        "by René Thomas. It has a simple set of equations that are cyclically symmetric "
        "in the x, y, and z variables, forming a complex, highly symmetric lattice-like structure."
    ),
    params=PARAMS, prepare=_prepare, make_frame=_make_frame,
))
