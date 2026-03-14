from __future__ import annotations

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass


PORTABLE_ENCODER_ORDER = (
    "h264_qsv",
    "h264_nvenc",
    "h264_amf",
    "h264_videotoolbox",
    "libx264",
)


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
    raise FileNotFoundError("Could not resolve ffmpeg. Pass an explicit ffmpeg path.")


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
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return result.returncode == 0


def pick_portable_video_encoder(ffmpeg_path, encoder_order=PORTABLE_ENCODER_ORDER) -> str:
    ffmpeg_path = str(ffmpeg_path)
    for encoder in encoder_order:
        if encoder_smoke_test(ffmpeg_path, encoder):
            return encoder
    return "libx264"


def detect_nvidia() -> bool:
    nvidia_smi = shutil.which("nvidia-smi")
    if not nvidia_smi:
        return False
    result = subprocess.run(
        [nvidia_smi, "--query-gpu=name", "--format=csv,noheader"],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    if result.returncode != 0:
        return False
    return "NVIDIA" in result.stdout


def detect_windows_gpu_vendor() -> str | None:
    powershell = shutil.which("powershell")
    if not powershell:
        return None
    result = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-Command",
            "(Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name) -join \"`n\"",
        ],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    if result.returncode != 0:
        return None
    names = result.stdout.lower()
    if "nvidia" in names:
        return "nvidia"
    if "intel" in names:
        return "intel"
    if "amd" in names or "radeon" in names:
        return "amd"
    return None


def detect_linux_gpu_vendor() -> str | None:
    cmd = shutil.which("lspci")
    if not cmd:
        return None
    result = subprocess.run(
        [cmd, "-nn"],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    if result.returncode != 0:
        return None
    text = result.stdout.lower()
    if "8086" in text:
        return "intel"
    if "1002" in text or "amd" in text or "radeon" in text:
        return "amd"
    return None


def detect_apple_silicon() -> bool:
    if platform.system() != "Darwin":
        return False
    if platform.machine() == "arm64":
        return True
    result = subprocess.run(
        ["sysctl", "-n", "sysctl.proc_translated"],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    return result.returncode == 0 and result.stdout.strip() == "1"


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

    if detect_nvidia():
        encoder = pick_portable_video_encoder(ffmpeg, ("h264_nvenc", "libx264"))
        profile = "NVIDIA_NVENC" if encoder == "h264_nvenc" else "SAFE_MODE"
        return HardwareProfile(profile=profile, encoder=encoder, workers=conservative_worker_limit(profile), ffmpeg_path=ffmpeg)

    if detect_apple_silicon():
        encoder = pick_portable_video_encoder(ffmpeg, ("h264_videotoolbox", "libx264"))
        profile = "APPLE_SILICON" if encoder == "h264_videotoolbox" else "SAFE_MODE"
        return HardwareProfile(profile=profile, encoder=encoder, workers=conservative_worker_limit(profile), ffmpeg_path=ffmpeg)

    system = platform.system()
    vendor = None
    if system == "Windows":
        vendor = detect_windows_gpu_vendor()
    elif system == "Linux":
        vendor = detect_linux_gpu_vendor()

    if vendor == "intel":
        encoder = pick_portable_video_encoder(ffmpeg, ("h264_qsv", "libx264"))
        profile = "INTEL_QSV" if encoder == "h264_qsv" else "SAFE_MODE"
        return HardwareProfile(profile=profile, encoder=encoder, workers=conservative_worker_limit(profile), ffmpeg_path=ffmpeg)
    if vendor == "nvidia":
        encoder = pick_portable_video_encoder(ffmpeg, ("h264_nvenc", "libx264"))
        profile = "NVIDIA_NVENC" if encoder == "h264_nvenc" else "SAFE_MODE"
        return HardwareProfile(profile=profile, encoder=encoder, workers=conservative_worker_limit(profile), ffmpeg_path=ffmpeg)
    if vendor == "amd":
        encoder = pick_portable_video_encoder(ffmpeg, ("h264_amf", "libx264"))
        profile = "AMD_AMF" if encoder == "h264_amf" else "SAFE_MODE"
        return HardwareProfile(profile=profile, encoder=encoder, workers=conservative_worker_limit(profile), ffmpeg_path=ffmpeg)

    encoder = pick_portable_video_encoder(ffmpeg)
    profile = "SAFE_MODE" if encoder == "libx264" else "GENERIC_ACCEL"
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
