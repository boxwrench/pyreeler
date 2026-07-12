"""Tests for opening a rendered file in the OS player (no Textual needed)."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from pyreeler.tui import player  # noqa: E402


def test_linux_uses_xdg_open(monkeypatch):
    calls = {}
    monkeypatch.setattr(player.sys, "platform", "linux")
    monkeypatch.setattr(player.subprocess, "Popen",
                        lambda args, **kw: calls.update(args=args))
    path = Path("/tmp/x.mp4")
    player.open_in_player(path)
    assert calls["args"][0] == "xdg-open"
    assert calls["args"][1] == str(path)


def test_macos_uses_open(monkeypatch):
    calls = {}
    monkeypatch.setattr(player.sys, "platform", "darwin")
    monkeypatch.setattr(player.subprocess, "Popen",
                        lambda args, **kw: calls.update(args=args))
    player.open_in_player(Path("/tmp/x.mp4"))
    assert calls["args"][0] == "open"


def test_windows_uses_startfile(monkeypatch):
    calls = {}
    monkeypatch.setattr(player.sys, "platform", "win32")
    monkeypatch.setattr(player.os, "startfile",
                        lambda p: calls.update(path=p), raising=False)
    player.open_in_player(Path("C:/tmp/x.mp4"))
    assert "x.mp4" in calls["path"]
