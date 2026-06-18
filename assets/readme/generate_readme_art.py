#!/usr/bin/env python3
"""Generate the animated phosphor-green SVG art used in the README.

The README art is, fittingly, code-generated — the same idea PyReeler is built
on. Each function emits a standalone animated SVG (SMIL animation survives when
the file is embedded via <img> on GitHub). Math draws itself in CRT green.

Run:  python3 assets/readme/generate_readme_art.py
Out:  banner.svg, wave-divider.svg, lissajous.svg, lorenz.svg  (this folder)
"""
from __future__ import annotations

import math
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent

# Phosphor palette — matched to the GitHub Pages site (index.html).
BG = "#0d1117"
PHOSPHOR = "#39ff14"      # classic P1 CRT green
PHOSPHOR_DIM = "#1f8f3a"
PHOSPHOR_CORE = "#d6ffcc"  # hot center of the glow
GRID = "#15311c"


def _glow(filter_id: str = "glow", blur: float = 3.5) -> str:
    """A reusable phosphor bloom filter (Gaussian blur merged under the source)."""
    return f"""
    <filter id="{filter_id}" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="{blur}" result="b"/>
      <feMerge>
        <feMergeNode in="b"/>
        <feMergeNode in="b"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>"""


def _scanlines(width: int, height: int, opacity: float = 0.10) -> str:
    """Horizontal CRT scanline overlay + one bright bar sweeping top to bottom."""
    return f"""
  <defs>
    <pattern id="scan" width="1" height="3" patternUnits="userSpaceOnUse">
      <rect width="{width}" height="1" fill="{PHOSPHOR}" opacity="{opacity}"/>
    </pattern>
  </defs>
  <rect width="{width}" height="{height}" fill="url(#scan)"/>
  <rect width="{width}" height="14" fill="{PHOSPHOR}" opacity="0.06">
    <animate attributeName="y" from="-14" to="{height}" dur="6s" repeatCount="indefinite"/>
  </rect>"""


def _comet_path(points: list[tuple[float, float]], *, dim_op: float = 0.22,
                dur: float = 6.0, head: float = 0.06, width: float = 2.2,
                filter_id: str = "glow") -> str:
    """A path drawn twice: a faint full trace + a bright 'comet' running along it."""
    d = "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return f"""
  <path d="{d}" fill="none" stroke="{PHOSPHOR_DIM}" stroke-width="{width}"
        opacity="{dim_op}" filter="url(#{filter_id})"/>
  <path d="{d}" fill="none" stroke="{PHOSPHOR}" stroke-width="{width}"
        stroke-linecap="round" pathLength="1"
        stroke-dasharray="{head} {1 - head}" filter="url(#{filter_id})">
    <animate attributeName="stroke-dashoffset" from="0" to="-1"
             dur="{dur}s" repeatCount="indefinite"/>
  </path>"""


def lissajous(a: int = 3, b: int = 2, delta: float = math.pi / 2,
              n: int = 600) -> list[tuple[float, float]]:
    """Sample a Lissajous figure: x=sin(a t+δ), y=sin(b t)."""
    pts = []
    for i in range(n + 1):
        t = 2 * math.pi * i / n
        x = math.sin(a * t + delta)
        y = math.sin(b * t)
        pts.append((x, y))
    return pts


def lorenz(n: int = 7000, dt: float = 0.006,
           sigma: float = 10.0, rho: float = 28.0, beta: float = 8 / 3):
    """Integrate the Lorenz system; return the (x, z) projection — the butterfly."""
    x, y, z = 0.1, 0.0, 0.0
    pts = []
    for _ in range(n):
        x += sigma * (y - x) * dt
        y += (x * (rho - z) - y) * dt
        z += (x * y - beta * z) * dt
        pts.append((x, z))
    return pts


def _fit(points, width, height, pad):
    """Scale/translate sample points into a (width × height) box with padding."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    sx = (width - 2 * pad) / (maxx - minx or 1)
    sy = (height - 2 * pad) / (maxy - miny or 1)
    s = min(sx, sy)
    ox = (width - s * (maxx - minx)) / 2
    oy = (height - s * (maxy - miny)) / 2
    # Flip Y so the math orientation reads naturally.
    return [(ox + (x - minx) * s, height - (oy + (y - miny) * s)) for x, y in points]


def write_banner() -> None:
    w, h = 1200, 340
    # An oscilloscope "signal": a sine that scrolls. Drawn 2x wide and translated
    # by exactly one screen so the loop is seamless.
    sig = []
    for i in range(0, 2 * w + 1, 6):
        t = i / w * 2 * math.pi * 3
        y = 250 + 26 * math.sin(t)
        sig.append((i, y))
    sig_d = "M " + " L ".join(f"{x},{y:.1f}" for x, y in sig)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="PyReeler">
  <defs>{_glow('glow', 4)}
    <radialGradient id="vig" cx="50%" cy="45%" r="75%">
      <stop offset="0%" stop-color="{BG}"/>
      <stop offset="100%" stop-color="#05080b"/>
    </radialGradient>
  </defs>
  <rect width="{w}" height="{h}" fill="url(#vig)"/>

  <!-- faint oscilloscope grid -->
  <g stroke="{GRID}" stroke-width="1">
    {''.join(f'<line x1="{x}" y1="0" x2="{x}" y2="{h}"/>' for x in range(0, w, 48))}
    {''.join(f'<line x1="0" y1="{y}" x2="{w}" y2="{y}"/>' for y in range(0, h, 48))}
  </g>

  <!-- scrolling signal -->
  <g clip-path="inset(0)">
    <path d="{sig_d}" fill="none" stroke="{PHOSPHOR}" stroke-width="2"
          opacity="0.5" filter="url(#glow)">
      <animateTransform attributeName="transform" type="translate"
        from="0,0" to="-{w},0" dur="7s" repeatCount="indefinite"/>
    </path>
  </g>

  <!-- HUD corner ticks -->
  <g stroke="{PHOSPHOR}" stroke-width="2" opacity="0.7" filter="url(#glow)">
    <path d="M24,24 h34 M24,24 v34" fill="none"/>
    <path d="M{w - 24},24 h-34 M{w - 24},24 v34" fill="none"/>
    <path d="M24,{h - 24} h34 M24,{h - 24} v-34" fill="none"/>
    <path d="M{w - 24},{h - 24} h-34 M{w - 24},{h - 24} v-34" fill="none"/>
  </g>

  <!-- title with phosphor flicker -->
  <g font-family="'Courier New', ui-monospace, monospace" text-anchor="middle" filter="url(#glow)">
    <text x="{w / 2}" y="158" font-size="118" font-weight="bold"
          fill="{PHOSPHOR_CORE}" letter-spacing="10">PYREELER
      <animate attributeName="opacity" values="1;0.86;1;0.93;1;0.8;1"
               dur="3.4s" repeatCount="indefinite"/>
    </text>
    <text x="{w / 2}" y="200" font-size="24" fill="{PHOSPHOR}" letter-spacing="4"
          opacity="0.92">// code-generated cinema, conjured from math</text>
    <rect x="{w / 2 + 286}" y="182" width="14" height="22" fill="{PHOSPHOR}">
      <animate attributeName="opacity" values="1;1;0;0" dur="1.1s" repeatCount="indefinite"/>
    </rect>
  </g>

  {_scanlines(w, h)}
</svg>
"""
    (OUT_DIR / "banner.svg").write_text(svg, encoding="utf-8")


def write_wave_divider() -> None:
    w, h = 1200, 56
    pts = []
    for i in range(0, 2 * w + 1, 5):
        t = i / w * 2 * math.pi * 4
        y = h / 2 + (h / 2 - 6) * math.sin(t)
        pts.append((i, y))
    d = "M " + " L ".join(f"{x},{y:.1f}" for x, y in pts)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="">
  <defs>{_glow('glow', 2.4)}</defs>
  <g clip-path="inset(0)">
    <path d="{d}" fill="none" stroke="{PHOSPHOR}" stroke-width="2"
          opacity="0.8" filter="url(#glow)">
      <animateTransform attributeName="transform" type="translate"
        from="0,0" to="-{w},0" dur="5s" repeatCount="indefinite"/>
    </path>
  </g>
</svg>
"""
    (OUT_DIR / "wave-divider.svg").write_text(svg, encoding="utf-8")


def write_lissajous() -> None:
    w, h = 420, 420
    pts = _fit(lissajous(3, 2), w, h, 56)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="Lissajous curve">
  <defs>{_glow('glow', 3)}</defs>
  <rect width="{w}" height="{h}" fill="{BG}"/>
  <g stroke="{GRID}" stroke-width="1">
    {''.join(f'<line x1="{x}" y1="0" x2="{x}" y2="{h}"/>' for x in range(0, w, 42))}
    {''.join(f'<line x1="0" y1="{y}" x2="{w}" y2="{y}"/>' for y in range(0, h, 42))}
  </g>
  {_comet_path(pts, dur=5, head=0.07, width=2.4)}
  <text x="{w / 2}" y="{h - 18}" text-anchor="middle"
        font-family="'Courier New', monospace" font-size="15" fill="{PHOSPHOR_DIM}">
    x=sin(3t+π/2)  y=sin(2t)
  </text>
  {_scanlines(w, h, 0.06)}
</svg>
"""
    (OUT_DIR / "lissajous.svg").write_text(svg, encoding="utf-8")


def write_lorenz() -> None:
    w, h = 420, 420
    pts = _fit(lorenz(), w, h, 46)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="Lorenz attractor">
  <defs>{_glow('glow', 3)}</defs>
  <rect width="{w}" height="{h}" fill="{BG}"/>
  <g stroke="{GRID}" stroke-width="1">
    {''.join(f'<line x1="{x}" y1="0" x2="{x}" y2="{h}"/>' for x in range(0, w, 42))}
    {''.join(f'<line x1="0" y1="{y}" x2="{w}" y2="{y}"/>' for y in range(0, h, 42))}
  </g>
  {_comet_path(pts, dur=9, head=0.05, width=1.8)}
  <text x="{w / 2}" y="{h - 18}" text-anchor="middle"
        font-family="'Courier New', monospace" font-size="15" fill="{PHOSPHOR_DIM}">
    Lorenz  σ=10  ρ=28  β=8/3
  </text>
  {_scanlines(w, h, 0.06)}
</svg>
"""
    (OUT_DIR / "lorenz.svg").write_text(svg, encoding="utf-8")


def main() -> None:
    write_banner()
    write_wave_divider()
    write_lissajous()
    write_lorenz()
    for name in ("banner", "wave-divider", "lissajous", "lorenz"):
        print(f"wrote {name}.svg")


if __name__ == "__main__":
    main()
