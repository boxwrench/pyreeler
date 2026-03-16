# Reaction-Diffusion

Simulating chemical reactions on a grid to produce organic patterns. Gray-Scott, Turing patterns, and variants.

## Overview

Two chemicals (U and V) react and diffuse on a grid. Simple rules create complex patterns: spots, stripes, spirals, coral-like growth.

## Gray-Scott Equations

```
dU/dt = Du * ∇²U - U*V² + F*(1-U)
dV/dt = Dv * ∇²V + U*V² - (F+k)*V
```

Where:
- Du, Dv: Diffusion rates (U diffuses faster)
- F: Feed rate
- k: Kill rate
- ∇²: Laplacian (blurring)

## Python Implementation

```python
import numpy as np
from scipy.ndimage import convolve

def laplacian(grid):
    """5-point stencil Laplacian."""
    kernel = np.array([[0, 1, 0],
                       [1, -4, 1],
                       [0, 1, 0]])
    return convolve(grid, kernel, mode='nearest')

def gray_scott_step(U, V, Du=0.16, Dv=0.08, F=0.035, k=0.06, dt=1.0):
    """Single simulation step."""
    Lu = laplacian(U)
    Lv = laplacian(V)

    uvv = U * V * V

    U += (Du * Lu - uvv + F * (1 - U)) * dt
    V += (Dv * Lv + uvv - (F + k) * V) * dt

    return U, V

def init_gray_scott(size=256):
    """Initialize with noise and central seed."""
    U = np.ones((size, size))
    V = np.zeros((size, size))

    # Seed center
    r = size // 10
    center = size // 2
    U[center-r:center+r, center-r:center+r] = 0.5
    V[center-r:center+r, center-r:center+r] = 0.25

    # Add noise
    U += np.random.randn(size, size) * 0.01
    V += np.random.randn(size, size) * 0.01

    return U, V
```

## Parameter Regimes

| Pattern | F | k | Character |
|---------|---|---|-----------|
| Coral | 0.0545 | 0.062 | Growing branches |
| Fingerprint | 0.037 | 0.06 | Parallel stripes |
| Spots | 0.025 | 0.06 | Stable dots |
| Chaos | 0.026 | 0.051 | Turbulent |
| Mitosis | 0.022 | 0.051 | Dividing cells |

## Rendering

```python
def render_gray_scott(U, V, mode='V'):
    """Render chemical concentration to image.

    mode: 'U' = inhibitor (black background, white spots)
          'V' = activator (white background, black spots)
          'both' = false color
    """
    if mode == 'U':
        return (U * 255).astype(np.uint8)
    elif mode == 'V':
        return (V * 255).astype(np.uint8)
    else:
        # False color: U in red, V in blue
        rgb = np.zeros((*U.shape, 3), dtype=np.uint8)
        rgb[:, :, 0] = (U * 255).astype(np.uint8)
        rgb[:, :, 2] = (V * 255).astype(np.uint8)
        return rgb
```

## Animation Strategies

### 1. Parameter Drift
Slowly sweep through pattern regimes:
```python
F = 0.035 + np.sin(frame * 0.001) * 0.01
k = 0.06 + np.cos(frame * 0.001) * 0.005
```

### 2. Multiple Seeds
Start with different initial conditions, crossfade between simulations.

### 3. Temporal Accumulation
Each frame is one simulation step. Film is just the simulation playing out.

## Performance Notes

- Grid size matters: 256×256 is fast, 512×512 is 4× slower
- SciPy convolution is optimized but still the bottleneck
- For real-time: use smaller grid, fewer steps per frame
- Numba JIT can speed up 10× if needed

## File Size

- Organic patterns compress reasonably well
- Fine stripes/fingerprint patterns: harder to compress
- Use CRF 25-28 for web-friendly sizes

## Dependencies

- NumPy
- SciPy (for ndimage.convolve)

## Alternative: Simple Blur Instead of Laplacian

If SciPy unavailable, use simple box blur:

```python
def simple_laplacian(grid):
    """Approximate Laplacian with simple blur."""
    blurred = (np.roll(grid, 1, 0) + np.roll(grid, -1, 0) +
               np.roll(grid, 1, 1) + np.roll(grid, -1, 1)) / 4
    return blurred - grid
```

## AI Direction

- "coral growth" → F=0.0545, k=0.062
- "zebra stripes" → F=0.037, k=0.06
- "living cells" → F=0.022, k=0.051
- "slow evolution" → Small dt, gradual parameter drift
- "rapid transformation" → Large dt, oscillating parameters

## References

- Pearson, J. E. (1993). "Complex Patterns in a Simple System"
- [Reaction-Diffusion Tutorial](https://karlsims.com/rd.html)

---

*Status: Documented, needs SciPy dependency check*
