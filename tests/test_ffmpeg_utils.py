"""Focused tests for the shared FFmpeg resolver."""

import sys
from types import SimpleNamespace

import pytest

from templates.video import ffmpeg_utils


def test_resolve_ffmpeg_explicit_path_wins(monkeypatch):
    def unexpected_lookup(_name):
        raise AssertionError("PATH lookup should not run for an explicit path")

    monkeypatch.setattr(ffmpeg_utils.shutil, "which", unexpected_lookup)

    assert ffmpeg_utils.resolve_ffmpeg("/opt/custom/ffmpeg") == "/opt/custom/ffmpeg"


def test_resolve_ffmpeg_system_path_wins(monkeypatch):
    monkeypatch.setattr(
        ffmpeg_utils.shutil,
        "which",
        lambda name: "/usr/local/bin/ffmpeg" if name == "ffmpeg" else None,
    )
    monkeypatch.setitem(
        sys.modules,
        "imageio_ffmpeg",
        SimpleNamespace(get_ffmpeg_exe=lambda: pytest.fail("fallback should not run")),
    )

    assert ffmpeg_utils.resolve_ffmpeg() == "/usr/local/bin/ffmpeg"


def test_resolve_ffmpeg_uses_python_fallback_when_path_is_empty(monkeypatch):
    monkeypatch.setattr(ffmpeg_utils.shutil, "which", lambda _name: None)
    monkeypatch.setitem(
        sys.modules,
        "imageio_ffmpeg",
        SimpleNamespace(get_ffmpeg_exe=lambda: "/cache/imageio/ffmpeg"),
    )

    assert ffmpeg_utils.resolve_ffmpeg() == "/cache/imageio/ffmpeg"


def test_resolve_ffmpeg_explains_both_installation_options(monkeypatch):
    monkeypatch.setattr(ffmpeg_utils.shutil, "which", lambda _name: None)
    monkeypatch.setitem(sys.modules, "imageio_ffmpeg", None)

    with pytest.raises(FileNotFoundError) as exc_info:
        ffmpeg_utils.resolve_ffmpeg()

    message = str(exc_info.value)
    assert "system PATH" in message
    assert "pip install imageio-ffmpeg" in message
