"""Strange Attractor visualization module for PyReeler experimental.

Pure NumPy implementation of chaotic dynamical systems.

Usage:
    from experimental.tools.attractors import generate_lorenz, render_frame

    trajectory = generate_lorenz(n_points=5000, n_particles=100)
    frame = render_frame(trajectory, frame_num=0, total_frames=1440, width=1280, height=720)
"""
import time
import warnings

import numpy as np
from PIL import Image


# =============================================================================
# PERFORMANCE ESTIMATION & MONITORING
# =============================================================================

# Empirical timing constants (seconds per particle-trail combination)
# Measured on typical modern CPU (Ryzen/Intel i7 class)
EMPIRICAL_TIME_PER_PIXEL = 0.00005  # ~50 microseconds per particle×trail
MAX_RECOMMENDED_PARTICLES = 100
MAX_RECOMMENDED_TRAIL = 1000
TIMEOUT_SECONDS = 60  # Bailout threshold


class RenderTimeoutError(Exception):
    """Raised when rendering exceeds timeout threshold."""
    pass


def estimate_render_time(
    n_frames: int,
    n_particles: int,
    trail_length: int,
    width: int = 854,
    height: int = 480
) -> float:
    """Estimate total render time in seconds.

    Args:
        n_frames: Total number of frames to render
        n_particles: Number of particles in trajectory
        trail_length: Trail length per particle
        width, height: Output resolution

    Returns:
        Estimated time in seconds
    """
    # Vectorized version is much faster - scale factor applied
    vectorized_factor = 0.1  # 10x faster than nested loops

    operations = n_frames * n_particles * min(trail_length, 100)
    base_time = operations * EMPIRICAL_TIME_PER_PIXEL * vectorized_factor

    # Resolution scaling (rough approximation)
    resolution_factor = (width * height) / (854 * 480)

    return base_time * resolution_factor


def check_render_safety(
    n_frames: int,
    n_particles: int,
    trail_length: int,
    width: int = 854,
    height: int = 480,
    raise_warning: bool = True
) -> tuple[bool, float, str]:
    """Check if render parameters are safe and provide recommendations.

    Args:
        n_frames: Total number of frames
        n_particles: Number of particles
        trail_length: Trail length
        width, height: Output resolution
        raise_warning: If True, emit warnings for unsafe parameters

    Returns:
        (is_safe, estimated_time, recommendation_message)
    """
    estimated = estimate_render_time(n_frames, n_particles, trail_length, width, height)

    issues = []

    if n_particles > MAX_RECOMMENDED_PARTICLES:
        issues.append(f"particles ({n_particles} > {MAX_RECOMMENDED_PARTICLES})")

    if trail_length > MAX_RECOMMENDED_TRAIL:
        issues.append(f"trail_length ({trail_length} > {MAX_RECOMMENDED_TRAIL})")

    if estimated > TIMEOUT_SECONDS:
        issues.append(f"estimated time ({estimated:.1f}s > {TIMEOUT_SECONDS}s timeout)")

    is_safe = len(issues) == 0

    if issues and raise_warning:
        msg = f"Render may be slow: {', '.join(issues)}. Estimated: {estimated:.1f}s"
        warnings.warn(msg, UserWarning, stacklevel=2)

    recommendation = "Parameters look good." if is_safe else f"Reduce: {', '.join(issues)}"

    return is_safe, estimated, recommendation


class RenderMonitor:
    """Monitors render progress and can bail out if taking too long."""

    def __init__(self, total_frames: int, timeout_seconds: float = TIMEOUT_SECONDS):
        self.total_frames = total_frames
        self.timeout_seconds = timeout_seconds
        self.start_time = None
        self.frame_times = []

    def start(self):
        """Start the monitoring timer."""
        self.start_time = time.time()

    def check_frame(self, frame_num: int) -> bool:
        """Check if we should continue rendering.

        Args:
            frame_num: Current frame number

        Returns:
            True if should continue, False if should bail

        Raises:
            RenderTimeoutError: If timeout exceeded
        """
        if self.start_time is None:
            self.start()

        elapsed = time.time() - self.start_time

        # Check global timeout
        if elapsed > self.timeout_seconds:
            raise RenderTimeoutError(
                f"Render timeout: {elapsed:.1f}s > {self.timeout_seconds}s "
                f"({frame_num}/{self.total_frames} frames rendered)"
            )

        # Track frame timing for ETA
        self.frame_times.append(elapsed)

        return True

    def get_eta(self, current_frame: int) -> float:
        """Get estimated time remaining."""
        if not self.frame_times or current_frame == 0:
            return 0.0

        avg_time_per_frame = self.frame_times[-1] / current_frame
        remaining_frames = self.total_frames - current_frame
        return avg_time_per_frame * remaining_frames

    def get_progress_str(self, current_frame: int) -> str:
        """Get formatted progress string."""
        pct = 100 * current_frame / self.total_frames
        elapsed = time.time() - self.start_time if self.start_time else 0
        eta = self.get_eta(current_frame)

        return f"{pct:.0f}% ({current_frame}/{self.total_frames}) | {elapsed:.1f}s elapsed | {eta:.1f}s ETA"


def lorenz_step(x, y, z, sigma=10, rho=28, beta=8/3, dt=0.01):
    """Single integration step of Lorenz equations."""
    dx = sigma * (y - x) * dt
    dy = (x * (rho - z) - y) * dt
    dz = (x * y - beta * z) * dt
    return x + dx, y + dy, z + dz


def rossler_step(x, y, z, a=0.2, b=0.2, c=5.7, dt=0.01):
    """Single integration step of Rössler equations."""
    dx = (-y - z) * dt
    dy = (x + a * y) * dt
    dz = (b + z * (x - c)) * dt
    return x + dx, y + dy, z + dz


def generate_lorenz(
    n_points: int = 10000,
    n_particles: int = 1,
    sigma: float = 10,
    rho: float = 28,
    beta: float = 8/3,
    dt: float = 0.01
) -> np.ndarray:
    """Generate Lorenz attractor trajectory.

    Args:
        n_points: Number of integration steps
        n_particles: Number of simultaneous trajectories
        sigma, rho, beta: Lorenz parameters
        dt: Integration time step

    Returns:
        Array of shape (n_points, n_particles, 3) containing [x, y, z]
    """
    # Initialize with slight variations for multiple particles
    np.random.seed(42)  # Reproducible
    positions = np.random.randn(n_particles, 3) * 0.1 + np.array([1, 1, 25])
    trajectory = np.zeros((n_points, n_particles, 3))

    for i in range(n_points):
        for p in range(n_particles):
            x, y, z = positions[p]
            positions[p] = lorenz_step(x, y, z, sigma, rho, beta, dt)
        trajectory[i] = positions.copy()

    return trajectory


def generate_rossler(
    n_points: int = 10000,
    n_particles: int = 1,
    a: float = 0.2,
    b: float = 0.2,
    c: float = 5.7,
    dt: float = 0.01
) -> np.ndarray:
    """Generate Rössler attractor trajectory.

    Args:
        n_points: Number of integration steps
        n_particles: Number of simultaneous trajectories
        a, b, c: Rössler parameters
        dt: Integration time step

    Returns:
        Array of shape (n_points, n_particles, 3) containing [x, y, z]
    """
    np.random.seed(42)
    positions = np.random.randn(n_particles, 3) * 0.1 + np.array([1, 1, 0])
    trajectory = np.zeros((n_points, n_particles, 3))

    for i in range(n_points):
        for p in range(n_particles):
            x, y, z = positions[p]
            positions[p] = rossler_step(x, y, z, a, b, c, dt)
        trajectory[i] = positions.copy()

    return trajectory


def rotate_points(points, angle_x=0, angle_y=0, angle_z=0):
    """Rotate points around origin.

    Args:
        points: Array of shape (N, 3) containing [x, y, z]
        angle_x, angle_y, angle_z: Rotation angles in radians

    Returns:
        Rotated points array of same shape
    """
    # Rotation around X axis
    if angle_x != 0:
        cos_x, sin_x = np.cos(angle_x), np.sin(angle_x)
        y_new = points[:, 1] * cos_x - points[:, 2] * sin_x
        z_new = points[:, 1] * sin_x + points[:, 2] * cos_x
        points = np.column_stack([points[:, 0], y_new, z_new])

    # Rotation around Y axis
    if angle_y != 0:
        cos_y, sin_y = np.cos(angle_y), np.sin(angle_y)
        x_new = points[:, 0] * cos_y - points[:, 2] * sin_y
        z_new = points[:, 0] * sin_y + points[:, 2] * cos_y
        points = np.column_stack([x_new, points[:, 1], z_new])

    # Rotation around Z axis
    if angle_z != 0:
        cos_z, sin_z = np.cos(angle_z), np.sin(angle_z)
        x_new = points[:, 0] * cos_z - points[:, 1] * sin_z
        y_new = points[:, 0] * sin_z + points[:, 1] * cos_z
        points = np.column_stack([x_new, y_new, points[:, 2]])

    return points


def render_frame(
    trajectory: np.ndarray,
    frame_num: int,
    total_frames: int,
    width: int = 1280,
    height: int = 720,
    trail_length: int = 500,
    brightness: float = 0.5
) -> Image.Image:
    """Render a single frame of attractor animation (NUMPY VECTORIZED).

    Args:
        trajectory: Array of shape (n_points, n_particles, 3)
        frame_num: Current frame number
        total_frames: Total frames in animation
        width, height: Output image dimensions
        trail_length: Number of previous points to show
        brightness: Base brightness (0-1)

    Returns:
        PIL Image
    """
    n_points, n_particles, _ = trajectory.shape

    # Calculate rotation angle (full rotation over animation)
    angle = 2 * np.pi * frame_num / total_frames

    # Normalize trajectory to 0-1 range
    mins = trajectory.min(axis=(0, 1))
    maxs = trajectory.max(axis=(0, 1))
    ranges = maxs - mins
    ranges[ranges == 0] = 1  # Avoid division by zero

    # Determine which points to show (trailing window)
    center_idx = int((frame_num / total_frames) * (n_points - 1))
    start_idx = max(0, center_idx - trail_length)
    end_idx = min(n_points, center_idx + 1)

    # Extract window of points for ALL particles: (window_size, n_particles, 3)
    window = trajectory[start_idx:end_idx, :, :].copy()
    window_size = window.shape[0]

    # Rotate ALL points at once
    # Window shape: (window_size, n_particles, 3)
    # Reshape to (window_size * n_particles, 3) for rotation
    flat_points = window.reshape(-1, 3)
    rotated = rotate_points(flat_points, angle_y=angle, angle_x=angle * 0.3)

    # Normalize
    rotated = (rotated - mins) / ranges

    # Project to 2D (drop Z)
    x = (rotated[:, 0] * (width - 100) + 50).astype(int)
    y = (rotated[:, 1] * (height - 100) + 50).astype(int)

    # Calculate age falloff for each point
    # Age goes from 0 (newest) to 1 (oldest) within the window
    age = np.linspace(0, 1, window_size)
    age_weights = 1 - age * 0.5  # Newer points are brighter

    # Broadcast weights to all particles
    weights = np.repeat(age_weights, n_particles) * brightness

    # Filter valid coordinates
    valid = (x >= 0) & (x < width) & (y >= 0) & (y < height)
    x_valid = x[valid]
    y_valid = y[valid]
    w_valid = weights[valid]

    # Accumulate using np.add.at (vectorized)
    img = np.zeros((height, width), dtype=np.float32)
    np.add.at(img, (y_valid, x_valid), w_valid)

    # Normalize and convert to uint8
    if img.max() > 0:
        img = img / img.max()
    img = np.clip(img * 255, 0, 255).astype(np.uint8)

    return Image.fromarray(img, 'L')


def render_frame_color(
    trajectory: np.ndarray,
    frame_num: int,
    total_frames: int,
    width: int = 1280,
    height: int = 720,
    trail_length: int = 500
) -> Image.Image:
    """Render colored frame with velocity-based coloring.

    Returns RGB image where hue represents velocity.
    """
    n_points, n_particles, _ = trajectory.shape
    angle = 2 * np.pi * frame_num / total_frames

    mins = trajectory.min(axis=(0, 1))
    maxs = trajectory.max(axis=(0, 1))
    ranges = maxs - mins
    ranges[ranges == 0] = 1

    center_idx = int((frame_num / total_frames) * (n_points - 1))
    start_idx = max(0, center_idx - trail_length)
    end_idx = min(n_points, center_idx + 1)

    # RGB image
    img = np.zeros((height, width, 3), dtype=np.float32)

    # Calculate velocities for coloring
    velocities = np.diff(trajectory, axis=0, prepend=trajectory[:1])
    speeds = np.linalg.norm(velocities, axis=2)
    speed_min = speeds.min()
    speed_max = speeds.max()

    for p in range(n_particles):
        points = trajectory[start_idx:end_idx, p, :].copy()
        speed = speeds[start_idx:end_idx, p]

        points = rotate_points(points, angle_y=angle)
        points = (points - mins) / ranges

        x = (points[:, 0] * (width - 100) + 50).astype(int)
        y = (points[:, 1] * (height - 100) + 50).astype(int)

        # Normalize speed to 0-1 for coloring
        if speed_max > speed_min:
            speed_norm = (speed - speed_min) / (speed_max - speed_min)
        else:
            speed_norm = np.zeros_like(speed)

        for i, (xi, yi, s) in enumerate(zip(x, y, speed_norm)):
            if 0 <= xi < width and 0 <= yi < height:
                # Color by speed: slow=blue, fast=red
                img[yi, xi, 0] += s * 0.3  # Red
                img[yi, xi, 2] += (1 - s) * 0.3  # Blue
                img[yi, xi, 1] += 0.1  # Green tint

    img = np.clip(img / img.max() * 255, 0, 255).astype(np.uint8)
    return Image.fromarray(img, 'RGB')


if __name__ == "__main__":
    # Demo: generate test frames
    from pathlib import Path

    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)

    print("Strange Attractor Demo")
    print("=" * 40)

    # Generate Lorenz
    print("Generating Lorenz attractor...")
    lorenz = generate_lorenz(n_points=5000, n_particles=50)
    frame = render_frame(lorenz, frame_num=0, total_frames=1440, width=640, height=360)
    frame.save(output_dir / "lorenz_frame_0.png")
    print(f"  Saved: lorenz_frame_0.png")

    frame = render_frame(lorenz, frame_num=720, total_frames=1440, width=640, height=360)
    frame.save(output_dir / "lorenz_frame_720.png")
    print(f"  Saved: lorenz_frame_720.png")

    # Generate Rössler
    print("Generating Rössler attractor...")
    rossler = generate_rossler(n_points=5000, n_particles=50)
    frame = render_frame(rossler, frame_num=360, total_frames=1440, width=640, height=360)
    frame.save(output_dir / "rossler_frame_360.png")
    print(f"  Saved: rossler_frame_360.png")

    # Color version
    print("Generating color Lorenz...")
    frame_color = render_frame_color(lorenz, frame_num=360, total_frames=1440, width=640, height=360)
    frame_color.save(output_dir / "lorenz_color_360.png")
    print(f"  Saved: lorenz_color_360.png")

    print("=" * 40)
    print(f"Test files in: {output_dir}")
