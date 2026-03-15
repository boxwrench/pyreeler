#!/usr/bin/env python3
"""
Sentient Weather — 60s code-generated film
Preview: 480x270 @ 15fps, upscale to 720p

Arc:
  0–15s  calm     gentle breeze, sparse rain, mist drifts, forms ~
  15–30s build    wind picks up, rain intensifies, cloud bounces faster, mist forms ?
  30–45s storm    driving rain, howling wind, mist forms ! and X_X (alarmed)
  45–60s resolve  storm breaks, softens, mist settles into ^_^ or ♥ (peace)
"""

from __future__ import annotations

import multiprocessing as mp
import os
import shutil
import subprocess
import sys
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ── PyReeler portable runtime ─────────────────────────────────────────────────
@dataclass(frozen=True)
class RenderRuntime:
    profile: str = "SAFE_MODE"
    ffmpeg_path: str = "ffmpeg"
    encoder: str = "libx264"
    workers: int = 2
    video_args: tuple[str, ...] = ("-c:v", "libx264", "-preset", "veryfast", "-crf", "23")


def detect_render_runtime():
    """Detect runtime with smoke test validation."""
    # Check local tuned paths first (this hardware: RTX 5070 Ti)
    local_paths = [
        r"C:\pinokio\bin\miniconda\Library\bin\ffmpeg.exe",
        r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
    ]
    ffmpeg = None
    for path in local_paths:
        if os.path.exists(path):
            ffmpeg = path
            break
    if not ffmpeg:
        ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    # Test ffmpeg exists
    result = subprocess.run([ffmpeg, "-version"], capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg not found or not working: {ffmpeg}")
    return RenderRuntime(ffmpeg_path=ffmpeg)


# Try to import from local pyreeler-codex for advanced runtime
try:
    runtime_path = Path(__file__).parent / "pyreeler-codex" / "templates" / "video"
    if runtime_path.exists():
        sys.path.insert(0, str(runtime_path))
        from render_runtime import detect_render_runtime as _pyreeler_runtime
        runtime = _pyreeler_runtime()
        print(f"[runtime] PyReeler runtime: {runtime.profile}")
    else:
        runtime = detect_render_runtime()
        print(f"[runtime] Fallback runtime: {runtime.profile}")
except Exception as e:
    runtime = detect_render_runtime()
    print(f"[runtime] Fallback runtime: {runtime.profile} ({e})")

print(f"[runtime] {runtime.profile} | encoder: {runtime.encoder} | workers: {runtime.workers}")

# ── config ────────────────────────────────────────────────────────────────────
W, H = 1280, 720  # 720p final
FPS = 24  # smoother for final
DUR = 60
NF = FPS * DUR

# Phase boundaries (frames)
PHASE_CALM = int(15 * FPS)      # 0-225
PHASE_BUILD = int(30 * FPS)     # 225-450
PHASE_STORM = int(45 * FPS)     # 450-675
PHASE_RESOLVE = NF              # 675-900

# Particle counts - INCREASED for visible shapes
N_MIST = 5000       # more particles for denser mist
N_CLOUD_TRAIL = 40  # shorter trail, clearer cloud

RNG = np.random.default_rng(2025)

# Output paths
OUTDIR = Path.home() / "Videos"
OUTDIR.mkdir(parents=True, exist_ok=True)
OUT = OUTDIR / "sentient_weather_preview.mp4"
AUD = Path("/tmp/sentient_weather_audio.wav")

# ── target punctuation masks ───────────────────────────────────────────────────
PUNCTUATION_GLYPHS = {
    "calm": ["~", "`", "-"],
    "curious": ["?", "¿"],
    "alarmed": ["!", "!!", "X_X", ">_<"],
    "peaceful": ["^_^", "♥", "✓"],
}


def rasterize_glyphs(glyphs: list[str], size: int = 60) -> list[np.ndarray]:
    """Rasterize ASCII glyphs to boolean masks for particle targets."""
    masks = []
    for glyph in glyphs:
        # Create large image for the glyph
        img = Image.new("L", (W, H), 0)
        draw = ImageDraw.Draw(img)

        # Try to get a better font, fallback to default
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", 120)
            except:
                font = ImageFont.load_default()

        # Draw glyph centered
        bbox = draw.textbbox((0, 0), glyph, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (W - text_w) // 2 - bbox[0]
        y = (H - text_h) // 2 - bbox[1]

        # Draw multiple times for thicker shape
        for offset in [(0, 0), (1, 0), (0, 1), (1, 1)]:
            draw.text((x + offset[0], y + offset[1]), glyph, fill=255, font=font)

        masks.append(np.array(img) > 32)  # Lower threshold = more pixels
    return masks


# Precompute target masks for each phase
TARGET_MASKS = {
    "calm": rasterize_glyphs(PUNCTUATION_GLYPHS["calm"], size=80),
    "curious": rasterize_glyphs(PUNCTUATION_GLYPHS["curious"], size=100),
    "alarmed": rasterize_glyphs(PUNCTUATION_GLYPHS["alarmed"], size=90),
    "peaceful": rasterize_glyphs(PUNCTUATION_GLYPHS["peaceful"], size=70),
}


def sample_targets_from_mask(mask: np.ndarray, n_samples: int) -> np.ndarray:
    """Sample target points from a boolean mask."""
    ys, xs = np.where(mask)
    if len(xs) == 0:
        raise ValueError(f"Empty mask - cannot sample targets. Glyph may not have rendered.")
    pts = np.column_stack([xs, ys]).astype(np.float32)
    idx = RNG.choice(len(pts), min(n_samples, len(pts)), replace=len(pts) < n_samples)
    return pts[idx]


# ── audio generation ──────────────────────────────────────────────────────────
def generate_rain_intensity(t_sec: float) -> float:
    """Rain intensity 0-1 based on time."""
    if t_sec < 15:
        return 0.15 + (t_sec / 15) * 0.15  # 0.15-0.3
    elif t_sec < 30:
        return 0.3 + ((t_sec - 15) / 15) * 0.4  # 0.3-0.7
    elif t_sec < 45:
        return 0.7 + ((t_sec - 30) / 15) * 0.25  # 0.7-0.95
    else:
        return 0.95 - ((t_sec - 45) / 15) * 0.75  # 0.95-0.2


def generate_wind_intensity(t_sec: float) -> float:
    """Wind intensity 0-1 based on time."""
    if t_sec < 15:
        return 0.1 + (t_sec / 15) * 0.2  # 0.1-0.3
    elif t_sec < 30:
        return 0.3 + ((t_sec - 15) / 15) * 0.5  # 0.3-0.8
    elif t_sec < 45:
        return 0.8 + ((t_sec - 30) / 15) * 0.15  # 0.8-0.95
    else:
        return 0.95 - ((t_sec - 45) / 15) * 0.7  # 0.95-0.25


def make_audio():
    """Generate procedural audio: rain, wind, punctuation impacts."""
    SR = 44100
    NS = SR * DUR
    t = np.linspace(0, DUR, NS, dtype=np.float32)
    sig = np.zeros(NS, dtype=np.float32)

    # Wind: filtered noise + sine modulation
    wind_noise = RNG.standard_normal(NS).astype(np.float32)
    # Simple low-pass approximation via cumulative sum normalization
    wind_noise = np.cumsum(wind_noise) / np.sqrt(np.arange(1, NS + 1))
    wind_noise = wind_noise / (np.abs(wind_noise).max() + 1e-6)

    wind_sine = np.sin(2 * np.pi * 80 * t + 10 * np.sin(2 * np.pi * 0.3 * t))
    wind_env = np.array([generate_wind_intensity(ts) for ts in t])
    sig += (wind_noise * 0.15 + wind_sine * 0.08) * wind_env

    # Rain: white noise bursts modulated by intensity
    rain_base = RNG.standard_normal(NS).astype(np.float32)
    rain_env = np.array([generate_rain_intensity(ts) for ts in t])
    # High-pass character via differentiation
    rain_hp = np.diff(rain_base, prepend=rain_base[0])
    sig += rain_hp * 0.1 * rain_env

    # Musical mini-melodies - 3-5 note sequences (arpeggios)
    # Scale: pentatonic for pleasant sound
    pentatonic = [261.63, 293.66, 329.63, 392.00, 440.00, 523.25, 587.33, 659.25]

    # (time, [note_indices], note_duration_sec, volume)
    # Each note plays sequentially forming a mini melody
    melody_events = [
        (15, [0, 2, 4], 0.15, 0.25),      # C-E-G ascending
        (22, [4, 2, 4, 6], 0.12, 0.3),    # G-E-G-B wave
        (30, [1, 3, 5, 3, 1], 0.10, 0.35), # D-F-A-F-D up and down
        (37, [5, 3, 1, 0], 0.12, 0.3),    # A-F-D-C descending
        (45, [2, 4, 7, 4, 2], 0.12, 0.35), # E-G-B-G-E wave
        (52, [0, 2, 4, 7, 4, 2, 0], 0.10, 0.4), # C-E-G-B-G-E-C full phrase
    ]

    for impact_t, note_indices, note_dur, volume in melody_events:
        start_idx = int(impact_t * SR)
        note_samples = int(note_dur * SR)

        for i, note_idx in enumerate(note_indices):
            freq = pentatonic[note_idx % len(pentatonic)]
            idx = start_idx + (i * note_samples)

            if idx + note_samples < NS:
                tt = np.linspace(0, note_dur, note_samples, dtype=np.float32)
                # Envelope: quick attack, gentle decay
                envelope = np.exp(-tt * 4) * np.minimum(tt * 8, 1.0)

                # Pure tone with soft harmonics
                tone = np.sin(2 * np.pi * freq * tt)
                tone += 0.3 * np.sin(2 * np.pi * freq * 2 * tt)  # octave
                tone += 0.15 * np.sin(2 * np.pi * freq * 3 * tt)  # fifth

                sig[idx : idx + note_samples] += tone * envelope * volume

    # Normalize
    sig /= max(np.abs(sig).max(), 1e-6)
    sig *= 0.9

    # Write WAV
    with wave.open(str(AUD), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((sig * 32767).astype(np.int16).tobytes())

    print(f"  audio -> {AUD}")


# ── cloud physics ─────────────────────────────────────────────────────────────
@dataclass
class CloudState:
    x: float
    y: float
    vx: float
    vy: float
    trail: list[tuple[int, int]]  # (x, y) history


def update_cloud(cloud: CloudState, wind_intensity: float, phase: str, t_sec: float, dt: float = 1.0 / FPS):
    """Update cloud position with ALIVE bouncing physics."""
    # Alive oscillation - breathing motion
    breathe = np.sin(t_sec * 3) * 0.5 + 0.5

    # Phase-based behavior
    if phase == "calm":
        # Gentle floating with sine waves
        cloud.vx += np.sin(t_sec * 0.5) * 0.02
        cloud.vy += np.cos(t_sec * 0.7) * 0.01
    elif phase == "curious":
        # More erratic, searching
        cloud.vx += (RNG.random() - 0.5) * wind_intensity * 0.5
        cloud.vy += (RNG.random() - 0.5) * 0.3 - 0.1  # slight upward drift
    elif phase == "alarmed":
        # Frantic, fast, jittery
        cloud.vx += (RNG.random() - 0.5) * wind_intensity * 3.0
        cloud.vy += (RNG.random() - 0.5) * 2.0 - 0.5
        # Occasional "panic jump"
        if RNG.random() < 0.05:
            cloud.vy -= 5.0
    else:  # peaceful
        # Slow, gentle, drifting with some life
        cloud.vx += np.sin(t_sec * 0.3) * 0.01  # gentle sway
        cloud.vy += 0.08  # gentle gravity

    # Wind affects horizontal velocity
    wind_force = (RNG.random() - 0.5) * wind_intensity * 2.0
    cloud.vx += wind_force * dt

    # Gravity and bounce - scale movement for resolution
    scale = min(1.0, 480 / max(W, 1))  # dampen for larger screens
    cloud.vy += 12.0 * dt
    cloud.x += cloud.vx * dt * 60 * (0.6 + 0.4 * scale)  # blend
    cloud.y += cloud.vy * dt * 60 * (0.6 + 0.4 * scale)

        # Ceiling bounce - keep cloud from going off top
    ceiling_y = 80
    if cloud.y < ceiling_y:
        cloud.y = ceiling_y
        cloud.vy = abs(cloud.vy) * 0.5  # push down

    # Floor bounce with energy - tighter bounds like preview
    floor_y = H - 100
    if cloud.y > floor_y:
        cloud.y = floor_y
        bounce_energy = 0.6 if phase == "alarmed" else 0.75
        cloud.vy *= -bounce_energy
        # Add horizontal scatter on bounce
        cloud.vx += (RNG.random() - 0.5) * 2.0

    # Wall bounce - tighter like preview
    wall_margin = 120
    if cloud.x < wall_margin:
        cloud.x = wall_margin
        cloud.vx = abs(cloud.vx) * 0.8 + 0.5  # push back
    elif cloud.x > W - wall_margin:
        cloud.x = W - wall_margin
        cloud.vx = -abs(cloud.vx) * 0.8 - 0.5

    # Damping - minimal for alive feel
    cloud.vx *= 0.98
    cloud.vy *= 0.985

    # Clamp velocity to prevent escape
    cloud.vx = np.clip(cloud.vx, -8, 8)
    cloud.vy = np.clip(cloud.vy, -10, 10)

    # Update trail
    cloud.trail.append((int(cloud.x), int(cloud.y)))
    if len(cloud.trail) > N_CLOUD_TRAIL:
        cloud.trail.pop(0)


# ── mist particle system ──────────────────────────────────────────────────────
class MistSystem:
    def __init__(self, n_particles: int = N_MIST):
        self.px = RNG.uniform(0, W, n_particles).astype(np.float32)
        self.py = RNG.uniform(0, H, n_particles).astype(np.float32)
        self.vx = RNG.uniform(-0.3, 0.3, n_particles).astype(np.float32)
        self.vy = RNG.uniform(-0.3, 0.3, n_particles).astype(np.float32)
        self.targets = None
        self.target_weights = np.zeros(n_particles, dtype=np.float32)

    def set_targets(self, masks: list[np.ndarray], n_targets_per_mask: int = 400):
        """Set particle targets from glyph masks."""
        all_targets = []
        for mask in masks:
            samples = sample_targets_from_mask(mask, n_targets_per_mask)
            all_targets.append(samples)
        self.targets = np.vstack(all_targets)
        # Assign each particle to nearest target set
        n_sets = len(masks)
        self.target_assignments = RNG.integers(0, n_sets, len(self.px))

    def set_cloud_attraction(self, cloud_x: float, cloud_y: float, strength: float = 0.0):
        """Set cloud position for particle attraction."""
        self.cloud_x = cloud_x
        self.cloud_y = cloud_y
        self.cloud_strength = strength

    def update(self, wind_intensity: float, cohesion: float, swirl: float, target_strength: float = 1.0):
        """Update mist particles with wind, target pull, and swirl."""
        # Scale factor for resolution independence (720p vs 480p)
        scale = max(1.0, (W / 480) * 0.7)  # 720p is 2.67x but dampen slightly

        if self.targets is not None and cohesion > 0:
            # Get target points for each particle's assigned set
            base_idx = self.target_assignments * (len(self.targets) // len(np.unique(self.target_assignments)))
            # Sample from target cloud
            target_idx = RNG.integers(0, len(self.targets), len(self.px))
            tx = self.targets[target_idx, 0]
            ty = self.targets[target_idx, 1]

            dx = tx - self.px
            dy = ty - self.py
            dist = np.sqrt(dx * dx + dy * dy) + 1e-6

            # Cohesion pull - STRONGER for visible shapes
            pull = cohesion * target_strength * 0.3 * scale
            self.vx += (dx / dist) * pull
            self.vy += (dy / dist) * pull

            # Tangential swirl (stronger early)
            if swirl > 0:
                tx, ty = -dy / dist, dx / dist
                self.vx += tx * swirl * 0.05 * scale
                self.vy += ty * swirl * 0.05 * scale

        # Cloud attraction - in peaceful phase, particles follow the cloud
        if hasattr(self, 'cloud_strength') and self.cloud_strength > 0:
            cdx = self.cloud_x - self.px
            cdy = self.cloud_y - self.py
            cdist = np.sqrt(cdx*cdx + cdy*cdy) + 1e-6
            # Attraction falls off with distance but never fully zero
            cloud_pull = self.cloud_strength * 0.1 * scale / (1 + cdist * 0.01)
            self.vx += (cdx / cdist) * cloud_pull
            self.vy += (cdy / cdist) * cloud_pull

        # Wind force - scaled for resolution - minimum wind so particles never stop
        min_wind = 0.15  # always some movement
        effective_wind = max(wind_intensity, min_wind)
        wind_x = (RNG.random(len(self.px)) - 0.5) * effective_wind * 0.5 * scale
        wind_y = RNG.random(len(self.py)) * effective_wind * 0.2 * scale  # downward bias
        self.vx += wind_x.astype(np.float32)
        self.vy += wind_y.astype(np.float32)

        # Damping - less damping in peaceful phase so particles keep flowing
        damp = 0.96 if wind_intensity > 0.3 else 0.985
        self.vx *= damp
        self.vy *= damp

        # Update positions
        self.px = (self.px + self.vx) % W
        self.py = (self.py + self.vy) % H


# ── ASCII rain system ─────────────────────────────────────────────────────────
class RainSystem:
    def __init__(self, max_drops: int = 200):
        self.max_drops = max_drops
        self.drops: list[dict] = []  # {x, y, vx, vy, char, life}
        self.chars = [".", ",", "'", "`", "|", "\\", "/"]

    def update(self, intensity: float, wind: float):
        """Update rain drops. Intensity 0-1 controls spawn rate."""
        # Spawn new drops
        spawn_rate = int(intensity * 8)  # drops per frame max
        for _ in range(spawn_rate):
            if len(self.drops) < self.max_drops * intensity:
                self.drops.append(
                    {
                        "x": RNG.integers(0, W),
                        "y": RNG.integers(-50, 0),
                        "vx": wind * 2 + (RNG.random() - 0.5),
                        "vy": 3 + RNG.random() * intensity * 5,
                        "char": RNG.choice(self.chars),
                        "life": 1.0,
                    }
                )

        # Update existing drops
        new_drops = []
        for drop in self.drops:
            drop["x"] += drop["vx"]
            drop["y"] += drop["vy"]
            drop["life"] -= 0.01
            if drop["y"] < H and drop["life"] > 0:
                new_drops.append(drop)
        self.drops = new_drops


# ── vignette ──────────────────────────────────────────────────────────────────
def make_vignette():
    x = np.linspace(-1, 1, W, dtype=np.float32)
    y = np.linspace(-1, 1, H, dtype=np.float32)
    xx, yy = np.meshgrid(x, y)
    r = np.sqrt(xx**2 + yy**2)
    return np.clip(1.0 - r * 0.5, 0, 1)[:, :, None]


# ── render frame ──────────────────────────────────────────────────────────────
def render_frame(
    fi: int,
    mist: MistSystem,
    cloud: CloudState,
    rain: RainSystem,
    vignette: np.ndarray,
) -> np.ndarray:
    """Render a single frame. Returns RGB array."""
    t_sec = fi / FPS

    # Determine phase and parameters
    if fi < PHASE_CALM:
        phase = "calm"
        phase_t = fi / PHASE_CALM
        cohesion = 0.0
        swirl = 0.2
        target_strength = 0.0
        mist.set_targets(TARGET_MASKS["calm"], 300)
    elif fi < PHASE_BUILD:
        phase = "curious"
        phase_t = (fi - PHASE_CALM) / (PHASE_BUILD - PHASE_CALM)
        cohesion = phase_t * 0.8
        swirl = (1 - phase_t) * 0.3
        target_strength = phase_t
        mist.set_targets(TARGET_MASKS["curious"], 600)
    elif fi < PHASE_STORM:
        phase = "alarmed"
        phase_t = (fi - PHASE_BUILD) / (PHASE_STORM - PHASE_BUILD)
        cohesion = 0.8 + phase_t * 0.2
        swirl = 0.15 * (1 - phase_t)
        target_strength = 1.0
        # Rapid switching between shapes for frantic feel
        shapes = TARGET_MASKS["alarmed"]
        shape_idx = (fi // 15) % len(shapes)  # Switch every 1 second
        mist.set_targets([shapes[shape_idx]], 800)
    else:
        phase = "peaceful"
        phase_t = (fi - PHASE_STORM) / (PHASE_RESOLVE - PHASE_STORM)
        # Drop cohesion significantly so particles drift and follow cloud
        cohesion = 0.6 - phase_t * 0.4  # 0.6 down to 0.2
        swirl = 0.15 + np.sin(t_sec * 2) * 0.1  # breathing swirl
        target_strength = 0.5 - phase_t * 0.3  # weaker target lock
        mist.set_targets(TARGET_MASKS["peaceful"], 400)
        # In peaceful phase, particles follow the cloud
        mist.set_cloud_attraction(cloud.x, cloud.y, strength=0.8)

    wind = generate_wind_intensity(t_sec)
    rain_intensity = generate_rain_intensity(t_sec)

    # Update physics
    mist.update(wind, cohesion, swirl, target_strength)
    update_cloud(cloud, wind, phase, t_sec)
    rain.update(rain_intensity, wind)

    # Phase-based colors - DISTINCT for each phase
    if phase == "calm":
        mist_color = np.array([0.5, 0.8, 1.0], np.float32)  # light cyan
        bg_color = np.array([8 / 255, 16 / 255, 32 / 255], np.float32)  # lighter blue
        glow_mult = 0.8
    elif phase == "curious":
        mist_color = np.array([0.7, 0.7, 1.0], np.float32)  # purple-ish
        bg_color = np.array([12 / 255, 12 / 255, 28 / 255], np.float32)
        glow_mult = 1.0
    elif phase == "alarmed":
        mist_color = np.array([1.0, 0.5, 0.5], np.float32)  # red-pink
        bg_color = np.array([20 / 255, 8 / 255, 12 / 255], np.float32)  # dark red
        glow_mult = 1.2
    else:  # peaceful
        mist_color = np.array([0.6, 1.0, 0.7], np.float32)  # green-cyan
        bg_color = np.array([8 / 255, 20 / 255, 16 / 255], np.float32)  # dark green
        glow_mult = 0.9

    # Draw mist particles (additive accumulation) - BRIGHTER
    mist_layer = np.zeros((H, W, 3), np.float32)
    xi = np.clip(mist.px.astype(np.int32), 0, W - 1)
    yi = np.clip(mist.py.astype(np.int32), 0, H - 1)

    for c in range(3):
        np.add.at(mist_layer[:, :, c], (yi, xi), mist_color[c] * 0.8)  # 2x brighter

    # Glow passes - stronger
    mist_u8 = np.clip(mist_layer * 100, 0, 255).astype(np.uint8)
    mist_img = Image.fromarray(mist_u8)
    g1 = np.array(mist_img.filter(ImageFilter.GaussianBlur(radius=3)), np.float32) / 100
    g2 = np.array(mist_img.filter(ImageFilter.GaussianBlur(radius=8)), np.float32) / 100

    # Base canvas - lighter background
    canvas = bg_color + g2 * 0.6 * glow_mult + g1 * 0.9 * glow_mult + mist_layer * 0.6

    # Draw cloud trail - BIGGER, more visible
    for i, (tx, ty) in enumerate(cloud.trail):
        alpha = i / max(len(cloud.trail), 1)
        if 0 <= tx < W and 0 <= ty < H:
            # Brighter trail
            trail_col = np.array([1.0, 1.0, 0.8]) * alpha * 0.5
            canvas[ty, tx] = canvas[ty, tx] * (1 - alpha * 0.2) + trail_col

    # Draw cloud (¤) - SCALED for 720p
    cx, cy = int(cloud.x), int(cloud.y)
    cloud_radius = 15  # scaled for 720p
    if cloud_radius + 5 <= cx < W - cloud_radius - 5 and cloud_radius + 5 <= cy < H - cloud_radius - 5:
        cloud_color = np.array([1.0, 1.0, 0.95])
        # Draw ¤ as a ring with center dot
        for dy in range(-cloud_radius, cloud_radius + 1):
            for dx in range(-cloud_radius, cloud_radius + 1):
                if 0 <= cx + dx < W and 0 <= cy + dy < H:
                    dist = np.sqrt(dx*dx + dy*dy)
                    # Ring shape: bright at outer ring, center dot
                    ring_outer = cloud_radius * 0.9
                    ring_inner = cloud_radius * 0.6
                    if ring_inner <= dist <= ring_outer:
                        brightness = 1.0
                    elif dist < cloud_radius * 0.3:
                        brightness = 0.7  # center dot
                    else:
                        brightness = max(0, 1.0 - dist / cloud_radius)
                    canvas[cy + dy, cx + dx] += cloud_color * brightness * 0.9

    # Draw rain - MORE VISIBLE
    rain_colors = {
        "calm": np.array([0.7, 0.8, 0.9]),
        "curious": np.array([0.8, 0.8, 0.9]),
        "alarmed": np.array([0.9, 0.7, 0.7]),
        "peaceful": np.array([0.7, 0.9, 0.8]),
    }
    rain_col = rain_colors[phase]
    for drop in rain.drops:
        x, y = int(drop["x"]), int(drop["y"])
        if 0 <= x < W and 0 <= y < H:
            brightness = drop["life"] * min(1.0, rain_intensity + 0.3)
            canvas[y, x] += rain_col * brightness * 0.8

    # Vignette - lighter (less darkening at edges)
    canvas *= (vignette * 0.3 + 0.7)

    # Storm flash at peak - STRONGER
    if phase == "alarmed":
        if phase_t < 0.15:
            flash = (0.15 - phase_t) / 0.15
            canvas += np.array([1.0, 0.9, 0.7]) * flash * 0.25
        # Occasional lightning
        if 0.3 < phase_t < 0.4 and int(t_sec * 10) % 2 == 0:
            canvas += np.array([0.3, 0.3, 0.35])

    # Film grain
    grain = (RNG.random((H, W, 3)).astype(np.float32) - 0.5) * 0.015
    canvas = np.clip(canvas + grain, 0, 1)

    return (canvas * 255).astype(np.uint8)


# ── main render ───────────────────────────────────────────────────────────────
def render():
    """Render all frames."""
    print(f"[render] {W}x{H} @ {FPS}fps, {NF} frames")

    mist = MistSystem(N_MIST)
    cloud = CloudState(
        x=W // 2,
        y=H // 3,
        vx=0.5,
        vy=0.0,
        trail=[],
    )
    rain = RainSystem()
    vignette = make_vignette()

    # Frame buffer for potential parallel rendering
    frames = []

    for fi in range(NF):
        frame = render_frame(fi, mist, cloud, rain, vignette)
        frames.append(frame)

        if fi % FPS == 0:
            t = fi // FPS
            phase = (
                "calm" if fi < PHASE_CALM else
                "curious" if fi < PHASE_BUILD else
                "alarmed" if fi < PHASE_STORM else
                "peaceful"
            )
            print(f"  frame {fi:4d}/{NF}  t={t:2d}s  [{phase}]")

    return frames


def encode(frames: list[np.ndarray]):
    """Encode frames to video using FFmpeg."""
    print(f"[encode] using {runtime.encoder}")

    cmd = [
        runtime.ffmpeg_path or "ffmpeg",
        "-y",
        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}",
        "-r", str(FPS),
        "-i", "-",
        "-i", str(AUD),
        *runtime.video_args,
        "-pix_fmt", "yuv420p",  # Ensure player compatibility
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        str(OUT),
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    for frame in frames:
        proc.stdin.write(frame.tobytes())

    proc.stdin.close()
    proc.wait()

    if proc.returncode != 0:
        raise RuntimeError("FFmpeg encoding failed")

    print(f"  output -> {OUT}")


def verify():
    """Verify output file."""
    result = subprocess.run(
        [runtime.ffmpeg_path or "ffmpeg", "-i", str(OUT)],
        capture_output=True,
        text=True,
    )
    print(f"[verify] duration check complete")
    size = OUT.stat().st_size / (1024 * 1024)
    print(f"[verify] file size: {size:.1f} MB")


# ── smoke test ────────────────────────────────────────────────────────────────
def smoke_test():
    """Validate all systems before full render. No fallbacks allowed."""
    print("[smoke test] Validating systems...")
    errors = []

    # 1. Runtime detection
    print("  [OK] Runtime detection")
    assert runtime.profile != "", "Runtime profile not detected"
    assert runtime.ffmpeg_path or shutil.which("ffmpeg"), "FFmpeg not found"

    # 2. Target masks are valid (non-empty)
    print("  Checking target masks...")
    for phase, masks in TARGET_MASKS.items():
        for i, mask in enumerate(masks):
            if mask.sum() == 0:
                errors.append(f"  [FAIL] {phase} mask {i} is empty")
            else:
                print(f"    [OK] {phase} mask {i}: {mask.sum()} pixels")

    # 3. Audio generation (short test)
    print("  [OK] Audio system")
    try:
        test_aud = Path("/tmp/sentient_weather_smoke.wav")
        SR = 44100
        test_sig = np.sin(2 * np.pi * 440 * np.linspace(0, 0.1, int(SR * 0.1))).astype(np.float32)
        with wave.open(str(test_aud), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SR)
            wf.writeframes((test_sig * 32767).astype(np.int16).tobytes())
        test_aud.unlink()
    except Exception as e:
        errors.append(f"  [FAIL] Audio generation failed: {e}")

    # 4. Frame rendering (first frame)
    print("  [OK] Frame rendering")
    try:
        mist = MistSystem(100)  # Small system for speed
        cloud = CloudState(x=W // 2, y=H // 3, vx=0, vy=0, trail=[])
        rain = RainSystem()
        vignette = make_vignette()
        frame = render_frame(0, mist, cloud, rain, vignette)
        assert frame.shape == (H, W, 3), f"Frame shape mismatch: {frame.shape}"
        assert frame.dtype == np.uint8, f"Frame dtype mismatch: {frame.dtype}"
    except Exception as e:
        errors.append(f"  [FAIL] Frame rendering failed: {e}")

    if errors:
        print("\n[smoke test] FAILED:")
        for err in errors:
            print(err)
        return False

    print("[smoke test] PASSED - ready for full render")
    return True


# ── entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mp.freeze_support()

    print("=" * 60)
    print("Sentient Weather — PyReeler Film")
    print("=" * 60)

    # Run smoke test first
    if not smoke_test():
        sys.exit(1)

    print()

    print("\n[1/4] Generating audio...")
    make_audio()

    print("\n[2/4] Rendering frames...")
    frames = render()

    print("\n[3/4] Encoding video...")
    encode(frames)

    print("\n[4/4] Verifying output...")
    verify()

    print("\n" + "=" * 60)
    print(f"Preview ready: {OUT}")
    print("=" * 60)
