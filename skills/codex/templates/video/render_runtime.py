from __future__ import annotations

from dataclasses import dataclass

from .ffmpeg_utils import HardwareProfile, detect_host_profile, encoder_args_for_portable


@dataclass(frozen=True)
class RenderRuntime:
    profile: str
    ffmpeg_path: str
    encoder: str
    workers: int
    video_args: tuple[str, ...]


def detect_render_runtime(ffmpeg_path=None, workers: int | None = None) -> RenderRuntime:
    host: HardwareProfile = detect_host_profile(ffmpeg_path)
    chosen_workers = max(1, workers) if workers is not None else host.workers
    return RenderRuntime(
        profile=host.profile,
        ffmpeg_path=host.ffmpeg_path or "",
        encoder=host.encoder,
        workers=chosen_workers,
        video_args=tuple(encoder_args_for_portable(host.encoder)),
    )
