"""Tests for the streaming render engine."""
import gc
import shutil
import sys
import weakref
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


def test_render_film_streams_frames_and_reports_progress(tmp_path, monkeypatch):
    monkeypatch.setattr(engine, "detect_render_runtime", lambda: _FakeRuntime())
    captured = {}

    def consume(frames, out, runtime, fps):
        assert not isinstance(frames, (list, tuple))
        refs = []
        values = []
        for frame in frames:
            refs.append(weakref.ref(frame))
            values.append(frame.getpixel((0, 0))[0])
            del frame
            gc.collect()
            assert sum(ref() is not None for ref in refs) <= 1
        captured.update(values=values, live=sum(ref() is not None for ref in refs))

    monkeypatch.setattr(engine, "_encode_frames", consume)
    seen = []
    params = {
        "duration": 1.0,
        "fps": 5,
        "width": 32,
        "height": 24,
        "palette": "phosphor",
    }
    out = engine.render_film(
        _solid_recipe(),
        params,
        tmp_path / "x.mp4",
        on_progress=lambda done, total: seen.append((done, total)),
    )

    assert captured == {"values": [0, 1, 2, 3, 4], "live": 0}
    assert seen == [(1, 5), (2, 5), (3, 5), (4, 5), (5, 5)]
    assert out == tmp_path / "x.mp4"


def test_encode_frames_rejects_empty_iterator(tmp_path):
    with pytest.raises(ValueError, match="no frames"):
        engine._encode_frames(iter(()), tmp_path / "x.mp4", _FakeRuntime(), 4)


def test_encode_frames_surfaces_ffmpeg_stderr_after_broken_pipe(
    tmp_path, monkeypatch
):
    class Pipe:
        def write(self, _data):
            raise BrokenPipeError

        def close(self):
            pass

    class Process:
        stdin = Pipe()

        def wait(self):
            return 7

    def popen(_cmd, *, stdin, stderr):
        assert stdin is engine.subprocess.PIPE
        stderr.write(b"encoder exploded")
        return Process()

    monkeypatch.setattr(engine.subprocess, "Popen", popen)
    frame = Image.new("RGB", (8, 6))
    with pytest.raises(RuntimeError, match="ffmpeg exited with code 7: encoder exploded"):
        engine._encode_frames(iter([frame]), tmp_path / "x.mp4", _FakeRuntime(), 4)


def test_encode_frames_reaps_ffmpeg_when_frame_generation_fails(
    tmp_path, monkeypatch
):
    class Pipe:
        def write(self, _data):
            pass

        def close(self):
            pass

    class Process:
        stdin = Pipe()
        waited = False

        def wait(self):
            self.waited = True
            return 0

    process = Process()
    monkeypatch.setattr(engine.subprocess, "Popen", lambda *args, **kwargs: process)

    first = Image.new("RGB", (8, 6))

    def frames():
        yield first
        raise LookupError("frame failed")

    with pytest.raises(LookupError, match="frame failed"):
        engine._encode_frames(frames(), tmp_path / "x.mp4", _FakeRuntime(), 4)
    assert process.waited

@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_render_film_writes_real_mp4(tmp_path):
    import pyreeler.recipes as recipes

    recipe = recipes.get("lorenz")
    params = recipes.resolve_params(
        recipe,
        {
            "duration": 1.0,
            "fps": 4,
            "points": 800,
            "width": 160,
            "height": 120,
        },
    )
    out = engine.render_film(recipe, params, tmp_path / "lorenz.mp4")
    assert out.exists() and out.stat().st_size > 0
