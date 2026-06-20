"""Tests for the TUI launch banner. The animated path needs a real TTY, so these
exercise the deterministic static fallback (what runs under pytest's captured IO)."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from pyreeler.tui import banner  # noqa: E402


def test_render_banner_returns_multiline_logo(capsys):
    out = banner.render_banner(animate=False)
    assert out.count("\n") >= 5          # a multi-line ASCII logo
    assert capsys.readouterr().out.strip()  # it printed something


def test_render_banner_animate_is_safe_without_tty(capsys):
    # Under pytest stdout is not a TTY, so animate=True must fall back, never raise,
    # and must not blow up even if TerminalTextEffects' API differs.
    out = banner.render_banner(animate=True)
    assert out.count("\n") >= 5
