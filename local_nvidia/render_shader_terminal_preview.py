#!/usr/bin/env python3
from __future__ import annotations

import argparse
import struct
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import wgpu
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from wgpu_runtime import detect_local_shader_runtime


WGSL_SHADER = """
struct Uniforms {
    resolution: vec2<f32>,
    time_sec: f32,
    reveal: f32,
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
        q = q * 2.03 + vec2<f32>(13.1, 7.3);
        amp = amp * 0.5;
    }
    return value;
}

@vertex
fn vs_main(@builtin(vertex_index) vid: u32) -> VSOut {
    var pos = array<vec2<f32>, 3>(
        vec2<f32>(-1.0, -3.0),
        vec2<f32>(-1.0, 1.0),
        vec2<f32>(3.0, 1.0)
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
    let centered = uv * 2.0 - vec2<f32>(1.0, 1.0);
    let grid = abs(fract(uv * vec2<f32>(18.0, 12.0)) - 0.5);
    let grid_line = smoothstep(0.48, 0.50, max(grid.x, grid.y));
    let scan = 0.88 + 0.12 * sin(uv.y * uniforms.resolution.y * 1.2);
    let wave = sin((uv.y + t * 0.11) * 40.0 + fbm(uv * 4.0 + t * 0.2) * 6.0);
    let mist = fbm(uv * 6.0 + vec2<f32>(t * 0.08, -t * 0.05));
    let pulse = fbm(uv * 10.0 - vec2<f32>(t * 0.3, 0.0));
    let glitch_band = smoothstep(0.78, 0.98, sin((uv.y * 9.0 - t * 2.2) * 7.0) * 0.5 + 0.5);
    let reveal_flash = smoothstep(0.72, 1.0, uniforms.reveal) * smoothstep(0.0, 0.2, uv.x) * (1.0 - smoothstep(0.75, 1.0, uv.x));
    let vignette = clamp(1.0 - dot(centered * vec2<f32>(0.92, 0.72), centered * vec2<f32>(0.92, 0.72)) * 0.42, 0.12, 1.0);

    var color = vec3<f32>(0.01, 0.05, 0.02);
    color = color + vec3<f32>(0.02, 0.23, 0.08) * mist;
    color = color + vec3<f32>(0.03, 0.40, 0.12) * pulse * 0.7;
    color = color + vec3<f32>(0.10, 0.92, 0.32) * pow(max(wave, 0.0), 4.0) * 0.6;
    color = color + vec3<f32>(0.08, 0.90, 0.30) * grid_line * 0.18;
    color = color + vec3<f32>(0.12, 0.85, 0.35) * glitch_band * 0.08;
    color = color + vec3<f32>(0.18, 1.0, 0.50) * reveal_flash * 0.12;
    color = color * scan * vignette;

    return vec4<f32>(color, 1.0);
}
"""


TEXT_SEQUENCE = [
    (0.0, 4.0, "C:\\\\> dir /s /b"),
    (3.0, 7.2, "searching for ghost process..."),
    (6.0, 10.5, "warning: PYREEL not found"),
    (9.0, 13.8, "netstat -ano | findstr 31337"),
    (12.5, 18.0, "trace route interrupted"),
    (17.0, 22.5, "somebody is already in the shell"),
    (21.5, 26.4, "whoami"),
    (24.8, 30.0, "PYREEL> you looked away"),
]


def parse_args():
    parser = argparse.ArgumentParser(description="Local shader-backed terminal preview.")
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--duration", type=float, default=12.0)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path.home() / "Videos" / "local-shader-terminal-preview.mp4",
    )
    return parser.parse_args()


def resolve_font():
    candidates = [
        Path("C:/Windows/Fonts/consola.ttf"),
        Path("C:/Windows/Fonts/lucon.ttf"),
        Path("C:/Windows/Fonts/cour.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    raise FileNotFoundError("No monospaced font found for terminal overlay.")


class ShaderTerminalRenderer:
    def __init__(self, width: int, height: int):
        runtime, adapter = detect_local_shader_runtime()
        self.runtime = runtime
        self.adapter = adapter
        self.device = adapter.request_device_sync()
        self.width = width
        self.height = height
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
        self.bind_group_layout = self.device.create_bind_group_layout(
            entries=[
                {
                    "binding": 0,
                    "visibility": wgpu.ShaderStage.FRAGMENT,
                    "buffer": {"type": wgpu.BufferBindingType.uniform},
                }
            ]
        )
        self.pipeline_layout = self.device.create_pipeline_layout(bind_group_layouts=[self.bind_group_layout])
        self.bind_group = self.device.create_bind_group(
            layout=self.bind_group_layout,
            entries=[{"binding": 0, "resource": {"buffer": self.uniform_buffer, "offset": 0, "size": 16}}],
        )
        self.shader = self.device.create_shader_module(code=WGSL_SHADER)
        self.pipeline = self.device.create_render_pipeline(
            layout=self.pipeline_layout,
            vertex={"module": self.shader, "entry_point": "vs_main", "buffers": []},
            fragment={
                "module": self.shader,
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
        self.font = ImageFont.truetype(resolve_font(), 24)
        self.font_big = ImageFont.truetype(resolve_font(), 62)

    def render_background(self, time_sec: float, reveal: float) -> np.ndarray:
        payload = struct.pack("4f", float(self.width), float(self.height), float(time_sec), float(reveal))
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
        frame = frame[:, : self.unpadded_bytes_per_row].reshape(self.height, self.width, 4).copy()
        self.readback.unmap()
        return frame

    def overlay_text(self, frame_rgba: np.ndarray, time_sec: float, reveal: float) -> bytes:
        image = Image.fromarray(frame_rgba, mode="RGBA")
        draw = ImageDraw.Draw(image)
        margin_x = 52
        base_y = 78
        line_gap = 34

        draw.rectangle((38, 42, self.width - 38, self.height - 42), outline=(36, 255, 126, 90), width=2)
        draw.text((margin_x, base_y - 34), "SESSION // GHOST IN THE MACHINE", font=self.font, fill=(104, 255, 168, 180))

        visible_lines = []
        for start, end, text in TEXT_SEQUENCE:
            if start <= time_sec <= end:
                visible_lines.append(text)
            elif time_sec > end:
                visible_lines.append(text)

        visible_lines = visible_lines[-7:]
        for idx, text in enumerate(visible_lines):
            jitter = int(np.sin(time_sec * 4.0 + idx) * 2.0)
            draw.text((margin_x, base_y + idx * line_gap + jitter), text, font=self.font, fill=(130, 255, 170, 210))

        if 7.5 <= time_sec <= 10.2:
            draw.text((self.width * 0.62, self.height * 0.24), "PY", font=self.font_big, fill=(170, 255, 200, 70))
        if 14.8 <= time_sec <= 17.3:
            draw.text((self.width * 0.18, self.height * 0.72), "RE", font=self.font_big, fill=(170, 255, 200, 76))
        if 22.6 <= time_sec <= 24.7:
            draw.text((self.width * 0.73, self.height * 0.54), "EL", font=self.font_big, fill=(170, 255, 200, 84))

        if reveal > 0.0:
            alpha = int(255 * min(1.0, reveal * 1.3))
            title = Image.new("RGBA", image.size, (0, 0, 0, 0))
            title_draw = ImageDraw.Draw(title)
            title_draw.text((self.width * 0.18, self.height * 0.40), "PYREEL", font=self.font_big, fill=(190, 255, 215, alpha))
            title = title.filter(ImageFilter.GaussianBlur(radius=5.0))
            image = Image.alpha_composite(image, title)

        rgb = np.array(image.convert("RGB"), dtype=np.uint8)
        return rgb.tobytes()


def start_encoder(output: Path, width: int, height: int, fps: int, runtime) -> subprocess.Popen:
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        runtime.ffmpeg_path,
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{width}x{height}",
        "-r",
        str(fps),
        "-i",
        "-",
        *runtime.video_args,
        "-pix_fmt",
        "yuv420p",
        str(output),
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def main():
    args = parse_args()
    total_frames = int(round(args.duration * args.fps))
    renderer = ShaderTerminalRenderer(args.width, args.height)

    print(f"[gpu] adapter={renderer.runtime.adapter_name}")
    print(f"[gpu] backend={renderer.runtime.backend}")
    print(f"[encode] ffmpeg={renderer.runtime.ffmpeg_path}")
    print(f"[encode] encoder={renderer.runtime.encoder}")

    proc = start_encoder(args.output, args.width, args.height, args.fps, renderer.runtime)
    frame_start = time.perf_counter()
    try:
        assert proc.stdin is not None
        for frame_index in range(total_frames):
            time_sec = frame_index / args.fps
            reveal = min(1.0, max(0.0, (time_sec - args.duration * 0.72) / (args.duration * 0.18)))
            frame_rgba = renderer.render_background(time_sec, reveal)
            proc.stdin.write(renderer.overlay_text(frame_rgba, time_sec, reveal))
            if frame_index % args.fps == 0 or frame_index + 1 == total_frames:
                print(f"[render] {frame_index + 1}/{total_frames} frames", flush=True)
    finally:
        if proc.stdin and not proc.stdin.closed:
            proc.stdin.close()

    stderr = proc.stderr.read().decode("utf-8", errors="replace")
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"ffmpeg failed: {stderr[-1200:]}")

    elapsed = time.perf_counter() - frame_start
    print(f"[done] wrote {args.output}")
    print(f"[timing] frame+encode_seconds={elapsed:.2f}")


if __name__ == "__main__":
    main()
