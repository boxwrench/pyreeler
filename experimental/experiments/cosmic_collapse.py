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
from dataclasses import dataclass
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
    """Return all time-varying parameters for time t in [0, 30]."""
    cube_alpha = smoothstep(4.0, 8.0, t)

    if t < 8.0:
        lens_K = 0.0
    elif t < 22.0:
        lens_K = 0.55 * smoothstep(8.0, 22.0, t)
    else:
        lens_K = lerp(0.55, 0.95, smoothstep(22.0, 29.0, t))

    particle_density = smoothstep(8.0, 12.0, t)
    infall = smoothstep(22.0, 29.0, t)
    text_alpha = 1.0 - smoothstep(25.0, 27.5, t)

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


# ---------- Starfield ----------

def generate_starfield() -> np.ndarray:
    """Generate STAR_COUNT stars in a spherical shell. Returns (N, 4): xyz+brightness."""
    rng = np.random.default_rng(STAR_SEED)
    dirs = rng.normal(size=(STAR_COUNT, 3))
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    radii = rng.uniform(8.0, 25.0, size=STAR_COUNT)
    xyz = dirs * radii[:, None]
    brightness = rng.uniform(0.3, 1.0, size=STAR_COUNT)
    return np.concatenate([xyz, brightness[:, None]], axis=1)


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


def render_starfield_layer(stars: np.ndarray, t: float) -> Image.Image:
    """Render the un-lensed starfield as an RGBA layer."""
    img = Image.new("RGBA", (W, H), (5, 5, 12, 255))
    pixels = np.array(img)

    rot = get_rotation_matrix(t * 0.01, t * 0.013, 0.0)
    rotated = stars[:, :3] @ rot.T
    pts2d, z_eff = project_points(rotated, W, H)

    visible = (
        (pts2d[:, 0] >= 1) & (pts2d[:, 0] < W - 1) &
        (pts2d[:, 1] >= 1) & (pts2d[:, 1] < H - 1) &
        (z_eff > 0.5)
    )
    pts = pts2d[visible].astype(int)
    bri = stars[visible, 3]
    depths = z_eff[visible]

    intensity = np.clip(255.0 * bri * (12.0 / depths), 30, 255).astype(np.uint8)
    pixels[pts[:, 1], pts[:, 0]] = np.stack(
        [intensity, intensity, np.minimum(255, intensity + 30),
         np.full_like(intensity, 255)], axis=1
    )

    bright_mask = intensity > 180
    bx = pts[bright_mask, 0]
    by = pts[bright_mask, 1]
    bint = (intensity[bright_mask] // 3).astype(np.uint8)
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        x = np.clip(bx + dx, 0, W - 1)
        y = np.clip(by + dy, 0, H - 1)
        pixels[y, x, 0] = np.maximum(pixels[y, x, 0], bint)
        pixels[y, x, 1] = np.maximum(pixels[y, x, 1], bint)
        pixels[y, x, 2] = np.maximum(pixels[y, x, 2], np.minimum(255, bint.astype(np.int32) + 20).astype(np.uint8))

    return Image.fromarray(pixels, mode="RGBA")


# ---------- Gravitational Lensing ----------

def apply_lensing(layer: Image.Image, lens_centers: list, K: float) -> Image.Image:
    """Warp `layer` by Schwarzschild-style radial displacement around each lens center."""
    if K <= 0.0 or not lens_centers:
        return layer.copy()

    src = np.array(layer, dtype=np.float32)
    h, w = src.shape[:2]

    yy, xx = np.meshgrid(np.arange(h, dtype=np.float32),
                         np.arange(w, dtype=np.float32),
                         indexing="ij")

    sum_dx = np.zeros_like(xx)
    sum_dy = np.zeros_like(yy)

    for cx, cy, strength in lens_centers:
        dx = xx - cx
        dy = yy - cy
        r2 = dx * dx + dy * dy + 1.0
        k_eff = K * strength * 4000.0
        scale = np.minimum(k_eff / r2, 0.95)
        sum_dx -= scale * dx
        sum_dy -= scale * dy

    src_x = xx + sum_dx
    src_y = yy + sum_dy

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


# ---------- Cube + Black-Hole Faces ----------

def find_coeffs(pa, pb):
    matrix = []
    for p1, p2 in zip(pa, pb):
        matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0]*p1[0], -p2[0]*p1[1]])
        matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1]*p1[0], -p2[1]*p1[1]])
    A = np.matrix(matrix, dtype=float)
    B = np.array(pb).reshape(8)
    res = np.linalg.solve(A, B)
    return np.array(res).reshape(8)


def create_black_hole_texture(size=512):
    """Accretion-disk style: dark singularity, bright orange ring, cyan glow."""
    y, x = np.ogrid[-1:1:size*1j, -1:1:size*1j]
    dist = np.sqrt(x*x + y*y)
    theta = np.arctan2(y, x)

    # Swirl pattern in the disk
    swirl = 0.5 + 0.5 * np.sin(theta * 4 + dist * 18)

    # Bright accretion ring (peak at dist=0.4, falls off both sides)
    ring = np.exp(-((dist - 0.4) ** 2) / 0.015) * 255

    # Outer corona (soft falloff outside the ring)
    corona = np.clip(1.0 - (dist - 0.45) * 1.6, 0, 1) * 180
    corona[dist < 0.45] = 0

    # Inner void (kill light near singularity)
    void = (dist < 0.25).astype(float)

    # Compose alpha
    alpha = np.maximum(ring, corona)
    alpha *= (1.0 - void)
    alpha = np.clip(alpha, 0, 255)

    # Color: ring is hot orange-yellow, corona is cyan-magenta
    ring_norm = ring / 255.0
    cor_norm = corona / 255.0
    r = np.clip(ring_norm * 255 + cor_norm * 180 * swirl + ring_norm * 60 * swirl, 0, 255)
    g = np.clip(ring_norm * 200 + cor_norm * 60 + ring_norm * 100 * swirl, 0, 255)
    b = np.clip(ring_norm * 80 + cor_norm * 220, 0, 255)

    img_data = np.stack([r, g, b, alpha], axis=-1).astype(np.uint8)
    return Image.fromarray(img_data, mode="RGBA")


def create_cube():
    vertices = np.array([
        [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
        [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]
    ], dtype=float)
    faces = [
        (4, 5, 6, 7),
        (1, 0, 3, 2),
        (0, 4, 7, 3),
        (5, 1, 2, 6),
        (3, 7, 6, 2),
        (0, 1, 5, 4),
    ]
    return vertices, faces


def render_cube_layer(t: float, state: dict, bh_texture: Image.Image,
                      light_dir: np.ndarray) -> tuple[Image.Image, list]:
    """Render cube + black-hole faces. Returns (RGBA layer, lens_centers list)."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lens_centers: list = []

    if state["cube_alpha"] <= 0.001:
        return layer, lens_centers

    vertices, faces = create_cube()
    rot = get_rotation_matrix(t * 0.45, t * 0.27, t * 0.09)
    rotated = vertices @ rot.T
    cube_2d, _ = project_points(rotated, W, H)

    face_depths = []
    for face in faces:
        z_avg = np.mean([rotated[v, 2] for v in face])
        face_depths.append((z_avg, face))
    face_depths.sort(key=lambda x: x[0], reverse=True)

    bh_rotated = bh_texture.rotate(t * 30.0, resample=Image.BILINEAR)
    src_pa = [(0, 0), (bh_rotated.width, 0),
              (bh_rotated.width, bh_rotated.height), (0, bh_rotated.height)]

    draw = ImageDraw.Draw(layer)
    alpha = state["cube_alpha"]

    for _, face in face_depths:
        v0, v1, v2 = rotated[face[0]], rotated[face[1]], rotated[face[2]]
        normal = np.cross(v1 - v0, v2 - v1)
        n_len = np.linalg.norm(normal)
        if n_len < 1e-6:
            continue
        normal = normal / n_len

        if normal[2] >= 0:
            continue

        intensity = float(np.clip((np.dot(normal, light_dir) + 1.0) / 2.0, 0.1, 1.0))
        target_pb = [tuple(cube_2d[v]) for v in face]

        try:
            coeffs = find_coeffs(target_pb, src_pa)
        except np.linalg.LinAlgError:
            continue

        warped = bh_rotated.transform((W, H), Image.PERSPECTIVE, coeffs, Image.BILINEAR)

        if intensity < 1.0:
            r, g, b, a = warped.split()
            r = r.point(lambda i, k=intensity: int(i * k))
            g = g.point(lambda i, k=intensity: int(i * k))
            b = b.point(lambda i, k=intensity: int(i * k))
            warped = Image.merge("RGBA", (r, g, b, a))

        if alpha < 1.0:
            r, g, b, a = warped.split()
            a = a.point(lambda i, k=alpha: int(i * k))
            warped = Image.merge("RGBA", (r, g, b, a))

        mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mask).polygon(target_pb, fill=int(255 * alpha))
        layer.paste(warped, (0, 0), mask)

        outline_col = (
            0,
            int(120 * intensity * alpha),
            int(100 * intensity * alpha),
            int(60 * alpha),
        )
        draw.polygon(target_pb, outline=outline_col)

        cx = float(np.mean([cube_2d[v, 0] for v in face]))
        cy = float(np.mean([cube_2d[v, 1] for v in face]))
        face_strength = float(-normal[2])
        lens_centers.append((cx, cy, face_strength * alpha))

    return layer, lens_centers


# ---------- Particle Nebula ----------

def clifford_attractor(count, a, b, c, d):
    x, y = 0.1, 0.1
    points = []
    for _ in range(count):
        xn = np.sin(a * y) + c * np.cos(a * x)
        yn = np.sin(b * x) + d * np.cos(b * y)
        z = np.sin(xn * yn) * 2.5
        points.append([xn * 6, yn * 6, z])
        x, y = xn, yn
    return np.array(points)


def render_particles_layer(cloud: np.ndarray, t: float, state: dict) -> Image.Image:
    """Render Clifford particles, density-modulated with act-3 infall."""
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
    alpha = (alpha * (1.0 - 0.7 * state["infall"])).astype(np.uint8)

    pixels[pts[:, 1], pts[:, 0]] = np.stack(
        [np.zeros_like(alpha), np.full_like(alpha, 200),
         np.full_like(alpha, 255), alpha], axis=1
    )
    return Image.fromarray(pixels, mode="RGBA")


# ---------- God's-CLI Text Track ----------

TYPING_CPS = 30.0


@dataclass
class TextLine:
    start_t: float
    text: str
    is_command: bool
    isolated: bool = False


class TextTrack:
    """Owns the god's-CLI script timeline."""

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
        if t <= line.start_t:
            return ""
        chars = int((t - line.start_t) * TYPING_CPS)
        return line.text[:chars]

    def visible_at(self, t: float, max_lines: int = 10) -> list:
        started = [l for l in self.timeline
                   if l.start_t <= t and not l.isolated]
        return started[-max_lines:]

    def isolated_visible_at(self, t: float):
        for line in self.timeline:
            if line.isolated and line.start_t <= t <= line.start_t + 1.5:
                return line
        return None

    def keystroke_events(self) -> list:
        return [l.start_t for l in self.timeline if l.is_command]


def _load_font(size: int = 22):
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


def render_text_layer(track: TextTrack, t: float, font, big_font, state: dict) -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    block_alpha = state["text_alpha"]
    if block_alpha > 0.001:
        visible = track.visible_at(t)
        line_h = 28
        x = 40
        y = H - 80
        a = int(255 * block_alpha)
        for line in reversed(visible):
            typed = track.typed_text(line, t)
            color = (0, 220, 200) if line.is_command else (180, 240, 200)
            draw.text((x, y), typed, fill=(*color, a), font=font)
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

    iso = track.isolated_visible_at(t)
    if iso is not None:
        typed = track.typed_text(iso, t)
        elapsed = t - iso.start_t
        iso_alpha = 1.0 if elapsed < 1.5 else 0.0
        if iso_alpha > 0:
            bbox = draw.textbbox((0, 0), iso.text, font=big_font)
            tx = (W - (bbox[2] - bbox[0])) // 2
            ty = (H - (bbox[3] - bbox[1])) // 2
            draw.text((tx, ty), typed, fill=(0, 220, 200, int(255 * iso_alpha)),
                      font=big_font)

    return layer


# ---------- Frame Rendering ----------

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
    if "big_font" not in ctx:
        ctx["big_font"] = _load_font(40)

    starfield = render_starfield_layer(ctx["stars"], t)
    cube_layer, lens_centers = render_cube_layer(
        t, state, ctx["bh_texture"], ctx["light_dir"]
    )
    particles = render_particles_layer(ctx["cloud"], t, state)
    text_layer = render_text_layer(ctx["text_track"], t, ctx["font"], ctx["big_font"], state)

    if state["lens_K"] > 0.0 and lens_centers:
        starfield = apply_lensing(starfield, lens_centers, state["lens_K"])

    composite = Image.alpha_composite(starfield, particles)
    composite = Image.alpha_composite(composite, cube_layer)
    composite = Image.alpha_composite(composite, text_layer)
    return composite.convert("RGB")


def smoke_render(out_path: Path) -> None:
    """Render sample frames at several t-values."""
    ctx: dict = {}
    for t_sec in [3.5, 15.0, 26.0, 28.4]:
        frame_num = int(t_sec * FPS)
        img = render_frame(frame_num, ctx)
        p = out_path.with_name(f"{out_path.stem}_t{t_sec:04.1f}.png")
        img.save(p)
        print(f"smoke t={t_sec}s -> {p}")


# ---------- Audio ----------

SR = 44100


def fm_wave(duration: float, sr: int, carrier: float, modulator: float,
            index_env) -> np.ndarray:
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
    """Sample audio_intensity at sr resolution."""
    n = sr * DURATION_SEC
    ts = np.linspace(0, DURATION_SEC, n, False)
    # Sample at 100Hz and upsample for speed
    coarse_n = 100 * DURATION_SEC
    coarse_ts = np.linspace(0, DURATION_SEC, coarse_n, False)
    coarse = np.array([arc_state(float(t))["audio_intensity"] for t in coarse_ts])
    return np.interp(ts, coarse_ts, coarse)


def compose_audio() -> tuple:
    """Build the layered cosmic_collapse audio. Returns (sr, int16 samples)."""
    n = SR * DURATION_SEC
    t_full = np.linspace(0, DURATION_SEC, n, False)

    # Drone (38Hz FM)
    intensity_curve = _arc_intensity_curve(SR)
    index_env = 1.5 + 4.0 * intensity_curve
    drone = fm_wave(DURATION_SEC, SR, 38.0, 38.2, index_env) * 0.45

    # Shimmer pad
    pad_env = np.zeros(n)
    coarse_steps = 100 * DURATION_SEC
    for i in range(coarse_steps):
        t = i / 100.0
        amp = 0.0
        if t >= 8.0:
            amp = smoothstep(8.0, 18.0, t)
        if t >= 22.0:
            amp *= max(0.0, 1.0 - smoothstep(22.0, 28.0, t))
        start = i * (SR // 100)
        end = start + (SR // 100)
        pad_env[start:end] = amp
    pad_env = pad_env[:n]

    rng = np.random.default_rng(0xA1)
    noise = rng.normal(0, 1, n)
    # One-pole low-pass (vectorized via scipy alternative — but stay numpy-only)
    a = 0.02
    lpf = np.zeros(n)
    last = 0.0
    for i in range(n):
        last = last + a * (noise[i] - last)
        lpf[i] = last

    fm_partial = fm_wave(DURATION_SEC, SR, 220.0, 110.0, 1.5) * 0.18
    shimmer = (lpf * 0.25 + fm_partial) * pad_env

    # Events: lens bursts + keystrokes + swell + sub-bass
    events = np.zeros(n)

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


# ---------- Self-Healing ----------

class SelfHealer:
    """3-frame audit before committing to the full render."""

    SAMPLE_TIMES = [(4.0, 5.0), (15.0, 12.0), (27.0, 8.0)]
    MAX_ATTEMPTS = 5

    def __init__(self) -> None:
        self.rng = np.random.default_rng()

    def _try_params(self):
        return (
            float(self.rng.uniform(-2.5, -1.0)),
            float(self.rng.uniform(1.2, 2.5)),
            float(self.rng.uniform(0.5, 2.0)),
            float(self.rng.uniform(0.3, 1.5)),
        )

    def find_good_params(self):
        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            a, b, c, d = self._try_params()
            cloud = clifford_attractor(PARTICLE_COUNT, a, b, c, d)
            ctx: dict = {"cloud": cloud}

            print(f"   [AUDIT] Attempt {attempt}: a={a:.2f} b={b:.2f} c={c:.2f} d={d:.2f}")
            ok = True
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true",
                        help="Render sample PNGs at several t-values and exit")
    args = parser.parse_args()
    if args.smoke:
        smoke_render(REPO_ROOT / "experimental" / "cosmic_collapse_smoke.png")
    else:
        render_full()
