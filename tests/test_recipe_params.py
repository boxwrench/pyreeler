"""Tests for parameter merging, coercion, and validation."""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from pyreeler.recipes import base  # noqa: E402
from pyreeler.recipes import params as P  # noqa: E402


def _recipe():
    return base.Recipe(
        name="t", summary="", params=(base.Param("rho", float, 28.0, min=0, max=100),),
        prepare=lambda p: None, make_frame=lambda pr, p, i, n: None,
    )


def test_merged_params_prepends_standard():
    names = [p.name for p in P.merged_params(_recipe())]
    assert names[:5] == ["duration", "fps", "width", "height", "palette"]
    assert names[-1] == "rho"


def test_resolve_applies_defaults_and_coerces_types():
    out = P.resolve_params(_recipe(), {"rho": "30", "fps": "12"})
    assert out["rho"] == 30.0 and isinstance(out["rho"], float)
    assert out["fps"] == 12 and isinstance(out["fps"], int)
    assert out["duration"] == 30.0  # default applied


def test_resolve_rejects_out_of_range():
    with pytest.raises(P.ParamError):
        P.resolve_params(_recipe(), {"rho": 250})


def test_resolve_rejects_bad_choice():
    with pytest.raises(P.ParamError):
        P.resolve_params(_recipe(), {"palette": "chartreuse"})


def test_resolve_rejects_unknown_param():
    with pytest.raises(P.ParamError):
        P.resolve_params(_recipe(), {"nope": 1})


def test_resolve_rejects_below_min():
    with pytest.raises(P.ParamError):
        P.resolve_params(_recipe(), {"rho": -1})


def test_resolve_rejects_bad_type_coercion():
    with pytest.raises(P.ParamError):
        P.resolve_params(_recipe(), {"fps": "notanumber"})
