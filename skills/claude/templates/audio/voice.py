from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def render_edge_tts(
    text: str,
    output_path,
    voice: str = "en-US-AriaNeural",
    rate: str = "+0%",
    pitch: str = "+0Hz",
):
    edge_tts_bin = shutil.which("edge-tts")
    if not edge_tts_bin:
        raise RuntimeError("Install edge-tts to render voice lines.")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        edge_tts_bin,
        "--voice",
        voice,
        "--rate",
        rate,
        "--pitch",
        pitch,
        "--text",
        text,
        "--write-media",
        str(output_path),
    ]
    subprocess.run(cmd, check=True)
    return output_path
