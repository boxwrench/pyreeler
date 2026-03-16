#!/usr/bin/env python3
"""PyReeler Experimental Sampler - 60 second technique demonstration.

Demonstrates 4 visual techniques and 4 audio techniques, 5 seconds each.
Audio and video are interleaved for efficiency - not strictly paired.

Timeline:
0-5s:   Lorenz Attractor (orbit) + FM Bell (A=880Hz)
5-10s:  Same attractor + FM Brass Swell
10-15s: Bytebeat Glitch Rhythm + Same attractor
15-20s: Same bytebeat + FM Drone starts (layered)
20-25s: Reaction-Diffusion Coral Growth + Drone continues
25-30s: Same RD + FM Brass Swell (build)
30-35s: Rössler Attractor (orbit) + Bytebeat Melodic
35-40s: Same Rössler + FM Woodwind
40-45s: Lorenz Parameter Drift + FM Drone (deep)
45-50s: Same drift + Brass Swell (climax)
50-55s: Particle Cloud + Glitch Texture
55-60s: All techniques fade / resolution

Usage:
    python sampler_demo.py

Output:
    ~/Videos/experimental_sampler.mp4
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "tools"))

from fm_synth import fm_wave, adsr_envelope, bell_tone, brass_tone, woodwind_tone
from attractors import generate_lorenz, generate_rossler, render_frame, RenderMonitor, RenderTimeoutError

# =============================================================================
# CONFIGURATION
# =============================================================================

OUTPUT_PATH = Path(os.path.expanduser("~/Videos/experimental_sampler.mp4"))
FPS = 24
SEGMENT_DURATION = 5  # seconds per technique
NUM_SEGMENTS = 12
TOTAL_DURATION = 60  # Full 60 seconds with vectorized renderer
NUM_SEGMENTS = 12    # 0-60s
TOTAL_FRAMES = FPS * TOTAL_DURATION

W, H = 854, 480  # 480p for faster rendering
CANVAS_W, CANVAS_H = 1067, 600  # 1.25x viewport for camera movement

FFMPEG_PATH = r"C:\pinokio\bin\miniconda\Library\bin\ffmpeg.exe"

# =============================================================================
# PRECOMPUTED TRAJECTORIES (Computed once at startup)
# =============================================================================

class TrajectoryCache:
    """Cache for all precomputed attractor trajectories."""
    lorenz_main = None      # 0-15s: Main Lorenz orbit
    rossler_main = None     # 30-40s: Rössler orbit
    lorenz_drift = None     # 40-50s: List of trajectories with different rho
    particle_cloud = None   # 50-55s: Dense particle cloud


def precompute_all_trajectories():
    """Precompute all attractor trajectories before rendering.

    This separates simulation from rendering - solve ODEs once, then just
    index into cached data during frame generation.
    """
    from attractors import check_render_safety

    print("  Precomputing Lorenz main trajectory (0-15s)...")
    TrajectoryCache.lorenz_main = generate_lorenz(
        n_points=3000, n_particles=30, sigma=10, rho=28, beta=8/3, dt=0.01
    )
    check_render_safety(360, 30, 400, W, H)

    print("  Precomputing Rössler trajectory (30-40s)...")
    TrajectoryCache.rossler_main = generate_rossler(
        n_points=3000, n_particles=30, a=0.2, b=0.2, c=5.7, dt=0.01
    )
    check_render_safety(240, 30, 400, W, H)

    print("  Precomputing Lorenz drift trajectories (40-50s)...")
    # Precompute 6 trajectories with rho from 28 to 40
    TrajectoryCache.lorenz_drift = [
        generate_lorenz(n_points=1000, n_particles=20, sigma=10, rho=28 + i * 2.4, beta=8/3, dt=0.01)
        for i in range(6)
    ]
    check_render_safety(240, 20, 200, W, H)

    print("  Precomputing particle cloud trajectory (50-60s)...")
    # REDUCED: 100 particles instead of 200 for vectorized performance
    TrajectoryCache.particle_cloud = generate_lorenz(
        n_points=2000, n_particles=100, sigma=10, rho=28, beta=8/3, dt=0.01
    )
    check_render_safety(240, 100, 100, W, H)

    print("  All trajectories cached.")


# =============================================================================
# VISUAL SEGMENTS
# =============================================================================

def render_lorenz_orbit(frame: int, total_frames: int) -> Image.Image:
    """0-15s: Lorenz attractor with slow orbit."""
    angle = 2 * np.pi * frame / (FPS * 15)  # Full rotation over 15s
    return render_frame(TrajectoryCache.lorenz_main, frame, FPS * 15, W, H,
                       trail_length=400, brightness=0.4)


def render_rossler_orbit(frame: int, total_frames: int) -> Image.Image:
    """30-40s: Rössler attractor orbit."""
    segment_frame = frame - (30 * FPS)
    return render_frame(TrajectoryCache.rossler_main, segment_frame, FPS * 10, W, H,
                       trail_length=400, brightness=0.5)


def render_lorenz_drift(frame: int, total_frames: int) -> Image.Image:
    """40-50s: Lorenz with parameter drift."""
    segment_frame = frame - (40 * FPS)
    t = segment_frame / (FPS * 10)

    # Select precomputed trajectory based on time (0-5)
    traj_idx = min(int(t * 6), 5)
    trajectory = TrajectoryCache.lorenz_drift[traj_idx]

    # Index into trajectory (loop if needed)
    frame_idx = segment_frame % trajectory.shape[0]

    return render_frame(trajectory, frame_idx, trajectory.shape[0], W, H,
                       trail_length=200, brightness=0.5)


def render_particle_cloud(frame: int, total_frames: int) -> Image.Image:
    """50-60s: Dense particle cloud (100 particles, vectorized)."""
    segment_frame = frame - (50 * FPS)

    # Shorter trails = more chaotic
    # 100 particles instead of 200 for performance (vectorized handles it well)
    return render_frame(TrajectoryCache.particle_cloud, segment_frame, FPS * 10, W, H,
                       trail_length=100, brightness=0.15)


def render_rd_coral(frame: int, total_frames: int) -> Image.Image:
    """20-30s: Reaction-diffusion coral growth."""
    # Simplified RD approximation using noise patterns
    # (Full RD would require scipy, keeping this lightweight)
    segment_frame = frame - (20 * FPS)
    t = segment_frame / (FPS * 10)

    # Create evolving pattern
    img = np.zeros((H, W), dtype=np.uint8)

    # Generate branching pattern with sine waves
    y, x = np.ogrid[:H, :W]
    center_y, center_x = H // 2, W // 2

    # Distance from center
    dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
    angle = np.arctan2(y - center_y, x - center_x)

    # Branching pattern
    pattern = np.sin(angle * 5 + dist * 0.02 - t * 4) * \
              np.cos(angle * 3 + t * 2) * \
              np.exp(-dist / (300 + t * 100))

    # Normalize and convert
    img = ((pattern - pattern.min()) / (pattern.max() - pattern.min()) * 255).astype(np.uint8)

    return Image.fromarray(img, 'L').convert('RGB')


def render_title_card(frame: int, text: str, subtext: str = "") -> Image.Image:
    """Render a title card with technique name."""
    img = Image.new('RGB', (W, H), (10, 10, 15))
    draw = ImageDraw.Draw(img)

    # Try to use a nice font, fall back to default
    try:
        font_large = ImageFont.truetype("consola.ttf", 48)
        font_small = ImageFont.truetype("consola.ttf", 24)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Center text
    bbox = draw.textbbox((0, 0), text, font=font_large)
    text_width = bbox[2] - bbox[0]
    x = (W - text_width) // 2
    y = H // 2 - 30

    draw.text((x, y), text, fill=(0, 255, 100), font=font_large)

    if subtext:
        bbox2 = draw.textbbox((0, 0), subtext, font=font_small)
        text_width2 = bbox2[2] - bbox2[0]
        x2 = (W - text_width2) // 2
        draw.text((x2, y + 60), subtext, fill=(100, 200, 100), font=font_small)

    return img


def render_segment(frame: int, total_frames: int = TOTAL_FRAMES) -> Image.Image:
    """Route to appropriate visual segment."""
    second = frame // FPS

    if second < 15:
        return render_lorenz_orbit(frame, total_frames)
    elif second < 20:
        return render_rd_coral(frame, total_frames)
    elif second < 30:
        return render_rd_coral(frame, total_frames)
    elif second < 40:
        return render_rossler_orbit(frame, total_frames)
    elif second < 50:
        return render_lorenz_drift(frame, total_frames)
    elif second < 55:
        return render_particle_cloud(frame, total_frames)
    else:
        # Fade to black
        return Image.new('RGB', (W, H), (0, 0, 0))


# =============================================================================
# AUDIO GENERATION
# =============================================================================

def generate_audio_segment(
    start_sec: float,
    duration: float,
    sample_rate: int = 48000
) -> np.ndarray:
    """Generate audio for a 5-second segment."""
    samples = int(duration * sample_rate)
    audio = np.zeros(samples, dtype=np.float32)

    # Determine which audio technique based on start time
    if start_sec < 5:
        # FM Bell (A=880Hz)
        audio = bell_tone(duration, sample_rate, freq=880, index=3.0)
        audio *= 0.7

    elif start_sec < 10:
        # FM Brass Swell
        audio = brass_tone(duration, sample_rate, freq=220, index=5.0)
        audio *= 0.6

    elif start_sec < 15:
        # Bytebeat Glitch
        t = np.arange(samples) + int(start_sec * sample_rate)
        byte_audio = (t * (t >> 8 | t >> 9) & 46 & t >> 8) & 255
        audio = ((byte_audio - 128) / 128).astype(np.float32)
        # Filter slightly
        for i in range(1, len(audio)):
            audio[i] = audio[i-1] * 0.3 + audio[i] * 0.7
        audio *= 0.3

    elif start_sec < 20:
        # Bytebeat + FM Drone layer
        t = np.arange(samples) + int(start_sec * sample_rate)
        byte_audio = (t * (t >> 8 | t >> 9) & 46 & t >> 8) & 255
        glitch = ((byte_audio - 128) / 128).astype(np.float32)
        for i in range(1, len(glitch)):
            glitch[i] = glitch[i-1] * 0.3 + glitch[i] * 0.7

        drone = fm_wave(duration, sample_rate, 110, 110, 1.2)
        env = adsr_envelope(duration, sample_rate, 2.0, 3.0, 0.8, 5.0)
        drone = drone * env

        audio = glitch * 0.2 + drone * 0.5

    elif start_sec < 25:
        # FM Drone continues
        audio = fm_wave(duration, sample_rate, 110, 110, 1.0)
        env = adsr_envelope(duration, sample_rate, 0.5, 1.0, 0.9, 5.0)
        audio = audio * env * 0.5

    elif start_sec < 30:
        # FM Brass Build
        audio = brass_tone(duration, sample_rate, freq=330, index=6.0)
        audio *= 0.7

    elif start_sec < 35:
        # Bytebeat Melodic
        t = np.arange(samples) + int(start_sec * sample_rate)
        byte_audio = ((t * (t >> 5 | t >> 8)) >> (t >> 16)) & 255
        audio = ((byte_audio - 128) / 128).astype(np.float32)
        # Stronger filter for melodic quality
        for i in range(1, len(audio)):
            audio[i] = audio[i-1] * 0.5 + audio[i] * 0.5
        audio *= 0.4

    elif start_sec < 40:
        # FM Woodwind
        audio = woodwind_tone(duration, sample_rate, freq=330, index=2.0)
        audio *= 0.6

    elif start_sec < 45:
        # FM Drone (deep)
        audio = fm_wave(duration, sample_rate, 55, 55, 1.5)
        env = adsr_envelope(duration, sample_rate, 3.0, 5.0, 0.9, 5.0)
        audio = audio * env * 0.5

    elif start_sec < 50:
        # Brass Swell (climax)
        audio = brass_tone(duration, sample_rate, freq=440, index=6.0)
        audio *= 0.8

    elif start_sec < 55:
        # Glitch Texture
        t = np.arange(samples) + int(start_sec * sample_rate)
        byte_audio = (t * 5 & t >> 7) | (t * 3 & t >> 10) & 255
        audio = ((byte_audio - 128) / 128).astype(np.float32)
        for i in range(1, len(audio)):
            audio[i] = audio[i-1] * 0.4 + audio[i] * 0.6
        audio *= 0.25

    else:
        # Fade to silence
        audio = np.zeros(samples, dtype=np.float32)

    return audio


def generate_full_audio(duration: float = TOTAL_DURATION, sample_rate: int = 48000) -> np.ndarray:
    """Generate complete audio track."""
    print("  Generating audio...")
    segments = []

    for sec in range(0, int(duration), SEGMENT_DURATION):
        seg_duration = min(SEGMENT_DURATION, duration - sec)
        segment = generate_audio_segment(float(sec), seg_duration, sample_rate)
        segments.append(segment)

    return np.concatenate(segments)


# =============================================================================
# RENDER
# =============================================================================

def render():
    """Render the complete sampler film (sequential for stability)."""
    print(f"Experimental Sampler - {TOTAL_DURATION}s technique demonstration")
    print(f"Resolution: {W}x{H} (480p)")
    print(f"Output: {OUTPUT_PATH}")
    print()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Generate audio first
    print("[1/3] Generating audio...")
    audio = generate_full_audio()
    print(f"  Audio: {len(audio)/48000:.1f}s")
    print()

    # Save audio temp
    audio_path = OUTPUT_PATH.with_suffix('.wav')
    audio_int16 = (audio * 32767).astype(np.int16)
    audio_path.write_bytes(audio_int16.tobytes())

    # Convert to proper WAV
    wav_path = OUTPUT_PATH.with_name('temp_audio.wav')
    cmd = [
        FFMPEG_PATH, '-y',
        '-f', 's16le', '-ar', '48000', '-ac', '1',
        '-i', str(audio_path),
        str(wav_path)
    ]
    subprocess.run(cmd, capture_output=True)
    audio_path.unlink()

    # Render video - write frames to disk first (reliable but slower)
    print("[2/3] Rendering video...")

    frames_dir = OUTPUT_PATH.with_name('frames')
    frames_dir.mkdir(exist_ok=True)

    # Precompute all trajectories (separate simulation from rendering)
    precompute_all_trajectories()
    print(f"  Rendering {TOTAL_FRAMES} frames to disk...")

    # Sequential frame generation with monitoring
    monitor = RenderMonitor(TOTAL_FRAMES, timeout_seconds=120)  # 2 min max
    monitor.start()

    try:
        for frame_num in range(TOTAL_FRAMES):
            monitor.check_frame(frame_num)  # Will raise RenderTimeoutError if exceeded
            frame = render_segment(frame_num)
            frame.save(frames_dir / f'frame_{frame_num:05d}.png')

            if frame_num % (FPS * 5) == 0:  # Progress every 5 seconds
                print(f"  {monitor.get_progress_str(frame_num)}")

        print("  100%")
    except RenderTimeoutError as e:
        print()
        print(f"  RENDER TIMEOUT: {e}")
        print("  This segment may be too intensive. Try:")
        print("    - Reducing particles (try 50 instead of 100)")
        print("    - Reducing trail_length (try 50 instead of 100)")
        print("    - Lowering resolution (try 640x360)")
        raise
    print()

    # Encode from disk
    print("  Encoding video...")
    video_path = OUTPUT_PATH.with_name('temp_video.mp4')
    cmd = [
        FFMPEG_PATH, '-y',
        '-framerate', str(FPS),
        '-i', str(frames_dir / 'frame_%05d.png'),
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
        '-pix_fmt', 'yuv420p',
        str(video_path)
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        print(f"  FFmpeg error: {result.stderr.decode()[:200]}")
    print()

    # Mux
    print("[3/3] Combining...")
    cmd = [
        FFMPEG_PATH, '-y',
        '-i', str(video_path),
        '-i', str(wav_path),
        '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
        '-shortest',
        str(OUTPUT_PATH)
    ]
    subprocess.run(cmd, capture_output=True)

    # Cleanup
    video_path.unlink()
    wav_path.unlink()
    import shutil
    shutil.rmtree(frames_dir, ignore_errors=True)

    file_size = OUTPUT_PATH.stat().st_size / (1024 * 1024)
    print(f"Done! {OUTPUT_PATH}")
    print(f"Size: {file_size:.1f} MB")
    print()
    print("Segments:")
    print("  0-15s:  Lorenz Attractor + FM Bell/Brass/Glitch")
    print("  15-20s: Bytebeat + FM Drone (layered)")
    print("  20-30s: RD Coral Growth + Drone/Brass")
    print("  30-40s: Rössler Attractor + Bytebeat/Woodwind")
    print("  40-50s: Lorenz Drift + FM Drone/Brass (climax)")
    print("  50-60s: Particle Cloud + Glitch / Fade (vectorized)")


if __name__ == "__main__":
    render()
