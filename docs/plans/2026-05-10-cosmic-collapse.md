# Cosmic Collapse Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `experimental/experiments/cosmic_collapse.py` — a 30s, 1280×720, 30fps generative film that follows a three-act arc (Genesis / Bloom / Collapse), with gravitational lensing of a starfield as the headline visual, a god's-CLI text track as narrative spine, and event-synced FM audio.

**Architecture:** Single Python script that owns one `arc_state(t)` controller as the timeline source of truth, drives a layered render (starfield → lensing → cube → black-hole faces → particle nebula → text track), and a layered audio mixer that consumes the same timeline events. Self-healing audits 3 sample frames before committing to a 900-frame render.

**Tech Stack:** Python, NumPy, Pillow, FFmpeg (already installed). No new dependencies.

**Spec:** `docs/specs/2026-05-10-cosmic-collapse-design.md`

---

## File Structure

| File | Purpose |
|------|---------|
| `experimental/experiments/cosmic_collapse.py` | The film generator (single self-contained script) |
| `experimental/experiments/test_cosmic_collapse.py` | Pytest unit tests for arc, lensing, text, audio |
| `experimental/cosmic_collapse.mp4` | Final output (gitignored) |
| `experimental/experiments/cosmic_experiment.py` | Reference baseline — DO NOT MODIFY |

---

## Conventions for this plan

- All paths are repo-relative.
- Run all `python` and `pytest` commands from the repo root: `C:\GitHub\pyreeler`.
- Tests use plain pytest. Install if missing: `python -m pip install pytest`.
- "Run smoke" = `python experimental/experiments/cosmic_collapse.py --smoke` (renders 1 frame at t=15, saves PNG, exits — defined in Task 2).
- Commit after each task. Use the commit messages shown.

---

## Chunk 1: Skeleton + Arc Controller

### Task 1: Create script with imports, constants, and `arc_state(t)`

**Files:**
- Create: `experimental/experiments/cosmic_collapse.py`
- Create: `experimental/experiments/test_cosmic_collapse.py`

- [ ] **Step 1: Write the failing test for `arc_state`**

Create `experimental/experiments/test_cosmic_collapse.py`:

```python
"""Unit tests for cosmic_collapse film generator."""
import math
import numpy as np
import pytest
from PIL import Image

import cosmic_collapse as cc


def test_arc_state_at_t0_is_void():
    s = cc.arc_state(0.0)
    assert s["cube_alpha"] == 0.0
    assert s["lens_K"] == 0.0
    assert s["particle_density"] == 0.0
    assert s["infall"] == 0.0
    assert s["text_alpha"] == 1.0
    assert 0.0 <= s["audio_intensity"] <= 0.3


def test_arc_state_act2_peak():
    s = cc.arc_state(15.0)
    assert s["cube_alpha"] == 1.0
    assert 0.4 <= s["lens_K"] <= 0.6
    assert s["particle_density"] == 1.0
    assert s["infall"] == 0.0
    assert s["text_alpha"] == 1.0


def test_arc_state_collapse_end():
    s = cc.arc_state(29.0)
    assert s["cube_alpha"] == 1.0
    assert 0.85 <= s["lens_K"] <= 1.0
    assert s["infall"] >= 0.95
    assert s["text_alpha"] == 0.0


def test_arc_state_text_fade_window():
    s_before = cc.arc_state(24.9)
    s_mid = cc.arc_state(26.25)
    s_after = cc.arc_state(27.5)
    assert s_before["text_alpha"] == 1.0
    assert 0.3 < s_mid["text_alpha"] < 0.7
    assert s_after["text_alpha"] == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest experimental/experiments/test_cosmic_collapse.py -v`
Expected: ImportError or `module has no attribute 'arc_state'`.

- [ ] **Step 3: Create `cosmic_collapse.py` with imports, constants, and `arc_state`**

Create `experimental/experiments/cosmic_collapse.py`:

```python
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

    # Lens K: 0 in act 1, ramps to ~0.55 by t=22, spikes to ~0.95 by t=29
    if t < 8.0:
        lens_K = 0.0
    elif t < 22.0:
        lens_K = 0.55 * smoothstep(8.0, 22.0, t)
    else:
        lens_K = lerp(0.55, 0.95, smoothstep(22.0, 29.0, t))

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
```

No `__init__.py` is needed — pytest auto-prepends the test file's directory to sys.path, so `import cosmic_collapse as cc` resolves directly.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest experimental/experiments/test_cosmic_collapse.py -v`
Expected: 4 passing tests.

- [ ] **Step 5: Commit**

```bash
git add experimental/experiments/cosmic_collapse.py experimental/experiments/test_cosmic_collapse.py
git commit -m "feat(cosmic-collapse): scaffold script + arc_state controller with tests"
```

---

### Task 2: Wire `--smoke` mode and a placeholder `render_frame`

**Files:**
- Modify: `experimental/experiments/cosmic_collapse.py`

- [ ] **Step 1: Add a placeholder `render_frame` and smoke entry-point**

In `cosmic_collapse.py`, ABOVE the `if __name__ == "__main__":` block, add:

```python
# ---------- Frame Rendering (will be filled in by later tasks) ----------

def render_frame(frame_num: int, ctx: dict) -> Image.Image:
    """Render a single 1280x720 RGB frame. Wired up across later tasks."""
    t = frame_num / FPS
    state = arc_state(t)
    img = Image.new("RGB", (W, H), (5, 5, 12))
    draw = ImageDraw.Draw(img)
    draw.text((40, 40), f"t={t:.2f}s  cube={state['cube_alpha']:.2f}  K={state['lens_K']:.2f}",
              fill=(0, 220, 200))
    return img


def smoke_render(out_path: Path) -> None:
    """Render one frame at t=15 and save it as PNG."""
    frame_num = 15 * FPS
    img = render_frame(frame_num, ctx={})
    img.save(out_path)
    print(f"smoke frame written to {out_path}")
```

Then replace the `if __name__ == "__main__":` block with:

```python
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true",
                        help="Render one frame at t=15 to PNG and exit")
    args = parser.parse_args()
    if args.smoke:
        smoke_render(REPO_ROOT / "experimental" / "cosmic_collapse_smoke.png")
    else:
        print("Full render not yet wired — see later tasks")
        sys.exit(0)
```

- [ ] **Step 2: Run smoke and verify the PNG appears**

Run: `python experimental/experiments/cosmic_collapse.py --smoke`
Expected: prints `smoke frame written to ...` and creates `experimental/cosmic_collapse_smoke.png` (a dark frame with timing text). Open it and confirm.

- [ ] **Step 3: Commit**

```bash
git add experimental/experiments/cosmic_collapse.py
git commit -m "feat(cosmic-collapse): smoke mode + placeholder render_frame"
```

---

## Chunk 2: Starfield and Gravitational Lensing

### Task 3: Deterministic starfield generation

**Files:**
- Modify: `experimental/experiments/cosmic_collapse.py`
- Modify: `experimental/experiments/test_cosmic_collapse.py`

- [ ] **Step 1: Add failing tests**

Append to `test_cosmic_collapse.py`:

```python
def test_generate_starfield_count_and_shape():
    stars = cc.generate_starfield()
    assert stars.shape == (cc.STAR_COUNT, 4)  # x, y, z, brightness


def test_generate_starfield_is_deterministic():
    a = cc.generate_starfield()
    b = cc.generate_starfield()
    assert (a == b).all()


def test_generate_starfield_radius_range():
    stars = cc.generate_starfield()
    radii = np.sqrt((stars[:, :3] ** 2).sum(axis=1))
    assert radii.min() >= 7.5
    assert radii.max() <= 26.0
```

Add `import numpy as np` to the test file's imports if not already present (it imports `cc` which imports numpy, but tests use `np` directly here).

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest experimental/experiments/test_cosmic_collapse.py -v -k starfield`
Expected: 3 failures (`generate_starfield` not defined).

- [ ] **Step 3: Implement `generate_starfield`**

In `cosmic_collapse.py`, add below the helpers section:

```python
# ---------- Starfield ----------

def generate_starfield() -> np.ndarray:
    """Generate STAR_COUNT stars distributed in a spherical shell.

    Returns array of shape (STAR_COUNT, 4): [x, y, z, brightness].
    Deterministic — same seed every call.
    """
    rng = np.random.default_rng(STAR_SEED)
    # Uniform points on sphere via normal-then-normalize
    dirs = rng.normal(size=(STAR_COUNT, 3))
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    radii = rng.uniform(8.0, 25.0, size=STAR_COUNT)
    xyz = dirs * radii[:, None]
    brightness = rng.uniform(0.3, 1.0, size=STAR_COUNT)
    return np.concatenate([xyz, brightness[:, None]], axis=1)
```

- [ ] **Step 4: Run tests to verify pass**

Run: `python -m pytest experimental/experiments/test_cosmic_collapse.py -v -k starfield`
Expected: 3 passing tests.

- [ ] **Step 5: Commit**

```bash
git add experimental/experiments/cosmic_collapse.py experimental/experiments/test_cosmic_collapse.py
git commit -m "feat(cosmic-collapse): deterministic starfield generation"
```

---

### Task 4: Port 3D math helpers and render the un-lensed starfield layer

**Files:**
- Modify: `experimental/experiments/cosmic_collapse.py`

- [ ] **Step 1: Port rotation/projection helpers from cosmic_experiment.py**

In `cosmic_collapse.py`, add a `# ---------- 3D Math ----------` section below the helpers section, with the following functions copied verbatim from `experimental/experiments/cosmic_experiment.py:11-23`:

```python
# ---------- 3D Math ----------

def get_rotation_matrix(rx, ry, rz):
    rot_x = np.array([[1, 0, 0], [0, np.cos(rx), -np.sin(rx)], [0, np.sin(rx), np.cos(rx)]])
    rot_y = np.array([[np.cos(ry), 0, np.sin(ry)], [0, 1, 0], [-np.sin(ry), 0, np.cos(ry)]])
    rot_z = np.array([[np.cos(rz), -np.sin(rz), 0], [np.sin(rz), np.cos(rz), 0], [0, 0, 1]])
    return rot_z @ rot_y @ rot_x


def project_points(points, width, height, field_of_view=800, viewer_distance=6):
    z_eff = points[:, 2] + viewer_distance
    z_eff = np.where(z_eff < 0.1, 0.1, z_eff)
    factor = field_of_view / z_eff
    x_2d = points[:, 0] * factor + width / 2
    y_2d = points[:, 1] * factor + height / 2
    return np.stack([x_2d, y_2d], axis=1), z_eff
```

- [ ] **Step 2: Add `render_starfield_layer`**

Add to the same section:

```python
def render_starfield_layer(stars: np.ndarray, t: float) -> Image.Image:
    """Render the (un-lensed) starfield as an RGBA layer.

    Stars are rotated very slowly so the parallax feels alive, but not distracting.
    """
    img = Image.new("RGBA", (W, H), (5, 5, 12, 255))
    pixels = np.array(img)

    rot = get_rotation_matrix(t * 0.01, t * 0.013, 0.0)
    rotated = stars[:, :3] @ rot.T
    pts2d, z_eff = project_points(rotated, W, H)

    # Keep only on-screen, in-front stars
    visible = (
        (pts2d[:, 0] >= 1) & (pts2d[:, 0] < W - 1) &
        (pts2d[:, 1] >= 1) & (pts2d[:, 1] < H - 1) &
        (z_eff > 0.5)
    )
    pts = pts2d[visible].astype(int)
    bri = stars[visible, 3]
    depths = z_eff[visible]

    # Brightness scales with distance (close = brighter)
    intensity = np.clip(255.0 * bri * (12.0 / depths), 30, 255).astype(np.uint8)

    pixels[pts[:, 1], pts[:, 0]] = np.stack(
        [intensity, intensity, np.minimum(255, intensity + 30),
         np.full_like(intensity, 255)], axis=1
    )
    # Soft second-ring around bright stars to suggest glow
    bright_mask = intensity > 180
    bx = pts[bright_mask, 0]
    by = pts[bright_mask, 1]
    bint = (intensity[bright_mask] // 3).astype(np.uint8)
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        x = np.clip(bx + dx, 0, W - 1)
        y = np.clip(by + dy, 0, H - 1)
        pixels[y, x, 0] = np.maximum(pixels[y, x, 0], bint)
        pixels[y, x, 1] = np.maximum(pixels[y, x, 1], bint)
        pixels[y, x, 2] = np.maximum(pixels[y, x, 2], bint + 20)

    return Image.fromarray(pixels, mode="RGBA")
```

- [ ] **Step 3: Update `render_frame` to actually render the starfield**

Replace the body of `render_frame` with:

```python
def render_frame(frame_num: int, ctx: dict) -> Image.Image:
    t = frame_num / FPS
    state = arc_state(t)
    stars = ctx.get("stars")
    if stars is None:
        stars = generate_starfield()
        ctx["stars"] = stars

    starfield = render_starfield_layer(stars, t)
    img = starfield.convert("RGB")

    draw = ImageDraw.Draw(img)
    draw.text((40, 40), f"t={t:.2f}s  cube={state['cube_alpha']:.2f}  K={state['lens_K']:.2f}",
              fill=(0, 220, 200))
    return img
```

- [ ] **Step 4: Run smoke and visually check**

Run: `python experimental/experiments/cosmic_collapse.py --smoke`
Expected: smoke PNG now shows ~hundreds of stars in a dark blue field, plus the timing text. Open `experimental/cosmic_collapse_smoke.png` to confirm.

- [ ] **Step 5: Commit**

```bash
git add experimental/experiments/cosmic_collapse.py
git commit -m "feat(cosmic-collapse): render un-lensed starfield layer"
```

---

### Task 5: Implement gravitational lensing displacement

**Files:**
- Modify: `experimental/experiments/cosmic_collapse.py`
- Modify: `experimental/experiments/test_cosmic_collapse.py`

- [ ] **Step 1: Add failing tests for the displacement math**

Append to `test_cosmic_collapse.py`:

```python
def test_lensing_zero_K_is_identity():
    """K=0 means no displacement — output equals input."""
    src = np.zeros((H_TEST := 64, W_TEST := 64, 4), dtype=np.uint8)
    src[20:30, 20:30] = [255, 100, 100, 255]
    img = Image.fromarray(src, mode="RGBA")
    out = cc.apply_lensing(img, lens_centers=[(32.0, 32.0, 1.0)], K=0.0)
    assert (np.array(out) == src).all()


def test_lensing_displaces_pixels_radially():
    """With K>0 a pixel near the lens center is sampled from further out."""
    src = np.zeros((64, 64, 4), dtype=np.uint8)
    # Concentric ring of bright pixels far from center
    for r in range(20, 25):
        for theta in np.linspace(0, 2 * np.pi, 60):
            x = int(32 + r * np.cos(theta))
            y = int(32 + r * np.sin(theta))
            if 0 <= x < 64 and 0 <= y < 64:
                src[y, x] = [255, 255, 255, 255]
    img = Image.fromarray(src, mode="RGBA")
    out = cc.apply_lensing(img, lens_centers=[(32.0, 32.0, 1.0)], K=0.5)
    out_arr = np.array(out)
    # The bright ring should be pulled inward — pixels at smaller radii
    # should now have nonzero brightness compared to the original.
    assert out_arr[28:36, 28:36, 0].sum() > src[28:36, 28:36, 0].sum()
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest experimental/experiments/test_cosmic_collapse.py -v -k lensing`
Expected: 2 failures (`apply_lensing` not defined).

- [ ] **Step 3: Implement `apply_lensing`**

In `cosmic_collapse.py`, add a new section below 3D math:

```python
# ---------- Gravitational Lensing ----------

def apply_lensing(layer: Image.Image, lens_centers: list, K: float) -> Image.Image:
    """Warp `layer` by Schwarzschild-style radial displacement around each lens center.

    lens_centers: list of (cx, cy, strength) tuples in screen coords.
        strength is a per-lens multiplier (0..1) that scales K.
    K: global lens strength in [0, 1]. K=0 returns input unchanged.

    Implementation: build a (H, W) meshgrid; for each lens, accumulate
    a radial offset; bilinear-sample the source layer at the displaced coords.
    """
    if K <= 0.0 or not lens_centers:
        return layer.copy()

    src = np.array(layer, dtype=np.float32)
    h, w = src.shape[:2]

    yy, xx = np.meshgrid(np.arange(h, dtype=np.float32),
                         np.arange(w, dtype=np.float32),
                         indexing="ij")

    # Accumulated displacement
    sum_dx = np.zeros_like(xx)
    sum_dy = np.zeros_like(yy)

    for cx, cy, strength in lens_centers:
        dx = xx - cx
        dy = yy - cy
        r2 = dx * dx + dy * dy + 1.0  # +1 epsilon to avoid singularity at center
        # Per-lens scale factor of the radial vector
        # We want sample point = center + (1 - K_eff/r^2) * (p - center)
        # so displacement contribution = -K_eff/r^2 * (p - center).
        # Cap so we don't fold inside event horizon.
        k_eff = K * strength * 4000.0  # tune: ~4000 px^2 maps to ~30px event horizon at K=0.5
        scale = np.minimum(k_eff / r2, 0.95)
        sum_dx -= scale * dx
        sum_dy -= scale * dy

    src_x = xx + sum_dx
    src_y = yy + sum_dy

    # Bilinear sample
    x0 = np.floor(src_x).astype(np.int32)
    y0 = np.floor(src_y).astype(np.int32)
    x1 = x0 + 1
    y1 = y0 + 1
    fx = src_x - x0
    fy = src_y - y0

    x0 = np.clip(x0, 0, w - 1); x1 = np.clip(x1, 0, w - 1)
    y0 = np.clip(y0, 0, h - 1); y1 = np.clip(y1, 0, h - 1)

    out = np.zeros_like(src)
    for c in range(src.shape[2]):
        ch = src[..., c]
        out[..., c] = (
            ch[y0, x0] * (1 - fx) * (1 - fy) +
            ch[y0, x1] *      fx  * (1 - fy) +
            ch[y1, x0] * (1 - fx) *      fy  +
            ch[y1, x1] *      fx  *      fy
        )
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), mode="RGBA")
```

- [ ] **Step 4: Run tests to verify pass**

Run: `python -m pytest experimental/experiments/test_cosmic_collapse.py -v -k lensing`
Expected: 2 passing tests.

- [ ] **Step 5: Wire lensing into `render_frame` for visual confirmation**

Modify `render_frame` to apply lensing using a temporary fixed lens center at screen middle:

```python
def render_frame(frame_num: int, ctx: dict) -> Image.Image:
    t = frame_num / FPS
    state = arc_state(t)
    stars = ctx.get("stars")
    if stars is None:
        stars = generate_starfield()
        ctx["stars"] = stars

    starfield = render_starfield_layer(stars, t)
    if state["lens_K"] > 0.0:
        starfield = apply_lensing(
            starfield,
            lens_centers=[(W / 2, H / 2, 1.0)],
            K=state["lens_K"],
        )
    img = starfield.convert("RGB")

    draw = ImageDraw.Draw(img)
    draw.text((40, 40), f"t={t:.2f}s  K={state['lens_K']:.2f}", fill=(0, 220, 200))
    return img
```

- [ ] **Step 6: Run smoke and confirm lensing is visible**

Run: `python experimental/experiments/cosmic_collapse.py --smoke`
Expected: starfield is visibly bent around the screen center (stars curve toward the middle). Open `experimental/cosmic_collapse_smoke.png` and confirm the warp.

- [ ] **Step 7: Commit**

```bash
git add experimental/experiments/cosmic_collapse.py experimental/experiments/test_cosmic_collapse.py
git commit -m "feat(cosmic-collapse): gravitational lensing displacement on starfield"
```

---

## Chunk 3: Cube, Black-Hole Faces, and Particle Nebula

### Task 6: Port cube + black-hole texture rendering, modulated by `cube_alpha`

**Files:**
- Modify: `experimental/experiments/cosmic_collapse.py`

- [ ] **Step 1: Port cube/texture/coeffs helpers**

Copy these functions verbatim from `experimental/experiments/cosmic_experiment.py`:

- `find_coeffs` (lines 27-38)
- `create_black_hole_texture` (lines 42-58)
- `create_cube` (lines 60-75)

Place them in a new section `# ---------- Cube + Black-Hole Faces ----------` of `cosmic_collapse.py`.

- [ ] **Step 2: Add a `render_cube_layer` function with arc modulation**

Add to the same section:

```python
def render_cube_layer(t: float, state: dict, bh_texture: Image.Image,
                      light_dir: np.ndarray) -> tuple[Image.Image, list]:
    """Render the cube + black-hole faces. Returns (RGBA layer, lens_centers).

    lens_centers is a list of (cx, cy, strength) for each visible black-hole face,
    so the lensing pass can warp the starfield around them.
    """
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lens_centers: list = []

    if state["cube_alpha"] <= 0.001:
        return layer, lens_centers

    vertices, faces = create_cube()
    rot = get_rotation_matrix(t * 0.45, t * 0.27, t * 0.09)
    rotated = vertices @ rot.T
    cube_2d, _ = project_points(rotated, W, H)

    # Depth sort
    face_depths = []
    for face in faces:
        z_avg = np.mean([rotated[v, 2] for v in face])
        face_depths.append((z_avg, face))
    face_depths.sort(key=lambda x: x[0], reverse=True)

    # Animated accretion: rotate texture per-frame so each face shimmers
    bh_rotated = bh_texture.rotate(t * 30.0, resample=Image.BILINEAR)
    src_pa = [(0, 0), (bh_rotated.width, 0),
              (bh_rotated.width, bh_rotated.height), (0, bh_rotated.height)]

    draw = ImageDraw.Draw(layer)

    for _, face in face_depths:
        v0, v1, v2 = rotated[face[0]], rotated[face[1]], rotated[face[2]]
        normal = np.cross(v1 - v0, v2 - v1)
        n_len = np.linalg.norm(normal)
        if n_len < 1e-6:
            continue
        normal = normal / n_len

        if normal[2] >= 0:  # backface cull
            continue

        intensity = float(np.clip((np.dot(normal, light_dir) + 1.0) / 2.0, 0.1, 1.0))

        target_pb = [tuple(cube_2d[v]) for v in face]
        coeffs = find_coeffs(src_pa, target_pb)
        warped = bh_rotated.transform((W, H), Image.PERSPECTIVE, coeffs, Image.BILINEAR)

        if intensity < 1.0:
            r, g, b, a = warped.split()
            r = r.point(lambda i, k=intensity: int(i * k))
            g = g.point(lambda i, k=intensity: int(i * k))
            b = b.point(lambda i, k=intensity: int(i * k))
            warped = Image.merge("RGBA", (r, g, b, a))

        # Apply cube_alpha to this face's alpha channel
        alpha = state["cube_alpha"]
        if alpha < 1.0:
            r, g, b, a = warped.split()
            a = a.point(lambda i, k=alpha: int(i * k))
            warped = Image.merge("RGBA", (r, g, b, a))

        mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mask).polygon(target_pb, fill=int(255 * alpha))
        layer.paste(warped, (0, 0), mask)

        outline_col = (
            0,
            int(255 * intensity * alpha),
            int(200 * intensity * alpha),
            int(200 * alpha),
        )
        draw.polygon(target_pb, outline=outline_col)

        # Face center as lens center (strength weighted by face camera-facing-ness)
        cx = float(np.mean([cube_2d[v, 0] for v in face]))
        cy = float(np.mean([cube_2d[v, 1] for v in face]))
        face_strength = float(-normal[2])  # 0..1, peak when face directly at camera
        lens_centers.append((cx, cy, face_strength * alpha))

    return layer, lens_centers
```

- [ ] **Step 3: Wire into `render_frame` so the cube composites over the lensed starfield**

Replace `render_frame` body:

```python
def render_frame(frame_num: int, ctx: dict) -> Image.Image:
    t = frame_num / FPS
    state = arc_state(t)

    if "stars" not in ctx:
        ctx["stars"] = generate_starfield()
    if "bh_texture" not in ctx:
        ctx["bh_texture"] = create_black_hole_texture(512)
    if "light_dir" not in ctx:
        ld = np.array([0.5, 0.5, -0.5])
        ctx["light_dir"] = ld / np.linalg.norm(ld)

    starfield = render_starfield_layer(ctx["stars"], t)

    cube_layer, lens_centers = render_cube_layer(
        t, state, ctx["bh_texture"], ctx["light_dir"]
    )

    if state["lens_K"] > 0.0 and lens_centers:
        starfield = apply_lensing(starfield, lens_centers, state["lens_K"])

    composite = Image.alpha_composite(starfield, cube_layer)
    img = composite.convert("RGB")

    draw = ImageDraw.Draw(img)
    draw.text(
        (40, 40),
        f"t={t:.2f}s  cube={state['cube_alpha']:.2f}  K={state['lens_K']:.2f}",
        fill=(0, 220, 200),
    )
    return img
```

- [ ] **Step 4: Run smoke and confirm**

Run: `python experimental/experiments/cosmic_collapse.py --smoke`
Expected: smoke PNG shows starfield + a textured cube with black-hole faces, with the starfield bent around each black-hole face.

- [ ] **Step 5: Commit**

```bash
git add experimental/experiments/cosmic_collapse.py
git commit -m "feat(cosmic-collapse): cube + black-hole faces with per-face lensing"
```

---

### Task 7: Particle nebula with density modulation and infall

**Files:**
- Modify: `experimental/experiments/cosmic_collapse.py`

- [ ] **Step 1: Port `clifford_attractor`**

Copy `clifford_attractor` from `experimental/experiments/cosmic_experiment.py:77-86` into a new `# ---------- Particle Nebula ----------` section.

- [ ] **Step 2: Add `render_particles_layer`**

```python
def render_particles_layer(cloud: np.ndarray, t: float, state: dict) -> Image.Image:
    """Render Clifford attractor particles, density-modulated and with act-3 infall."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if state["particle_density"] <= 0.001:
        return layer

    rot = get_rotation_matrix(t * 0.12, t * 0.05, t * 0.18)
    rotated = cloud @ rot.T
    pts2d, depths = project_points(rotated, W, H)

    n = int(len(cloud) * state["particle_density"])
    if n <= 0:
        return layer
    pts2d = pts2d[:n]
    depths = depths[:n]

    # Infall: pull positions toward screen center
    if state["infall"] > 0.0:
        cx, cy = W / 2, H / 2
        pts2d = pts2d.copy()
        pts2d[:, 0] = cx + (pts2d[:, 0] - cx) * (1.0 - state["infall"])
        pts2d[:, 1] = cy + (pts2d[:, 1] - cy) * (1.0 - state["infall"])

    valid = (
        (pts2d[:, 0] >= 0) & (pts2d[:, 0] < W) &
        (pts2d[:, 1] >= 0) & (pts2d[:, 1] < H)
    )
    pts = pts2d[valid].astype(int)
    d = depths[valid]

    pixels = np.array(layer)
    alpha = np.clip(160 - d * 12, 5, 220).astype(np.uint8)
    # Alpha also dims with infall (particles dissolve)
    alpha = (alpha * (1.0 - 0.7 * state["infall"])).astype(np.uint8)

    pixels[pts[:, 1], pts[:, 0]] = np.stack(
        [np.zeros_like(alpha), np.full_like(alpha, 200),
         np.full_like(alpha, 255), alpha], axis=1
    )
    return Image.fromarray(pixels, mode="RGBA")
```

- [ ] **Step 3: Wire into `render_frame`**

Update the `render_frame` body — composite the particle layer between the cube and the lensed starfield. Replace `render_frame` with:

```python
def render_frame(frame_num: int, ctx: dict) -> Image.Image:
    t = frame_num / FPS
    state = arc_state(t)

    if "stars" not in ctx:
        ctx["stars"] = generate_starfield()
    if "bh_texture" not in ctx:
        ctx["bh_texture"] = create_black_hole_texture(512)
    if "light_dir" not in ctx:
        ld = np.array([0.5, 0.5, -0.5])
        ctx["light_dir"] = ld / np.linalg.norm(ld)
    if "cloud" not in ctx:
        # Default Clifford params; self-healer will replace these
        ctx["cloud"] = clifford_attractor(PARTICLE_COUNT, -1.7, 1.8, 1.2, 0.9)

    starfield = render_starfield_layer(ctx["stars"], t)
    cube_layer, lens_centers = render_cube_layer(
        t, state, ctx["bh_texture"], ctx["light_dir"]
    )
    particles = render_particles_layer(ctx["cloud"], t, state)

    if state["lens_K"] > 0.0 and lens_centers:
        starfield = apply_lensing(starfield, lens_centers, state["lens_K"])

    composite = Image.alpha_composite(starfield, particles)
    composite = Image.alpha_composite(composite, cube_layer)
    img = composite.convert("RGB")

    draw = ImageDraw.Draw(img)
    draw.text(
        (40, 40),
        f"t={t:.2f}s  cube={state['cube_alpha']:.2f}  K={state['lens_K']:.2f}",
        fill=(0, 220, 200),
    )
    return img
```

- [ ] **Step 4: Run smoke and visually confirm**

Run: `python experimental/experiments/cosmic_collapse.py --smoke`
Expected: smoke PNG (t=15) shows starfield + particles + cube, all composited.

- [ ] **Step 5: Smoke at t=27 to verify infall**

Temporarily edit the line `frame_num = 15 * FPS` in `smoke_render` to `frame_num = 27 * FPS`, run, confirm particles are visibly pulled toward screen center, then revert to `15 * FPS`.

- [ ] **Step 6: Commit**

```bash
git add experimental/experiments/cosmic_collapse.py
git commit -m "feat(cosmic-collapse): particle nebula with density modulation and infall"
```

---

## Chunk 4: God's-CLI Text Track

### Task 8: TextTrack timeline + tests

**Files:**
- Modify: `experimental/experiments/cosmic_collapse.py`
- Modify: `experimental/experiments/test_cosmic_collapse.py`

- [ ] **Step 1: Add failing tests**

Append to `test_cosmic_collapse.py`:

```python
def test_text_track_lines_at_known_times():
    tt = cc.TextTrack()
    # Spec: t=0.4 is first $ line
    visible_at_1s = tt.visible_at(1.0)
    assert any("universe.init" in line.text for line in visible_at_1s)


def test_text_track_typing_progresses():
    tt = cc.TextTrack()
    line0 = tt.timeline[0]
    full = line0.text
    early = tt.typed_text(line0, line0.start_t + 0.05)
    late = tt.typed_text(line0, line0.start_t + 5.0)
    assert len(early) < len(full)
    assert late == full


def test_text_track_keystroke_events_count():
    tt = cc.TextTrack()
    events = tt.keystroke_events()
    # Each $-prefixed line yields one keystroke event
    cmd_lines = [l for l in tt.timeline if l.text.startswith("$")]
    assert len(events) == len(cmd_lines)


def test_text_track_exit_line_is_isolated():
    tt = cc.TextTrack()
    exit_lines = [l for l in tt.timeline if l.text.strip() == "$ exit"]
    assert len(exit_lines) == 1
    assert exit_lines[0].isolated is True
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest experimental/experiments/test_cosmic_collapse.py -v -k text_track`
Expected: 4 failures (`TextTrack` not defined).

- [ ] **Step 3: Implement `TextTrack`**

Add to `cosmic_collapse.py` in a new `# ---------- God's-CLI Text Track ----------` section:

```python
# ---------- God's-CLI Text Track ----------

from dataclasses import dataclass

TYPING_CPS = 30.0  # characters per second


@dataclass
class TextLine:
    start_t: float
    text: str
    is_command: bool      # True if starts with "$ "
    isolated: bool = False  # True for the final $ exit


class TextTrack:
    """Owns the god's-CLI script timeline.

    Per spec: 18 lines from t=0.4 to t=28.0. The final $ exit is "isolated":
    it is rendered as a single line at full alpha after the main block has
    faded out, and triggers the sub-bass impact at t=28.
    """

    SCRIPT: list = [
        (0.4,  "$ universe.init(seed=0xDEADBEEF)"),
        (1.2,  "> and there was void."),
        (2.5,  "$ spawn stars --n=3000"),
        (3.4,  "> and the dark was given points."),
        (5.0,  "$ alloc cube --dim=3"),
        (6.6,  "> and a shape was given form."),
        (8.0,  "$ ignite singularities --faces=6"),
        (9.6,  "> and the shape consumed light."),
        (12.0, "$ bend space --k=0.4"),
        (13.2, "> and the heavens curved."),
        (16.0, "$ summon nebula --particles=15000"),
        (17.6, "> and the void was filled."),
        (20.0, "$ tune gravity --k=0.8"),
        (22.0, "$ collapse --target=center"),
        (23.0, "> and the form fell inward."),
        (25.5, "$ kill light"),
        (26.5, "> and it was good."),
        (28.0, "$ exit"),
    ]

    def __init__(self) -> None:
        self.timeline: list[TextLine] = []
        for start_t, text in self.SCRIPT:
            is_cmd = text.startswith("$")
            isolated = (text.strip() == "$ exit")
            self.timeline.append(TextLine(start_t, text, is_cmd, isolated))

    def typed_text(self, line: TextLine, t: float) -> str:
        """Return how much of `line.text` has been typed by time t."""
        if t <= line.start_t:
            return ""
        chars = int((t - line.start_t) * TYPING_CPS)
        return line.text[:chars]

    def visible_at(self, t: float, max_lines: int = 10) -> list[TextLine]:
        """Return the most recent up-to-`max_lines` non-isolated lines that
        have started typing by time t. Excludes the isolated $ exit line."""
        started = [l for l in self.timeline
                   if l.start_t <= t and not l.isolated]
        return started[-max_lines:]

    def isolated_visible_at(self, t: float) -> TextLine | None:
        """Return the isolated $ exit line if it's currently active."""
        for line in self.timeline:
            if line.isolated and line.start_t <= t <= line.start_t + 1.5:
                return line
        return None

    def keystroke_events(self) -> list[float]:
        """Return list of times where a keystroke click should fire (one per $ line)."""
        return [l.start_t for l in self.timeline if l.is_command]
```

- [ ] **Step 4: Run tests to verify pass**

Run: `python -m pytest experimental/experiments/test_cosmic_collapse.py -v -k text_track`
Expected: 4 passing tests.

- [ ] **Step 5: Commit**

```bash
git add experimental/experiments/cosmic_collapse.py experimental/experiments/test_cosmic_collapse.py
git commit -m "feat(cosmic-collapse): TextTrack timeline + typing/scrolling logic"
```

---

### Task 9: Render the text-track layer (typing + scrolling + fade)

**Files:**
- Modify: `experimental/experiments/cosmic_collapse.py`

- [ ] **Step 1: Add `render_text_layer` and font loader**

In `cosmic_collapse.py`, after the `TextTrack` class:

```python
def _load_font(size: int = 22) -> ImageFont.ImageFont:
    for path in filter(None, [
        os.environ.get("PYREEL_FONT"),
        "DejaVuSansMono-Bold.ttf",
        "DejaVuSansMono.ttf",
        "consola.ttf",
        "cour.ttf",
    ]):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def render_text_layer(track: TextTrack, t: float, font: ImageFont.ImageFont,
                      state: dict) -> Image.Image:
    """Render the god's-CLI text block (lower-left) and the isolated exit line."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    # Block fade alpha from arc state
    block_alpha = state["text_alpha"]
    if block_alpha > 0.001:
        visible = track.visible_at(t)
        line_h = 28
        x = 40
        # Bottom-up stack
        y = H - 80
        for line in reversed(visible):
            typed = track.typed_text(line, t)
            color = (0, 220, 200) if line.is_command else (180, 240, 200)
            a = int(255 * block_alpha)
            draw.text((x, y), typed, fill=(*color, a), font=font)
            # Blinking cursor on the actively-typing line (most recent, not done)
            if line is visible[-1] and len(typed) < len(line.text):
                if int(t * 2) % 2 == 0:
                    bbox = draw.textbbox((x, y), typed, font=font)
                    draw.rectangle(
                        [bbox[2] + 2, y + 4, bbox[2] + 14, y + 24],
                        fill=(*color, a),
                    )
            y -= line_h
            if y < 40:
                break

    # Isolated $ exit line — center of screen, types in 0.5s, holds 1s
    iso = track.isolated_visible_at(t)
    if iso is not None:
        typed = track.typed_text(iso, t)
        # Display alpha: full while active, holds for 1s after typing
        elapsed = t - iso.start_t
        iso_alpha = 1.0 if elapsed < 1.5 else 0.0
        if iso_alpha > 0:
            big = _load_font(36)
            bbox = draw.textbbox((0, 0), iso.text, font=big)
            tx = (W - (bbox[2] - bbox[0])) // 2
            ty = (H - (bbox[3] - bbox[1])) // 2
            draw.text((tx, ty), typed, fill=(0, 220, 200, int(255 * iso_alpha)),
                      font=big)

    return layer
```

- [ ] **Step 2: Wire text layer into `render_frame`**

Update `render_frame` to compose the text layer last and replace the debug HUD text. Replace `render_frame` body:

```python
def render_frame(frame_num: int, ctx: dict) -> Image.Image:
    t = frame_num / FPS
    state = arc_state(t)

    if "stars" not in ctx:
        ctx["stars"] = generate_starfield()
    if "bh_texture" not in ctx:
        ctx["bh_texture"] = create_black_hole_texture(512)
    if "light_dir" not in ctx:
        ld = np.array([0.5, 0.5, -0.5])
        ctx["light_dir"] = ld / np.linalg.norm(ld)
    if "cloud" not in ctx:
        ctx["cloud"] = clifford_attractor(PARTICLE_COUNT, -1.7, 1.8, 1.2, 0.9)
    if "text_track" not in ctx:
        ctx["text_track"] = TextTrack()
    if "font" not in ctx:
        ctx["font"] = _load_font(22)

    starfield = render_starfield_layer(ctx["stars"], t)
    cube_layer, lens_centers = render_cube_layer(
        t, state, ctx["bh_texture"], ctx["light_dir"]
    )
    particles = render_particles_layer(ctx["cloud"], t, state)
    text_layer = render_text_layer(ctx["text_track"], t, ctx["font"], state)

    if state["lens_K"] > 0.0 and lens_centers:
        starfield = apply_lensing(starfield, lens_centers, state["lens_K"])

    composite = Image.alpha_composite(starfield, particles)
    composite = Image.alpha_composite(composite, cube_layer)
    composite = Image.alpha_composite(composite, text_layer)
    return composite.convert("RGB")
```

- [ ] **Step 3: Render two smoke frames and confirm text behavior**

Temporarily change `smoke_render` to render frames at multiple t-values:

```python
def smoke_render(out_path: Path) -> None:
    ctx: dict = {}
    for t_sec in [3.5, 15.0, 26.0, 28.4]:
        frame_num = int(t_sec * FPS)
        img = render_frame(frame_num, ctx)
        p = out_path.with_name(f"{out_path.stem}_t{t_sec:04.1f}.png")
        img.save(p)
        print(f"smoke t={t_sec}s -> {p}")
```

Run: `python experimental/experiments/cosmic_collapse.py --smoke`
Expected: 4 PNGs:
- `t=3.5`: text block visible (couple lines), no cube yet, no lensing
- `t=15.0`: text block (~6 lines stacked), cube + particles, lensing visible
- `t=26.0`: text block fading out, particles falling toward center
- `t=28.4`: main text gone; large `$ exit` line centered

After confirming, leave the multi-frame smoke as-is (useful for later QA).

- [ ] **Step 4: Commit**

```bash
git add experimental/experiments/cosmic_collapse.py
git commit -m "feat(cosmic-collapse): god's-CLI text layer with typing, scrolling, fade, and isolated exit"
```

---

## Chunk 5: Audio

### Task 10: Audio scaffolding (drone) + tests

**Files:**
- Modify: `experimental/experiments/cosmic_collapse.py`
- Modify: `experimental/experiments/test_cosmic_collapse.py`

- [ ] **Step 1: Add failing tests for audio length and shape**

Append to `test_cosmic_collapse.py`:

```python
def test_compose_audio_length_matches_duration():
    sr, samples = cc.compose_audio()
    assert sr == 44100
    expected = sr * cc.DURATION_SEC
    # Allow up to 1 sample of rounding
    assert abs(len(samples) - expected) <= 1


def test_compose_audio_dtype_int16():
    _, samples = cc.compose_audio()
    assert samples.dtype == np.int16


def test_compose_audio_has_subbass_impact_at_t28():
    sr, samples = cc.compose_audio()
    # The 0.5s window starting at t=28 should be louder than the 0.5s window at t=10
    win = int(0.5 * sr)
    s28 = samples[28 * sr : 28 * sr + win].astype(np.int32)
    s10 = samples[10 * sr : 10 * sr + win].astype(np.int32)
    rms = lambda x: float(np.sqrt(np.mean(x * x)))
    assert rms(s28) > rms(s10) * 1.3
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest experimental/experiments/test_cosmic_collapse.py -v -k compose_audio`
Expected: 3 failures.

- [ ] **Step 3: Add audio module with drone layer only**

Add a new section to `cosmic_collapse.py`:

```python
# ---------- Audio ----------

SR = 44100


def fm_wave(duration: float, sr: int, carrier: float, modulator: float,
            index_env: np.ndarray) -> np.ndarray:
    n = int(sr * duration)
    t = np.linspace(0, duration, n, False)
    if np.isscalar(index_env):
        index_env = np.full(n, float(index_env))
    elif len(index_env) != n:
        index_env = np.interp(np.linspace(0, 1, n),
                              np.linspace(0, 1, len(index_env)), index_env)
    mod = index_env * np.sin(2 * np.pi * modulator * t)
    return np.sin(2 * np.pi * carrier * t + mod)


def _arc_intensity_curve(sr: int) -> np.ndarray:
    """Sample arc_state(t)['audio_intensity'] across the full duration."""
    n = sr * DURATION_SEC
    ts = np.linspace(0, DURATION_SEC, n, False)
    return np.array([arc_state(float(t))["audio_intensity"] for t in ts[::sr // 100]])


def compose_audio() -> tuple[int, np.ndarray]:
    """Build the layered cosmic_collapse audio. Returns (sample_rate, int16 samples)."""
    n = SR * DURATION_SEC

    # --- Layer 1: Drone (38Hz FM, modulation index follows arc) ---
    intensity_lo = _arc_intensity_curve(SR)
    index_env = 1.5 + 4.0 * intensity_lo
    drone = fm_wave(DURATION_SEC, SR, 38.0, 38.2, index_env) * 0.45

    # --- Layer 2 & 3 stubs (filled in next tasks) ---
    shimmer = np.zeros(n)
    events = np.zeros(n)

    # --- Sub-bass impact at t=28 (placed here so the test passes) ---
    impact_start = 28 * SR
    impact_dur = int(1.5 * SR)
    impact_t = np.linspace(0, 1.5, impact_dur, False)
    attack = np.minimum(impact_t / 0.05, 1.0)
    decay = np.exp(-2.5 * impact_t)
    impact_env = attack * decay
    impact_wave = np.sin(2 * np.pi * 30.0 * impact_t) * impact_env * 0.95
    end = min(impact_start + impact_dur, n)
    events[impact_start:end] += impact_wave[: end - impact_start]

    mixed = drone + shimmer + events
    mixed = np.clip(mixed, -1.0, 1.0)
    return SR, (mixed * 32767).astype(np.int16)
```

- [ ] **Step 4: Run tests to verify pass**

Run: `python -m pytest experimental/experiments/test_cosmic_collapse.py -v -k compose_audio`
Expected: 3 passing tests.

- [ ] **Step 5: Commit**

```bash
git add experimental/experiments/cosmic_collapse.py experimental/experiments/test_cosmic_collapse.py
git commit -m "feat(cosmic-collapse): audio drone layer + sub-bass impact + tests"
```

---

### Task 11: Add shimmer pad and lens-burst event layers

**Files:**
- Modify: `experimental/experiments/cosmic_collapse.py`

- [ ] **Step 1: Implement shimmer pad and lens bursts inside `compose_audio`**

Replace the body of `compose_audio` (specifically the `shimmer` and `events` sections) with:

```python
def compose_audio() -> tuple[int, np.ndarray]:
    n = SR * DURATION_SEC
    t_full = np.linspace(0, DURATION_SEC, n, False)

    # --- Layer 1: Drone ---
    intensity_lo = _arc_intensity_curve(SR)
    index_env = 1.5 + 4.0 * intensity_lo
    drone = fm_wave(DURATION_SEC, SR, 38.0, 38.2, index_env) * 0.45

    # --- Layer 2: Shimmer pad (act 2 onward) ---
    # Filtered noise + 220Hz FM partial; envelope opens at t=8, peaks t=18, ducks at collapse.
    pad_env = np.zeros(n)
    for i, t in enumerate(t_full[::SR // 100]):
        # Sample envelope at 100Hz then upsample by piecewise-constant repeat
        s = arc_state(float(t))
        amp = 0.0
        if t >= 8.0:
            amp = smoothstep(8.0, 18.0, t)
        if t >= 22.0:
            amp *= max(0.0, 1.0 - smoothstep(22.0, 28.0, t))
        pad_env[i * (SR // 100):(i + 1) * (SR // 100)] = amp
    pad_env = pad_env[:n]
    rng = np.random.default_rng(0xA1)
    noise = rng.normal(0, 1, n)
    # Cheap one-pole low-pass to take edge off
    lpf = np.zeros(n)
    a = 0.02
    last = 0.0
    for i in range(n):
        last = last + a * (noise[i] - last)
        lpf[i] = last
    fm_partial = fm_wave(DURATION_SEC, SR, 220.0, 110.0, np.full(n, 1.5)) * 0.18
    shimmer = (lpf * 0.25 + fm_partial) * pad_env

    # --- Layer 3: Events (sub-bass + lens bursts + keystrokes) ---
    events = np.zeros(n)

    # Lens bursts at fixed event times
    lens_event_times = [12.0, 14.5, 17.0, 19.5, 21.0]
    for et in lens_event_times:
        start = int(et * SR)
        dur = 0.25
        burst_n = int(dur * SR)
        bt = np.linspace(0, dur, burst_n, False)
        env = np.exp(-12 * bt)
        carrier = 110.0 if int(et) % 2 == 0 else 220.0
        burst = np.sin(2 * np.pi * carrier * bt) * np.sin(2 * np.pi * 7.0 * bt) * env * 0.32
        end = min(start + burst_n, n)
        events[start:end] += burst[: end - start]

    # Keystroke clicks on every $ line (TextTrack is the source of truth)
    track = TextTrack()
    for kt in track.keystroke_events():
        start = int(kt * SR)
        click_n = int(0.04 * SR)
        if start + click_n > n:
            continue
        click_rng = np.random.default_rng(int(kt * 1000))
        click = click_rng.normal(0, 1, click_n)
        env = np.exp(-180 * np.linspace(0, 0.04, click_n, False))
        events[start:start + click_n] += click * env * 0.18

    # Reverse-FM swell t=22 -> t=28, then sub-bass impact at t=28
    swell_start = int(22 * SR)
    swell_dur = int(6 * SR)
    swt = np.linspace(0, 6.0, swell_dur, False)
    rising_pitch = 60.0 + (180.0 * (swt / 6.0) ** 2)
    swell = np.sin(2 * np.pi * np.cumsum(rising_pitch) / SR)
    swell_env = (swt / 6.0) ** 2 * 0.35
    end = min(swell_start + swell_dur, n)
    events[swell_start:end] += (swell * swell_env)[: end - swell_start]

    impact_start = 28 * SR
    impact_dur = int(1.5 * SR)
    impact_t = np.linspace(0, 1.5, impact_dur, False)
    attack = np.minimum(impact_t / 0.05, 1.0)
    decay = np.exp(-2.5 * impact_t)
    impact_env = attack * decay
    impact_wave = np.sin(2 * np.pi * 30.0 * impact_t) * impact_env * 0.95
    end = min(impact_start + impact_dur, n)
    events[impact_start:end] += impact_wave[: end - impact_start]

    mixed = drone + shimmer + events
    mixed = np.clip(mixed, -1.0, 1.0)
    return SR, (mixed * 32767).astype(np.int16)
```

- [ ] **Step 2: Run all tests**

Run: `python -m pytest experimental/experiments/test_cosmic_collapse.py -v`
Expected: all tests still pass.

- [ ] **Step 3: Bonus listen-test (optional but recommended)**

Quick listen — write the audio to a wav and play it:

```bash
python -c "import sys; sys.path.insert(0, 'experimental/experiments'); import wave, cosmic_collapse as cc; sr, s = cc.compose_audio(); w = wave.open('experimental/cosmic_collapse_audio_preview.wav','wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(s.tobytes()); w.close(); print('wrote preview wav')"
```

Listen to `experimental/cosmic_collapse_audio_preview.wav`. Confirm: drone throughout, shimmer pad lifts in act 2, lens-burst blips around 12–21s, swell + sub-bass impact at 28s.

- [ ] **Step 4: Commit**

```bash
git add experimental/experiments/cosmic_collapse.py
git commit -m "feat(cosmic-collapse): shimmer pad, lens bursts, keystrokes, reverse swell"
```

---

## Chunk 6: Self-Healing and Full Render

### Task 12: 3-frame self-healing audit

**Files:**
- Modify: `experimental/experiments/cosmic_collapse.py`

- [ ] **Step 1: Add `SelfHealer`**

In `cosmic_collapse.py`, add a new section near the bottom:

```python
# ---------- Self-Healing ----------

class SelfHealer:
    """Pre-render audit: render 3 sample frames (acts 1/2/3) and check contrast.

    Re-rolls Clifford attractor params up to 5 times. Star + lens params are
    deterministic and never re-rolled.
    """

    SAMPLE_TIMES = [(4.0, 5.0), (15.0, 12.0), (27.0, 8.0)]  # (t_sec, min_contrast)
    MAX_ATTEMPTS = 5

    def __init__(self) -> None:
        self.rng = np.random.default_rng()

    def _try_params(self) -> tuple[float, float, float, float]:
        return (
            float(self.rng.uniform(-2.5, -1.0)),
            float(self.rng.uniform(1.2, 2.5)),
            float(self.rng.uniform(0.5, 2.0)),
            float(self.rng.uniform(0.3, 1.5)),
        )

    def find_good_params(self) -> tuple[float, float, float, float] | None:
        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            a, b, c, d = self._try_params()
            cloud = clifford_attractor(PARTICLE_COUNT, a, b, c, d)
            ctx: dict = {"cloud": cloud}

            ok = True
            print(f"   [AUDIT] Attempt {attempt}: a={a:.2f} b={b:.2f} c={c:.2f} d={d:.2f}")
            for t_sec, min_contrast in self.SAMPLE_TIMES:
                frame = render_frame(int(t_sec * FPS), ctx)
                stats = ImageStat.Stat(frame)
                contrast = float(np.mean(stats.stddev))
                print(f"     t={t_sec}s contrast={contrast:.2f} (min {min_contrast})")
                if contrast < min_contrast:
                    ok = False
                    break
            if ok:
                print(f">> AUDIT PASS on attempt {attempt}")
                return (a, b, c, d)
        print(">> AUDIT FAILED after max attempts")
        return None
```

- [ ] **Step 2: Confirm it imports cleanly**

Run: `python -c "import sys; sys.path.insert(0, 'experimental/experiments'); import cosmic_collapse as cc; print(cc.SelfHealer)"`
Expected: prints the class.

- [ ] **Step 3: Commit**

```bash
git add experimental/experiments/cosmic_collapse.py
git commit -m "feat(cosmic-collapse): 3-frame self-healing audit"
```

---

### Task 13: Full render pipeline (frames + audio + ffmpeg mux)

**Files:**
- Modify: `experimental/experiments/cosmic_collapse.py`

- [ ] **Step 1: Add `render_full` and update CLI**

Add at the bottom of `cosmic_collapse.py`, just above `if __name__ == "__main__":`:

```python
# ---------- Full Render Pipeline ----------

FFMPEG_CANDIDATES = [
    os.environ.get("PYREEL_FFMPEG"),
    "ffmpeg",
]


def _ffmpeg_path() -> str:
    for path in filter(None, FFMPEG_CANDIDATES):
        try:
            subprocess.run([path, "-version"], capture_output=True, check=True)
            return path
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    raise RuntimeError("ffmpeg not found; tried: " + ", ".join(FFMPEG_CANDIDATES))


def render_full() -> None:
    healer = SelfHealer()
    params = healer.find_good_params()
    if params is None:
        sys.exit(1)
    a, b, c, d = params
    cloud = clifford_attractor(PARTICLE_COUNT, a, b, c, d)
    ctx: dict = {"cloud": cloud}

    if TEMP_FRAMES_DIR.exists():
        shutil.rmtree(TEMP_FRAMES_DIR)
    TEMP_FRAMES_DIR.mkdir(parents=True)

    print(f">> RENDERING {TOTAL_FRAMES} frames at {W}x{H} @ {FPS}fps")
    for i in range(TOTAL_FRAMES):
        if i % 30 == 0:
            print(f"   frame {i}/{TOTAL_FRAMES}  (t={i/FPS:.1f}s)")
        img = render_frame(i, ctx)
        img.save(TEMP_FRAMES_DIR / f"frame_{i:04d}.png")

    print(">> SYNTHESIZING AUDIO")
    sr, samples = compose_audio()
    with wave.open(str(TEMP_AUDIO), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(samples.tobytes())

    print(">> ENCODING + MUXING")
    ffmpeg = _ffmpeg_path()
    cmd = [
        ffmpeg, "-y",
        "-framerate", str(FPS),
        "-i", str(TEMP_FRAMES_DIR / "frame_%04d.png"),
        "-i", str(TEMP_AUDIO),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(OUTPUT_VIDEO),
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        print(result.stderr.decode(errors="replace"))
        sys.exit(2)

    shutil.rmtree(TEMP_FRAMES_DIR)
    TEMP_AUDIO.unlink()
    print(f">> DONE: {OUTPUT_VIDEO}")
```

Update the CLI block:

```python
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true",
                        help="Render sample PNGs at several t-values and exit")
    args = parser.parse_args()
    if args.smoke:
        smoke_render(REPO_ROOT / "experimental" / "cosmic_collapse_smoke.png")
    else:
        render_full()
```

- [ ] **Step 2: Run a small frame range first to sanity check timing**

Add a temporary debug guard — put this near the top of `render_full` and remove later:

```python
# DEBUG: Uncomment to render only the first 60 frames for a quick check
# global TOTAL_FRAMES_OVERRIDE
# limit = 60
```

(No actual code change — just a note. Skip if you want to go straight to full render.)

Run: `python experimental/experiments/cosmic_collapse.py`
Expected: self-healing prints attempts, then 900 frames render (this will take 8–20 minutes), then ffmpeg mux completes.

- [ ] **Step 3: Verify the output file**

Run: `python -c "import subprocess; r = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1', r'experimental/cosmic_collapse.mp4'], capture_output=True, text=True); print('duration =', r.stdout.strip())"`
Expected: prints `duration = 30.000000` (or within 0.05s).

Open `experimental/cosmic_collapse.mp4` and confirm against the spec's 6 success criteria:
1. ✅ 30s @ 1280×720 with audio
2. ✅ Lensing visible during act 2 (12–22s)
3. ✅ God's-CLI text typed at the spec'd timestamps
4. ✅ Sub-bass at t=28 with `$ exit`
5. ✅ Self-healing passed within 5 attempts
6. ✅ No new dependencies (`pip freeze` matches before/after)

- [ ] **Step 4: Update .gitignore so we don't accidentally commit the mp4**

Check `.gitignore`:

Run: `git check-ignore -v experimental/cosmic_collapse.mp4`

If not ignored, append to `.gitignore`:

```
experimental/cosmic_collapse.mp4
experimental/cosmic_collapse_smoke*.png
experimental/cosmic_collapse_audio_preview.wav
experimental/cosmic_collapse_frames/
```

- [ ] **Step 5: Final commit**

```bash
git add experimental/experiments/cosmic_collapse.py .gitignore
git commit -m "feat(cosmic-collapse): full render pipeline + self-healing + ffmpeg mux"
```

---

## Done

After Task 13, `experimental/cosmic_collapse.mp4` exists locally. Watch it. If a beat misfires (lensing too subtle, sub-bass too quiet, a text line mistimed), tune the constants in `arc_state` and the relevant render fn — those are the parameters worth the engineer's time.

## Self-Review Result

- **Spec coverage**: every success criterion from the spec maps to a task — 30s/720p output (Task 13), lensing visible (Task 5/6), god's-CLI timing (Task 8/9), sub-bass at t=28 (Task 10/11), self-healing (Task 12), no new deps (only stdlib + numpy + PIL). ✅
- **Placeholder scan**: clean — every code step has full code; the only "stub" is the explicit zero-array shimmer/events in Task 10, which is filled in by Task 11. ✅
- **Type consistency**: `arc_state` keys (`cube_alpha`, `lens_K`, `particle_density`, `infall`, `text_alpha`, `audio_intensity`) are referenced consistently across Tasks 1, 6, 7, 9, 10, 11. `TextTrack` methods (`visible_at`, `typed_text`, `keystroke_events`, `isolated_visible_at`) defined in Task 8 are used in Tasks 9 and 11. `apply_lensing` signature `(layer, lens_centers, K)` defined in Task 5 is used identically in Task 6/7. ✅
