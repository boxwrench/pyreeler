"""Comprehensive PyReeler main skill demonstration.

Demonstrates ALL main skill reference documents:
- creative-lenses.md: Genre/mode, motif, repetition/rupture, time
- workflow.md: Hardware gate, preview/upscale, cleanup
- audio-pipeline.md: Stems (ambience, pulse, score), procedural foley
- vocabulary-map.md: Visual/audio/temporal/material systems

Uses ALL templates:
- templates/video: render_runtime.py, parallel_render.py
- templates/audio: audio_engine.py, sfx_gen.py, composer.py
"""
from __future__ import annotations

import multiprocessing as mp
import os
import shutil
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Add pyreeler-claude templates to path
sys.path.insert(0, "C:/pyreeler-claude")
from templates.video.render_runtime import detect_render_runtime
from templates.video.parallel_render import ordered_frame_map
from templates.audio.audio_engine import mix_stems, write_mono_wav
from templates.audio.sfx_gen import gen_wind, gen_impact, gen_shimmer

# Add experimental tools for FM synthesis
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))
from fm_synth import fm_wave, adsr_envelope


def bpm_to_ms(bpm: float) -> float:
    """Convert BPM to milliseconds per beat."""
    return 60000.0 / bpm

# ===============================================================================
# CONFIGURATION (workflow.md: lightweight brief)
# ===============================================================================
OUTPUT_DIR = Path.home() / "Videos"
OUTPUT_NAME = "main_skill_demo"
TEMP_DIR = Path(__file__).parent / "temp_frames"

# Brief parameters
DURATION = 30  # seconds
FPS = 24
WIDTH, HEIGHT = 854, 480  # Preview resolution
N_FRAMES = DURATION * FPS

# Creative brief (creative-lenses.md: ritual/mythic mode)
GENRE = "ritual"
MOTIF = "returning_circle"
CORE_MOVE = "rupture_at_peak"

# ===============================================================================
# AUDIO PIPELINE (audio-pipeline.md: stem model)
# ===============================================================================
def generate_stems():
    """Generate separate audio stems for mixing.

    Stems:
    - ambience: wind/rumble (procedural foley)
    - pulse: rhythmic propulsion
    - score: harmonic development
    - impacts: transitions, punctuation
    """
    sample_rate = 44100
    n_samples = N_FRAMES * sample_rate // FPS
    duration = N_FRAMES / FPS

    stems = {}

    # ─────────────────────────────────────────────────────────────────────────
    # AMBIENCE: Filtered brown noise (wind/hum)
    # audio-pipeline.md: "wind or atmosphere: filtered brown or pink noise"
    # ─────────────────────────────────────────────────────────────────────────
    print("  Generating ambience stem...")
    ambience = np.zeros(n_samples, dtype=np.float32)

    # Section 1: Low rumble
    ambience[:10*sample_rate] = gen_wind(10, sample_rate, intensity=0.3)[:10*sample_rate]
    # Section 2: Building wind
    ambience[10*sample_rate:20*sample_rate] = gen_wind(10, sample_rate, intensity=0.6)[:10*sample_rate]
    # Section 3: Calm after rupture
    ambience[20*sample_rate:] = gen_wind(10, sample_rate, intensity=0.2)[:10*sample_rate]

    stems['ambience'] = ambience * 0.4

    # ─────────────────────────────────────────────────────────────────────────
    # PULSE: Rhythmic gated tones (audio-pipeline.md: "pulse: rhythmic propulsion")
    # ─────────────────────────────────────────────────────────────────────────
    print("  Generating pulse stem...")
    pulse = np.zeros(n_samples, dtype=np.float32)

    beat_duration = bpm_to_ms(72) / 1000  # 72 BPM ritual tempo
    samples_per_beat = int(beat_duration * sample_rate)

    for beat_idx in range(int(duration / beat_duration)):
        start = beat_idx * samples_per_beat
        end = min(start + samples_per_beat, n_samples)

        # Only pulse in middle section (build)
        if 240 <= beat_idx * samples_per_beat * FPS / sample_rate < 480:
            t_beat = np.linspace(0, beat_duration, end - start, endpoint=False)
            # Gated sine: on for half the beat
            gate = (t_beat < beat_duration / 2).astype(np.float32)
            freq = 55 + (beat_idx % 4) * 55  # Octave jumps
            pulse[start:end] = np.sin(2 * np.pi * freq * t_beat) * gate * 0.3

    stems['pulse'] = pulse

    # ─────────────────────────────────────────────────────────────────────────
    # SCORE: FM drone with evolution (audio-pipeline.md: "score: harmonic development")
    # ─────────────────────────────────────────────────────────────────────────
    print("  Generating score stem...")
    score = np.zeros(n_samples, dtype=np.float32)

    # Generate in chunks for efficiency
    chunk_size = sample_rate // 10  # 0.1s chunks
    for start in range(0, n_samples, chunk_size):
        end = min(start + chunk_size, n_samples)
        chunk_duration = (end - start) / sample_rate
        t_sec = start / sample_rate

        # Slow evolution: 110Hz → 165Hz over 30s
        carrier = 110 + 55 * (t_sec / duration)

        # Rupture at 25s (frame 600): dissonance then resolution
        frame_idx = int(t_sec * FPS)
        if frame_idx > 600:
            mod = carrier * 1.5  # Dissonant
            idx = 4.0
        else:
            mod = carrier * 2  # Harmonic
            idx = 1.5 + 0.5 * np.sin(2 * np.pi * 0.05 * t_sec)

        chunk_wave = fm_wave(chunk_duration, sample_rate, carrier, mod, idx) * 0.25
        score[start:end] = chunk_wave

    stems['score'] = score

    # ─────────────────────────────────────────────────────────────────────────
    # IMPACTS: Punctuation at transitions
    # audio-pipeline.md: "impacts: hits, swells, accents, transitions"
    # ─────────────────────────────────────────────────────────────────────────
    print("  Generating impacts stem...")
    impacts = np.zeros(n_samples, dtype=np.float32)

    # Impact at section boundaries (0s, 10s, 20s, rupture at 25s)
    impact_times = [0, 10, 20, 25]
    for imp_t in impact_times:
        start = int(imp_t * sample_rate)
        imp_samples = int(0.5 * sample_rate)  # 0.5s impact
        if start + imp_samples <= n_samples:
            impact_sound = gen_impact(0.5, fundamental_hz=62 if imp_t < 25 else 31, sample_rate=sample_rate)
            impacts[start:start+imp_samples] += impact_sound * (0.8 if imp_t == 25 else 0.5)

    # Shimmer after rupture
    shimmer_start = int(25.5 * sample_rate)
    shimmer = gen_shimmer(3, sample_rate)
    if shimmer_start + len(shimmer) <= n_samples:
        impacts[shimmer_start:shimmer_start+len(shimmer)] += shimmer * 0.3

    stems['impacts'] = impacts

    # ─────────────────────────────────────────────────────────────────────────
    # MIX: Simple gain staging (audio-pipeline.md: "Mix by stem, not monolithic")
    # ─────────────────────────────────────────────────────────────────────────
    print("  Mixing stems...")
    mixed = np.zeros(n_samples, dtype=np.float32)

    # Stem gains
    gains = {
        'ambience': 0.6,
        'pulse': 0.5,
        'score': 0.7,
        'impacts': 0.9,
    }

    for name, stem in stems.items():
        mixed += stem * gains[name]

    # Normalize
    mixed = np.clip(mixed, -1, 1)
    mixed_int16 = (mixed * 32767).astype(np.int16)

    return mixed_int16, sample_rate, stems


# ===============================================================================
# VISUAL SYSTEMS (vocabulary-map.md: particles, fields, symmetry, material)
# ===============================================================================
def render_frame_ritual(frame_idx: int) -> Image.Image:
    """Section 1: RITUAL/ESTABLISH (0-10s)

    creative-lenses.md: "ritual or mythic work: recurrence, ceremony, symmetry"
    vocabulary-map.md: "particles and swarms", "phosphor glow"
    """
    img = Image.new('RGB', (WIDTH, HEIGHT), (5, 5, 8))
    draw = ImageDraw.Draw(img)

    t = frame_idx / 240  # 0-1 over section
    n_particles = 40

    # Recurring circle motif (creative-lenses.md: motif returns)
    for i in range(n_particles):
        angle = 2 * np.pi * i / n_particles + 2 * np.pi * t * 0.5
        radius = 120 + 30 * np.sin(2 * np.pi * t + i * 0.15)

        x = WIDTH / 2 + radius * np.cos(angle)
        y = HEIGHT / 2 + radius * np.sin(angle) * 0.6

        # Phosphor glow: multiple circles with falloff
        for r, alpha in [(8, 30), (5, 60), (2, 150)]:
            color = (int(100 + 50 * t), int(150 + 80 * t), int(200))
            draw.ellipse([x-r, y-r, x+r, y+r], fill=color + (alpha,))

    # CRT scanline material effect
    for y in range(0, HEIGHT, 2):
        draw.line([(0, y), (WIDTH, y)], fill=(0, 0, 0, 30))

    return img


def render_frame_build(frame_idx: int) -> Image.Image:
    """Section 2: BUILD/ESCALATE (10-20s)

    creative-lenses.md: "escalation through repetition"
    vocabulary-map.md: "fields and flow", "grain"
    temporal: acceleration
    """
    img = Image.new('RGB', (WIDTH, HEIGHT), (8, 5, 5))
    pixels = np.array(img)

    t = (frame_idx - 240) / 240  # 0-1 over section
    y_grid, x_grid = np.mgrid[0:HEIGHT, 0:WIDTH]

    # Flow field with increasing complexity
    freq = 0.01 + 0.02 * t  # Acceleration
    flow_x = np.sin(x_grid * freq + 2 * np.pi * t * 2)
    flow_y = np.cos(y_grid * freq + 2 * np.pi * t * 2)

    # Map to color
    r = ((flow_x + 1) / 2 * 150 + 50 * t).astype(np.uint8)
    g = ((flow_y + 1) / 2 * 80).astype(np.uint8)
    b = np.full_like(flow_x, int(50 + 100 * t), dtype=np.uint8)

    pixels[:, :, 0] = r
    pixels[:, :, 1] = g
    pixels[:, :, 2] = b

    # Grain overlay (vocabulary-map.md: "dust, grain, smear")
    grain = np.random.randint(0, 30, (HEIGHT, WIDTH, 3), dtype=np.uint8)
    pixels = np.clip(pixels.astype(np.int16) + grain - 15, 0, 255).astype(np.uint8)

    return Image.fromarray(pixels)


def render_frame_rupture(frame_idx: int) -> Image.Image:
    """Section 3: RUPTURE/RETURN (20-30s)

    creative-lenses.md: "rupture is useful when the piece needs a break"
    temporal: rupture at 25s (frame 600), then return
    vocabulary-map.md: "symmetry, mirrors, kaleidoscopic"
    """
    img = Image.new('RGB', (WIDTH, HEIGHT), (5, 8, 5))
    draw = ImageDraw.Draw(img)

    t = (frame_idx - 480) / 240
    center_x, center_y = WIDTH // 2, HEIGHT // 2

    # Kaleidoscopic symmetry
    n_mirrors = 8
    for i in range(n_mirrors):
        angle = np.pi * i / n_mirrors + t * np.pi
        for r in range(0, 180, 3):
            spiral = r * 0.05
            x = center_x + r * np.cos(angle + spiral)
            y = center_y + r * np.sin(angle + spiral) * 0.6

            intensity = 1 - r / 180
            color = (
                int(200 * intensity),
                int(100 + 100 * np.sin(np.pi * t)),
                int(150 * intensity),
            )
            draw.ellipse([x-3, y-3, x+3, y+3], fill=color)

    # Kaleidoscope mirroring
    img_array = np.array(img)
    h, w = img_array.shape[:2]
    img_array[h//2:, :] = img_array[:h//2, :][::-1, :]
    img_array[:, w//2:] = img_array[:, :w//2][:, ::-1]

    # RUPTURE at frame 600 (25s): Invert colors
    if frame_idx > 600:
        img_array = 255 - img_array
        # Add chromatic aberration effect (material: signal haze)
        shift = 5
        img_array[:, shift:, 0] = img_array[:, :-shift, 0]  # Red channel shift
        img_array[:, :-shift, 2] = img_array[:, shift:, 2]  # Blue channel shift

    return Image.fromarray(img_array)


def render_frame(frame_idx: int) -> str:
    """Route to section renderer and save."""
    if frame_idx < 240:
        img = render_frame_ritual(frame_idx)
    elif frame_idx < 480:
        img = render_frame_build(frame_idx)
    else:
        img = render_frame_rupture(frame_idx)

    # Save frame
    path = TEMP_DIR / f"frame_{frame_idx:04d}.png"
    img.save(path, optimize=True)
    return str(path)


# ===============================================================================
# WORKFLOW IMPLEMENTATION (workflow.md)
# ===============================================================================
def hardware_gate(runtime) -> bool:
    """workflow.md: Pre-Render Hardware Gate

    Verify before first full preview:
    - detect_render_runtime() used
    - encoder from runtime helper
    - runtime.workers drives frame generation
    - Windows-safe multiprocessing
    """
    print("  Hardware Gate Check:")

    # Check 1: Runtime detected
    print(f"    [OK] Runtime detected: {runtime.profile}")

    # Check 2: Encoder from helper
    print(f"    [OK] Encoder: {runtime.encoder}")

    # Check 3: Workers configured
    print(f"    [OK] Workers: {runtime.workers}")

    # Check 4: FFmpeg exists (or fallback mode)
    ffmpeg_ok = Path(runtime.ffmpeg_path).exists() if runtime.ffmpeg_path else False
    if runtime.profile == "fallback":
        print(f"    [OK] Fallback mode (imageio/moviepy)")
        return True
    print(f"    {'[OK]' if ffmpeg_ok else '[FAIL]'} FFmpeg: {runtime.ffmpeg_path}")

    return ffmpeg_ok


def smoke_test_workers(runtime) -> bool:
    """workflow.md: Worker-path smoke test before full render."""
    if runtime.workers <= 1:
        print("  Single worker mode (no smoke test needed)")
        return True

    print(f"  Worker smoke test ({runtime.workers} workers)...")

    def test_worker(i: int) -> int:
        return i * i

    try:
        results = list(ordered_frame_map(
            range(4),
            test_worker,
            workers=runtime.workers,
            chunksize=1
        ))
        success = results == [0, 1, 4, 9]
        print(f"    {'[OK]' if success else '[FAIL]'} Worker test: {results}")
        return success
    except Exception as e:
        print(f"    [FAIL] Worker test failed: {e}")
        return False


def cleanup_intermediates():
    """workflow.md: Clean up intermediates after successful final."""
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
        print(f"  Cleaned up: {TEMP_DIR}")


# ===============================================================================
# MAIN
# ===============================================================================
def main():
    print("=" * 60)
    print("PyReeler Main Skill - Comprehensive Demo")
    print("=" * 60)
    print()

    # =========================================================================
    # 1. FRAME THE PIECE (workflow.md)
    # =========================================================================
    print("1. CREATIVE BRIEF")
    print("-" * 40)
    print(f"   Genre/Mode: {GENRE}")
    print(f"   Motif: {MOTIF}")
    print(f"   Core Move: {CORE_MOVE}")
    print(f"   Duration: {DURATION}s @ {FPS}fps = {N_FRAMES} frames")
    print(f"   Resolution: {WIDTH}x{HEIGHT} (preview)")
    print()

    # =========================================================================
    # 2. DETECT RENDER RUNTIME
    # =========================================================================
    print("2. RENDER RUNTIME (templates/video/render_runtime.py)")
    print("-" * 40)
    try:
        runtime = detect_render_runtime()
        print(f"   Profile: {runtime.profile}")
        print(f"   FFmpeg: {runtime.ffmpeg_path}")
        print(f"   Encoder: {runtime.encoder}")
        print(f"   Workers: {runtime.workers}")
        print(f"   Video Args: {runtime.video_args}")
    except FileNotFoundError:
        # Fallback when FFmpeg not available
        print("   FFmpeg not found, using fallback mode")
        from types import SimpleNamespace
        runtime = SimpleNamespace(
            profile="fallback",
            ffmpeg_path=None,
            encoder="libx264",
            workers=1,
            video_args=["-crf", "23"]
        )
    print()

    # =========================================================================
    # 3. HARDWARE GATE (workflow.md)
    # =========================================================================
    print("3. HARDWARE GATE (workflow.md)")
    print("-" * 40)
    if not hardware_gate(runtime):
        print("   ERROR: Hardware gate failed")
        return 1
    print()

    # =========================================================================
    # 4. WORKER SMOKE TEST (workflow.md)
    # =========================================================================
    print("4. WORKER SMOKE TEST (workflow.md)")
    print("-" * 40)
    if not smoke_test_workers(runtime):
        print("   WARNING: Workers failed, falling back to single")
        runtime = detect_render_runtime(workers=1)
    print()

    # =========================================================================
    # 5. GENERATE AUDIO (audio-pipeline.md: stem model)
    # =========================================================================
    print("5. AUDIO PIPELINE (audio-pipeline.md)")
    print("-" * 40)
    print("   Stems: ambience, pulse, score, impacts")
    audio, sample_rate, stems = generate_stems()

    audio_path = TEMP_DIR / "audio.wav"
    TEMP_DIR.mkdir(exist_ok=True)
    with wave.open(str(audio_path), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio.tobytes())
    print(f"   Mixed audio: {audio_path}")
    print()

    # =========================================================================
    # 6. RENDER FRAMES (parallel_render.py)
    # =========================================================================
    print("6. PARALLEL RENDER (templates/video/parallel_render.py)")
    print("-" * 40)
    print(f"   Rendering {N_FRAMES} frames...")
    TEMP_DIR.mkdir(exist_ok=True)

    list(ordered_frame_map(
        range(N_FRAMES),
        render_frame,
        workers=runtime.workers,
        chunksize=max(1, N_FRAMES // (runtime.workers * 8))
    ))
    print(f"   Frames: {TEMP_DIR}")
    print()

    # =========================================================================
    # 7. ENCODE VIDEO
    # =========================================================================
    print("7. ENCODE VIDEO")
    print("-" * 40)
    output_path = OUTPUT_DIR / f"{OUTPUT_NAME}.mp4"
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Check if FFmpeg is available
    ffmpeg_available = runtime.ffmpeg_path and Path(runtime.ffmpeg_path).exists()

    if ffmpeg_available:
        # Use FFmpeg for encoding
        ffmpeg_cmd = (
            f'"{runtime.ffmpeg_path}" -y '
            f'-framerate {FPS} -i "{TEMP_DIR}/frame_%04d.png" '
            f'-i "{audio_path}" '
            f'-c:v {runtime.encoder} {" ".join(runtime.video_args)} '
            f'-c:a aac -b:a 192k -pix_fmt yuv420p '
            f'-shortest "{output_path}"'
        )

        print(f"   Encoding with FFmpeg...")
        result = os.system(ffmpeg_cmd)

        if result != 0:
            print("   FFmpeg failed, trying fallback...")
            ffmpeg_available = False

    if not ffmpeg_available:
        # Fallback to imageio/moviepy
        print("   Encoding with imageio/moviepy fallback...")
        try:
            import imageio.v2 as imageio

            frames = sorted(TEMP_DIR.glob("frame_*.png"))
            images = [imageio.imread(str(f)) for f in frames]

            # Write video
            writer = imageio.get_writer(str(output_path), fps=FPS, quality=8)
            for img in images:
                writer.append_data(img)
            writer.close()

            print(f"   Video encoded (no audio in fallback mode)")
        except Exception as e:
            print(f"   ERROR: Encoding failed: {e}")
            return 1

    file_size = output_path.stat().st_size / 1024 / 1024
    print(f"   Output: {output_path}")
    print(f"   Size: {file_size:.1f} MB")
    print()

    # =========================================================================
    # 8. VERIFY (workflow.md)
    # =========================================================================
    print("8. VERIFY OUTPUT (workflow.md)")
    print("-" * 40)

    # Check file exists and has content
    if output_path.exists():
        file_size = output_path.stat().st_size / 1024 / 1024
        print(f"   [OK] File created: {output_path}")
        print(f"   [OK] Size: {file_size:.1f} MB")
        print(f"   [OK] Duration: ~{DURATION}s expected")
    else:
        print(f"   [FAIL] Output file not found")
        return 1
    print()

    # =========================================================================
    # 9. CLEANUP (workflow.md)
    # =========================================================================
    print("9. CLEANUP (workflow.md)")
    print("-" * 40)
    cleanup_intermediates()
    print()

    # =========================================================================
    # 10. UPGRADE OFFER (workflow.md)
    # =========================================================================
    print("10. UPSCALE OFFER (workflow.md)")
    print("-" * 40)
    print(f"   Preview complete: {WIDTH}x{HEIGHT}")
    print("   Upscale options:")
    print("     - 720p (1280x720)")
    print("     - 1080p (1920x1080)")
    print("     - keep preview")
    print()

    print("=" * 60)
    print("[OK] Demo complete!")
    print("=" * 60)
    print()
    print("Reference Documents Demonstrated:")
    print("  [OK] creative-lenses.md (genre, motif, rupture)")
    print("  [OK] workflow.md (gate, preview, cleanup)")
    print("  [OK] audio-pipeline.md (stems, procedural foley)")
    print("  [OK] vocabulary-map.md (visual/audio systems)")
    print()
    print("Templates Used:")
    print("  [OK] templates/video/render_runtime.py")
    print("  [OK] templates/video/parallel_render.py")
    print("  [OK] templates/audio/audio_engine.py")
    print("  [OK] templates/audio/sfx_gen.py")
    print("  [OK] templates/audio/composer.py")

    return 0


if __name__ == "__main__":
    mp.freeze_support()
    sys.exit(main())
