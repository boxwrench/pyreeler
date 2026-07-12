"""Focused tests for the shared FFmpeg resolver."""

import subprocess
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


def test_encoder_smoke_test_exercises_encoder_at_subprocess_boundary(monkeypatch):
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(ffmpeg_utils.subprocess, "run", fake_run)

    assert ffmpeg_utils.encoder_smoke_test("/opt/ffmpeg", "h264_nvenc") is True
    command, kwargs = calls[0]
    assert command[0] == "/opt/ffmpeg"
    assert command[command.index("-c:v") + 1] == "h264_nvenc"
    assert command[-2:] == ["null", "-"]
    assert kwargs == {"capture_output": True, "text": True, "check": False, "timeout": 5}


def test_encoder_smoke_test_rejects_failed_encoder_initialization(monkeypatch):
    monkeypatch.setattr(
        ffmpeg_utils.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=1),
    )

    assert ffmpeg_utils.encoder_smoke_test("ffmpeg", "h264_amf") is False


def test_default_encoder_candidates_are_only_nvidia_amd_and_cpu():
    assert ffmpeg_utils.PORTABLE_ENCODER_ORDER == (
        "h264_nvenc",
        "h264_amf",
        "libx264",
    )
    assert not {
        "h264_qsv",
        "h264_videotoolbox",
        "h264_vaapi",
    }.intersection(ffmpeg_utils.PORTABLE_ENCODER_ORDER)


@pytest.mark.parametrize(
    ("working", "expected", "probed"),
    [
        ({"h264_nvenc"}, "h264_nvenc", ["h264_nvenc"]),
        (
            {"h264_amf"},
            "h264_amf",
            ["h264_nvenc", "h264_amf"],
        ),
        (
            {"libx264"},
            "libx264",
            ["h264_nvenc", "h264_amf", "libx264"],
        ),
    ],
)
def test_encoder_selection_uses_first_working_candidate(
    monkeypatch, working, expected, probed
):
    calls = []

    def fake_smoke_test(ffmpeg_path, encoder):
        assert ffmpeg_path == "/opt/ffmpeg"
        calls.append(encoder)
        return encoder in working

    monkeypatch.setattr(ffmpeg_utils, "encoder_smoke_test", fake_smoke_test)

    assert ffmpeg_utils.pick_portable_video_encoder("/opt/ffmpeg") == expected
    assert calls == probed


@pytest.mark.parametrize(
    ("encoder", "expected"),
    [
        (
            "h264_nvenc",
            ["-c:v", "h264_nvenc", "-preset", "p5", "-cq", "22", "-b:v", "0"],
        ),
        (
            "h264_amf",
            ["-c:v", "h264_amf", "-quality", "balanced", "-qp_i", "22", "-qp_p", "24"],
        ),
        (
            "libx264",
            ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23"],
        ),
    ],
)
def test_supported_encoder_arguments(encoder, expected):
    assert ffmpeg_utils.encoder_args_for_portable(encoder) == expected


def test_encoder_selection_raises_when_no_candidate_works(monkeypatch):
    probed = []

    def reject_candidate(_ffmpeg_path, encoder):
        probed.append(encoder)
        return False

    monkeypatch.setattr(ffmpeg_utils, "encoder_smoke_test", reject_candidate)

    with pytest.raises(RuntimeError, match="(?i)no working.*encoder") as exc_info:
        ffmpeg_utils.pick_portable_video_encoder("/opt/ffmpeg")

    message = str(exc_info.value)
    assert "h264_nvenc" in message
    assert "h264_amf" in message
    assert "libx264" in message
    assert probed == list(ffmpeg_utils.PORTABLE_ENCODER_ORDER)


@pytest.mark.parametrize(
    "error",
    [
        subprocess.TimeoutExpired(cmd=["ffmpeg"], timeout=5),
        OSError("could not launch ffmpeg"),
    ],
)
def test_encoder_smoke_test_treats_probe_errors_as_failure(monkeypatch, error):
    def fail_probe(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(ffmpeg_utils.subprocess, "run", fail_probe)

    assert ffmpeg_utils.encoder_smoke_test("ffmpeg", "h264_nvenc") is False
