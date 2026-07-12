from __future__ import annotations

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass


PORTABLE_ENCODER_ORDER = (
    "h264_nvenc",
    "h264_amf",
    "libx264",
)
ENCODER_SMOKE_TIMEOUT_SECONDS = 5


@dataclass(frozen=True)
class HardwareProfile:
    profile: str
    encoder: str
    workers: int
    ffmpeg_path: str | None = None
    notes: str = ""


def resolve_ffmpeg(ffmpeg_path=None) -> str:
    if ffmpeg_path:
        return str(ffmpeg_path)
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe:
            return exe
    except ImportError:
        pass
    raise FileNotFoundError("Could not resolve ffmpeg. Install it to your system PATH, or run `pip install imageio-ffmpeg`.")


def encoder_smoke_test(ffmpeg_path, encoder: str, width: int = 320, height: int = 180, fps: int = 15, seconds: float = 0.25) -> bool:
    cmd = [
        str(ffmpeg_path),
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        f"testsrc2=size={width}x{height}:rate={fps}",
        "-t",
        str(seconds),
        "-c:v",
        encoder,
        "-f",
        "null",
        "-",
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=ENCODER_SMOKE_TIMEOUT_SECONDS,
        )
    except (subprocess.TimeoutExpired, OSError):
        return False
    return result.returncode == 0


def pick_portable_video_encoder(ffmpeg_path, encoder_order=PORTABLE_ENCODER_ORDER) -> str:
    ffmpeg_path = str(ffmpeg_path)
    for encoder in encoder_order:
        if encoder_smoke_test(ffmpeg_path, encoder):
            return encoder
    candidates = ", ".join(encoder_order)
    raise RuntimeError(f"No working FFmpeg video encoder found; attempted: {candidates}")



def conservative_worker_limit(profile: str, logical_cores: int | None = None) -> int:
    override = os.environ.get("PYREEL_WORKERS_OVERRIDE")
    if override:
        try:
            return max(1, int(override))
        except ValueError:
            pass
    cores = max(1, logical_cores or (os.cpu_count() or 1))
    if profile == "SAFE_MODE":
        return max(1, cores // 2)
    if profile == "APPLE_SILICON":
        return max(1, int(cores * 0.75))
    return max(1, min(4, cores - 2))


def detect_host_profile(ffmpeg_path=None) -> HardwareProfile:
    ffmpeg = resolve_ffmpeg(ffmpeg_path)
    encoder = pick_portable_video_encoder(ffmpeg)
    profile = {
        "h264_nvenc": "NVIDIA_NVENC",
        "h264_amf": "AMD_AMF",
    }.get(encoder, "SAFE_MODE")
    return HardwareProfile(profile=profile, encoder=encoder, workers=conservative_worker_limit(profile), ffmpeg_path=ffmpeg)


def encoder_args_for_portable(encoder: str) -> list[str]:
    if encoder == "h264_nvenc":
        return ["-c:v", encoder, "-preset", "p5", "-cq", "22", "-b:v", "0"]
    if encoder == "h264_qsv":
        return ["-c:v", encoder, "-preset", "veryfast", "-global_quality", "23"]
    if encoder == "h264_amf":
        return ["-c:v", encoder, "-quality", "balanced", "-qp_i", "22", "-qp_p", "24"]
    if encoder == "h264_videotoolbox":
        return ["-c:v", encoder, "-b:v", "4M"]
    return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23"]


def resolve_local_ffmpeg_candidates() -> list[str]:
    candidates = []
    configured = os.environ.get("PYREEL_LOCAL_FFMPEG_CANDIDATES", "")
    for candidate in configured.split(os.pathsep):
        candidate = candidate.strip()
        if candidate:
            candidates.append(candidate)
    found = shutil.which("ffmpeg")
    if found:
        candidates.append(found)
    deduped = []
    seen = set()
    for candidate in candidates:
        if candidate not in seen:
            deduped.append(candidate)
            seen.add(candidate)
    return deduped
