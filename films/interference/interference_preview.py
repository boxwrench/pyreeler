#!/usr/bin/env python3
"""Interference — A 60-second geometric moiré pattern film (OPTIMIZED).

Multiple overlapping line grids create evolving interference patterns
as the viewpoint drifts across a dense field.

OPTIMIZATIONS:
- CRF 28 for web-friendly file sizes
- Quantized angle caching for grid lines
- Smaller canvas (1600x900 vs 1920x1080)
"""
from __future__ import annotations

import math
import os
import subprocess
import sys
from dataclasses import dataclass
from multiprocessing import freeze_support
from pathlib import Path
from typing import List, Tuple

import numpy as np
from PIL import Image, ImageDraw

# External tool paths
FFMPEG_PATH = r"C:\pinokio\bin\miniconda\Library\bin\ffmpeg.exe"
FLUIDSYNTH_PATH = r"C:\Users\wests\.fluidsynth\bin\fluidsynth.exe"
SOUNDFONT_PATH = r"C:\Users\wests\.fluidsynth\TimGM6mb.sf2"


# =============================================================================
# CONFIGURATION
# =============================================================================

# Output settings
OUTPUT_PATH = Path(os.path.expanduser("~/Videos/interference_preview.mp4"))

# Timing
FPS = 24
DURATION = 60  # seconds
TOTAL_FRAMES = FPS * DURATION

# Resolution (720p preview)
W, H = 1280, 720

# Virtual canvas (larger than viewport for camera movement)
# OPTIMIZED: Smaller canvas = faster rendering, less memory
CANVAS_W, CANVAS_H = 1600, 900  # Was 1920x1080

# Color palette
BG_COLOR = (0, 0, 0)
LINE_COLOR = (255, 255, 255)
ALT_LINE_COLOR = (224, 255, 255)  # Light cyan

# OPTIMIZED: Grid line cache to avoid recalculation
_grid_line_cache: dict = {}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class GridLayer:
    """A single grid of lines at a specific angle."""
    angle_deg: float
    line_count: int
    color: Tuple[int, int, int]


# =============================================================================
# GRID RENDERING
# =============================================================================

def create_grid_lines(
    angle_deg: float,
    line_count: int,
    canvas_w: int,
    canvas_h: int
) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
    """Generate line endpoints for a grid at given angle.

    OPTIMIZED: Uses angle quantization and caching to avoid recalculation.
    """
    # Quantize angle to reduce cache misses (0.5 degree precision)
    quantized_angle = round(angle_deg * 2) / 2
    cache_key = (quantized_angle, line_count, canvas_w, canvas_h)

    if cache_key in _grid_line_cache:
        return _grid_line_cache[cache_key]

    lines = []
    angle_rad = math.radians(quantized_angle)

    # Diagonal to ensure lines cover entire canvas
    diagonal = math.sqrt(canvas_w**2 + canvas_h**2)
    perp_angle = angle_rad + math.pi / 2

    for i in range(line_count):
        # Parameter from -1 to 1 across the canvas
        if line_count > 1:
            t = (i / (line_count - 1)) * 2 - 1
        else:
            t = 0

        # Center point of this line
        center_x = canvas_w / 2 + t * diagonal * math.cos(perp_angle) / 2
        center_y = canvas_h / 2 + t * diagonal * math.sin(perp_angle) / 2

        # Line extends along the angle direction
        dx = diagonal * math.cos(angle_rad) / 2
        dy = diagonal * math.sin(angle_rad) / 2

        start = (center_x - dx, center_y - dy)
        end = (center_x + dx, center_y + dy)
        lines.append((start, end))

    # Cache the result
    _grid_line_cache[cache_key] = lines
    return lines


def crop_to_viewport(
    frame: Image.Image,
    camera_x: float,
    camera_y: float,
    zoom: float,
    viewport_w: int,
    viewport_h: int
) -> Image.Image:
    """Crop a portion of the canvas based on camera position and zoom."""
    visible_w = viewport_w / zoom
    visible_h = viewport_h / zoom

    left = int(camera_x - visible_w / 2)
    top = int(camera_y - visible_h / 2)
    right = int(left + visible_w)
    bottom = int(top + visible_h)

    # Clamp to canvas bounds
    left = max(0, min(left, frame.width - int(visible_w)))
    top = max(0, min(top, frame.height - int(visible_h)))
    right = min(frame.width, left + int(visible_w))
    bottom = min(frame.height, top + int(visible_h))

    cropped = frame.crop((left, top, right, bottom))
    return cropped.resize((viewport_w, viewport_h), Image.Resampling.LANCZOS)


# =============================================================================
# CAMERA AND LAYER SCHEDULE
# =============================================================================

def get_camera_position(
    frame: int,
    total_frames: int,
    canvas_w: int,
    canvas_h: int,
    viewport_w: int,
    viewport_h: int
) -> Tuple[float, float, float]:
    """Calculate camera position (x, y) and zoom for a given frame."""
    t = frame / total_frames

    center_x = canvas_w / 2
    center_y = canvas_h / 2

    # Movement amplitude
    amplitude_x = (canvas_w - viewport_w) / 3
    amplitude_y = (canvas_h - viewport_h) / 3

    # Lissajous curve for smooth drifting
    angle = t * 2 * math.pi * 0.5
    x = center_x + amplitude_x * math.sin(angle * 2)
    y = center_y + amplitude_y * math.sin(angle * 3 + math.pi / 4)

    # Breathing zoom
    zoom_base = 1.0
    zoom_breath = 0.15 * math.sin(t * 2 * math.pi * 2)
    zoom = zoom_base + zoom_breath

    return (x, y, zoom)


def get_active_layers(frame: int, total_frames: int = TOTAL_FRAMES) -> List[GridLayer]:
    """Determine which grid layers are active based on frame number.

    Faster density ramp with rotating angles over time.
    """
    t = frame / total_frames  # Normalized time 0-1

    # Continuous rotation: grids slowly rotate 0-15 degrees over the film
    base_rotation = t * 15

    # Layer schedule: (start_frame, base_angle, line_count, color)
    # Compressed schedule: all layers by ~25s, denser lines
    layer_schedule = [
        (0, 0, 50, LINE_COLOR),           # Vertical at start, 50 lines
        (120, 15, 60, ALT_LINE_COLOR),    # +15° at 5s
        (240, -15, 70, LINE_COLOR),       # -15° at 10s
        (360, 90, 80, ALT_LINE_COLOR),    # Horizontal at 15s
        (480, 30, 90, LINE_COLOR),        # +30° at 20s
        (600, 45, 110, ALT_LINE_COLOR),   # +45° at 25s
        (720, 60, 130, LINE_COLOR),       # +60° at 30s
    ]

    active = []
    for start_frame, base_angle, count, color in layer_schedule:
        if frame >= start_frame:
            # Each layer rotates at slightly different rate
            rotation_offset = base_rotation * (1 + (start_frame / 720))
            angle = base_angle + rotation_offset
            active.append(GridLayer(angle, count, color))

    return active


# =============================================================================
# FRAME RENDERING
# =============================================================================

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

    # Get active layers for this frame (with rotation over time)
    layers = get_active_layers(frame_num, TOTAL_FRAMES)

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

    # Get camera position and crop
    cam_x, cam_y, zoom = get_camera_position(
        frame_num, TOTAL_FRAMES, canvas_w, canvas_h, viewport_w, viewport_h
    )

    viewport = crop_to_viewport(canvas, cam_x, cam_y, zoom, viewport_w, viewport_h)
    return viewport


# =============================================================================
# AUDIO GENERATION (MIDI + SoundFont)
# =============================================================================



def generate_midi_score(midi_path: Path, duration: float = DURATION) -> None:
    """Generate a MIDI score for the interference film.

    Creates an ambient/instrumental piece that matches the visual density arc:
    - Sparse beginning (0-10s): few notes, space
    - Building layers (10-30s): more voices, harmonies
    - Dense middle (30-45s): full orchestration
    - Resolution (45-60s): thinning out, held tones
    """
    try:
        from midiutil import MIDIFile
    except ImportError as exc:
        raise RuntimeError("Install midiutil: pip install midiutil") from exc

    midi = MIDIFile(3)  # 3 tracks

    # Track 0: Ambient pad (program 95 - Pad 1)
    # Track 1: Arpeggio/motion (program 91 - Pad 4)
    # Track 2: Bass pulse (program 33 - Electric Bass)

    tempo = 72  # Slow, contemplative

    for track in range(3):
        midi.addTempo(track, 0, tempo)

    # Programs
    midi.addProgramChange(0, 0, 0, 95)   # Pad 1 (new age)
    midi.addProgramChange(1, 1, 0, 91)   # Pad 4 (choir)
    midi.addProgramChange(2, 2, 0, 33)   # Electric Bass

    # Scale: C minor pentatonic + extensions
    # C, Eb, F, G, Bb, (C)
    base_notes = [48, 51, 53, 55, 58, 60, 63, 65]  # C3 to C5 range

    total_beats = int(duration * tempo / 60)

    # Track 0: Ambient pad - long sustained notes
    # Sparse at start, denser in middle, resolve at end
    pad_notes = [48, 55, 51, 58, 53, 60, 55, 63]  # Evolving harmony

    beat = 0
    note_idx = 0
    while beat < total_beats:
        # Density increases then decreases
        t = beat / total_beats
        density = 1.0 - abs(t - 0.5) * 1.5  # Peak at middle
        density = max(0.2, min(0.9, density))

        # Add note with probability based on density
        if np.random.random() < density:
            note = pad_notes[note_idx % len(pad_notes)]
            duration_beats = 4 + np.random.randint(0, 4)  # Long sustained
            velocity = 50 + int(density * 30)

            midi.addNote(0, 0, note, beat, duration_beats, velocity)
            note_idx += 1

        beat += 2  # Check every 2 beats

    # Track 1: Arpeggio figure - creates motion
    arp_notes = [60, 63, 65, 68, 72, 68, 65, 63]  # Higher register

    beat = 0
    note_idx = 0
    arp_speed = 2  # Notes every 2 beats initially

    while beat < total_beats:
        t = beat / total_beats

        # Speed up in middle section
        if 0.3 < t < 0.7:
            arp_speed = 1  # Faster
        else:
            arp_speed = 2  # Slower

        if beat % arp_speed < 1:
            note = arp_notes[note_idx % len(arp_notes)]
            velocity = 40 + int(np.sin(t * np.pi) * 30)  # Louder in middle
            midi.addNote(1, 1, note, beat, 1.5, velocity)
            note_idx += 1

        beat += 1

    # Track 2: Bass pulse - rhythmic foundation
    # Starts at 15s, builds intensity
    start_beat = int(15 * tempo / 60)
    beat = start_beat

    bass_pattern = [36, 36, 43, 36, 41, 36, 43, 41]  # C2, G2, F2 patterns
    pattern_idx = 0

    while beat < total_beats:
        t = (beat - start_beat) / (total_beats - start_beat)

        # Every 2 beats (half note pulse)
        if beat % 2 == 0:
            note = bass_pattern[pattern_idx % len(bass_pattern)]
            # Intensity builds
            velocity = 60 + int(t * 35)
            midi.addNote(2, 2, note, beat, 1.5, velocity)
            pattern_idx += 1

        beat += 1

    # Write MIDI file
    midi_path.parent.mkdir(parents=True, exist_ok=True)
    with open(midi_path, "wb") as f:
        midi.writeFile(f)


def render_midi_with_fluidsynth(midi_path: Path, wav_path: Path) -> bool:
    """Render MIDI to WAV using FluidSynth with a SoundFont."""
    fluidsynth_bin = Path(FLUIDSYNTH_PATH)
    if not fluidsynth_bin.exists():
        print(f"Warning: FluidSynth not found at {fluidsynth_bin}")
        return False

    sf2_path = Path(SOUNDFONT_PATH)
    if not sf2_path.exists():
        print(f"Warning: SoundFont not found at {sf2_path}")
        return False

    print(f"  Using SoundFont: {sf2_path}")

    cmd = [
        fluidsynth_bin,
        "-ni",
        str(sf2_path),
        str(midi_path),
        "-F",
        str(wav_path),
        "-r",
        "48000",
        "-g",
        "0.7",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  FluidSynth error: {result.stderr[:200]}")
        return False

    return True


def generate_and_render_audio(output_path: Path) -> Path | None:
    """Generate MIDI score and render to WAV with SoundFont."""
    midi_path = output_path.with_suffix('.mid')
    wav_path = output_path.with_suffix('.wav')

    print("  Generating MIDI score...")
    generate_midi_score(midi_path, DURATION)

    print("  Rendering with SoundFont...")
    if render_midi_with_fluidsynth(midi_path, wav_path):
        # Clean up MIDI file
        midi_path.unlink()
        return wav_path
    else:
        # Fallback: keep MIDI, user can render manually
        print("  Falling back to MIDI only")
        return None


# =============================================================================
# VIDEO ENCODING
# =============================================================================

def create_ffmpeg_process(ffmpeg_path: str, video_args: tuple, output_path: Path) -> subprocess.Popen:
    """Create FFmpeg subprocess for piped video encoding."""
    cmd = [
        ffmpeg_path,
        '-y',
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-pix_fmt', 'rgb24',
        '-s', f'{W}x{H}',
        '-r', str(FPS),
        '-i', '-',
        *video_args,
        str(output_path)
    ]

    return subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE
    )


def mux_audio_video(ffmpeg_path: str, video_path: Path, audio_path: Path, output_path: Path) -> None:
    """Combine video and audio into final output."""
    cmd = [
        ffmpeg_path,
        '-y',
        '-i', str(video_path),
        '-i', str(audio_path),
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        str(output_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Mux warning: {result.stderr}")
        # Copy video without audio if mux fails
        import shutil
        shutil.copy(video_path, output_path)


# =============================================================================
# MAIN RENDER
# =============================================================================

def render_film() -> None:
    """Render the complete film with audio."""
    print(f"Interference — {DURATION}s geometric moiré film")
    print(f"Output: {OUTPUT_PATH}")
    print()

    # Use hardcoded FFmpeg path with libx264
    print("[0/3] Setting up encoder...")
    ffmpeg_path = FFMPEG_PATH
    # OPTIMIZED: CRF 28 = web-friendly quality, much smaller files
    video_args = ("-c:v", "libx264", "-preset", "slow", "-crf", "28", "-pix_fmt", "yuv420p")
    print(f"  FFmpeg: {ffmpeg_path}")
    print(f"  Encoder: libx264")
    print()

    # Create output directory
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Temporary paths
    temp_video = OUTPUT_PATH.with_name(OUTPUT_PATH.stem + '_video_only.mp4')
    temp_audio = OUTPUT_PATH.with_suffix('.wav')

    try:
        # Step 1: Render video
        print(f"[1/3] Rendering video ({TOTAL_FRAMES} frames)...")
        ffmpeg = create_ffmpeg_process(ffmpeg_path, video_args, temp_video)

        for frame_num in range(TOTAL_FRAMES):
            frame = render_frame(frame_num)
            ffmpeg.stdin.write(frame.tobytes())

            # Progress every 5 seconds
            if frame_num % (FPS * 5) == 0:
                progress = frame_num / TOTAL_FRAMES * 100
                print(f"  Video: {progress:.0f}%")

        ffmpeg.stdin.close()
        stderr = ffmpeg.stderr.read() if ffmpeg.stderr else b''
        ffmpeg.wait()

        if ffmpeg.returncode != 0:
            print(f"FFmpeg error: {stderr.decode('utf-8', errors='ignore')[:500]}")
            raise RuntimeError(f"Video encoding failed with code {ffmpeg.returncode}")

        print("  Video: 100%")
        print()

        # Step 2: Generate audio
        print("[2/3] Generating audio (MIDI + SoundFont)...")
        wav_path = generate_and_render_audio(OUTPUT_PATH)
        if wav_path:
            print(f"  Audio rendered: {wav_path}")
        else:
            print("  Audio generation failed, will use video only")
        print()

        # Step 3: Mux
        print("[3/3] Combining video and audio...")
        mux_audio_video(ffmpeg_path, temp_video, temp_audio, OUTPUT_PATH)
        print()

        # Get file size
        file_size = OUTPUT_PATH.stat().st_size / (1024 * 1024)
        print(f"Done! {OUTPUT_PATH}")
        print(f"Size: {file_size:.1f} MB")

    finally:
        # Cleanup temp files
        for temp in [temp_video, temp_audio]:
            if temp.exists():
                temp.unlink()


if __name__ == "__main__":
    freeze_support()
    render_film()
