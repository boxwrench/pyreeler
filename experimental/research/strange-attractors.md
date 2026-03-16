# Strange Attractors

Chaotic dynamical systems that produce beautiful, non-repeating particle trajectories. Pure NumPy, elegant results.

## Overview

Strange attractors are sets of differential equations that, despite being deterministic, produce apparently random behavior. The particles never repeat the same path but stay bounded within a characteristic shape.

## The Lorenz Attractor

The classic: three equations, three parameters, butterfly wings.

```python
import numpy as np

def lorenz_step(x, y, z, sigma=10, rho=28, beta=8/3, dt=0.01):
    """Single integration step of Lorenz equations."""
    dx = sigma * (y - x) * dt
    dy = (x * (rho - z) - y) * dt
    dz = (x * y - beta * z) * dt
    return x + dx, y + dy, z + dz

def generate_lorenz(n_points=10000, n_particles=1):
    """Generate Lorenz attractor trajectory."""
    # Initialize with slight variations for multiple particles
    positions = np.random.randn(n_particles, 3) * 0.1 + np.array([1, 1, 25])
    trajectory = np.zeros((n_points, n_particles, 3))

    for i in range(n_points):
        for p in range(n_particles):
            x, y, z = positions[p]
            positions[p] = lorenz_step(x, y, z)
        trajectory[i] = positions.copy()

    return trajectory  # shape: (n_points, n_particles, 3)
```

## The Rössler Attractor

Simpler, band-like structure. Good for circular/spiral compositions.

```python
def rossler_step(x, y, z, a=0.2, b=0.2, c=5.7, dt=0.01):
    """Single integration step of Rössler equations."""
    dx = (-y - z) * dt
    dy = (x + a * y) * dt
    dz = (b + z * (x - c)) * dt
    return x + dx, y + dy, z + dz
```

## Rendering to Image

```python
def render_attractor(trajectory, width=1280, height=720):
    """Render trajectory to grayscale image with motion blur."""
    from PIL import Image

    # Normalize to image coordinates
    mins = trajectory.min(axis=(0, 1))
    maxs = trajectory.max(axis=(0, 1))
    normalized = (trajectory - mins) / (maxs - mins)

    # Project to 2D (drop Z or rotate)
    x = (normalized[:, :, 0] * (width - 20) + 10).astype(int)
    y = (normalized[:, :, 1] * (height - 20) + 10).astype(int)

    # Accumulate into image
    img = np.zeros((height, width))
    for i in range(len(trajectory)):
        for p in range(trajectory.shape[1]):
            xi, yi = x[i, p], y[i, p]
            if 0 <= xi < width and 0 <= yi < height:
                img[yi, xi] += 0.1  # Accumulate

    # Normalize and convert
    img = np.clip(img / img.max() * 255, 0, 255).astype(np.uint8)
    return Image.fromarray(img, 'L')
```

## Color by Velocity

```python
def velocity_color(trajectory):
    """Calculate velocity magnitude for each point."""
    velocities = np.diff(trajectory, axis=0, prepend=trajectory[:1])
    speed = np.linalg.norm(velocities, axis=2)
    return speed  # Use as color intensity or hue
```

## Parameters for Different Moods

| System | Parameters | Character |
|--------|------------|-----------|
| Lorenz (classic) | σ=10, ρ=28, β=8/3 | Balanced chaos |
| Lorenz (dense) | σ=14, ρ=45, β=4/3 | More loops, denser |
| Rössler (classic) | a=0.2, b=0.2, c=5.7 | Clean bands |
| Rössler (chaotic) | a=0.1, b=0.1, c=14 | More turbulent |

## Animation Strategies

### 1. Camera Orbit
Rotate viewpoint around the attractor:
```python
def rotate_view(points, angle):
    """Rotate points around Y axis."""
    cos_a, sin_a = np.cos(angle), np.sin(angle)
    x_new = points[:, 0] * cos_a - points[:, 2] * sin_a
    z_new = points[:, 0] * sin_a + points[:, 2] * cos_a
    return np.stack([x_new, points[:, 1], z_new], axis=1)
```

### 2. Parameter Drift
Slowly change attractor parameters over time:
```python
# Interpolate rho from 28 to 35 over film duration
rho = 28 + (frame / total_frames) * 7
```

### 3. Particle Birth/Death
Fade particles in and out, keeping trajectory count constant but cycling which are visible.

### 4. Accumulation Trail
Each frame adds new points, old points fade:
```python
# Keep last N points, fade alpha by age
trail_length = 500
frame_points = trajectory[frame % len(trajectory)]
```

## Performance Notes

- 10,000 points × 1 particle: instant
- 10,000 points × 100 particles: ~0.1s
- 10,000 points × 1000 particles: ~1s (still reasonable)
- Integration step size matters: dt=0.01 is stable, 0.001 is smoother but 10× slower
- Precompute trajectory once, render with different views

## File Size Considerations

- Additive blending (glowing trails) compresses well
- Sharp particle dots with black background: moderate compression
- Fine line work (connecting particles): harder to compress, use CRF 28

## AI Direction Prompts

- "butterfly wings" → Lorenz, classic parameters
- "circular/spiral" → Rössler
- "dense/turbulent" → Increase ρ (Lorenz) or c (Rössler)
- "meditative/slow" → Slow camera orbit, long trails
- "chaotic/energetic" → Fast parameter drift, short trails
- "ethereal/glowing" → Additive blending, many particles, low individual opacity

## Integration with PyReeler

```python
from experimental.tools.attractors import generate_lorenz, render_frame

# Precompute trajectory (expensive, do once)
trajectory = generate_lorenz(n_points=5000, n_particles=500)

# Render per frame (cheap)
def render(frame_num, total_frames):
    angle = 2 * np.pi * frame_num / total_frames  # One full rotation
    return render_frame(trajectory, angle, width=1280, height=720)
```

## Dependencies

- NumPy
- Pillow (for image output)

## References

- Lorenz, E. N. (1963). "Deterministic Nonperiodic Flow"
- Pickover, C. (1990). "Computers, Pattern, Chaos and Beauty"

---

*Status: Ready to implement*
