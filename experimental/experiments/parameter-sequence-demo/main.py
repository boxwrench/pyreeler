"""ParameterSequence Demo Film - Cross-Domain Parameter Automation

Demonstrates ParameterSequence driving both visual (attractors) and audio (FM)
techniques simultaneously. One sequence file, multiple domains.

Structure: 4 segments × 15 seconds = 60 seconds total
- 0-15s:  Lorenz + FM Bell    (Cosmic birth)
- 15-30s: Rössler + FM Drone  (Deep orbit)
- 30-45s: Lorenz + FM Drone   (Chaos returns)
- 45-60s: Rössler + FM Bell   (Resolution)

Run: python experiments/parameter-sequence-demo/main.py
"""
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

# Add experimental tools to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from attractors import (
    generate_lorenz,
    generate_rossler,
    render_frame,
    estimate_render_time,
    check_safety,
)
from fm_synth import fm_wave, adsr_envelope, mix_stems
from parameter_sequence import ParameterSequence

# ============================================================================
# FILM CONFIGURATION
# ============================================================================

FPS = 24
DURATION = 60  # seconds
TOTAL_FRAMES = FPS * DURATION
WIDTH, HEIGHT = 854, 480
SAMPLE_RATE = 48000

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================================
# PARAMETER SEQUENCES - Narrative Arc
# ============================================================================

def create_sequences():
    """Define parameter curves for all techniques."""

    # --- Lorenz Attractor (0-15s and 30-45s) ---
    lorenz_seq = ParameterSequence()
    # Trail length: short trails → long trails → short
    lorenz_seq.record(0, 'trail_length', 100)
    lorenz_seq.record(15 * FPS, 'trail_length', 400)
    lorenz_seq.record(30 * FPS, 'trail_length', 400)
    lorenz_seq.record(45 * FPS, 'trail_length', 100)
    # Particle count: sparse → dense → sparse
    lorenz_seq.record(0, 'n_particles', 30)
    lorenz_seq.record(20 * FPS, 'n_particles', 80)
    lorenz_seq.record(40 * FPS, 'n_particles', 30)
    # Camera zoom: wide → close → wide
    lorenz_seq.record(0, 'zoom', 0.8)
    lorenz_seq.record(25 * FPS, 'zoom', 1.5)
    lorenz_seq.record(50 * FPS, 'zoom', 0.8)

    # --- Rössler Attractor (15-30s and 45-60s) ---
    rossler_seq = ParameterSequence()
    # Trail length: smooth build
    rossler_seq.record(15 * FPS, 'trail_length', 200)
    rossler_seq.record(30 * FPS, 'trail_length', 600)
    rossler_seq.record(45 * FPS, 'trail_length', 200)
    rossler_seq.record(60 * FPS, 'trail_length', 400)
    # Step size: slow evolution → fast → slow
    rossler_seq.record(15 * FPS, 'step_size', 0.01)
    rossler_seq.record(22 * FPS, 'step_size', 0.03)
    rossler_seq.record(38 * FPS, 'step_size', 0.015)
    rossler_seq.record(55 * FPS, 'step_size', 0.025)
    # Brightness: dim → bright → dim
    rossler_seq.record(15 * FPS, 'brightness', 0.5)
    rossler_seq.record(35 * FPS, 'brightness', 1.0)
    rossler_seq.record(50 * FPS, 'brightness', 0.7)

    # --- FM Bell (0-15s and 45-60s) ---
    bell_seq = ParameterSequence()
    # Modulation index: pure → complex → pure
    bell_seq.record(0, 'index', 0.5)
    bell_seq.record(10 * FPS, 'index', 4.0)
    bell_seq.record(20 * FPS, 'index', 2.0)
    bell_seq.record(50 * FPS, 'index', 3.0)
    bell_seq.record(60 * FPS, 'index', 0.5)
    # Carrier frequency: ascending arc
    bell_seq.record(0, 'carrier', 220)
    bell_seq.record(15 * FPS, 'carrier', 440)
    bell_seq.record(45 * FPS, 'carrier', 330)
    bell_seq.record(60 * FPS, 'carrier', 220)

    # --- FM Drone (15-30s and 30-45s) ---
    drone_seq = ParameterSequence()
    # Modulation ratio: harmonic drift
    drone_seq.record(15 * FPS, 'ratio', 1.0)
    drone_seq.record(25 * FPS, 'ratio', 1.5)
    drone_seq.record(35 * FPS, 'ratio', 2.0)
    drone_seq.record(45 * FPS, 'ratio', 1.0)
    # Index: subtle → intense → subtle
    drone_seq.record(15 * FPS, 'index', 1.0)
    drone_seq.record(30 * FPS, 'index', 5.0)
    drone_seq.record(45 * FPS, 'index', 2.0)
    # Base frequency: low rumble
    drone_seq.record(15 * FPS, 'carrier', 55)
    drone_seq.record(30 * FPS, 'carrier', 65)
    drone_seq.record(45 * FPS, 'carrier', 55)

    return lorenz_seq, rossler_seq, bell_seq, drone_seq


# ============================================================================
# PRECOMPUTATION STRATEGY
# ============================================================================

def precompute_attractors(lorenz_seq, rossler_seq):
    """Precompute all attractor trajectories upfront."""
    print("Precomputing attractor trajectories...")
    start = time.time()

    # Get max particles needed across all frames
    max_lorenz_particles = max(
        int(lorenz_seq.get_value(f, 'n_particles', 30))
        for f in range(TOTAL_FRAMES)
    )
    max_rossler_particles = 50  # Fixed for Rössler

    # Lorenz trajectory (used at 0-15s and 30-45s)
    lorenz_traj = generate_lorenz(
        n_points=5000,
        n_particles=max_lorenz_particles,
        sigma=10.0,
        rho=28.0,
        beta=8/3,
        dt=0.01
    )

    # Rössler trajectory (used at 15-30s and 45-60s)
    rossler_traj = generate_rossler(
        n_points=6000,
        n_particles=max_rossler_particles,
        a=0.2,
        b=0.2,
        c=5.7,
        dt=0.01
    )

    elapsed = time.time() - start
    print(f"  Lorenz: {max_lorenz_particles} particles, 5000 points")
    print(f"  Rössler: {max_rossler_particles} particles, 6000 points")
    print(f"  Precompute time: {elapsed:.1f}s")

    return lorenz_traj, rossler_traj


def render_frame_with_params(trajectory, frame, seq, default_params):
    """Render a single frame with parameters from sequence."""
    params = {
        'trail_length': int(seq.get_value(frame, 'trail_length', default_params['trail_length'])),
        'n_particles': int(seq.get_value(frame, 'n_particles', default_params.get('n_particles', 50))),
        'step_size': seq.get_value(frame, 'step_size', 0.01),
        'brightness': seq.get_value(frame, 'brightness', 1.0),
    }

    # Use actual particle count from params (may be less than precomputed)
    n_particles = params['n_particles']
    traj_subset = trajectory[:, :n_particles, :]

    img = render_frame(
        traj_subset,
        frame_num=frame,
        total_frames=TOTAL_FRAMES,
        width=WIDTH,
        height=HEIGHT,
        trail_length=params['trail_length'],
        zoom=seq.get_value(frame, 'zoom', 1.0),
    )

    # Apply brightness
    img_array = np.array(img).astype(np.float32)
    img_array *= params['brightness']
    img_array = np.clip(img_array, 0, 255).astype(np.uint8)

    return Image.fromarray(img_array)


# ============================================================================
# AUDIO GENERATION
# ============================================================================

def generate_audio_segment(seq, duration, is_drone=True):
    """Generate audio using parameter sequence."""
    samples_needed = int(duration * SAMPLE_RATE)
    samples_per_frame = SAMPLE_RATE // FPS

    all_samples = []

    for frame_offset in range(int(duration * FPS)):
        frame = frame_offset  # Will be adjusted by caller

        if is_drone:
            carrier = seq.get_value(frame, 'carrier', 55)
            ratio = seq.get_value(frame, 'ratio', 1.0)
            index = seq.get_value(frame, 'index', 2.0)

            modulator = carrier * ratio
            wave = fm_wave(
                duration=1.0/FPS,
                sample_rate=SAMPLE_RATE,
                carrier=carrier,
                modulator=modulator,
                index=index
            )

            # Drone envelope - long sustain
            env = adsr_envelope(
                duration=1.0/FPS,
                sample_rate=SAMPLE_RATE,
                attack=0.05,
                decay=0.1,
                sustain=0.8,
                release=0.1
            )
        else:
            carrier = seq.get_value(frame, 'carrier', 220)
            index = seq.get_value(frame, 'index', 2.0)
            modulator = carrier * 1.4  # Fixed ratio for bell

            wave = fm_wave(
                duration=1.0/FPS,
                sample_rate=SAMPLE_RATE,
                carrier=carrier,
                modulator=modulator,
                index=index
            )

            # Bell envelope - sharp attack, quick decay
            env = adsr_envelope(
                duration=1.0/FPS,
                sample_rate=SAMPLE_RATE,
                attack=0.001,
                decay=0.3,
                sustain=0.1,
                release=1.5
            )

        frame_audio = wave * env
        all_samples.append(frame_audio)

    return np.concatenate(all_samples)[:samples_needed]


# ============================================================================
# MAIN RENDER LOOP
# ============================================================================

def main():
    print("=" * 60)
    print("ParameterSequence Demo Film")
    print("4 Techniques | Moderate Complexity | 60 Seconds")
    print("=" * 60)

    # Create parameter sequences
    lorenz_seq, rossler_seq, bell_seq, drone_seq = create_sequences()

    # Save sequences for inspection
    seq_dir = OUTPUT_DIR / "sequences"
    seq_dir.mkdir(exist_ok=True)
    lorenz_seq.save(seq_dir / "lorenz.json")
    rossler_seq.save(seq_dir / "rossler.json")
    bell_seq.save(seq_dir / "bell.json")
    drone_seq.save(seq_dir / "drone.json")
    print(f"\nSequences saved to: {seq_dir}")

    # Safety check
    print("\n--- Safety Check ---")
    est_time = estimate_render_time(TOTAL_FRAMES, 80, 400, WIDTH, HEIGHT)
    print(f"Estimated render time: {est_time:.0f}s")

    if est_time > 300:
        print("WARNING: Render may take >5 minutes. Consider reducing quality.")
        response = input("Continue? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            return

    # Precompute attractors
    print("\n--- Precomputation ---")
    lorenz_traj, rossler_traj = precompute_attractors(lorenz_seq, rossler_seq)

    # Render video frames
    print("\n--- Rendering Video ---")
    frames_dir = OUTPUT_DIR / "frames"
    frames_dir.mkdir(exist_ok=True)

    render_start = time.time()

    for frame in range(TOTAL_FRAMES):
        if frame % FPS == 0:
            elapsed = time.time() - render_start
            fps_rate = frame / elapsed if elapsed > 0 else 0
            pct = 100 * frame / TOTAL_FRAMES
            print(f"  Frame {frame}/{TOTAL_FRAMES} ({pct:.0f}%) - {fps_rate:.1f} fps", end='\r')

        # Determine which technique based on time
        if frame < 15 * FPS:
            # Lorenz (0-15s)
            img = render_frame_with_params(
                lorenz_traj, frame, lorenz_seq,
                {'trail_length': 100, 'n_particles': 30}
            )
        elif frame < 30 * FPS:
            # Rössler (15-30s)
            img = render_frame_with_params(
                rossler_traj, frame, rossler_seq,
                {'trail_length': 200, 'n_particles': 50}
            )
        elif frame < 45 * FPS:
            # Lorenz (30-45s)
            img = render_frame_with_params(
                lorenz_traj, frame, lorenz_seq,
                {'trail_length': 400, 'n_particles': 80}
            )
        else:
            # Rössler (45-60s)
            img = render_frame_with_params(
                rossler_traj, frame, rossler_seq,
                {'trail_length': 400, 'n_particles': 50}
            )

        img.save(frames_dir / f"frame_{frame:05d}.png")

    render_elapsed = time.time() - render_start
    print(f"\n  Video render: {render_elapsed:.1f}s")

    # Generate audio
    print("\n--- Generating Audio ---")
    audio_start = time.time()

    # Segment 1: Lorenz + Bell (0-15s)
    audio_1 = generate_audio_segment(bell_seq, 15, is_drone=False)

    # Segment 2: Rössler + Drone (15-30s)
    audio_2 = generate_audio_segment(drone_seq, 15, is_drone=True)

    # Segment 3: Lorenz + Drone (30-45s)
    audio_3 = generate_audio_segment(drone_seq, 15, is_drone=True)

    # Segment 4: Rössler + Bell (45-60s)
    audio_4 = generate_audio_segment(bell_seq, 15, is_drone=False)

    # Combine
    full_audio = np.concatenate([audio_1, audio_2, audio_3, audio_4])
    full_audio = np.clip(full_audio, -1, 1)

    # Save audio
    from scipy.io import wavfile
    wavfile.write(OUTPUT_DIR / "audio.wav", SAMPLE_RATE, (full_audio * 32767).astype(np.int16))

    audio_elapsed = time.time() - audio_start
    print(f"  Audio render: {audio_elapsed:.1f}s")

    # Encode video
    print("\n--- Encoding Video ---")
    import subprocess

    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(frames_dir / "frame_%05d.png"),
        "-i", str(OUTPUT_DIR / "audio.wav"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        str(OUTPUT_DIR / "demo.mp4")
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  Output: {OUTPUT_DIR / 'demo.mp4'}")
    else:
        print(f"  FFmpeg error: {result.stderr}")

    # Summary
    total_time = time.time() - render_start
    print("\n" + "=" * 60)
    print(f"Total render time: {total_time:.1f}s")
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
