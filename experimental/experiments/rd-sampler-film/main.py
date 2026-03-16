"""Reaction-Diffusion Sampler Film - Organic Pattern Evolution

Demonstrates Gray-Scott reaction-diffusion patterns morphing through
different regimes: coral, spots, chaos, and fingerprint patterns.

Structure: 4 segments × 15 seconds = 60 seconds total
- 0-15s:  Coral growth (F=0.0545, k=0.062)
- 15-30s: Fingerprint/Stripes (F=0.037, k=0.06)
- 30-45s: Chaotic turbulence (F=0.026, k=0.051)
- 45-60s: Return to Coral with variation

Run: python experiments/rd-sampler-film/main.py
"""
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

# Add experimental tools to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from parameter_sequence import ParameterSequence

# Try to import scipy, fall back to simple implementation
try:
    from scipy.ndimage import convolve
    HAS_SCIPY = True
    print("Using SciPy for Laplacian")
except ImportError:
    HAS_SCIPY = False
    print("SciPy not available, using simple Laplacian")

# ============================================================================
# REACTION-DIFFUSION SIMULATION
# ============================================================================

def laplacian(grid):
    """5-point stencil Laplacian."""
    if HAS_SCIPY:
        kernel = np.array([[0, 1, 0],
                           [1, -4, 1],
                           [0, 1, 0]])
        return convolve(grid, kernel, mode='nearest')
    else:
        # Simple Laplacian without SciPy
        return (np.roll(grid, 1, 0) + np.roll(grid, -1, 0) +
                np.roll(grid, 1, 1) + np.roll(grid, -1, 1) -
                4 * grid)


def gray_scott_step(U, V, Du=0.16, Dv=0.08, F=0.035, k=0.06, dt=1.0):
    """Single Gray-Scott simulation step."""
    Lu = laplacian(U)
    Lv = laplacian(V)

    uvv = U * V * V

    U += (Du * Lu - uvv + F * (1 - U)) * dt
    V += (Dv * Lv + uvv - (F + k) * V) * dt

    # Clamp to valid range
    U = np.clip(U, 0, 1)
    V = np.clip(V, 0, 1)

    return U, V


def init_gray_scott(size=256, seed_radius=None):
    """Initialize with central seed."""
    U = np.ones((size, size))
    V = np.zeros((size, size))

    if seed_radius is None:
        seed_radius = size // 10

    center = size // 2
    y, x = np.ogrid[-center:size-center, -center:size-center]
    mask = x*x + y*y <= seed_radius*seed_radius

    U[mask] = 0.5
    V[mask] = 0.25

    # Add small noise
    U += np.random.randn(size, size) * 0.01
    V += np.random.randn(size, size) * 0.01

    return U, V


def render_rd(U, V, mode='V', contrast=1.0):
    """Render chemical concentration to RGB image."""
    if mode == 'V':
        # Activator - black background, white patterns
        img = (V * 255 * contrast).astype(np.uint8)
        rgb = np.stack([img, img, img], axis=-1)
    elif mode == 'U':
        # Inhibitor - inverse
        img = ((1 - U) * 255 * contrast).astype(np.uint8)
        rgb = np.stack([img, img, img], axis=-1)
    elif mode == 'both':
        # False color: U in cyan, V in magenta
        rgb = np.zeros((*U.shape, 3), dtype=np.uint8)
        rgb[:, :, 0] = (V * 255).astype(np.uint8)  # Red from V
        rgb[:, :, 1] = ((U + V) * 127).astype(np.uint8)  # Green from both
        rgb[:, :, 2] = (U * 255).astype(np.uint8)  # Blue from U

    return rgb


# ============================================================================
# FILM CONFIGURATION
# ============================================================================

FPS = 24
DURATION = 60
TOTAL_FRAMES = FPS * DURATION
SIZE = 256  # Grid size (256 is fast, 512 is slower but sharper)
DT = 1.0    # Time step per frame

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Pattern regimes (F, k values)
PATTERNS = {
    'coral': (0.0545, 0.062),
    'fingerprint': (0.037, 0.06),
    'spots': (0.025, 0.06),
    'chaos': (0.026, 0.051),
    'mitosis': (0.022, 0.051),
}


# ============================================================================
# PARAMETER SEQUENCES
# ============================================================================

def create_sequences():
    """Create parameter curves for MAXIMUM visual change throughout."""

    # F (feed rate) sequence - DRAMATIC swings from frame 0
    f_seq = ParameterSequence()
    # 0-5s: Immediate jumps between coral and fingerprint (BIG changes every 2s)
    f_seq.record(0, 'F', 0.0545)           # Classic coral
    f_seq.record(2 * FPS, 'F', 0.040)      # Jump to fingerprint zone (HUGE change)
    f_seq.record(4 * FPS, 'F', 0.056)      # Back to high coral
    f_seq.record(6 * FPS, 'F', 0.038)      # Deep fingerprint
    f_seq.record(8 * FPS, 'F', 0.052)      # Back to coral
    f_seq.record(10 * FPS, 'F', 0.042)     # Fingerprint again
    # 10-15s: Rapid toward chaos
    f_seq.record(12 * FPS, 'F', 0.034)     # Moving
    f_seq.record(14 * FPS, 'F', 0.028)     # Near chaos
    f_seq.record(16 * FPS, 'F', 0.024)     # Chaos
    f_seq.record(18 * FPS, 'F', 0.030)     # Back up
    f_seq.record(20 * FPS, 'F', 0.026)     # Chaos
    # 20-35s: Chaos zone with wild swings
    f_seq.record(23 * FPS, 'F', 0.022)     # Deep chaos
    f_seq.record(26 * FPS, 'F', 0.028)     # Back up
    f_seq.record(29 * FPS, 'F', 0.024)     # Down
    f_seq.record(32 * FPS, 'F', 0.030)     # Up
    f_seq.record(35 * FPS, 'F', 0.026)     # Chaos
    # 35-50s: Return journey
    f_seq.record(38 * FPS, 'F', 0.034)     # Through fingerprint
    f_seq.record(42 * FPS, 'F', 0.046)     # Near coral
    f_seq.record(46 * FPS, 'F', 0.053)     # Coral edge
    f_seq.record(50 * FPS, 'F', 0.056)     # Classic coral
    # 50-60s: Final coral variations
    f_seq.record(53 * FPS, 'F', 0.050)
    f_seq.record(56 * FPS, 'F', 0.057)
    f_seq.record(60 * FPS, 'F', 0.0545)    # End value

    # k (kill rate) sequence - OPPOSING swings for maximum disruption
    k_seq = ParameterSequence()
    # 0-5s: Wild swings
    k_seq.record(0, 'k', 0.058)            # Low coral
    k_seq.record(2 * FPS, 'k', 0.064)      # High coral
    k_seq.record(4 * FPS, 'k', 0.060)      # Mid
    k_seq.record(6 * FPS, 'k', 0.065)      # High
    k_seq.record(8 * FPS, 'k', 0.061)      # Mid
    k_seq.record(10 * FPS, 'k', 0.063)     # High
    # 10-15s: Dropping toward chaos
    k_seq.record(12 * FPS, 'k', 0.058)
    k_seq.record(14 * FPS, 'k', 0.054)
    k_seq.record(16 * FPS, 'k', 0.050)     # Chaos zone
    k_seq.record(18 * FPS, 'k', 0.048)     # Deep chaos
    k_seq.record(20 * FPS, 'k', 0.051)     # Chaos
    # 20-35s: Chaos oscillation
    k_seq.record(23 * FPS, 'k', 0.047)     # Deep
    k_seq.record(26 * FPS, 'k', 0.053)     # Up
    k_seq.record(29 * FPS, 'k', 0.049)     # Down
    k_seq.record(32 * FPS, 'k', 0.052)     # Up
    k_seq.record(35 * FPS, 'k', 0.054)     # Leaving
    # 35-50s: Return
    k_seq.record(38 * FPS, 'k', 0.059)
    k_seq.record(42 * FPS, 'k', 0.061)
    k_seq.record(46 * FPS, 'k', 0.063)
    k_seq.record(50 * FPS, 'k', 0.062)
    # 50-60s: Final variation
    k_seq.record(53 * FPS, 'k', 0.060)
    k_seq.record(56 * FPS, 'k', 0.064)
    k_seq.record(60 * FPS, 'k', 0.062)

    # Contrast/brightness - DRAMATIC pulsing from start
    contrast_seq = ParameterSequence()
    contrast_seq.record(0, 'contrast', 1.0)
    contrast_seq.record(2 * FPS, 'contrast', 1.8)   # BIG boost early
    contrast_seq.record(5 * FPS, 'contrast', 0.8)   # Dramatic dip
    contrast_seq.record(8 * FPS, 'contrast', 1.6)   # Boost
    contrast_seq.record(12 * FPS, 'contrast', 0.9)  # Dip
    contrast_seq.record(16 * FPS, 'contrast', 1.7)  # Boost
    contrast_seq.record(20 * FPS, 'contrast', 1.5)  # Chaos
    contrast_seq.record(25 * FPS, 'contrast', 2.0)  # Peak chaos
    contrast_seq.record(30 * FPS, 'contrast', 1.6)
    contrast_seq.record(35 * FPS, 'contrast', 1.4)
    contrast_seq.record(40 * FPS, 'contrast', 1.2)
    contrast_seq.record(45 * FPS, 'contrast', 1.3)
    contrast_seq.record(50 * FPS, 'contrast', 1.1)
    contrast_seq.record(55 * FPS, 'contrast', 1.4)
    contrast_seq.record(60 * FPS, 'contrast', 1.2)

    # Rendering mode - EARLY and FREQUENT switches
    mode_seq = ParameterSequence()
    mode_seq.record(0, 'mode', 'V')        # Standard
    mode_seq.record(4 * FPS, 'mode', 'U')  # Inhibitor view (4s in!)
    mode_seq.record(8 * FPS, 'mode', 'V')  # Back
    mode_seq.record(12 * FPS, 'mode', 'both')  # False color
    mode_seq.record(18 * FPS, 'mode', 'V')     # Back
    mode_seq.record(25 * FPS, 'mode', 'both')  # False color
    mode_seq.record(40 * FPS, 'mode', 'V')     # Back to standard
    mode_seq.record(50 * FPS, 'mode', 'both')  # Brief false color
    mode_seq.record(60 * FPS, 'mode', 'V')

    return f_seq, k_seq, contrast_seq, mode_seq


# ============================================================================
# AUDIO GENERATION
# ============================================================================

def generate_drone_audio(f_seq, k_seq, duration, sample_rate=48000):
    """Generate evolving drone based on RD parameters."""
    samples_needed = int(duration * sample_rate)
    samples_per_frame = sample_rate // FPS

    # Simple FM synthesis
    t_total = np.arange(samples_needed) / sample_rate

    # Base frequency modulated by F parameter
    base_freq = 55  # A1

    # Create frequency modulation from F values
    fm_signal = np.zeros(samples_needed)

    for frame in range(int(duration * FPS)):
        F = f_seq.get_value(frame, 'F', 0.035)
        k = k_seq.get_value(frame, 'k', 0.06)

        # Map F and k to audio parameters
        freq = base_freq + (F - 0.03) * 2000  # 20Hz to 100Hz range
        mod_freq = freq * (1 + k * 10)  # Modulation based on k
        index = 2.0 + (F - 0.02) * 50  # Modulation index

        start = frame * samples_per_frame
        end = min((frame + 1) * samples_per_frame, samples_needed)
        frame_t = np.arange(end - start) / sample_rate

        # FM synthesis
        mod = index * np.sin(2 * np.pi * mod_freq * frame_t)
        wave = np.sin(2 * np.pi * freq * frame_t + mod)

        fm_signal[start:end] = wave

    # Normalize
    fm_signal = fm_signal / np.max(np.abs(fm_signal)) * 0.8

    return fm_signal.astype(np.float32)


# ============================================================================
# MAIN RENDER LOOP
# ============================================================================

def main():
    print("=" * 60)
    print("Reaction-Diffusion Sampler Film")
    print("Organic Pattern Evolution - 60 Seconds")
    print("=" * 60)

    # Create parameter sequences
    f_seq, k_seq, contrast_seq, mode_seq = create_sequences()

    # Save sequences
    seq_dir = OUTPUT_DIR / "sequences"
    seq_dir.mkdir(exist_ok=True)
    f_seq.save(seq_dir / "feed_rate.json")
    k_seq.save(seq_dir / "kill_rate.json")
    contrast_seq.save(seq_dir / "contrast.json")
    mode_seq.save(seq_dir / "render_mode.json")
    print(f"\nSequences saved to: {seq_dir}")

    # Initialize simulation
    print("\n--- Initializing Simulation ---")
    U, V = init_gray_scott(SIZE, seed_radius=SIZE // 8)

    # Pre-warm simulation to get initial pattern
    print("  Pre-warming (300 steps)...")
    F_start, k_start = PATTERNS['coral']
    for _ in range(300):
        U, V = gray_scott_step(U, V, F=F_start, k=k_start, dt=DT)
    print("  Initial pattern established")

    # Render frames
    print("\n--- Rendering Frames ---")
    frames_dir = OUTPUT_DIR / "frames"
    frames_dir.mkdir(exist_ok=True)

    render_start = time.time()

    for frame in range(TOTAL_FRAMES):
        if frame % FPS == 0:
            elapsed = time.time() - render_start
            fps_rate = frame / elapsed if elapsed > 0 else 0
            pct = 100 * frame / TOTAL_FRAMES
            print(f"  Frame {frame}/{TOTAL_FRAMES} ({pct:.0f}%) - {fps_rate:.1f} fps", end='\r')

        # Get current parameters
        F = f_seq.get_value(frame, 'F', PATTERNS['coral'][0])
        k = k_seq.get_value(frame, 'k', PATTERNS['coral'][1])
        contrast = contrast_seq.get_value(frame, 'contrast', 1.0)

        # Determine render mode
        if frame < 30 * FPS:
            mode = 'V'
        elif frame < 45 * FPS:
            mode = 'both'  # False color for chaos section
        else:
            mode = 'V'

        # Simulation step
        U, V = gray_scott_step(U, V, F=F, k=k, dt=DT)

        # Render
        rgb = render_rd(U, V, mode=mode, contrast=contrast)
        img = Image.fromarray(rgb)

        # Upscale for video (256 -> 512 for better quality)
        img = img.resize((SIZE * 2, SIZE * 2), Image.NEAREST)

        img.save(frames_dir / f"frame_{frame:05d}.png")

    render_elapsed = time.time() - render_start
    print(f"\n  Frame render: {render_elapsed:.1f}s")

    # Generate audio
    print("\n--- Generating Audio ---")
    audio_start = time.time()

    audio = generate_drone_audio(f_seq, k_seq, DURATION)

    # Save audio
    try:
        import scipy.io.wavfile as wavfile
        wavfile.write(OUTPUT_DIR / "audio.wav", 48000, (audio * 32767).astype(np.int16))
        print(f"  Audio saved: {OUTPUT_DIR / 'audio.wav'}")
    except ImportError:
        print("  scipy.io.wavfile not available, skipping audio save")

    audio_elapsed = time.time() - audio_start
    print(f"  Audio render: {audio_elapsed:.1f}s")

    # Encode video
    print("\n--- Encoding Video ---")
    try:
        import imageio.v2 as imageio

        frames = sorted(frames_dir.glob("frame_*.png"))
        images = [imageio.imread(f) for f in frames]

        # Video only first
        writer = imageio.get_writer(OUTPUT_DIR / "rd_sampler.mp4", fps=FPS, quality=8)
        for img in images:
            writer.append_data(img)
        writer.close()

        print(f"  Video: {OUTPUT_DIR / 'rd_sampler.mp4'}")

        # Try to add audio with moviepy
        try:
            from moviepy import ImageSequenceClip, AudioFileClip

            clip = ImageSequenceClip([str(f) for f in frames], fps=FPS)
            audio_clip = AudioFileClip(str(OUTPUT_DIR / "audio.wav"))
            clip = clip.with_audio(audio_clip)
            clip.write_videofile(
                str(OUTPUT_DIR / "rd_sampler_final.mp4"),
                fps=FPS,
                codec='libx264',
                audio_codec='aac',
                logger=None
            )
            print(f"  Final: {OUTPUT_DIR / 'rd_sampler_final.mp4'}")
        except Exception as e:
            print(f"  Could not add audio: {e}")
            print(f"  Video only output available")

    except Exception as e:
        print(f"  Encoding error: {e}")
        print(f"  Frames available in: {frames_dir}")

    # Summary
    total_time = time.time() - render_start
    print("\n" + "=" * 60)
    print(f"Total render time: {total_time:.1f}s")
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 60)
    print("\nPattern journey:")
    print("  0-15s:  Coral growth (branching organic)")
    print("  15-30s: Fingerprint/Stripes (parallel lines)")
    print("  30-45s: Chaotic turbulence (false color)")
    print("  45-60s: Return to Coral (full circle)")


if __name__ == "__main__":
    main()
