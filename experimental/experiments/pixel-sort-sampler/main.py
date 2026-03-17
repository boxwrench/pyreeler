"""Pixel Sort Sampler Film - Glitch Aesthetic

Demonstrates pixel sorting variants on generated source images:
- Threshold sorting (brightness-based)
- Interval sorting (row spacing)
- Masked sorting (selective application)
- Angle variations (horizontal, vertical, diagonal)

Structure: 4 segments × 15 seconds = 60 seconds total
- 0-15s:  Threshold sort intensification
- 15-30s: Interval/rhythm patterns
- 30-45s: Masked/glitch bursts
- 45-60s: Angle morphing (vertical → diagonal → horizontal)

Run: python experiments/pixel-sort-sampler/main.py
"""
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# Add experimental tools to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from pixel_sorting import pixel_sort, threshold_mask, masked_sort, interval_sort
from parameter_sequence import ParameterSequence

# ============================================================================
# FILM CONFIGURATION
# ============================================================================

FPS = 24
DURATION = 60
TOTAL_FRAMES = FPS * DURATION
WIDTH, HEIGHT = 854, 480

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================================
# SOURCE IMAGE GENERATION
# ============================================================================

def generate_source_image(frame, total_frames):
    """Generate evolving source images to sort.

    Creates gradients, noise patterns, and geometric shapes
    that respond well to pixel sorting.
    """
    # Base gradient
    img = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

    # Time-based parameters
    t = frame / total_frames

    # Animated gradient background
    for y in range(HEIGHT):
        for x in range(WIDTH):
            # Multiple overlapping sine waves
            r = int(128 + 127 * np.sin(x * 0.02 + t * 10) * np.cos(y * 0.01))
            g = int(128 + 127 * np.sin(y * 0.015 + t * 8) * np.sin(x * 0.008))
            b = int(128 + 127 * np.cos((x + y) * 0.01 + t * 12))
            img[y, x] = [r, g, b]

    pil_img = Image.fromarray(img)

    # Add geometric shapes for sorting targets
    draw = ImageDraw.Draw(pil_img)

    # Animated bright rectangles
    rx = int(WIDTH * (0.3 + 0.4 * np.sin(t * 6)))
    ry = int(HEIGHT * (0.3 + 0.4 * np.cos(t * 5)))
    draw.rectangle([rx, ry, rx + 100, ry + 150], fill=(255, 255, 200))

    # Second shape
    rx2 = int(WIDTH * (0.7 + 0.3 * np.cos(t * 4)))
    ry2 = int(HEIGHT * (0.6 + 0.3 * np.sin(t * 7)))
    draw.ellipse([rx2, ry2, rx2 + 80, ry2 + 80], fill=(200, 255, 255))

    # High contrast bars
    bar_x = int(WIDTH * t) % WIDTH
    draw.rectangle([bar_x, 0, bar_x + 20, HEIGHT], fill=(255, 100, 100))

    return pil_img


# ============================================================================
# PARAMETER SEQUENCES
# ============================================================================

def create_sequences():
    """Create parameter curves for pixel sorting effects."""

    # Threshold sequence (lower = more sorting)
    threshold_seq = ParameterSequence()
    # 0-15s: Threshold drops (more sorting over time)
    threshold_seq.record(0, 'threshold', 250)      # Almost no sorting
    threshold_seq.record(3 * FPS, 'threshold', 200)
    threshold_seq.record(6 * FPS, 'threshold', 150)
    threshold_seq.record(10 * FPS, 'threshold', 100)
    threshold_seq.record(15 * FPS, 'threshold', 80)  # Heavy sorting
    # 15-30s: Interval section - threshold stays low
    threshold_seq.record(20 * FPS, 'threshold', 120)
    threshold_seq.record(25 * FPS, 'threshold', 100)
    threshold_seq.record(30 * FPS, 'threshold', 150)
    # 30-45s: Masked section - varying threshold
    threshold_seq.record(35 * FPS, 'threshold', 180)
    threshold_seq.record(40 * FPS, 'threshold', 100)
    threshold_seq.record(45 * FPS, 'threshold', 120)
    # 45-60s: Angle section
    threshold_seq.record(50 * FPS, 'threshold', 100)
    threshold_seq.record(55 * FPS, 'threshold', 140)
    threshold_seq.record(60 * FPS, 'threshold', 200)

    # Interval sequence (for row-based sorting)
    interval_seq = ParameterSequence()
    interval_seq.record(0, 'interval', 0)          # Off
    interval_seq.record(15 * FPS, 'interval', 0)   # Still off
    interval_seq.record(16 * FPS, 'interval', 20)  # Start interval
    interval_seq.record(20 * FPS, 'interval', 10)  # More frequent
    interval_seq.record(25 * FPS, 'interval', 5)   # Dense
    interval_seq.record(30 * FPS, 'interval', 0)   # Off
    interval_seq.record(60 * FPS, 'interval', 0)

    # Angle sequence (only 0 or 90 to maintain image dimensions)
    angle_seq = ParameterSequence()
    angle_seq.record(0, 'angle', 90)          # Vertical
    angle_seq.record(15 * FPS, 'angle', 90)   # Keep vertical
    angle_seq.record(30 * FPS, 'angle', 90)   # Keep vertical
    angle_seq.record(45 * FPS, 'angle', 90)   # Keep vertical
    angle_seq.record(50 * FPS, 'angle', 0)    # Switch to horizontal
    angle_seq.record(55 * FPS, 'angle', 90)   # Back to vertical
    angle_seq.record(60 * FPS, 'angle', 0)    # End horizontal

    # Mask range (for masked sorting)
    mask_low_seq = ParameterSequence()
    mask_low_seq.record(0, 'mask_low', 0)
    mask_low_seq.record(30 * FPS, 'mask_low', 200)   # Only bright
    mask_low_seq.record(35 * FPS, 'mask_low', 150)
    mask_low_seq.record(40 * FPS, 'mask_low', 180)
    mask_low_seq.record(45 * FPS, 'mask_low', 0)

    mask_high_seq = ParameterSequence()
    mask_high_seq.record(0, 'mask_high', 255)
    mask_high_seq.record(30 * FPS, 'mask_high', 255)
    mask_high_seq.record(35 * FPS, 'mask_high', 220)
    mask_high_seq.record(40 * FPS, 'mask_high', 255)
    mask_high_seq.record(45 * FPS, 'mask_high', 255)

    return threshold_seq, interval_seq, angle_seq, mask_low_seq, mask_high_seq


# ============================================================================
# AUDIO GENERATION
# ============================================================================

def generate_glitch_audio(threshold_seq, duration, sample_rate=48000):
    """Generate glitchy audio that responds to sorting intensity."""
    samples_needed = int(duration * sample_rate)
    samples_per_frame = sample_rate // FPS

    audio = np.zeros(samples_needed, dtype=np.float32)

    for frame in range(int(duration * FPS)):
        threshold = threshold_seq.get_value(frame, 'threshold', 128)

        # Lower threshold = more sorting = more glitch
        # Map threshold to audio parameters
        intensity = (255 - threshold) / 255.0  # 0 to 1

        # Base tone
        freq = 50 + intensity * 200  # 50Hz to 250Hz

        start = frame * samples_per_frame
        end = min((frame + 1) * samples_per_frame, samples_needed)
        frame_t = np.arange(end - start) / sample_rate

        # Glitchy FM synthesis
        mod_index = intensity * 10  # More modulation when sorting more
        mod_freq = freq * (1 + intensity)
        mod = mod_index * np.sin(2 * np.pi * mod_freq * frame_t)
        wave = np.sin(2 * np.pi * freq * frame_t + mod)

        # Add bit-crush effect based on intensity
        if intensity > 0.5:
            # Reduce bit depth
            crush = int(8 * (1 - intensity) + 2)  # 2-6 bits
            wave = np.round(wave * (2**crush)) / (2**crush)

        audio[start:end] = wave * (0.3 + intensity * 0.4)

    # Normalize
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val * 0.8

    return audio


# ============================================================================
# MAIN RENDER LOOP
# ============================================================================

def main():
    print("=" * 60)
    print("Pixel Sort Sampler Film")
    print("Glitch Aesthetic - 60 Seconds")
    print("=" * 60)

    # Create parameter sequences
    threshold_seq, interval_seq, angle_seq, mask_low_seq, mask_high_seq = create_sequences()

    # Save sequences
    seq_dir = OUTPUT_DIR / "sequences"
    seq_dir.mkdir(exist_ok=True)
    threshold_seq.save(seq_dir / "threshold.json")
    interval_seq.save(seq_dir / "interval.json")
    angle_seq.save(seq_dir / "angle.json")
    mask_low_seq.save(seq_dir / "mask_low.json")
    mask_high_seq.save(seq_dir / "mask_high.json")
    print(f"\nSequences saved to: {seq_dir}")

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

        # Generate source image
        source_img = generate_source_image(frame, TOTAL_FRAMES)

        # Get parameters
        threshold = int(threshold_seq.get_value(frame, 'threshold', 200))
        interval = int(interval_seq.get_value(frame, 'interval', 0))
        angle = int(angle_seq.get_value(frame, 'angle', 90))
        mask_low = int(mask_low_seq.get_value(frame, 'mask_low', 0))
        mask_high = int(mask_high_seq.get_value(frame, 'mask_high', 255))

        # Apply pixel sorting based on segment
        if frame < 15 * FPS:
            # Segment 1: Threshold intensification
            result = pixel_sort(source_img, threshold=threshold, angle=90)

        elif frame < 30 * FPS:
            # Segment 2: Interval sorting
            if interval > 0:
                result = interval_sort(source_img, interval=interval, threshold=threshold, angle=90)
            else:
                result = pixel_sort(source_img, threshold=threshold, angle=90)

        elif frame < 45 * FPS:
            # Segment 3: Masked sorting
            if mask_low > 0:
                mask = threshold_mask(source_img, mask_low, mask_high)
                result = masked_sort(source_img, mask, angle=90)
            else:
                result = pixel_sort(source_img, threshold=threshold, angle=90)

        else:
            # Segment 4: Angle morphing
            result = pixel_sort(source_img, threshold=threshold, angle=angle)

        # Ensure consistent dimensions
        result_array = np.array(result)
        if result_array.shape != (HEIGHT, WIDTH, 3):
            # Resize to expected dimensions
            result_img = Image.fromarray(result_array)
            result_img = result_img.resize((WIDTH, HEIGHT), Image.NEAREST)
            result = result_img

        result.save(frames_dir / f"frame_{frame:05d}.png")

    render_elapsed = time.time() - render_start
    print(f"\n  Frame render: {render_elapsed:.1f}s")

    # Generate audio
    print("\n--- Generating Audio ---")
    audio_start = time.time()

    audio = generate_glitch_audio(threshold_seq, DURATION)

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
        writer = imageio.get_writer(OUTPUT_DIR / "pixel_sort.mp4", fps=FPS, quality=8)
        for img in images:
            writer.append_data(img)
        writer.close()

        print(f"  Video: {OUTPUT_DIR / 'pixel_sort.mp4'}")

        # Try to add audio with moviepy
        try:
            from moviepy import ImageSequenceClip, AudioFileClip

            clip = ImageSequenceClip([str(f) for f in frames], fps=FPS)
            audio_clip = AudioFileClip(str(OUTPUT_DIR / "audio.wav"))
            clip = clip.with_audio(audio_clip)
            clip.write_videofile(
                str(OUTPUT_DIR / "pixel_sort_final.mp4"),
                fps=FPS,
                codec='libx264',
                audio_codec='aac',
                logger=None
            )
            print(f"  Final: {OUTPUT_DIR / 'pixel_sort_final.mp4'}")
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
    print("\nSegment breakdown:")
    print("  0-15s:  Threshold intensification (more sorting over time)")
    print("  15-30s: Interval/rhythm patterns")
    print("  30-45s: Masked/glitch bursts")
    print("  45-60s: Angle morphing (vertical → diagonal → horizontal)")


if __name__ == "__main__":
    main()
