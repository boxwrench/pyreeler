from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_TEMPLATES = REPO_ROOT / "templates"
if str(SKILL_TEMPLATES) not in sys.path:
    sys.path.insert(0, str(SKILL_TEMPLATES))

from video.render_runtime import detect_render_runtime


@dataclass(frozen=True)
class LocalShaderRuntime:
    adapter_name: str
    backend: str
    ffmpeg_path: str
    encoder: str
    video_args: tuple[str, ...]


def resolve_local_ffmpeg_candidates():
    candidates = [
        Path(r"C:\pinokio\api\facefusion-pinokio.git\.env\Library\bin\ffmpeg.exe"),
        Path(r"C:\pinokio\api\wan2gp.git\app\ffmpeg_bins\ffmpeg.exe"),
    ]
    found = []
    for candidate in candidates:
        if candidate.exists():
            found.append(str(candidate))
    return found


def detect_local_ffmpeg_runtime():
    last_error = None
    for candidate in resolve_local_ffmpeg_candidates():
        try:
            return detect_render_runtime(ffmpeg_path=candidate)
        except FileNotFoundError as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    return detect_render_runtime()


def _load_wgpu() -> Any:
    try:
        import wgpu
    except ModuleNotFoundError as exc:
        raise RuntimeError("Install wgpu to use local shader rendering.") from exc
    return wgpu


def is_wgpu_available() -> bool:
    try:
        _load_wgpu()
    except RuntimeError:
        return False
    return True


def pick_discrete_adapter(wgpu_module=None):
    wgpu_module = wgpu_module or _load_wgpu()
    adapters = wgpu_module.gpu.enumerate_adapters_sync()
    discrete = [a for a in adapters if a.info.get("adapter_type") == "DiscreteGPU"]
    if not discrete:
        raise RuntimeError("No discrete GPU adapter found for local shader runtime.")

    nvidia = [a for a in discrete if "NVIDIA" in str(a.info.get("vendor", "")).upper() or "NVIDIA" in str(a.info.get("device", "")).upper()]
    chosen = nvidia[0] if nvidia else discrete[0]
    return chosen


def detect_local_shader_runtime() -> tuple[LocalShaderRuntime, Any]:
    runtime = detect_local_ffmpeg_runtime()
    adapter = pick_discrete_adapter()
    info = adapter.info
    return (
        LocalShaderRuntime(
            adapter_name=str(info.get("device", "Unknown GPU")),
            backend=str(info.get("backend_type", "unknown")),
            ffmpeg_path=runtime.ffmpeg_path,
            encoder=runtime.encoder,
            video_args=runtime.video_args,
        ),
        adapter,
    )
