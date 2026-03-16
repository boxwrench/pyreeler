# Experimental Sampler - Visual Reference Frames

Reference frames captured from the 50-second sampler film, showing each visual technique.

---

## Frame at 6 seconds

**Technique:** Lorenz Attractor (Orbit)
**Audio:** FM Bell → FM Brass transition

![6 seconds](ref_frame_06s.jpg)

### Visual Analysis
- **Pattern:** Clear butterfly-wing spiral structure with accumulation trails
- **Density:** Medium (30 particles, 400 trail length)
- **Quality:** Excellent - characteristic Lorenz "wings" clearly visible
- **Motion:** Slow rotation reveals 3D structure as trails build up

### Render Difficulty: ★★☆☆☆ (Easy)
| Factor | Rating | Notes |
|--------|--------|-------|
| Precompute | Fast | 3000 points × 30 particles |
| Per-frame | Fast | Just rotation + trail rendering |
| Memory | Low | ~700KB trajectory cache |

**Best for:** Meditative openings, mathematical beauty, establishing shots

---

## Frame at 18 seconds

**Technique:** Reaction-Diffusion Coral Growth (Sine Approximation)
**Audio:** Bytebeat + FM Drone layering

![18 seconds](ref_frame_18s.jpg)

### Visual Analysis
- **Pattern:** Radial branching with spiral interference
- **Density:** Uniform, smooth gradients
- **Quality:** Good - organic, coral-like emergence
- **Motion:** Pattern expands outward from center

### Render Difficulty: ★☆☆☆☆ (Very Easy)
| Factor | Rating | Notes |
|--------|--------|-------|
| Precompute | None | Pure math per frame |
| Per-frame | Very Fast | Simple sine operations |
| Memory | None | No cache needed |

**Best for:** Organic transitions, life/emergence themes, soft backgrounds

---

## Frame at 39 seconds

**Technique:** Rössler Attractor (Orbit)
**Audio:** Bytebeat Melodic → FM Woodwind

![39 seconds](ref_frame_39s.jpg)

### Visual Analysis
- **Pattern:** Band-like structure with fold
- **Density:** Sparse (30 particles, shorter trails)
- **Quality:** Dim but visible - characteristic Rössler "ribbon"
- **Motion:** Tighter, more contained than Lorenz

### Render Difficulty: ★★☆☆☆ (Easy)
| Factor | Rating | Notes |
|--------|--------|-------|
| Precompute | Fast | Similar to Lorenz |
| Per-frame | Fast | Simpler structure renders quickly |
| Memory | Low | ~700KB trajectory cache |

**Best for:** Contained chaos, spiral themes, contrast to Lorenz

---

## Frame at 43 seconds

**Technique:** Lorenz Attractor (Parameter Drift)
**Audio:** FM Drone (deep, building)

![43 seconds](ref_frame_43s.jpg)

### Visual Analysis
- **Pattern:** Simplified, more chaotic trajectory
- **Density:** Very sparse (20 particles, 200 trail length, rho=33.6)
- **Quality:** Minimal - drifting parameter thins the structure
- **Motion:** Unstable, beginning to transition

### Render Difficulty: ★★★☆☆ (Moderate)
| Factor | Rating | Notes |
|--------|--------|-------|
| Precompute | Medium | 6 trajectories × 1000 points × 20 particles |
| Per-frame | Fast | Just indexing precomputed arrays |
| Memory | Medium | ~2.4MB for all drift trajectories |

**Best for:** Transformation, instability, transition moments

---

## Render Difficulty Summary

| Technique | Difficulty | Time (854×480) | Visual Impact |
|-----------|------------|----------------|---------------|
| Lorenz Orbit | ★★☆☆☆ | ~15s precompute | High |
| RD Coral (Sine) | ★☆☆☆☆ | None | Medium |
| Rössler Orbit | ★★☆☆☆ | ~15s precompute | Medium |
| Lorenz Drift | ★★★☆☆ | ~30s precompute | Low (transitional) |
| Particle Cloud | ★★☆☆☆ | ~10s precompute | High (chaos) |

## Key Findings

### What Looks Best
1. **Lorenz Orbit at 6s** - Classic, readable, beautiful
2. **RD Coral at 18s** - Surprisingly organic from simple math
3. **Particle cloud** (not shown) - Dense, energetic

### What Doesn't Work as Well
- **Lorenz Drift at 43s** - Too sparse, loses visual interest
  - Fix: Increase particles or trail length for drift segments
  - Or: Use rho values closer to 28 (more loops)

### Compression Notes
- Lorenz attractors: Compress well (black background, sparse lines)
- RD patterns: Compress poorly (smooth gradients, fine detail)
- File size: 5.5MB for 50s at 854×480 = ~0.1MB/second (excellent)

## Render System Updates (2026-03-16)

### Vectorization Fixes
The original particle cloud caused hangs due to nested Python loops. Fixed with:
- **NumPy vectorization**: `np.add.at()` instead of nested loops
- **Particle reduction**: 200 → 100 particles (still visually dense)
- **Performance**: ~21s total render vs indefinite hang

### Safety Utilities Added
```python
from attractors import check_render_safety, RenderMonitor

# Pre-flight check
is_safe, est, rec = check_render_safety(
    n_frames=1440, n_particles=100, trail_length=100
)
# Returns: (True, 12.0, "Parameters look good.")

# Runtime monitoring
monitor = RenderMonitor(total_frames=1440, timeout_seconds=120)
monitor.start()
for i in range(1440):
    monitor.check_frame(i)  # Raises RenderTimeoutError if exceeded
```

### Updated Render Difficulty (Vectorized)

| Technique | Difficulty | Time (854×480) | Key Factor |
|-----------|------------|----------------|------------|
| Lorenz Orbit | ★☆☆☆☆ | ~3s | 30p/400trail |
| RD Coral | ★☆☆☆☆ | ~2s | Pure math |
| Rössler | ★☆☆☆☆ | ~3s | 30p/400trail |
| Lorenz Drift | ★☆☆☆☆ | ~2s | Precomputed array |
| Particle Cloud | ★★☆☆☆ | ~4s | 100p/100trail (was ★★★★★) |

**Previous bottleneck**: Python loops (20,000+ iterations/frame)
**Current**: NumPy vectorization (~3.6ms/frame)

---

*Frames extracted: 2026-03-16*
*Resolution: 854×480*
*Renderer: Vectorized NumPy (14x speedup)*
