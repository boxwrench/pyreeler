"""Aizawa attractor recipe."""
from __future__ import annotations

from experimental.tools.attractors import generate_aizawa

from .base import Param, Recipe, PALETTES, register
from ._plot import scatter_trail

PARAMS = (
    Param("a", float, 0.95, help="Aizawa a parameter"),
    Param("b", float, 0.7, help="Aizawa b parameter"),
    Param("c", float, 0.6, help="Aizawa c parameter"),
    Param("d", float, 3.5, help="Aizawa d parameter"),
    Param("e", float, 0.25, help="Aizawa e parameter"),
    Param("f", float, 0.1, help="Aizawa f parameter"),
    Param("points", int, 10000, min=100, help="trajectory integration steps"),
    Param("trail", int, 10000, min=1, help="trail length in points (>=points shows the whole attractor)"),
)


def _prepare(params):
    return generate_aizawa(
        n_points=params["points"], n_particles=1,
        a=params["a"], b=params["b"], c=params["c"],
        d=params["d"], e=params["e"], f=params["f"],
    )


def _make_frame(prepared, params, frame_idx, total):
    return scatter_trail(
        prepared, frame_idx, total,
        params["width"], params["height"], params["trail"],
        PALETTES[params["palette"]],
        thickness=params["thickness"],
    )


RECIPE = register(Recipe(
    name="aizawa",
    summary="Aizawa attractor — a beautiful spherical swirl.",
    description=(
        "The Aizawa attractor is a 3D strange attractor that creates a visually stunning "
        "sphere-like topological structure. It is governed by a system of differential equations "
        "that map out trajectories looping into an intricate spherical shape with a tube-like center."
    ),
    params=PARAMS, prepare=_prepare, make_frame=_make_frame,
))
