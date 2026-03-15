from __future__ import annotations

import argparse
import math
import multiprocessing as mp
import struct
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from functools import lru_cache, partial
from pathlib import Path
from time import perf_counter

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import wgpu

sys.dont_write_bytecode = True

TEMPLATES_ROOT = Path.home() / ".codex" / "skills" / "pyreeler" / "templates"
if str(TEMPLATES_ROOT) not in sys.path:
    sys.path.insert(0, str(TEMPLATES_ROOT))

LOCAL_ROOT = Path(__file__).resolve().parent
if str(LOCAL_ROOT) not in sys.path:
    sys.path.insert(0, str(LOCAL_ROOT))

from audio.audio_engine import mix_stems, write_mono_wav
from audio.sfx_gen import gen_impact, gen_shimmer, gen_wind
from video.ffmpeg_utils import resolve_local_ffmpeg_candidates
from video.parallel_render import ordered_frame_map
from video.render_runtime import detect_render_runtime
from wgpu_runtime import detect_local_shader_runtime


DURATION_SEC = 30.0
SAMPLE_RATE = 44100
DEFAULT_WIDTH = 720
DEFAULT_HEIGHT = 405
DEFAULT_FPS = 24

BACKGROUND_RGB = (3, 9, 8)
NEON_RGB = (128, 255, 212)
NEON_SOFT_RGB = (82, 225, 183)
WARNING_RGB = (255, 180, 84)
ALERT_RGB = (255, 94, 94)
GHOST_RGB = (180, 255, 230)
RAIN_GLYPHS = tuple("01$#/:?<>[]{}")


@dataclass(frozen=True)
class TextEvent:
    time_sec: float
    text: str
    style: str
    chars_per_sec: float = 28.0


@dataclass(frozen=True)
class RenderConfig:
    width: int
    height: int
    fps: int
    duration_sec: float


@dataclass(frozen=True)
class WorkerDecision:
    requested_workers: int
    active_workers: int
    fallback_happened: bool
    status: str
    detail: str


@dataclass(frozen=True)
class EncodeStats:
    total_frames: int
    frame_generation_sec: float
    ffmpeg_pipe_wait_sec: float
    ffmpeg_finalize_sec: float


EVENTS = (
    TextEvent(0.35, r"C:\> init_scan --target pyreel --mode ghost", "prompt", 31.0),
    TextEvent(1.65, "[boot] phosphor shell online", "response", 34.0),
    TextEvent(2.95, "[watchdog] hidden process attached to viewer", "warning", 32.0),
    TextEvent(4.35, r"C:\> where /r C:\ PYREEL.EXE", "prompt", 33.0),
    TextEvent(5.65, "INFO: 0 files copied", "response", 30.0),
    TextEvent(6.95, r"C:\> netstat -ano | find \"31337\"", "prompt", 34.0),
    TextEvent(8.1, "TCP 127.0.0.1:31337 LISTENING", "response", 31.0),
    TextEvent(9.35, r"C:\> tasklist | find \"PYREEL\"", "prompt", 35.0),
    TextEvent(10.55, "no image name matched the input", "response", 30.0),
    TextEvent(11.75, "[stderr] movement detected between frames", "warning", 34.0),
    TextEvent(13.0, r"C:\> type last_seen.log", "prompt", 34.0),
    TextEvent(14.1, "> always outside the raster", "response", 31.0),
    TextEvent(15.4, "[crt] signal bent around blind spot", "warning", 32.0),
    TextEvent(16.7, r"C:\> dir /s ghosts\machine", "prompt", 32.0),
    TextEvent(17.95, "Access is denied.", "alert", 36.0),
    TextEvent(19.15, "[signal] do not blink", "warning", 35.0),
    TextEvent(20.35, "PYREEL> you keep checking the wrong window", "pyreel", 31.0),
    TextEvent(21.65, "PYREEL> warmer", "pyreel", 36.0),
    TextEvent(22.75, "PYREEL> almost", "pyreel", 38.0),
    TextEvent(24.7, "PYREEL> stop looking at the text", "pyreel", 31.0),
    TextEvent(26.15, "PYREEL> look at the screen", "pyreel", 32.0),
    TextEvent(27.8, "PYREEL> ready or not", "pyreel", 33.0),
    TextEvent(29.0, "PYREEL> found you", "pyreel", 40.0),
)

GLITCH_MARKERS = (
    (2.95, 0.75),
    (6.95, 0.9),
    (11.75, 0.75),
    (15.4, 0.8),
    (19.15, 0.85),
    (24.7, 0.9),
    (26.15, 1.0),
    (27.8, 1.0),
    (29.0, 1.25),
)

IMPACT_TIMES = (2.95, 6.95, 11.75, 15.4, 19.15, 24.7, 26.15, 27.8, 29.0)

RAIN_STREAMS = tuple(
    (
        float(x_pos),
        10.0 + 9.0 * math.sin(index * 0.77 + 0.2),
        0.9 + (index % 4) * 0.35,
        index % len(RAIN_GLYPHS),
    )
    for index, x_pos in enumerate(
        (26, 48, 74, 106, 132, 568, 594, 622, 650, 684)
    )
)

WGSL_SHADER = """
struct Uniforms {
    resolution: vec2<f32>,
    time_sec: f32,
    glitch: f32,
};

struct VSOut {
    @builtin(position) pos: vec4<f32>,
    @location(0) uv: vec2<f32>,
};

@group(0) @binding(0)
var<uniform> uniforms: Uniforms;

fn hash21(p: vec2<f32>) -> f32 {
    let n = sin(dot(p, vec2<f32>(127.1, 311.7))) * 43758.5453;
    return fract(n);
}

fn noise(p: vec2<f32>) -> f32 {
    let i = floor(p);
    let f = fract(p);
    let a = hash21(i);
    let b = hash21(i + vec2<f32>(1.0, 0.0));
    let c = hash21(i + vec2<f32>(0.0, 1.0));
    let d = hash21(i + vec2<f32>(1.0, 1.0));
    let u = f * f * (3.0 - 2.0 * f);
    return mix(a, b, u.x) + (c - a) * u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
}

fn fbm(p: vec2<f32>) -> f32 {
    var value = 0.0;
    var amp = 0.5;
    var q = p;
    for (var i = 0; i < 4; i = i + 1) {
        value = value + noise(q) * amp;
        q = q * 2.02 + vec2<f32>(11.7, 5.3);
        amp = amp * 0.5;
    }
    return value;
}

@vertex
fn vs_main(@builtin(vertex_index) vid: u32) -> VSOut {
    var pos = array<vec2<f32>, 3>(
        vec2<f32>(-1.0, -3.0),
        vec2<f32>(-1.0,  1.0),
        vec2<f32>( 3.0,  1.0)
    );
    let p = pos[vid];
    var out: VSOut;
    out.pos = vec4<f32>(p, 0.0, 1.0);
    out.uv = 0.5 * (p + vec2<f32>(1.0, 1.0));
    return out;
}

@fragment
fn fs_main(in: VSOut) -> @location(0) vec4<f32> {
    let uv = in.uv;
    let t = uniforms.time_sec;
    let glitch = uniforms.glitch;
    let center = uv * 2.0 - vec2<f32>(1.0, 1.0);
    let grid = abs(fract(uv * vec2<f32>(18.0, 12.0)) - 0.5);
    let grid_line = smoothstep(0.48, 0.50, max(grid.x, grid.y));
    let drift = sin((uv.y + t * 0.12) * 38.0 + fbm(uv * 3.8 + vec2<f32>(t * 0.13, -t * 0.06)) * 7.0);
    let haze = fbm(uv * 5.5 + vec2<f32>(t * 0.08, -t * 0.03));
    let pulse = fbm(uv * 10.5 - vec2<f32>(t * 0.24, 0.0));
    let scan = 0.88 + 0.12 * sin(uv.y * uniforms.resolution.y * 1.2);
    let band = smoothstep(0.76, 0.98, sin((uv.y * 8.0 - t * 2.4) * 8.5) * 0.5 + 0.5);
    let split = glitch * (0.015 + 0.015 * sin(t * 11.0));
    let chroma = fbm((uv + vec2<f32>(split, 0.0)) * 9.0 + t * 0.4);
    let vignette = clamp(1.0 - dot(center * vec2<f32>(0.92, 0.74), center * vec2<f32>(0.92, 0.74)) * 0.42, 0.18, 1.0);

    var color = vec3<f32>(0.01, 0.05, 0.02);
    color = color + vec3<f32>(0.01, 0.18, 0.06) * haze;
    color = color + vec3<f32>(0.03, 0.42, 0.12) * pulse * 0.82;
    color = color + vec3<f32>(0.08, 0.92, 0.28) * pow(max(drift, 0.0), 4.0) * (0.46 + glitch * 0.32);
    color = color + vec3<f32>(0.08, 0.95, 0.32) * grid_line * 0.16;
    color = color + vec3<f32>(0.14, 1.0, 0.40) * band * glitch * 0.08;
    color.r = color.r + chroma * glitch * 0.04;
    color.b = color.b + (1.0 - chroma) * glitch * 0.03;
    color = color * scan * vignette;
    return vec4<f32>(color, 1.0);
}
"""

_SHADER_CACHE: dict[tuple[int, int], "ShaderBackgroundRenderer"] = {}


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    if edge0 == edge1:
        return 1.0 if value >= edge1 else 0.0
    amount = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return amount * amount * (3.0 - 2.0 * amount)


def triangle_pulse(value: float, center: float, half_width: float) -> float:
    if half_width <= 0.0:
        return 0.0
    return max(0.0, 1.0 - abs(value - center) / half_width)


def mix_values(low: float, high: float, amount: float) -> float:
    return low + (high - low) * amount


def resolve_ffmpeg_path() -> str:
    candidates = resolve_local_ffmpeg_candidates()
    if candidates:
        return candidates[0]
    raise FileNotFoundError("No ffmpeg binary found in PATH or pyreeler local candidates.")


@lru_cache(maxsize=None)
def get_font(size: int, role: str = "regular") -> ImageFont.FreeTypeFont:
    candidates = []
    if role == "large":
        candidates.extend(
            [
                Path("C:/Windows/Fonts/lucon.ttf"),
                Path("C:/Windows/Fonts/consolab.ttf"),
            ]
        )
    candidates.extend(
        [
            Path("C:/Windows/Fonts/consola.ttf"),
            Path("C:/Windows/Fonts/lucon.ttf"),
            Path("C:/Windows/Fonts/cour.ttf"),
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


@lru_cache(maxsize=None)
def scanline_mask(width: int, height: int) -> np.ndarray:
    rows = np.arange(height, dtype=np.float32)[:, None]
    return (0.9 - 0.13 * ((rows // 2) % 2)).astype(np.float32)


@lru_cache(maxsize=None)
def vignette_mask(width: int, height: int) -> np.ndarray:
    x_coords = np.linspace(-1.0, 1.0, width, dtype=np.float32)[None, :]
    y_coords = np.linspace(-1.0, 1.0, height, dtype=np.float32)[:, None]
    radius = np.sqrt(x_coords * x_coords + y_coords * y_coords)
    return np.clip(1.12 - radius * 0.52, 0.45, 1.0).astype(np.float32)


class ShaderBackgroundRenderer:
    def __init__(self, width: int, height: int):
        _, adapter = detect_local_shader_runtime()
        self.width = width
        self.height = height
        self.device = adapter.request_device_sync()
        self.texture = self.device.create_texture(
            size=(width, height, 1),
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.COPY_SRC,
            dimension=wgpu.TextureDimension.d2,
            format=wgpu.TextureFormat.rgba8unorm,
            mip_level_count=1,
            sample_count=1,
        )
        self.uniform_buffer = self.device.create_buffer(
            size=16,
            usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST,
        )
        bind_group_layout = self.device.create_bind_group_layout(
            entries=[
                {
                    "binding": 0,
                    "visibility": wgpu.ShaderStage.FRAGMENT,
                    "buffer": {"type": wgpu.BufferBindingType.uniform},
                }
            ]
        )
        pipeline_layout = self.device.create_pipeline_layout(bind_group_layouts=[bind_group_layout])
        self.bind_group = self.device.create_bind_group(
            layout=bind_group_layout,
            entries=[{"binding": 0, "resource": {"buffer": self.uniform_buffer, "offset": 0, "size": 16}}],
        )
        shader = self.device.create_shader_module(code=WGSL_SHADER)
        self.pipeline = self.device.create_render_pipeline(
            layout=pipeline_layout,
            vertex={"module": shader, "entry_point": "vs_main", "buffers": []},
            fragment={
                "module": shader,
                "entry_point": "fs_main",
                "targets": [{"format": wgpu.TextureFormat.rgba8unorm}],
            },
            primitive={"topology": wgpu.PrimitiveTopology.triangle_list},
        )
        self.bytes_per_pixel = 4
        self.unpadded_bytes_per_row = width * self.bytes_per_pixel
        self.aligned_bytes_per_row = ((self.unpadded_bytes_per_row + 255) // 256) * 256
        self.readback = self.device.create_buffer(
            size=self.aligned_bytes_per_row * height,
            usage=wgpu.BufferUsage.COPY_DST | wgpu.BufferUsage.MAP_READ,
        )

    def render_rgba(self, time_sec: float, glitch: float) -> np.ndarray:
        payload = struct.pack("4f", float(self.width), float(self.height), float(time_sec), float(glitch))
        self.device.queue.write_buffer(self.uniform_buffer, 0, payload)
        encoder = self.device.create_command_encoder()
        render_pass = encoder.begin_render_pass(
            color_attachments=[
                {
                    "view": self.texture.create_view(),
                    "resolve_target": None,
                    "load_op": wgpu.LoadOp.clear,
                    "store_op": wgpu.StoreOp.store,
                    "clear_value": (0.0, 0.0, 0.0, 1.0),
                }
            ]
        )
        render_pass.set_pipeline(self.pipeline)
        render_pass.set_bind_group(0, self.bind_group, [], 0, 999999)
        render_pass.draw(3, 1, 0, 0)
        render_pass.end()
        encoder.copy_texture_to_buffer(
            {"texture": self.texture, "mip_level": 0, "origin": (0, 0, 0)},
            {
                "buffer": self.readback,
                "offset": 0,
                "bytes_per_row": self.aligned_bytes_per_row,
                "rows_per_image": self.height,
            },
            (self.width, self.height, 1),
        )
        self.device.queue.submit([encoder.finish()])
        self.readback.map_sync(mode=wgpu.MapMode.READ)
        raw = self.readback.read_mapped()
        frame = np.frombuffer(raw, dtype=np.uint8).reshape(self.height, self.aligned_bytes_per_row)
        rgba = frame[:, : self.unpadded_bytes_per_row].reshape(self.height, self.width, 4).copy()
        self.readback.unmap()
        return rgba


def get_shader_renderer(width: int, height: int) -> ShaderBackgroundRenderer:
    key = (width, height)
    renderer = _SHADER_CACHE.get(key)
    if renderer is None:
        renderer = ShaderBackgroundRenderer(width, height)
        _SHADER_CACHE[key] = renderer
    return renderer


def color_for_style(style: str) -> tuple[int, int, int]:
    if style == "prompt":
        return NEON_RGB
    if style == "response":
        return NEON_SOFT_RGB
    if style == "warning":
        return WARNING_RGB
    if style == "alert":
        return ALERT_RGB
    return GHOST_RGB


def glow_for_style(style: str) -> tuple[int, int, int, int]:
    red, green, blue = color_for_style(style)
    alpha = 90 if style in {"prompt", "response"} else 120
    if style == "pyreel":
        alpha = 170
    return (red, green, blue, alpha)


def terminal_events_at(time_sec: float) -> list[tuple[TextEvent, str, bool, float]]:
    visible: list[tuple[TextEvent, str, bool, float]] = []
    for event in EVENTS:
        elapsed = time_sec - event.time_sec
        if elapsed < -0.05:
            break
        if elapsed < 0.0:
            continue
        shown_chars = min(len(event.text), max(0, int(elapsed * event.chars_per_sec)))
        if shown_chars <= 0:
            continue
        is_complete = shown_chars >= len(event.text)
        age = max(0.0, elapsed)
        visible.append((event, event.text[:shown_chars], is_complete, age))
    return visible[-10:]


def draw_text_with_glow(
    text_draw: ImageDraw.ImageDraw,
    glow_draw: ImageDraw.ImageDraw,
    position: tuple[float, float],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    glow_fill: tuple[int, int, int, int],
) -> None:
    glow_draw.text(position, text, font=font, fill=glow_fill)
    text_draw.text(position, text, font=font, fill=fill)


def draw_rain(
    text_draw: ImageDraw.ImageDraw,
    glow_draw: ImageDraw.ImageDraw,
    time_sec: float,
    width: int,
    height: int,
) -> None:
    font = get_font(16)
    drift = 0.15 * math.sin(time_sec * 0.61)
    for index, (x_pos, speed, offset, glyph_offset) in enumerate(RAIN_STREAMS):
        x_scale = width / DEFAULT_WIDTH
        x = x_pos * x_scale
        y_head = ((time_sec * speed * 32.0) + offset * 92.0) % (height + 180.0) - 140.0
        for slot in range(11):
            y = y_head - slot * 17.0
            if y < -22.0 or y > height + 16.0:
                continue
            intensity = 1.0 - slot / 13.0
            glyph = RAIN_GLYPHS[(glyph_offset + slot + int(time_sec * 12.0) + index) % len(RAIN_GLYPHS)]
            if 180.0 < x < width - 180.0:
                continue
            fill = (40, int(160 + intensity * 80), int(120 + intensity * 60))
            glow = (50, 180, 150, int(24 + intensity * 42))
            draw_text_with_glow(
                text_draw,
                glow_draw,
                (x + drift * slot, y),
                glyph,
                font,
                fill,
                glow,
            )


def draw_ghost(width: int, height: int, time_sec: float) -> Image.Image:
    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")

    pre_reveal = smoothstep(13.0, 24.5, time_sec)
    reveal = smoothstep(25.2, 29.0, time_sec)
    hold = triangle_pulse(time_sec, 25.1, 0.85)
    alpha = 8 + int(80 * pre_reveal + 170 * reveal)
    x_pos = width * mix_values(0.84, 0.53, reveal) + math.sin(time_sec * 0.85) * width * 0.014
    x_pos += math.sin(time_sec * 2.4) * width * 0.01 * (1.0 - reveal)
    y_pos = height * mix_values(0.58, 0.52, reveal) + math.sin(time_sec * 0.65 + 0.9) * height * 0.018

    head_w = width * mix_values(0.06, 0.082, reveal)
    head_h = height * mix_values(0.12, 0.15, reveal)
    body_w = width * mix_values(0.16, 0.23, reveal)
    body_h = height * mix_values(0.19, 0.28, reveal)

    outer_alpha = max(0, alpha - 48)
    body_alpha = int(alpha * (0.48 + reveal * 0.22))
    eye_alpha = int(70 + 150 * reveal + 40 * hold)
    mouth_alpha = int(22 + 70 * reveal)

    draw.ellipse(
        (x_pos - head_w * 1.2, y_pos - head_h * 1.1, x_pos + head_w * 1.2, y_pos + head_h * 1.1),
        fill=(70, 245, 200, outer_alpha),
    )
    draw.polygon(
        (
            (x_pos, y_pos - head_h * 1.25),
            (x_pos - body_w * 0.92, y_pos + body_h * 0.14),
            (x_pos - body_w * 0.62, y_pos + body_h),
            (x_pos + body_w * 0.62, y_pos + body_h),
            (x_pos + body_w * 0.92, y_pos + body_h * 0.14),
        ),
        fill=(64, 220, 186, body_alpha),
    )
    draw.ellipse(
        (x_pos - head_w, y_pos - head_h, x_pos + head_w, y_pos + head_h),
        fill=(110, 255, 220, alpha),
    )

    eye_y = y_pos - head_h * 0.12
    eye_w = head_w * mix_values(0.28, 0.34, reveal)
    eye_h = head_h * 0.12
    eye_shift = head_w * 0.36
    draw.rounded_rectangle(
        (x_pos - eye_shift - eye_w, eye_y - eye_h, x_pos - eye_shift + eye_w, eye_y + eye_h),
        radius=4,
        fill=(255, 255, 255, eye_alpha),
    )
    draw.rounded_rectangle(
        (x_pos + eye_shift - eye_w, eye_y - eye_h, x_pos + eye_shift + eye_w, eye_y + eye_h),
        radius=4,
        fill=(255, 255, 255, eye_alpha),
    )
    draw.arc(
        (x_pos - head_w * 0.24, y_pos + head_h * 0.05, x_pos + head_w * 0.24, y_pos + head_h * 0.38),
        start=10,
        end=170,
        fill=(220, 255, 240, mouth_alpha),
        width=2,
    )

    duplicate_offset = int((1.0 - reveal) * 18.0 * math.sin(time_sec * 21.0))
    if duplicate_offset:
        shifted = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        shifted.alpha_composite(layer, (duplicate_offset, 0))
        layer = Image.blend(layer, shifted, 0.24)

    return layer.filter(ImageFilter.GaussianBlur(radius=9))


def draw_terminal_panel(width: int, height: int, time_sec: float) -> Image.Image:
    panel = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    panel_draw = ImageDraw.Draw(panel, "RGBA")

    margin_x = int(width * 0.065)
    margin_y = int(height * 0.085)
    rect = (margin_x, margin_y, width - margin_x, height - margin_y)
    header_h = int(height * 0.082)
    panel_draw.rectangle(rect, fill=(2, 10, 8, 192), outline=(68, 180, 146, 120), width=1)
    panel_draw.rectangle(
        (rect[0], rect[1], rect[2], rect[1] + header_h),
        fill=(9, 26, 24, 220),
        outline=(94, 224, 186, 90),
        width=1,
    )
    panel_draw.rectangle(
        (rect[0] + 1, rect[3] - 22, rect[2] - 1, rect[3] - 1),
        fill=(2, 18, 16, 180),
    )
    panel_draw.line((rect[0], rect[1] + header_h, rect[2], rect[1] + header_h), fill=(84, 206, 166, 100), width=1)

    text_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer, "RGBA")
    glow_draw = ImageDraw.Draw(glow_layer, "RGBA")

    header_font = get_font(18)
    body_font = get_font(24)
    large_font = get_font(56, "large")
    small_font = get_font(16)

    draw_text_with_glow(
        text_draw,
        glow_draw,
        (rect[0] + 14, rect[1] + 10),
        "PYREEL TRACE // VIEWER SESSION",
        header_font,
        NEON_RGB,
        (94, 224, 186, 120),
    )
    header_right = f"blindspot {int(mix_values(88, 6, smoothstep(19.0, 29.0, time_sec))):02d}%"
    draw_text_with_glow(
        text_draw,
        glow_draw,
        (rect[2] - 176, rect[1] + 10),
        header_right,
        header_font,
        WARNING_RGB,
        (255, 182, 84, 96),
    )

    draw_rain(text_draw, glow_draw, time_sec, width, height)

    line_y = rect[1] + header_h + 18
    line_step = 30
    for event, line, is_complete, age in terminal_events_at(time_sec):
        fill = color_for_style(event.style)
        glow = glow_for_style(event.style)
        fade = max(0.25, 1.0 - age / 17.0)
        fill_faded = tuple(int(channel * fade) for channel in fill)
        glow_faded = (*glow[:3], int(glow[3] * fade))
        text = line
        if not is_complete and int(time_sec * 5.0) % 2 == 0:
            text += "_"
        draw_text_with_glow(
            text_draw,
            glow_draw,
            (rect[0] + 18, line_y),
            text,
            body_font,
            fill_faded,
            glow_faded,
        )
        line_y += line_step

    if time_sec > 25.4:
        big_alpha = int(26 + 110 * smoothstep(26.2, 29.1, time_sec))
        big_text = "PYREEL"
        big_size = text_draw.textbbox((0, 0), big_text, font=large_font)
        big_x = width * 0.5 - (big_size[2] - big_size[0]) / 2
        big_y = height * mix_values(0.18, 0.12, smoothstep(26.2, 29.1, time_sec))
        glow_draw.text((big_x, big_y), big_text, font=large_font, fill=(140, 255, 220, big_alpha))

    latency = 22 + int(26.0 * smoothstep(8.0, 29.0, time_sec) + 7.0 * math.sin(time_sec * 2.1))
    focus = int(mix_values(100.0, 6.0, smoothstep(22.0, 29.0, time_sec)))
    footer_lines = (
        f"signal: {'unstable' if time_sec < 20.0 else 'watching'}",
        f"latency: {latency}ms",
        f"focus: {focus:02d}%",
    )
    for index, footer in enumerate(footer_lines):
        draw_text_with_glow(
            text_draw,
            glow_draw,
            (rect[2] - 164, rect[3] - 62 + index * 16),
            footer,
            small_font,
            NEON_SOFT_RGB,
            (84, 214, 178, 62),
        )

    if 24.8 <= time_sec <= 26.0:
        line_x = rect[0] + 18
        line_y = rect[3] - 52
        if int(time_sec * 2.0) % 2 == 0:
            draw_text_with_glow(
                text_draw,
                glow_draw,
                (line_x, line_y),
                "C:\\>",
                body_font,
                GHOST_RGB,
                (180, 255, 230, 98),
            )

    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=5))
    panel = Image.alpha_composite(panel, glow_layer)
    panel = Image.alpha_composite(panel, text_layer)
    return panel


def glitch_strength(time_sec: float) -> float:
    glitch = 0.05 + 0.08 * smoothstep(10.0, 23.0, time_sec)
    for marker_time, amplitude in GLITCH_MARKERS:
        glitch += amplitude * triangle_pulse(time_sec, marker_time, 0.22)
    return min(1.0, glitch)


def base_frame(width: int, height: int, time_sec: float) -> Image.Image:
    renderer = get_shader_renderer(width, height)
    rgba = renderer.render_rgba(time_sec, glitch_strength(time_sec))
    return Image.fromarray(rgba, mode="RGBA")


def apply_postprocess(frame: Image.Image, frame_index: int, time_sec: float) -> bytes:
    rgb = np.asarray(frame.convert("RGB"), dtype=np.uint8).astype(np.int16)
    height, width = rgb.shape[:2]

    glitch = glitch_strength(time_sec)
    rng = np.random.default_rng(frame_index * 977 + 17)
    noise_amount = int(2 + 10 * glitch)
    noise = rng.integers(-noise_amount, noise_amount + 1, size=(height, width, 1), dtype=np.int16)
    rgb += noise

    if glitch > 0.08:
        stripe_count = max(1, int(2 + glitch * 6))
        for _ in range(stripe_count):
            stripe_height = int(rng.integers(4, max(6, height // 14)))
            start = int(rng.integers(0, max(1, height - stripe_height)))
            shift = int(rng.integers(-1 - int(10 * glitch), 2 + int(10 * glitch)))
            rgb[start : start + stripe_height] = np.roll(rgb[start : start + stripe_height], shift, axis=1)

        split = max(1, int(1 + glitch * 4))
        red = np.roll(rgb[:, :, 0], split, axis=1)
        blue = np.roll(rgb[:, :, 2], -split, axis=1)
        rgb[:, :, 0] = ((rgb[:, :, 0] * 3 + red) // 4).astype(np.int16)
        rgb[:, :, 2] = ((rgb[:, :, 2] * 3 + blue) // 4).astype(np.int16)

    flicker = 0.92 + 0.05 * math.sin(time_sec * 17.0 + 0.7) + 0.03 * math.sin(time_sec * 41.0)
    flicker += 0.06 * glitch

    mask = scanline_mask(width, height) * vignette_mask(width, height) * flicker
    rgb = np.clip(rgb.astype(np.float32) * mask[:, :, None], 0.0, 255.0).astype(np.uint8)
    return rgb.tobytes()


def render_frame(frame_index: int, config: RenderConfig) -> bytes:
    time_sec = min(config.duration_sec, frame_index / config.fps)
    width = config.width
    height = config.height

    frame = base_frame(width, height, time_sec)
    ghost = draw_ghost(width, height, time_sec)
    frame = Image.alpha_composite(frame, ghost)
    panel = draw_terminal_panel(width, height, time_sec)
    frame = Image.alpha_composite(frame, panel)

    if time_sec > 27.8:
        flash = triangle_pulse(time_sec, 29.0, 0.35)
        if flash > 0.0:
            flash_layer = Image.new(
                "RGBA",
                (width, height),
                (int(20 + flash * 60), int(255 * flash * 0.18), int(180 * flash * 0.16), int(32 + flash * 42)),
            )
            frame = Image.alpha_composite(frame, flash_layer)

    return apply_postprocess(frame, frame_index, time_sec)


def place_clip(target: np.ndarray, clip: np.ndarray, start_sec: float, sample_rate: int) -> None:
    start = int(start_sec * sample_rate)
    if start >= len(target):
        return
    end = min(len(target), start + len(clip))
    if end > start:
        target[start:end] += clip[: end - start]


def synth_pad(
    total_samples: int,
    sample_rate: int,
    start_sec: float,
    duration_sec: float,
    frequency_hz: float,
    gain: float,
    detune_ratio: float = 1.004,
) -> np.ndarray:
    start = int(start_sec * sample_rate)
    length = max(1, int(duration_sec * sample_rate))
    signal = np.zeros(total_samples, dtype=np.float32)
    end = min(total_samples, start + length)
    if end <= start:
        return signal

    local_t = np.arange(end - start, dtype=np.float32) / sample_rate
    attack = min(0.45, duration_sec * 0.18)
    release = min(0.75, duration_sec * 0.24)
    envelope = np.ones_like(local_t, dtype=np.float32)
    if attack > 0.0:
        attack_samples = max(1, int(attack * sample_rate))
        attack_samples = min(attack_samples, len(envelope))
        envelope[:attack_samples] = np.linspace(0.0, 1.0, attack_samples, dtype=np.float32)
    if release > 0.0:
        release_samples = max(1, int(release * sample_rate))
        release_samples = min(release_samples, len(envelope))
        envelope[-release_samples:] *= np.linspace(1.0, 0.0, release_samples, dtype=np.float32)
    sustain_curve = 0.8 + 0.2 * np.sin(local_t * 2.0 * math.pi * 0.31 + frequency_hz * 0.01)
    carrier = (
        0.62 * np.sin(2.0 * math.pi * frequency_hz * local_t)
        + 0.28 * np.sin(2.0 * math.pi * frequency_hz * detune_ratio * local_t + 0.2)
        + 0.16 * np.sin(2.0 * math.pi * frequency_hz * 2.01 * local_t + 1.3)
    )
    signal[start:end] = (carrier * envelope * sustain_curve * gain).astype(np.float32)
    return signal


def build_audio_mix(duration_sec: float = DURATION_SEC, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    total_samples = int(duration_sec * sample_rate)
    timeline = np.arange(total_samples, dtype=np.float32) / sample_rate

    ambience = 0.42 * gen_wind(duration_sec, sample_rate=sample_rate, intensity=0.42, seed=7)
    ambience += (
        0.12 * np.sin(2.0 * math.pi * 42.0 * timeline + 0.7 * np.sin(2.0 * math.pi * 0.08 * timeline))
        + 0.08 * np.sin(2.0 * math.pi * 84.0 * timeline + 0.13)
        + 0.04 * np.sin(2.0 * math.pi * 126.0 * timeline + 1.1)
    ).astype(np.float32)
    ambience_envelope = 0.84 + 0.16 * np.clip(timeline / max(duration_sec, 0.001), 0.0, 1.0)
    ambience *= (ambience_envelope + 0.08 * np.sin(2.0 * math.pi * 0.11 * timeline)).astype(np.float32)

    pulse = np.zeros(total_samples, dtype=np.float32)
    beat_time = 1.5
    beat_index = 0
    while beat_time < duration_sec - 0.5:
        ramp = smoothstep(3.0, 24.0, beat_time)
        bpm = mix_values(68.0, 112.0, ramp)
        interval = 60.0 / bpm
        beat_len = min(0.2, interval * 0.4)
        body_t = np.arange(int(beat_len * sample_rate), dtype=np.float32) / sample_rate
        envelope = np.exp(-body_t * mix_values(7.0, 11.0, ramp)).astype(np.float32)
        body = (
            np.sin(2.0 * math.pi * mix_values(48.0, 58.0, ramp) * body_t)
            + 0.18 * np.sin(2.0 * math.pi * 112.0 * body_t + 0.2)
        ).astype(np.float32)
        click = 0.05 * np.sign(np.sin(2.0 * math.pi * 1300.0 * body_t)).astype(np.float32) * np.exp(-body_t * 60.0)
        beat_clip = (body * envelope * 0.16 + click).astype(np.float32)
        place_clip(pulse, beat_clip, beat_time, sample_rate)
        if beat_index % 4 == 3 and beat_time > 18.0:
            offbeat = beat_time + interval * 0.5
            place_clip(pulse, beat_clip * 0.7, offbeat, sample_rate)
        beat_time += interval
        beat_index += 1

    impacts = np.zeros(total_samples, dtype=np.float32)
    for index, impact_time in enumerate(IMPACT_TIMES):
        impact = gen_impact(
            duration_sec=0.42 if impact_time < 24.0 else 0.55,
            fundamental_hz=58.0 + index * 2.3,
            sample_rate=sample_rate,
            noise_amount=0.12,
            seed=100 + index,
        )
        shimmer = gen_shimmer(0.8 if impact_time < 24.0 else 1.2, sample_rate=sample_rate, seed=200 + index)
        place_clip(impacts, impact * 0.28, impact_time, sample_rate)
        place_clip(impacts, shimmer * 0.22, impact_time + 0.03, sample_rate)

    score = np.zeros(total_samples, dtype=np.float32)
    score_layers = (
        (4.3, 3.0, 110.0, 0.16),
        (7.1, 2.7, 116.5, 0.17),
        (9.8, 3.0, 98.0, 0.18),
        (12.8, 2.8, 130.8, 0.17),
        (15.6, 3.1, 110.0, 0.17),
        (18.8, 2.8, 146.8, 0.18),
        (21.4, 2.5, 156.0, 0.18),
        (24.4, 2.8, 98.0, 0.19),
        (26.8, 3.4, 110.0, 0.22),
    )
    for start_sec, note_dur, frequency_hz, gain in score_layers:
        score += synth_pad(total_samples, sample_rate, start_sec, note_dur, frequency_hz, gain)
        score += synth_pad(total_samples, sample_rate, start_sec + 0.16, note_dur * 0.94, frequency_hz * 1.063, gain * 0.52)

    high_tension = np.zeros(total_samples, dtype=np.float32)
    for index, start_sec in enumerate((18.9, 21.6, 24.7, 27.6)):
        dur = 2.1 if index < 3 else 2.6
        frequency = 740.0 + index * 58.0
        local = synth_pad(total_samples, sample_rate, start_sec, dur, frequency, 0.055, 1.012)
        high_tension += local

    dip_center = 25.2
    dip_width = 1.05
    dip = np.clip(1.0 - 0.68 * np.maximum(0.0, 1.0 - np.abs((timeline - dip_center) / dip_width)), 0.22, 1.0).astype(
        np.float32
    )
    ambience *= dip
    pulse *= dip
    score *= dip

    reveal_gain = np.ones(total_samples, dtype=np.float32)
    reveal_start = int(26.0 * sample_rate)
    if reveal_start < total_samples:
        reveal_gain[reveal_start:] = np.linspace(1.0, 1.18, total_samples - reveal_start, dtype=np.float32)
    stems = {
        "ambience": ambience.astype(np.float32),
        "pulse": pulse.astype(np.float32),
        "impacts": impacts.astype(np.float32),
        "score": (score + high_tension).astype(np.float32),
    }
    mix = mix_stems(stems, gains={"ambience": 0.86, "pulse": 1.0, "impacts": 1.12, "score": 0.82}, duck_voice=False)
    return (mix * reveal_gain).astype(np.float32)


def run_worker_smoke_test(config: RenderConfig, workers: int) -> WorkerDecision:
    if workers <= 1:
        return WorkerDecision(
            requested_workers=workers,
            active_workers=1,
            fallback_happened=False,
            status="skipped",
            detail="requested worker count is 1; parallel smoke test not needed",
        )
    smoke_func = partial(render_frame, config=config)
    try:
        frames = list(ordered_frame_map(range(3), smoke_func, workers=workers))
    except (PermissionError, OSError) as exc:
        return WorkerDecision(
            requested_workers=workers,
            active_workers=1,
            fallback_happened=True,
            status="fallback",
            detail=f"{type(exc).__name__}: {exc}",
        )
    if len(frames) != 3:
        raise RuntimeError("Worker smoke test did not return the expected frame count.")
    return WorkerDecision(
        requested_workers=workers,
        active_workers=workers,
        fallback_happened=False,
        status="passed",
        detail="parallel worker path started cleanly",
    )


def ffprobe_path_for(ffmpeg_path: str) -> str | None:
    candidate = Path(ffmpeg_path).with_name("ffprobe.exe")
    if candidate.exists():
        return str(candidate)
    sibling = Path(ffmpeg_path).with_name("ffprobe")
    if sibling.exists():
        return str(sibling)
    return None


def encode_video(
    output_path: Path,
    audio_path: Path,
    config: RenderConfig,
    workers: int,
    ffmpeg_path: str,
    video_args: tuple[str, ...],
) -> EncodeStats:
    frame_func = partial(render_frame, config=config)
    total_frames = int(round(config.duration_sec * config.fps))
    frame_generation_sec = 0.0
    ffmpeg_pipe_wait_sec = 0.0

    cmd = [
        ffmpeg_path,
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{config.width}x{config.height}",
        "-r",
        str(config.fps),
        "-i",
        "-",
        "-i",
        str(audio_path),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-shortest",
        *video_args,
        "-vf",
        "pad=width=ceil(iw/2)*2:height=ceil(ih/2)*2",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    assert process.stdin is not None
    frame_iter = iter(ordered_frame_map(range(total_frames), frame_func, workers=workers))
    try:
        for frame_count in range(1, total_frames + 1):
            frame_start = perf_counter()
            frame_bytes = next(frame_iter)
            frame_generation_sec += perf_counter() - frame_start
            try:
                write_start = perf_counter()
                process.stdin.write(frame_bytes)
                ffmpeg_pipe_wait_sec += perf_counter() - write_start
            except OSError as exc:
                stderr_text = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
                process.wait()
                raise RuntimeError(f"ffmpeg closed the frame pipe early\n{stderr_text}") from exc
            if frame_count % config.fps == 0 or frame_count == total_frames:
                percent = (frame_count / total_frames) * 100.0
                print(f"[render] frames={frame_count}/{total_frames} ({percent:.1f}%)", flush=True)
    finally:
        process.stdin.close()

    finalize_start = perf_counter()
    stderr_text = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
    return_code = process.wait()
    ffmpeg_finalize_sec = perf_counter() - finalize_start
    if return_code != 0:
        raise RuntimeError(f"ffmpeg encode failed with exit code {return_code}\n{stderr_text}")
    return EncodeStats(
        total_frames=total_frames,
        frame_generation_sec=frame_generation_sec,
        ffmpeg_pipe_wait_sec=ffmpeg_pipe_wait_sec,
        ffmpeg_finalize_sec=ffmpeg_finalize_sec,
    )


def verify_output(output_path: Path, ffmpeg_path: str, duration_target: float) -> float | None:
    if not output_path.exists():
        raise FileNotFoundError(f"Expected output missing: {output_path}")
    if output_path.stat().st_size <= 0:
        raise RuntimeError(f"Output file is empty: {output_path}")

    ffprobe_path = ffprobe_path_for(ffmpeg_path)
    if ffprobe_path:
        duration_cmd = [
            ffprobe_path,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(output_path),
        ]
        result = subprocess.run(duration_cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            actual = float(result.stdout.strip())
            if abs(actual - duration_target) > 0.15:
                raise RuntimeError(f"Output duration {actual:.3f}s does not match target {duration_target:.3f}s")
            return actual
    return None

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a cyberpunk PyReel preview film.")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--fps", type=int, default=DEFAULT_FPS)
    parser.add_argument("--duration", type=float, default=DURATION_SEC)
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--smoke-test", action="store_true", help="Run the worker smoke test only.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path.home() / "Videos" / "pyreel_ghost_in_the_machine_preview.mp4",
    )
    parser.add_argument("--keep-audio-temp", action="store_true")
    return parser.parse_args()


def main() -> None:
    total_start = perf_counter()
    args = parse_args()

    shader_runtime, _adapter = detect_local_shader_runtime()
    runtime = detect_render_runtime(ffmpeg_path=shader_runtime.ffmpeg_path, workers=args.workers)
    config = RenderConfig(width=args.width, height=args.height, fps=args.fps, duration_sec=args.duration)

    requested_worker_label = str(args.workers) if args.workers is not None else "auto"
    print(f"[gpu] adapter={shader_runtime.adapter_name}", flush=True)
    print(f"[gpu] backend={shader_runtime.backend}", flush=True)
    print(f"[runtime] detected_runtime_profile={runtime.profile}", flush=True)
    print(f"[runtime] selected_ffmpeg_path={runtime.ffmpeg_path}", flush=True)
    print(f"[runtime] selected_encoder={runtime.encoder}", flush=True)
    print(f"[runtime] requested_worker_count={requested_worker_label}", flush=True)
    print(f"[runtime] runtime_helper_worker_count={runtime.workers}", flush=True)

    smoke_start = perf_counter()
    worker_decision = run_worker_smoke_test(config, runtime.workers)
    smoke_elapsed = perf_counter() - smoke_start
    print(f"[runtime] worker_smoke_test_result={worker_decision.status}", flush=True)
    print(f"[runtime] worker_smoke_test_detail={worker_decision.detail}", flush=True)
    print(f"[runtime] fallback_happened={'yes' if worker_decision.fallback_happened else 'no'}", flush=True)
    print(f"[runtime] active_worker_count={worker_decision.active_workers}", flush=True)
    if args.smoke_test:
        total_elapsed = perf_counter() - total_start
        print(f"[timing] worker_smoke_test_sec={smoke_elapsed:.3f}", flush=True)
        print("[timing] audio_generation_sec=0.000", flush=True)
        print("[timing] frame_generation_sec=0.000", flush=True)
        print("[timing] ffmpeg_encode_mux_sec=0.000", flush=True)
        print(f"[timing] total_wall_clock_sec={total_elapsed:.3f}", flush=True)
        return

    audio_start = perf_counter()
    audio_mix = build_audio_mix(duration_sec=args.duration, sample_rate=SAMPLE_RATE)
    audio_elapsed = perf_counter() - audio_start
    args.output.parent.mkdir(parents=True, exist_ok=True)

    audio_temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(prefix="pyreel_preview_", suffix=".wav", delete=False) as audio_handle:
            audio_temp_path = Path(audio_handle.name)
        write_mono_wav(audio_temp_path, audio_mix, sample_rate=SAMPLE_RATE)

        encode_stats = encode_video(
            output_path=args.output,
            audio_path=audio_temp_path,
            config=config,
            workers=worker_decision.active_workers,
            ffmpeg_path=runtime.ffmpeg_path,
            video_args=runtime.video_args,
        )
        actual_duration = verify_output(args.output, runtime.ffmpeg_path, args.duration)
        total_elapsed = perf_counter() - total_start
        ffmpeg_encode_mux_sec = encode_stats.ffmpeg_pipe_wait_sec + encode_stats.ffmpeg_finalize_sec
        print(f"[done] final_output_path={args.output}", flush=True)
        if actual_duration is not None:
            print(f"[done] final_output_duration_sec={actual_duration:.3f}", flush=True)
        else:
            print("[done] final_output_duration_sec=unknown", flush=True)
        print(f"[timing] audio_generation_sec={audio_elapsed:.3f}", flush=True)
        print(f"[timing] worker_smoke_test_sec={smoke_elapsed:.3f}", flush=True)
        print(f"[timing] frame_generation_sec={encode_stats.frame_generation_sec:.3f}", flush=True)
        print(
            f"[timing] ffmpeg_encode_mux_sec={ffmpeg_encode_mux_sec:.3f} "
            f"(pipe_wait={encode_stats.ffmpeg_pipe_wait_sec:.3f}, finalize={encode_stats.ffmpeg_finalize_sec:.3f})",
            flush=True,
        )
        print(f"[timing] total_wall_clock_sec={total_elapsed:.3f}", flush=True)
    finally:
        if audio_temp_path and audio_temp_path.exists() and not args.keep_audio_temp:
            audio_temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    mp.freeze_support()
    main()
