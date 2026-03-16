"""[Technique name] module for PyReeler experimental.

[One-line description]

Usage:
    from experimental.tools.TEMPLATE import generate, render

    data = generate(param_a=0.5, param_b=50)
    frame = render(data, frame_num=0, width=854, height=480)
"""
import warnings

import numpy as np
from PIL import Image


# Performance estimation constants
_EST_TIME_PER_OP = 0.00001  # 10 microseconds per operation


def estimate_render_time(n_frames, n_particles=None, width=854, height=480):
    """Estimate total render time in seconds.

    Args:
        n_frames: Number of frames to render
        n_particles: Number of particles (if applicable)
        width, height: Output resolution

    Returns:
        Estimated time in seconds
    """
    # Override with your actual estimation
    resolution_factor = (width * height) / (854 * 480)
    base_time = n_frames * _EST_TIME_PER_OP * resolution_factor

    if n_particles:
        base_time *= n_particles

    return base_time


def check_safety(n_frames, n_particles=None, width=854, height=480):
    """Check if parameters are safe for rendering.

    Returns:
        (is_safe, estimated_time, recommendation)
    """
    est = estimate_render_time(n_frames, n_particles, width, height)

    # Adjust thresholds for your technique
    MAX_TIME = 60  # seconds
    MAX_PARTICLES = 100

    issues = []
    if est > MAX_TIME:
        issues.append(f"estimated time ({est:.1f}s > {MAX_TIME}s)")
    if n_particles and n_particles > MAX_PARTICLES:
        issues.append(f"particles ({n_particles} > {MAX_PARTICLES})")

    is_safe = len(issues) == 0
    rec = "Parameters OK" if is_safe else f"Reduce: {', '.join(issues)}"

    if not is_safe:
        warnings.warn(rec, UserWarning)

    return is_safe, est, rec


def generate(param_a=0.5, param_b=50, **kwargs):
    """Generate/cache expensive data.

    Args:
        param_a: Description of param_a
        param_b: Description of param_b

    Returns:
        Data structure for render() function
    """
    # Implementation here
    data = {
        'param_a': param_a,
        'param_b': param_b,
        # Add computed data
    }
    return data


def render(data, frame_num, total_frames, width=854, height=480):
    """Render a single frame.

    Args:
        data: Output from generate()
        frame_num: Current frame number
        total_frames: Total frames in animation
        width, height: Output dimensions

    Returns:
        PIL Image
    """
    # Extract params
    param_a = data['param_a']
    param_b = data['param_b']

    # Create blank image
    img = np.zeros((height, width), dtype=np.float32)

    # Your rendering logic here
    # Use NumPy vectorization, avoid nested Python loops

    # Convert to PIL
    img = np.clip(img * 255, 0, 255).astype(np.uint8)
    return Image.fromarray(img, 'L')


if __name__ == "__main__":
    # Demo/test code
    from pathlib import Path

    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)

    print("Testing [technique name]")
    print("=" * 40)

    # Test generation
    print("Generating data...")
    data = generate(param_a=0.5, param_b=50)

    # Test safety check
    is_safe, est, rec = check_safety(120, width=854, height=480)
    print(f"Safety: {rec} (est. {est:.2f}s)")

    # Test render
    print("Rendering test frames...")
    for i in range(5):
        frame = render(data, i, 24, width=640, height=360)
        frame.save(output_dir / f"test_frame_{i:02d}.png")

    print(f"Test files in: {output_dir}")
