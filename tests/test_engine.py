"""Tests for the render engine (frame pipeline; encoder is stubbed)."""
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from pyreeler import engine  # noqa: E402
from pyreeler.recipes.base import Recipe  # noqa: E402


class _FakeRuntime:
    ffmpeg_path = "ffmpeg"
    video_args = ("-c:v", "libx264")
    workers = 1


def _solid_recipe():
    return Recipe(
        name="solid", summary="", params=(),
        prepare=lambda params: None,
        make_frame=lambda prepared, params, i, total: Image.fromarray(
            np.full((params["height"], params["width"], 3), i, dtype=np.uint8), "RGB"
        ),
    )


def test_render_film_iterates_all_frames_and_reports_progress(tmp_path, monkeypatch):
    monkeypatch.setattr(engine, "detect_render_runtime", lambda: _FakeRuntime())
    captured = {}
    monkeypatch.setattr(engine, "_encode_frames",
                        lambda frames, out, runtime, fps: captured.update(
                            n=len(frames), size=frames[0].size))
    seen = []
    params = {"duration": 1.0, "fps": 5, "width": 32, "height": 24, "palette": "phosphor"}
    out = engine.render_film(_solid_recipe(), params, tmp_path / "x.mp4",
                             on_progress=lambda d, t: seen.append((d, t)))
    assert captured["n"] == 5            # duration*fps frames
    assert captured["size"] == (32, 24)  # (width, height)
    assert seen[-1] == (5, 5)            # progress reached the end
    assert out == tmp_path / "x.mp4"


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_render_film_writes_real_mp4(tmp_path):
    import pyreeler.recipes as recipes
    r = recipes.get("lorenz")
    params = recipes.resolve_params(r, {"duration": 0.5, "fps": 4, "points": 800,
                                        "width": 160, "height": 120})
    out = engine.render_film(r, params, tmp_path / "lorenz.mp4")
    assert out.exists() and out.stat().st_size > 0
