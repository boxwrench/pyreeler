# Experimental Sampler Film

A 60-second demonstration of PyReeler experimental techniques—5 seconds each, with audio and video interleaved for efficiency.

## Quick Reference

| Time | Visual | Audio | Technique Category |
|------|--------|-------|-------------------|
| 0-5s | Lorenz Attractor (orbit) | FM Bell (A=880Hz) | Attractor + FM |
| 5-10s | Lorenz Attractor (continues) | FM Brass Swell | Attractor + FM |
| 10-15s | Lorenz Attractor (continues) | Bytebeat Glitch | Attractor + Bytebeat |
| 15-20s | Lorenz Attractor (fade) | Bytebeat + FM Drone (layered) | Attractor + Layered |
| 20-25s | Reaction-Diffusion (coral) | FM Drone (continues) | RD + FM |
| 25-30s | Reaction-Diffusion (coral) | FM Brass Build | RD + FM |
| 30-35s | Rössler Attractor (orbit) | Bytebeat Melodic | Attractor + Bytebeat |
| 35-40s | Rössler Attractor (continues) | FM Woodwind | Attractor + FM |
| 40-45s | Lorenz Drift (parameter change) | FM Drone (deep) | Attractor + FM |
| 45-50s | Lorenz Drift (continues) | FM Brass (climax) | Attractor + FM |
| 50-60s | Particle Cloud (chaotic) | Glitch Texture | Attractor + Bytebeat |
| 55-60s | (Particle cloud continues) | Fade to silence | — |

## Why This Structure

### Visual Efficiency
The Lorenz attractor runs continuously for 15 seconds (0-15s). This is efficient—we precompute once and just rotate the camera. The visual stays the same while audio changes, letting the viewer focus on how audio transforms the feel.

### Audio Efficiency
FM Drone (110Hz) starts at 15s and continues through 25s, bridging the Lorenz→Reaction-Diffusion transition. This layering technique smooths visual cuts.

### Demonstration Logic
Each technique gets a "solo" moment before combining:
- 0-5s: Clean FM Bell against known visual
- 10-15s: Bytebeat alone (glitch rhythm)
- 15-20s: **Layering demonstrated** (bytebeat + drone together)
- 30-35s: Bytebeat melodic (different formula)
- 40-50s: **Build and climax** (drone swells to brass)

## Key Parameters

### FM Synthesis
```python
# Bell (0-5s)
carrier = 880      # A5
modulator = 880    # 1:1 ratio
index = 3.0        # Metallic

# Brass (5-10s, 25-30s, 45-50s)
carrier = 220 or 330 or 440
modulator = carrier * 2  # 2:1 ratio
index = 5.0 to 6.0       # Bright

# Drone (15-25s, 40-45s)
carrier = 110 or 55      # Deep A
modulator = carrier      # 1:1 ratio
index = 1.0 to 1.5       # Mellow

# Woodwind (35-40s)
carrier = 330
modulator = carrier * 3  # 3:1 ratio
index = 2.0
```

### Bytebeat Formulas
```python
# Glitch Rhythm (10-15s, 50-55s)
(t * (t >> 8 | t >> 9) & 46 & t >> 8) & 255

# Melodic (30-35s)
((t * (t >> 5 | t >> 8)) >> (t >> 16)) & 255
```

### Attractors
```python
# Lorenz Orbit (0-15s)
sigma=10, rho=28, beta=8/3
particles=50, trail_length=800

# Rössler Orbit (30-40s)
a=0.2, b=0.2, c=5.7
particles=50, trail_length=600

# Lorenz Drift (40-50s)
rho animates 28→40 over 10 seconds
particles=30 (fewer for performance)

# Particle Cloud (50-55s)
particles=200, trail_length=100 (short, chaotic)
```

## Running It

```bash
cd experimental/experiments/sampler-film
python sampler_demo.py
```

Output: `~/Videos/experimental_sampler.mp4`

## Extending

To swap in your own technique:

1. **Add new visual**: Add function to `render_segment()` router
2. **Add new audio**: Add case to `generate_audio_segment()`
3. **Adjust timing**: Change `SEGMENT_DURATION` or segment logic

## What This Proves

- **Pure NumPy/PIL can generate compelling motion**
- **FM synthesis replaces SoundFont for electronic timbres**
- **Bytebeat adds texture layers efficiently**
- **Attractors provide infinite non-repeating footage**
- **Interleaving audio/video techniques maximizes demonstration density**

## Technical Improvements (2026-03-16)

### NumPy Vectorization
The `render_frame()` function uses NumPy vectorization instead of nested Python loops:

```python
# OLD: Nested loops (slow)
for p in range(n_particles):
    for i in range(trail_length):
        img[y, x] += brightness

# NEW: Vectorized (10x faster)
np.add.at(img, (y_valid, x_valid), weights)
```

**Result:** ~3.6ms/frame vs ~50ms/frame (14x speedup)

### Safety Monitoring
Built-in safety checks prevent runaway renders:

```python
from attractors import check_render_safety, RenderMonitor

# Pre-render estimate
is_safe, est_time, rec = check_render_safety(
    n_frames=1440, n_particles=100, trail_length=100
)

# Runtime monitoring with 120s timeout
monitor = RenderMonitor(total_frames=1440, timeout_seconds=120)
```

### Performance (854×480, 60s)

| Segment | Particles | Trail | Render Time |
|---------|-----------|-------|-------------|
| Lorenz Orbit | 30 | 400 | ~3s |
| RD Coral | N/A | N/A | ~2s |
| Rössler | 30 | 400 | ~3s |
| Lorenz Drift | 20 | 200 | ~2s |
| Particle Cloud | 100 | 100 | ~4s |
| **Total** | — | — | **~21s** |

**Previous attempt:** Hung indefinitely at 83% (~frame 1200)
**Current:** Completes 1440 frames in ~21 seconds

## Next Steps

- Replace RD approximation with real Gray-Scott simulation
- Add L-system plant growth segment
- Try feedback FM (self-modulating operator)
- Export stems for external mixing

---

*Created: 2026-03-15*
*Duration: 60 seconds*
*Techniques: 4 visual × 4 audio*
