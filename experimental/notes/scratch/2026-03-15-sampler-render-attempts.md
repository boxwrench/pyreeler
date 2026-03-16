# Sampler Render Attempts - 2026-03-15

## Attempt 1: 720p Sequential
- **Settings:** 1280×720, 50 particles, trail_length=800
- **Result:** Too slow, abandoned after ~5 minutes
- **Issue:** Attractor precomputation (5000 steps × 50 particles) is heavy

## Attempt 2: 480p Parallel (Multiprocessing)
- **Settings:** 854×480, multiprocessing with 23 workers
- **Result:** Failed - TypeError with render_segment() signature
- **Issue:** ordered_frame_map passes single arg, function expected 2

## Attempt 3: 480p Sequential
- **Settings:** 854×480, 30 particles, n_points=3000, trail_length=400
- **Progress:**
  - Audio generated successfully (60s)
  - Video reached 83% (1200/1440 frames)
  - File size: 2.3MB when interrupted
- **Issue:** Process hung at 83%, FFmpeg didn't finalize MP4

## Root Causes

### The 83% Hang
Likely causes:
1. Lorenz Drift segment (40-50s) generates new trajectory each frame
2. Parameter drift requires regenerating attractor with different rho
3. Not actually precomputed - computed on the fly

### FFmpeg MP4 Corruption
FFmpeg needs proper termination:
- `stdin.close()` done
- `ffmpeg.wait()` done
- But if process is killed, moov atom not written

## Working Parameters (Estimated)

Based on successful frame generation up to 83%:

| Setting | Value | Status |
|---------|-------|--------|
| Resolution | 854×480 | ✓ Good |
| Lorenz particles | 30 | ✓ Good |
| Lorenz points | 3000 | ✓ Good |
| Trail length | 400 | ✓ Good |
| FPS | 24 | ✓ Good |

## Fixes Needed

### 1. Precompute All Trajectories
Current code:
```python
# Lorenz Drift generates fresh trajectory per frame
rho = 28 + t * 12
trajectory = generate_lorenz(n_points=500, n_particles=30, rho=rho)
```

Fix: Precompute 6 trajectories with different rho values once at startup.

### 2. Use MKV or TS Container
MP4 requires moov atom at end. MKV/TS is more resilient to interruption.

### 3. Simplify RD Segment
Current RD uses sine approximation. Either:
- Use real Gray-Scott with scipy
- Use simpler visual placeholder

## Next Attempt Settings

```python
W, H = 854, 480
FPS = 24

# Precompute all attractors at module level
LORENZ_MAIN = generate_lorenz(n_points=3000, n_particles=30)
ROSSLER_MAIN = generate_rossler(n_points=3000, n_particles=30)
LORENZ_DRIFT = [generate_lorenz(n_points=1000, n_particles=20, rho=28+i*2) for i in range(6)]
PARTICLE_CLOUD = generate_lorenz(n_points=2000, n_particles=100)

# Use container format that survives crashes
output = "experimental_sampler.mkv"  # Not mp4
```

## Estimated Render Time

At 854×480 with optimized params:
- Audio generation: ~2s
- Attractor precompute: ~10s
- Frame rendering: ~30-60s (1440 frames)
- Mux: ~5s
- **Total: ~2 minutes**

## Hardware Notes

Machine: Windows 11, Python 3.14
- Sequential rendering is CPU-bound
- Multiprocessing would help but Windows pickling is tricky
- Memory usage: ~200MB with these settings

---

## Attempt 4: SUCCESS - Disk-Based Rendering (50s)

**Settings:** 854×480, 50s, disk-based frames
**Changes:**
- Fixed precomputation (all trajectories at startup)
- Write PNG frames to disk, then FFmpeg encode (no stdin pipe)
- Cut to 50s to avoid particle cloud issue

**Result:** ✓ **SUCCESS!** `experimental_sampler.mp4` - 5.5MB
- 1200 frames rendered, 50 seconds, valid MP4
- Audio: FM synthesis + bytebeat working correctly

**Timeline:**
- Audio: ~2s
- Precompute: ~10s
- Frame render: ~60s
- Encode: ~10s
- **Total: ~90 seconds**

**Key Finding:** FFmpeg stdin piping hangs on Windows. Disk-based is reliable.

---

## Attempt 5: FULL SUCCESS - Vectorized Renderer (60s)

**Date:** 2026-03-16
**Settings:** 854×480, 60s, vectorized renderer

### What Fixed It
1. **NumPy vectorization** - Replaced nested loops with `np.add.at()`
   - 14x speedup: 3.6ms/frame vs 50ms/frame
   - Eliminated Python iteration overhead
2. **Reduced particle count** - 200 → 100 particles for cloud
   - Still visually dense
   - Render time acceptable (~4s for 240 frames)
3. **Disk-based rendering** - PNG frames → FFmpeg encode
   - More reliable than stdin pipe on Windows
   - Slight overhead but consistent

### Final Stats
| Metric | Value |
|--------|-------|
| Duration | 60 seconds |
| Resolution | 854×480 |
| Frames | 1,440 |
| File size | 6.3 MB |
| Render time | ~21 seconds |
| Techniques | 4 visual × 4 audio |

### Safety System Now Available
```python
from attractors import check_render_safety, RenderMonitor

# Pre-flight check
check_render_safety(n_frames=1440, n_particles=100, trail_length=100)

# Runtime monitoring with auto-bailout
monitor = RenderMonitor(total_frames=1440, timeout_seconds=120)
```

### Lessons Learned
- **Vectorization matters**: Nested Python loops kill performance at scale
- **Precompute everything**: ODE solving during frame loop is a death sentence
- **Monitor progress**: Timeouts prevent infinite hangs
- **Start small, scale up**: Test at 30 particles before committing to 100

**Status:** COMPLETE - Film rendered successfully, all documentation updated.
