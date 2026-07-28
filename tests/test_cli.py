"""Tests for the pyreeler CLI argument handling and dispatch."""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from pyreeler import cli  # noqa: E402


def test_list_prints_both_recipes(capsys):
    rc = cli.main(["list"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "lorenz" in out and "rossler" in out


def test_render_maps_flags_to_resolved_params(monkeypatch, tmp_path):
    captured = {}
    monkeypatch.setattr(cli, "render_film",
                        lambda recipe, params, out, on_progress=None: captured.update(
                            recipe=recipe.name, params=params, out=out) or out)
    rc = cli.main(["render", "lorenz", "--rho", "30", "--duration", "1",
                   "--fps", "2", "-o", str(tmp_path / "f.mp4")])
    assert rc == 0
    assert captured["recipe"] == "lorenz"
    assert captured["params"]["rho"] == 30.0
    assert captured["params"]["fps"] == 2
    assert captured["out"] == tmp_path / "f.mp4"


def test_render_without_out_defaults_to_videos_and_never_clobbers(monkeypatch, tmp_path):
    # ~/Videos resolves via $HOME on POSIX / %USERPROFILE% on Windows; sandbox it.
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    captured = {}
    monkeypatch.setattr(cli, "render_film",
                        lambda recipe, params, out, on_progress=None: captured.update(out=out))
    # no -o -> lands under ~/Videos with the plain base name
    rc = cli.main(["render", "lorenz", "--duration", "1", "--fps", "2"])
    assert rc == 0
    assert captured["out"] == tmp_path / "Videos" / "lorenz.mp4"
    # the CLI created the destination dir for us
    assert (tmp_path / "Videos").is_dir()
    # once a render exists there, the next default render must not overwrite it
    (tmp_path / "Videos" / "lorenz.mp4").touch()
    cli.main(["render", "lorenz", "--duration", "1", "--fps", "2"])
    assert captured["out"] == tmp_path / "Videos" / "lorenz-2.mp4"


def test_render_unknown_recipe_exits_nonzero(capsys):
    rc = cli.main(["render", "loranz"])
    assert rc != 0
    assert "unknown recipe" in capsys.readouterr().err


def test_render_bad_param_exits_nonzero(capsys, monkeypatch):
    monkeypatch.setattr(cli, "render_film", lambda *a, **k: None)
    rc = cli.main(["render", "lorenz", "--palette", "chartreuse"])
    assert rc != 0
    assert "palette" in capsys.readouterr().err
