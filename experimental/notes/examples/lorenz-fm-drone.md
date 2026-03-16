# Example: Lorenz Attractor + FM Drone

**Contributor:** PyReeler experimental team
**Date:** 2026-03-15
**Status:** Proven combination, ready to use

## Overview

Slowly rotating Lorenz attractor with ethereal FM drone. Meditative, mathematical, slightly uncanny.

## Visual: Lorenz Attractor

### High Quality (Final Render)
```python
# 100 particles, long trails, slow rotation
trajectory = generate_lorenz(
    n_points=8000,
    n_particles=100,
    sigma=10,
    rho=28,
    beta=8/3,
    dt=0.01
)

# Render settings
trail_length = 1000  # Long trails
brightness = 0.3     # Dim individual particles
```

### Preview Quality (Fast Iteration)
```python
# 30 particles, medium trails (vectorized renderer)
from attractors import check_render_safety

trajectory = generate_lorenz(
    n_points=3000,
    n_particles=30,
    sigma=10,
    rho=28,
    beta=8/3,
    dt=0.01
)

# Check safety before rendering
check_render_safety(n_frames=1440, n_particles=30, trail_length=400)
# Returns: (True, 18.0, "Parameters look good.")

trail_length = 400
brightness = 0.4
```

### Key Choices
- **100 particles (final)**: Dense but not overwhelming
- **30 particles (preview)**: Fast iteration, still beautiful
- **Long trails**: Shows history without clutter
- **0.3 brightness**: Allows accumulation without blowing out

## Audio: FM Drone

```python
# Two layered tones
base = fm_wave(60.0, 48000, 110, 110, 1.5)      # 1:1, mellow
harmonic = fm_wave(60.0, 48000, 220, 110, 0.8)  # 2:1, subtle

# Long slow envelope
env = adsr_envelope(60.0, 48000, 5.0, 10.0, 0.7, 20.0)

drone = (base + harmonic * 0.5) * env * 0.5
```

### Key Choices
- **A=110Hz (A2)**: Low enough to be felt, high enough to have presence
- **Index 1.5**: Some harmonics but not harsh
- **Long attack (5s)**: No jarring start
- **20s release**: Fades out gently

## Synchronization

No strict sync. The drone is continuous. The attractor rotation provides visual motion. The combination creates a sense of "mathematical inevitability."

## Render Settings

```python
resolution = (1280, 720)
fps = 24
duration = 60  # seconds
crf = 26  # Geometric patterns, moderate compression
```

## Mood

Dark background, white/grey trails. Could add subtle blue tint in post. Contemplative, slightly ominous, beautiful in an abstract way.

## Variations to Try

| Change | Expected Result |
|--------|----------------|
| rho=45 | More loops, denser pattern |
| 200 particles | More chaotic, harder to read |
| Add velocity coloring | More dynamic visual |
| 2:1 FM ratio | Brighter, more "sci-fi" sound |

## Files

- `experiments/lorenz-drone/` - Full implementation (when created)
- `sampler-film/` - 0-15s segment uses this technique

## Performance Notes

### Vectorized Renderer (2026-03-16)
The attractor renderer now uses NumPy vectorization:
- **Before**: Nested Python loops (~50ms/frame)
- **After**: `np.add.at()` (~3.6ms/frame)
- **Speedup**: ~14x

### Recommended Settings by Use Case

| Use Case | Particles | Trail | Est. Time (60s @ 854×480) |
|----------|-----------|-------|---------------------------|
| Quick test | 10 | 200 | ~2s |
| Preview | 30 | 400 | ~4s |
| Production | 100 | 1000 | ~15s |

### Safety Check
```python
from attractors import check_render_safety

# Always check before long renders
is_safe, est, rec = check_render_safety(
    n_frames=1440, n_particles=100, trail_length=1000
)
# If is_safe is False, reduce parameters
```

## Tags

#strange-attractors #lorenz #fm-synthesis #drone #meditative #dark #mathematical #vectorized
