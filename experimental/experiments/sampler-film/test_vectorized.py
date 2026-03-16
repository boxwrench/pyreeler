#!/usr/bin/env python3
"""Test vectorized render_frame performance with safety monitoring."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path('../../../tools')))

import time

import numpy as np
from PIL import Image

from attractors import (
    check_render_safety,
    estimate_render_time,
    generate_lorenz,
    render_frame,
    RenderMonitor,
    RenderTimeoutError
)

W, H = 854, 480
FPS = 24
TEST_FRAMES = 120  # 5 seconds worth

print("=" * 60)
print("Vectorized Attractor Renderer - Performance Test")
print("=" * 60)
print()

# Test 1: Safety check for particle cloud parameters
print("1. SAFETY CHECK")
print("-" * 40)

configs = [
    ("Lorenz Orbit", 30, 400, 1200),
    ("Rossler Orbit", 30, 400, 1200),
    ("Lorenz Drift", 20, 200, 240),
    ("Particle Cloud", 200, 100, 120),
]

for name, particles, trail, frames in configs:
    is_safe, est, rec = check_render_safety(
        frames, particles, trail, W, H, raise_warning=False
    )
    status = "OK" if is_safe else "WARN"
    print(f"[{status}] {name}: {est:.1f}s - {rec}")

print()

# Test 2: Actual render timing
print("2. RENDER TIMING TEST")
print("-" * 40)

# Generate a small trajectory
traj = generate_lorenz(n_points=1000, n_particles=50)
print(f"Trajectory shape: {traj.shape}")
print()

# Time single frame rendering
print("Timing 10 frames...")
times = []
for i in range(10):
    start = time.time()
    frame = render_frame(traj, i, TEST_FRAMES, W, H, trail_length=200, brightness=0.5)
    elapsed = time.time() - start
    times.append(elapsed)

avg_time = sum(times) / len(times)
print(f"  Average per frame: {avg_time*1000:.1f}ms")
print(f"  Estimated for 1440 frames: {avg_time * 1440:.1f}s")
print(f"  Frame size: {frame.size}")
print()

# Test 3: Monitor functionality
print("3. MONITOR TEST")
print("-" * 40)

monitor = RenderMonitor(TEST_FRAMES, timeout_seconds=5)  # Short timeout for demo
monitor.start()

try:
    for i in range(TEST_FRAMES):
        monitor.check_frame(i)
        frame = render_frame(traj, i, TEST_FRAMES, W, H, trail_length=100, brightness=0.5)

        if i % 24 == 0:
            print(f"  {monitor.get_progress_str(i)}")

    print(f"  [OK] Completed {TEST_FRAMES} frames")

except RenderTimeoutError as e:
    print(f"  [TIMEOUT] {e}")

print()

# Test 4: Particle cloud stress test
print("4. PARTICLE CLOUD STRESS TEST")
print("-" * 40)

# This is what was causing the hang
is_safe, est, rec = check_render_safety(
    120, 200, 100, W, H, raise_warning=False
)
print(f"Particle cloud (200p, 100 trail, 120 frames):")
print(f"  Safe: {is_safe}")
print(f"  Estimated: {est:.1f}s")
print(f"  Rec: {rec}")

if not is_safe:
    print()
    print("  Reduced parameters for safety:")
    for particles in [100, 50, 30]:
        est = estimate_render_time(120, particles, 100, W, H)
        status = "OK" if est < 60 else "WARN"
        print(f"    [{status}] {particles} particles: {est:.1f}s")

print()
print("=" * 60)
print("Test complete.")
print("=" * 60)
