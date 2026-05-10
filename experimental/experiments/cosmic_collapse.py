"""Cosmic Collapse — 30s three-act generative film.

See docs/specs/2026-05-10-cosmic-collapse-design.md for the design.
"""
from __future__ import annotations

import argparse
import math
import os
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageStat

# ---------- Configuration ----------

W, H = 1280, 720
FPS = 30
DURATION_SEC = 30
TOTAL_FRAMES = FPS * DURATION_SEC  # 900

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
OUTPUT_VIDEO = REPO_ROOT / "experimental" / "cosmic_collapse.mp4"
TEMP_FRAMES_DIR = REPO_ROOT / "experimental" / "cosmic_collapse_frames"
TEMP_AUDIO = REPO_ROOT / "experimental" / "cosmic_collapse_audio.wav"

STAR_SEED = 0xC05A1C
STAR_COUNT = 3000
PARTICLE_COUNT = 15000

# ---------- Helpers ----------

def smoothstep(edge0: float, edge1: float, x: float) -> float:
    """Standard GLSL-style smoothstep; clamps to [0, 1]."""
    if edge1 == edge0:
        return 0.0 if x < edge0 else 1.0
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3 - 2 * t)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


# ---------- Arc Controller (single timeline source of truth) ----------

def arc_state(t: float) -> dict:
    """Return all time-varying parameters for time t in [0, 30].

    Returns a dict with: cube_alpha, lens_K, particle_density, infall,
    text_alpha, audio_intensity.
    """
    # Cube: invisible until t=4, fully visible by t=8
    cube_alpha = smoothstep(4.0, 8.0, t)

    # Lens K: 0 in act 1, ramps to ~0.5 by t=16, holds, then spikes to ~0.95 by t=29
    if t < 8.0:
        lens_K = 0.0
    elif t < 16.0:
        lens_K = 0.5 * smoothstep(8.0, 16.0, t)
    elif t < 22.0:
        lens_K = 0.5
    else:
        lens_K = lerp(0.5, 0.95, smoothstep(22.0, 29.0, t))

    # Particles: 0 in act 1, full by t=12, hold through act 2 and 3
    particle_density = smoothstep(8.0, 12.0, t)

    # Infall: 0 until t=22, completes at t=29
    infall = smoothstep(22.0, 29.0, t)

    # Text: full alpha until t=25, fades to 0 by t=27.5
    text_alpha = 1.0 - smoothstep(25.0, 27.5, t)

    # Audio intensity: low in act 1, peaks act 2, swells through act 3
    if t < 8.0:
        audio_intensity = 0.2 * smoothstep(0.0, 4.0, t)
    elif t < 22.0:
        audio_intensity = lerp(0.3, 0.85, smoothstep(8.0, 18.0, t))
    else:
        audio_intensity = lerp(0.85, 1.0, smoothstep(22.0, 28.0, t))

    return {
        "cube_alpha": cube_alpha,
        "lens_K": lens_K,
        "particle_density": particle_density,
        "infall": infall,
        "text_alpha": text_alpha,
        "audio_intensity": audio_intensity,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true",
                        help="Render one frame at t=15 to PNG and exit")
    args = parser.parse_args()
    if args.smoke:
        print("Smoke mode not yet wired — see Task 2")
    else:
        print("Full render not yet wired — see later tasks")
