# Interference Film Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a 60-second 720p code-generated film featuring geometric interference patterns from multiple overlapping line grids with a moving viewpoint.

**Architecture:** Single Python script using NumPy for frame buffers, PIL for line rendering, and piped FFmpeg for video encoding. Grid layers are accumulated over time while the virtual camera drifts across a larger canvas to reveal moiré patterns.

**Tech Stack:** Python, NumPy, Pillow, FFmpeg, scipy (for audio synthesis)

---

## File Structure

| File | Purpose |
|------|---------|
| `interference_preview.py` | Main film generation script (creates this file) |
| `C:/Users/wests/Videos/interference_preview.mp4` | Output video file |

---

## Chunk 1: Core Rendering Infrastructure

### Task 1: Create Script Structure and Imports

**Files:**
- Create: `interference_preview.py`

- [ ] **Step 1: Write imports and configuration constants**

```python
#!/usr/bin/env python3
"""Interference — A 60-second geometric moiré pattern film."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

import numpy as np
from PIL import Image, ImageDraw

# Resolution and timing
W, H = 1280, 720
FPS = 24
DURATION = 60
TOTAL_FRAMES = FPS * DURATION

# Virtual canvas (larger than viewport for camera movement)
CANVAS_W, CANVAS_H = 1920, 1080

# Color palette
BG_COLOR = (0, 0, 0)
LINE_COLOR = (255, 255, 255)
ALT_LINE_COLOR = (224, 255, 255)  # Light cyan

# FFmpeg path (adjust if needed)
FFMPEG_PATH = r"C:\pinokio\bin\miniconda\Library\bin\ffmpeg.exe"
OUTPUT_PATH = Path(r"C:\Users\wests\Videos\interference_preview.mp4")
```

- [ ] **Step 2: Add GridLayer dataclass**

```python
from dataclasses import dataclass


@dataclass
class GridLayer:
    """A single grid of lines at a specific angle."""
    angle_deg: float
    line_count: int
    color: Tuple[int, int, int]
    alpha: int = 255
```

- [ ] **Step 3: Verify imports work**

Run: `cd C:/Github/pyreeler && python -c "import numpy; from PIL import Image; print('OK')"`
Expected: `OK`

---

### Task 2: Grid Rendering System

**Files:**
- Modify: `interference_preview.py`

- [ ] **Step 1: Write line grid rendering function**

```python
def create_grid_lines(
    angle_deg: float,
    line_count: int,
    canvas_w: int,
    canvas_h: int
) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
    """Generate line endpoints for a grid at given angle.

    Returns list of (start_point, end_point) tuples.
    """
    import math

    lines = []
    angle_rad = math.radians(angle_deg)

    # Calculate diagonal to ensure lines cover entire canvas
    diagonal = math.sqrt(canvas_w**2 + canvas_h**2)

    # Lines are perpendicular to the angle direction
    perp_angle = angle_rad + math.pi / 2

    # Create lines spaced across the canvas
    for i in range(line_count):
        # Parameter from -1 to 1 across the canvas
        t = (i / (line_count - 1)) * 2 - 1 if line_count > 1 else 0

        # Center point of this line
        center_x = canvas_w / 2 + t * diagonal * math.cos(perp_angle) / 2
        center_y = canvas_h / 2 + t * diagonal * math.sin(perp_angle) / 2

        # Line extends along the angle direction
        dx = diagonal * math.cos(angle_rad) / 2
        dy = diagonal * math.sin(angle_rad) / 2

        start = (center_x - dx, center_y - dy)
        end = (center_x + dx, center_y + dy)
        lines.append((start, end))

    return lines
```

- [ ] **Step 2: Write viewport cropping function**

```python
def crop_to_viewport(
    frame: Image.Image,
    camera_x: float,
    camera_y: float,
    zoom: float,
    viewport_w: int,
    viewport_h: int
) -> Image.Image:
    """Crop a portion of the canvas based on camera position and zoom."""

    # Calculate visible area size
    visible_w = viewport_w / zoom
    visible_h = viewport_h / zoom

    # Calculate crop bounds (centered on camera)
    left = int(camera_x - visible_w / 2)
    top = int(camera_y - visible_h / 2)
    right = int(left + visible_w)
    bottom = int(top + visible_h)

    # Clamp to canvas bounds
    left = max(0, min(left, frame.width - visible_w))
    top = max(0, min(top, frame.height - visible_h))
    right = min(frame.width, left + visible_w)
    bottom = min(frame.height, top + visible_h)

    # Crop and resize to viewport
    cropped = frame.crop((left, top, right, bottom))
    return cropped.resize((viewport_w, viewport_h), Image.Resampling.LANCZOS)
```

- [ ] **Step 3: Test grid rendering**

Run: `python -c "
from interference_preview import create_grid_lines, GridLayer
lines = create_grid_lines(0, 10, 1920, 1080)
print(f'Generated {len(lines)} horizontal lines')
lines = create_grid_lines(45, 10, 1920, 1080)
print(f'Generated {len(lines)} diagonal lines')
print('OK')
"`
Expected:
```
Generated 10 horizontal lines
Generated 10 diagonal lines
OK
```

---

### Task 3: Camera Movement System

**Files:**
- Modify: `interference_preview.py`

- [ ] **Step 1: Write camera path function**

```python
def get_camera_position(
    frame: int,
    total_frames: int,
    canvas_w: int,
    canvas_h: int,
    viewport_w: int,
    viewport_h: int
) -> Tuple[float, float, float]:
    """Calculate camera position (x, y) and zoom for a given frame.

    Returns: (camera_x, camera_y, zoom)
    """
    import math

    # Normalize time 0-1
    t = frame / total_frames

    # Camera drifts in a gentle figure-8 pattern
    # Center of movement
    center_x = canvas_w / 2
    center_y = canvas_h / 2

    # Movement amplitude (how far from center)
    amplitude_x = (canvas_w - viewport_w) / 3
    amplitude_y = (canvas_h - viewport_h) / 3

    # Figure-8 parametric equations with slow drift
    # Primary movement: slow Lissajous curve
    angle = t * 2 * math.pi * 0.5  # Half cycle over full duration

    x = center_x + amplitude_x * math.sin(angle * 2)
    y = center_y + amplitude_y * math.sin(angle * 3 + math.pi/4)

    # Breathing zoom: subtle pulse
    zoom_base = 1.0
    zoom_breath = 0.15 * math.sin(t * 2 * math.pi * 2)  # 2 breaths
    zoom = zoom_base + zoom_breath

    return (x, y, zoom)
```

- [ ] **Step 2: Write layer activation schedule**

```python
def get_active_layers(frame: int) -> List[GridLayer]:
    """Determine which grid layers are active based on frame number."""

    # Layer schedule: (start_frame, angle_deg, line_count, color)
    layer_schedule = [
        (0, 0, 30, LINE_COLOR),           # Vertical, sparse
        (240, 15, 40, ALT_LINE_COLOR),    # +15°, 10s in
        (480, -15, 50, LINE_COLOR),       # -15°, 20s in
        (600, 90, 60, ALT_LINE_COLOR),    # Horizontal, 25s in
        (768, 30, 70, LINE_COLOR),        # +30°, 32s in
        (960, 45, 85, ALT_LINE_COLOR),    # +45°, 40s in
        (1080, 60, 100, LINE_COLOR),      # +60°, 45s in
    ]

    active = []
    for start_frame, angle, count, color in layer_schedule:
        if frame >= start_frame:
            active.append(GridLayer(angle, count, color))

    return active
```

- [ ] **Step 3: Test camera and layer functions**

Run: `python -c "
from interference_preview import get_camera_position, get_active_layers, CANVAS_W, CANVAS_H, W, H, TOTAL_FRAMES

# Test camera at start, middle, end
for f in [0, 720, 1440]:
    x, y, z = get_camera_position(f, TOTAL_FRAMES, CANVAS_W, CANVAS_H, W, H)
    print(f'Frame {f}: x={x:.0f}, y={y:.0f}, zoom={z:.2f}')

# Test layer activation
for f in [0, 300, 600, 1200]:
    layers = get_active_layers(f)
    print(f'Frame {f}: {len(layers)} layers active')

print('OK')
"`
Expected: Camera positions and layer counts at different times, ending with `OK`.

---

## Chunk 2: Frame Generation and Video Encoding

### Task 4: Frame Rendering Loop

**Files:**
- Modify: `interference_preview.py`

- [ ] **Step 1: Write frame rendering function**

```python
def render_frame(
    frame_num: int,
    canvas_w: int = CANVAS_W,
    canvas_h: int = CANVAS_H,
    viewport_w: int = W,
    viewport_h: int = H
) -> Image.Image:
    """Render a single frame with all active grid layers."""

    # Create black canvas
    canvas = Image.new('RGB', (canvas_w, canvas_h), BG_COLOR)
    draw = ImageDraw.Draw(canvas)

    # Get active layers for this frame
    layers = get_active_layers(frame_num)

    # Draw each layer
    for layer in layers:
        lines = create_grid_lines(
            layer.angle_deg,
            layer.line_count,
            canvas_w,
            canvas_h
        )

        for start, end in lines:
            draw.line([start, end], fill=layer.color, width=1)

    # Get camera position
    cam_x, cam_y, zoom = get_camera_position(
        frame_num,
        TOTAL_FRAMES,
        canvas_w,
        canvas_h,
        viewport_w,
        viewport_h
    )

    # Crop to viewport
    viewport = crop_to_viewport(
        canvas,
        cam_x,
        cam_y,
        zoom,
        viewport_w,
        viewport_h
    )

    return viewport
```

- [ ] **Step 2: Test render a single frame**

Run: `python -c "
from interference_preview import render_frame
import time

start = time.time()
frame = render_frame(0)
print(f'Frame size: {frame.size}')
print(f'Render time: {time.time() - start:.2f}s')
frame.save('test_frame.png')
print('Saved test_frame.png')
"`
Expected: Frame renders and saves successfully.

- [ ] **Step 3: Commit progress**

```bash
git add interference_preview.py
git commit -m "feat: add core grid rendering and camera system"
```

---

### Task 5: FFmpeg Video Encoding

**Files:**
- Modify: `interference_preview.py`

- [ ] **Step 1: Write FFmpeg setup and encoding**

```python
def create_ffmpeg_process(output_path: Path) -> subprocess.Popen:
    """Create FFmpeg subprocess for piped video encoding."""

    cmd = [
        FFMPEG_PATH,
        '-y',  # Overwrite output
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-pix_fmt', 'rgb24',
        '-s', f'{W}x{H}',
        '-r', str(FPS),
        '-i', '-',  # Read from stdin
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-preset', 'medium',
        '-crf', '18',
        str(output_path)
    ]

    return subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
```

- [ ] **Step 2: Write main render loop**

```python
def render_film() -> None:
    """Render the complete film and save to output path."""

    print(f"Rendering {DURATION}s film at {FPS}fps ({TOTAL_FRAMES} frames)")
    print(f"Output: {OUTPUT_PATH}")

    # Create output directory if needed
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Start FFmpeg
    ffmpeg = create_ffmpeg_process(OUTPUT_PATH)

    try:
        for frame_num in range(TOTAL_FRAMES):
            # Render frame
            frame = render_frame(frame_num)

            # Convert to bytes and write to FFmpeg
            frame_bytes = frame.tobytes()
            ffmpeg.stdin.write(frame_bytes)

            # Progress update every 5 seconds
            if frame_num % (FPS * 5) == 0:
                progress = frame_num / TOTAL_FRAMES * 100
                print(f"  {progress:.0f}% complete ({frame_num}/{TOTAL_FRAMES})")

        print("  100% complete - finalizing...")

    finally:
        ffmpeg.stdin.close()
        ffmpeg.wait()

    print(f"Done! Saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    render_film()
```

- [ ] **Step 3: Add Windows multiprocessing guard**

```python
if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()
    render_film()
```

---

## Chunk 3: Audio Generation

### Task 6: Procedural Audio System

**Files:**
- Modify: `interference_preview.py`

- [ ] **Step 1: Write audio synthesis functions**

```python
def generate_sine_wave(
    freq: float,
    duration: float,
    sample_rate: int = 48000,
    amplitude: float = 0.3
) -> np.ndarray:
    """Generate a sine wave at given frequency."""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = np.sin(2 * np.pi * freq * t) * amplitude
    return wave.astype(np.float32)


def apply_fade(wave: np.ndarray, fade_duration: int) -> np.ndarray:
    """Apply fade in/out to avoid clicks."""
    fade = np.linspace(0, 1, fade_duration)
    wave[:fade_duration] *= fade
    wave[-fade_duration:] *= fade[::-1]
    return wave
```

- [ ] **Step 2: Write drone layer generation**

```python
def generate_drone_layer(duration: float = DURATION) -> np.ndarray:
    """Generate the base drone audio layer."""
    sample_rate = 48000
    samples = int(sample_rate * duration)
    t = np.linspace(0, duration, samples, False)

    # Base frequency that shifts slightly
    base_freq = 100
    freq_shift = 20 * np.sin(t * 2 * np.pi / duration)  # Slow shift

    # Create frequency-modulated drone
    phase = np.cumsum(2 * np.pi * (base_freq + freq_shift) / sample_rate)
    drone = np.sin(phase) * 0.15

    # Add harmonics
    drone += np.sin(phase * 2) * 0.08
    drone += np.sin(phase * 3) * 0.04

    return drone.astype(np.float32)
```

- [ ] **Step 3: Write interference tone generation**

```python
def generate_interference_tones(duration: float = DURATION) -> np.ndarray:
    """Generate high harmonics triggered by dense interference moments."""
    sample_rate = 48000
    samples = int(sample_rate * duration)
    t = np.linspace(0, duration, samples, False)

    tones = np.zeros(samples, dtype=np.float32)

    # Trigger high tones when layers are dense (after frame 600)
    # Use 4 distinct moments
    trigger_times = [15, 25, 40, 50]  # seconds
    freqs = [800, 1200, 600, 1000]

    for trigger, freq in zip(trigger_times, freqs):
        start_sample = int(trigger * sample_rate)
        end_sample = int((trigger + 3) * sample_rate)
        if end_sample > samples:
            end_sample = samples

        tone_duration = (end_sample - start_sample) / sample_rate
        tone = generate_sine_wave(freq, tone_duration, sample_rate, 0.1)
        tone = apply_fade(tone, int(0.1 * sample_rate))

        tones[start_sample:end_sample] += tone

    return tones
```

- [ ] **Step 4: Write pulse layer**

```python
def generate_pulse_layer(duration: float = DURATION) -> np.ndarray:
    """Generate soft heartbeat pulse that emerges at 30s."""
    sample_rate = 48000
    samples = int(sample_rate * duration)
    t = np.linspace(0, duration, samples, False)

    pulse = np.zeros(samples, dtype=np.float32)

    # 70 BPM = 0.857s per beat
    bpm = 70
    beat_interval = 60 / bpm

    # Start at 30s, ramp up
    start_time = 30
    start_sample = int(start_time * sample_rate)

    beat_time = start_time
    beat_idx = 0

    while beat_time < duration:
        # Amplitude ramps up from 0 to 0.15
        progress = min(1.0, (beat_time - start_time) / 20)
        amp = progress * 0.12

        beat_sample = int(beat_time * sample_rate)
        beat_duration = int(0.15 * sample_rate)  # 150ms pulse

        if beat_sample + beat_duration < samples:
            # Simple decay envelope
            env = np.exp(-np.linspace(0, 5, beat_duration))
            pulse[beat_sample:beat_sample + beat_duration] += env * amp

        beat_time += beat_interval
        beat_idx += 1

    return pulse
```

- [ ] **Step 5: Write audio mixing and export**

```python
def generate_and_save_audio(output_path: Path) -> None:
    """Generate complete audio and save as WAV."""
    from scipy.io import wavfile

    print("Generating audio...")

    drone = generate_drone_layer()
    tones = generate_interference_tones()
    pulse = generate_pulse_layer()

    # Mix layers
    mixed = drone + tones + pulse

    # Normalize to prevent clipping
    max_val = np.max(np.abs(mixed))
    if max_val > 0.9:
        mixed = mixed / max_val * 0.9

    # Convert to 16-bit
    mixed_int16 = (mixed * 32767).astype(np.int16)

    wav_path = output_path.with_suffix('.wav')
    wavfile.write(wav_path, 48000, mixed_int16)

    print(f"Audio saved to {wav_path}")
    return wav_path
```

- [ ] **Step 6: Test audio generation**

Run: `python -c "
from interference_preview import generate_and_save_audio
from pathlib import Path
wav = generate_and_save_audio(Path('test_output.mp4'))
print(f'Audio file size: {wav.stat().st_size} bytes')
"`
Expected: Audio file generates successfully.

- [ ] **Step 7: Commit audio system**

```bash
git add interference_preview.py
git commit -m "feat: add procedural audio generation"
```

---

## Chunk 4: Final Assembly and Testing

### Task 7: Audio-Video Muxing

**Files:**
- Modify: `interference_preview.py`

- [ ] **Step 1: Update render_film to mux audio**

```python
def mux_audio_video(video_path: Path, audio_path: Path, output_path: Path) -> None:
    """Combine video and audio into final output."""

    cmd = [
        FFMPEG_PATH,
        '-y',
        '-i', str(video_path),
        '-i', str(audio_path),
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        str(output_path)
    ]

    subprocess.run(cmd, check=True, capture_output=True)
    print(f"Final output with audio: {output_path}")


def render_film() -> None:
    """Render the complete film with audio and save to output path."""

    print(f"Rendering {DURATION}s film at {FPS}fps ({TOTAL_FRAMES} frames)")

    # Temporary paths
    temp_video = OUTPUT_PATH.with_name(OUTPUT_PATH.stem + '_video_only.mp4')
    temp_audio = OUTPUT_PATH.with_suffix('.wav')

    try:
        # Step 1: Render video
        print(f"\n[1/3] Rendering video to {temp_video}")
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

        ffmpeg = create_ffmpeg_process(temp_video)

        for frame_num in range(TOTAL_FRAMES):
            frame = render_frame(frame_num)
            ffmpeg.stdin.write(frame.tobytes())

            if frame_num % (FPS * 5) == 0:
                progress = frame_num / TOTAL_FRAMES * 100
                print(f"  Video: {progress:.0f}%")

        ffmpeg.stdin.close()
        ffmpeg.wait()
        print("  Video: 100%")

        # Step 2: Generate audio
        print("\n[2/3] Generating audio...")
        generate_and_save_audio(OUTPUT_PATH)

        # Step 3: Mux
        print("\n[3/3] Combining video and audio...")

        # Move temp files for muxing
        temp_video_actual = OUTPUT_PATH.with_name(OUTPUT_PATH.stem + '_video_only.mp4')
        temp_audio_actual = OUTPUT_PATH.with_suffix('.wav')

        mux_audio_video(temp_video_actual, temp_audio_actual, OUTPUT_PATH)

        print(f"\nDone! Final output: {OUTPUT_PATH}")

    finally:
        # Cleanup temp files
        for temp in [temp_video, temp_audio]:
            if temp.exists():
                temp.unlink()
```

---

### Task 8: Final Testing

**Files:**
- Modify: `interference_preview.py` (if needed)
- Create: Final output video

- [ ] **Step 1: Run full render (accept long runtime)**

Run: `python interference_preview.py`
Expected: Progress updates every 5%, then audio generation, then muxing. Final message: `Done! Final output: C:\Users\wests\Videos\interference_preview.mp4`

- [ ] **Step 2: Verify output file exists and plays**

Run: `ls -lh "C:/Users/wests/Videos/interference_preview.mp4"`
Expected: File exists, size > 10MB for 60s video.

- [ ] **Step 3: Quick visual validation**

Open the video in a player and verify:
- Video starts with sparse vertical lines
- Layers add progressively
- Camera drifts smoothly
- Moiré patterns are visible
- Audio has drone and pulse layers

---

### Task 9: Final Commit

**Files:**
- Create: `interference_preview.py` (complete)

- [ ] **Step 1: Commit final film script**

```bash
git add interference_preview.py
git commit -m "feat: complete Interference film — 60s geometric moiré patterns

- Multiple grid layers at different angles
- Accumulating density arc (sparse to saturated)
- Moving viewpoint reveals moiré patterns
- Procedural audio: drone, interference tones, pulse
- 720p output with piped FFmpeg encoding"
```

---

## Success Criteria

- [ ] Script runs without errors
- [ ] Output video is exactly 60 seconds
- [ ] Video resolution is 1280x720
- [ ] File plays in standard video players
- [ ] Visual arc matches design (seed → layering → density → saturation → hold)
- [ ] Audio has all three layers (drone, tones, pulse)

---

## Notes for Implementer

1. **FFmpeg path**: The script uses `C:\pinokio\bin\miniconda\Library\bin\ffmpeg.exe`. If this doesn't exist on your system, update `FFMPEG_PATH` to point to your FFmpeg installation.

2. **Performance**: Rendering 1440 frames will take time (estimate 5-15 minutes depending on CPU). The script shows progress every 5 seconds.

3. **Memory**: Each frame is 1280x720 RGB (~2.7MB). The canvas is 1920x1080. This should fit comfortably in memory.

4. **Audio dependency**: Requires `scipy` for WAV export. Install with `pip install scipy` if needed.
