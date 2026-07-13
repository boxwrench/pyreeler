"""Behavioral tests for portable render-runtime assembly."""

from templates.video import render_runtime
from templates.video.ffmpeg_utils import HardwareProfile


def host(*, workers=3, encoder="h264_amf"):
    return HardwareProfile(
        profile="AMD_AMF",
        encoder=encoder,
        workers=workers,
        ffmpeg_path="/opt/ffmpeg",
    )


def test_detect_render_runtime_uses_validated_host_profile(monkeypatch):
    monkeypatch.setattr(render_runtime, "detect_host_profile", lambda path: host())
    monkeypatch.setattr(
        render_runtime,
        "encoder_args_for_portable",
        lambda encoder: ["-c:v", encoder, "-quality", "balanced"],
    )

    runtime = render_runtime.detect_render_runtime("/opt/ffmpeg")

    assert runtime.profile == "AMD_AMF"
    assert runtime.ffmpeg_path == "/opt/ffmpeg"
    assert runtime.encoder == "h264_amf"
    assert runtime.workers == 3
    assert runtime.video_args == ("-c:v", "h264_amf", "-quality", "balanced")


def test_worker_override_is_clamped_without_changing_encoder(monkeypatch):
    monkeypatch.setattr(render_runtime, "detect_host_profile", lambda _path: host(workers=8, encoder="libx264"))

    runtime = render_runtime.detect_render_runtime(workers=0)

    assert runtime.workers == 1
    assert runtime.encoder == "libx264"
    assert runtime.video_args[:4] == ("-c:v", "libx264", "-preset", "veryfast")
