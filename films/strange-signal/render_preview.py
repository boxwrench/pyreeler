"""Render the full-duration Strange Signal AI-film preview."""
from __future__ import annotations

import math
import multiprocessing as mp
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from templates.audio.audio_engine import mix_stems, write_mono_wav
from templates.video.parallel_render import ordered_frame_map
from templates.video.render_runtime import detect_render_runtime

DURATION = 20.0
FPS = 20
WIDTH, HEIGHT = 480, 270
TOTAL = int(DURATION * FPS)
SAMPLE_RATE = 48_000


def smoothstep(a: float, b: float, x: float) -> float:
    x = np.clip((x - a) / (b - a), 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def attractor(kind: str, count: int = 18_000) -> np.ndarray:
    p = np.empty((count, 3), dtype=np.float32)
    x, y, z = 0.1, 0.0, 0.0
    dt = 0.006
    for i in range(count + 1500):
        if kind == "aizawa":
            a, b, c, d, e, f = .95, .7, .6, 3.5, .25, .1
            dx = (z-b)*x-d*y
            dy = d*x+(z-b)*y
            dz = c+a*z-(z**3)/3-(x*x+y*y)*(1+e*z)+f*z*x**3
        else:
            b = .208186
            dx = math.sin(y)-b*x
            dy = math.sin(z)-b*y
            dz = math.sin(x)-b*z
        x += dx*dt; y += dy*dt; z += dz*dt
        if i >= 1500:
            p[i-1500] = x, y, z
    p -= p.mean(axis=0)
    p /= max(float(np.max(np.linalg.norm(p, axis=1))), 1e-6)
    return p


def project(points: np.ndarray, angle: float, scale: float, ox: float = 0.0) -> list[tuple[int, int]]:
    ca, sa = math.cos(angle), math.sin(angle)
    x = points[:, 0]*ca + points[:, 2]*sa
    z = -points[:, 0]*sa + points[:, 2]*ca
    y = points[:, 1]
    tilt = .72
    yp = y*tilt - z*.32
    return list(zip((WIDTH*.5 + ox + x*scale).astype(int), (HEIGHT*.5 + yp*scale).astype(int)))


class FrameRenderer:
    def __init__(self) -> None:
        self.a = attractor("aizawa")
        self.b = attractor("thomas")

    def __call__(self, idx: int) -> bytes:
        t = idx / FPS
        phase = t / DURATION
        rng = np.random.default_rng(4400 + idx)
        base = Image.new("RGB", (WIDTH, HEIGHT), (1, 3, 6))
        haze = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
        hp = haze.load()
        for _ in range(90):
            x, y = int(rng.integers(WIDTH)), int(rng.integers(HEIGHT))
            v = int(rng.integers(3, 16))
            hp[x, y] = (0, v, v + 4)
        base = Image.blend(base, haze.filter(ImageFilter.GaussianBlur(2)), .7)

        glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        sharp = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        gd, sd = ImageDraw.Draw(glow), ImageDraw.Draw(sharp)

        collapse = 1.0 - smoothstep(10.2, 11.15, t)
        rebirth = smoothstep(11.25, 12.2, t)
        energy = collapse if t < 11.2 else rebirth
        reveal_a = smoothstep(.5, 5.5, t)
        reveal_b = smoothstep(5.0, 9.5, t)
        if t > 11.2:
            reveal_a = reveal_b = rebirth

        n_a = max(4, int(len(self.a) * reveal_a))
        n_b = max(4, int(len(self.b) * reveal_b))
        angle = phase * math.tau * .72
        scale = 88 + 22*math.sin(phase*math.pi)
        pa = project(self.a[:n_a], angle, scale, -34*(1-rebirth) if t > 11.2 else -18*reveal_b)
        pb = project(self.b[:n_b], -angle*1.37, scale*1.08, 34*rebirth if t > 11.2 else 18*reveal_b)

        alpha_a = int(220 * energy)
        alpha_b = int(205 * energy * reveal_b)
        if len(pa) > 1:
            gd.line(pa, fill=(0, 220, 150, max(15, alpha_a//3)), width=5)
            sd.line(pa, fill=(65, 255, 175, alpha_a), width=1)
        if len(pb) > 1:
            gd.line(pb, fill=(25, 115, 255, max(12, alpha_b//3)), width=5)
            sd.line(pb, fill=(100, 180, 255, alpha_b), width=1)

        if 10.55 < t < 12.0:
            k = smoothstep(10.55, 11.15, t) * (1-smoothstep(11.45, 12.0, t))
            r = int(8 + 110*k)
            sd.ellipse((WIDTH//2-r, HEIGHT//2-r, WIDTH//2+r, HEIGHT//2+r), outline=(180, 255, 245, int(240*k)), width=2)
        if t > 17.2:
            resolve = smoothstep(17.2, 20, t)
            veil = Image.new("RGBA", (WIDTH, HEIGHT), (0, 2, 5, int(245*resolve)))
            sharp = Image.alpha_composite(sharp, veil)
            sd = ImageDraw.Draw(sharp)
            r = int(34*(1-resolve)+3)
            sd.ellipse((WIDTH//2-r, HEIGHT//2-r, WIDTH//2+r, HEIGHT//2+r), fill=(120,255,205,int(255*(1-resolve*.35))))

        base = Image.alpha_composite(base.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(4)))
        base = Image.alpha_composite(base, sharp)
        d = ImageDraw.Draw(base)
        for y in range(0, HEIGHT, 3):
            d.line((0, y, WIDTH, y), fill=(0, 0, 0, 34))
        d.text((12, HEIGHT-20), f"SIGNAL {idx:04d} / {TOTAL:04d}", fill=(42, 108, 91, 150))
        return base.convert("RGB").tobytes()


def audio_mix() -> np.ndarray:
    n = int(DURATION*SAMPLE_RATE)
    t = np.arange(n, dtype=np.float32)/SAMPLE_RATE
    rng = np.random.default_rng(771)
    ambience = .07*np.sin(2*np.pi*(43 + 2*np.sin(t*.17))*t)
    ambience += .025*np.sin(2*np.pi*86.2*t) + .012*rng.standard_normal(n)
    ambience *= (.45 + .55*np.sin(np.pi*np.minimum(t/DURATION, 1))**2)

    pulse = np.zeros(n, dtype=np.float32)
    for beat in np.arange(1.0, 18.0, .72):
        start = int(beat*SAMPLE_RATE); length = min(int(.32*SAMPLE_RATE), n-start)
        u = np.arange(length, dtype=np.float32)/SAMPLE_RATE
        amp = .10 + .12*smoothstep(3, 10, float(beat))
        pulse[start:start+length] += amp*np.sin(2*np.pi*(64-22*u)*u)*np.exp(-12*u)

    impacts = np.zeros(n, dtype=np.float32)
    for when, amp in ((5.0,.18),(10.85,.65),(11.45,.52),(17.2,.28)):
        start=int(when*SAMPLE_RATE); length=min(int(1.5*SAMPLE_RATE),n-start)
        u=np.arange(length,dtype=np.float32)/SAMPLE_RATE
        impacts[start:start+length] += amp*(np.sin(2*np.pi*38*u)+.25*rng.standard_normal(length))*np.exp(-4.8*u)

    shimmer = .018*np.sin(2*np.pi*(740 + 90*np.sin(t*.4))*t)
    shimmer *= smoothstep(11.3, 14.0, t) * (1-smoothstep(18.0, 20.0, t))
    silence = 1.0 - .93*(smoothstep(10.1,10.7,t)*(1-smoothstep(11.25,11.6,t)))
    for stem in (ambience, pulse, impacts, shimmer):
        stem *= silence
    return mix_stems({"ambience":ambience,"pulse":pulse,"impacts":impacts,"score":shimmer},
                     gains={"ambience":.8,"pulse":1.0,"impacts":.85,"score":.7})


def render(output: Path, workers_override: int | None = None, frame_count: int = TOTAL) -> None:
    runtime = detect_render_runtime()
    workers = runtime.workers if workers_override is None else workers_override
    renderer = FrameRenderer()
    with tempfile.TemporaryDirectory(prefix="strange-signal-") as td:
        wav = Path(td)/"mix.wav"
        write_mono_wav(wav, audio_mix(), SAMPLE_RATE)
        cmd = [runtime.ffmpeg_path, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{WIDTH}x{HEIGHT}", "-r", str(FPS), "-i", "-", "-i", str(wav),
               *runtime.video_args, "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
               "-shortest", "-movflags", "+faststart", str(output)]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        try:
            for frame in ordered_frame_map(range(frame_count), renderer, workers=workers):
                proc.stdin.write(frame)
        finally:
            proc.stdin.close()
        if proc.wait() != 0:
            raise RuntimeError("FFmpeg failed")


if __name__ == "__main__":
    mp.freeze_support()
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--workers", type=int)
    parser.add_argument("--frames", type=int, default=TOTAL)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    render(args.output, args.workers, args.frames)
