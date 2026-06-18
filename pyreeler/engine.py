"""Render a recipe to an mp4: precompute, map frames (optionally parallel), encode."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable

from templates.video.render_runtime import detect_render_runtime
from templates.video.parallel_render import ordered_frame_map


class _FrameJob:
    """A picklable per-frame callable (needed for multiprocessing workers)."""

    def __init__(self, recipe, params, prepared, total):
        self.recipe = recipe
        self.params = params
        self.prepared = prepared
        self.total = total

    def __call__(self, frame_idx):
        return self.recipe.make_frame(self.prepared, self.params, frame_idx, self.total)


def render_film(recipe, params: dict[str, Any], out_path,
                on_progress: Callable[[int, int], None] | None = None) -> Path:
    """Render `recipe` with resolved `params` to `out_path` (mp4); return the path."""
    out_path = Path(out_path)
    total = max(1, round(params["duration"] * params["fps"]))
    prepared = recipe.prepare(params)
    runtime = detect_render_runtime()
    job = _FrameJob(recipe, params, prepared, total)

    frames = []
    for done, image in enumerate(
        ordered_frame_map(range(total), job, runtime.workers), start=1
    ):
        frames.append(image)
        if on_progress is not None:
            on_progress(done, total)

    _encode_frames(frames, out_path, runtime, int(params["fps"]))
    return out_path


def _encode_frames(frames, out_path, runtime, fps: int) -> None:
    """Pipe RGB frames to FFmpeg and write out_path. Stubbed in unit tests.

    Note: frames are buffered in memory before encoding. This is fine for the
    short films PyReeler targets; streaming straight into FFmpeg is a future
    optimization (it would complicate per-frame progress reporting).
    """
    if not frames:
        raise ValueError("no frames to encode")
    width, height = frames[0].size
    ffmpeg = runtime.ffmpeg_path or "ffmpeg"
    cmd = [
        ffmpeg, "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{width}x{height}", "-r", str(fps),
        "-i", "-",
        *runtime.video_args,
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(out_path),
    ]
    # stderr -> a temp file (not a PIPE) so a chatty FFmpeg can't deadlock us
    # while we are busy writing frames to its stdin.
    with tempfile.TemporaryFile() as errfile:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=errfile)
        try:
            for image in frames:
                proc.stdin.write(image.convert("RGB").tobytes())
        except BrokenPipeError:
            # FFmpeg died mid-stream; fall through to reap it and surface the
            # real reason from its stderr (below) instead of a bare pipe error.
            pass
        finally:
            proc.stdin.close()  # always close, even if a write failed
        returncode = proc.wait()  # always reap, even after a broken pipe
        if returncode != 0:
            errfile.seek(0)
            detail = errfile.read().decode(errors="replace").strip()
            raise RuntimeError(f"ffmpeg exited with code {returncode}: {detail}")
