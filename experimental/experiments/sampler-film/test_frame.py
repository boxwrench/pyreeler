#!/usr/bin/env python3
"""Test script to isolate the frame 1200 issue."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "tools"))

import numpy as np
from PIL import Image
from attractors import generate_lorenz, generate_rossler, render_frame

W, H = 854, 480
FPS = 24

print("Testing frame rendering around 83% mark...")
print()

# Precompute trajectories (same as main script)
print("Precomputing...")
lorenz_main = generate_lorenz(n_points=3000, n_particles=30)
rossler_main = generate_rossler(n_points=3000, n_particles=30)
lorenz_drift = [generate_lorenz(n_points=1000, n_particles=20, rho=28 + i * 2.4) for i in range(6)]
particle_cloud = generate_lorenz(n_points=2000, n_particles=100)
print("Done.")
print()

# Test frames around 1200
test_frames = [1195, 1196, 1197, 1198, 1199, 1200, 1201, 1202, 1203]

for frame in test_frames:
    second = frame // FPS
    print(f"Frame {frame} ({second}s): ", end="")

    try:
        if second < 15:
            img = render_frame(lorenz_main, frame, FPS * 15, W, H, trail_length=400, brightness=0.4)
        elif second < 20:
            # RD Coral - simplified
            img = Image.new('RGB', (W, H), (50, 50, 50))
        elif second < 30:
            img = Image.new('RGB', (W, H), (60, 60, 60))
        elif second < 40:
            segment_frame = frame - (30 * FPS)
            img = render_frame(rossler_main, segment_frame, FPS * 10, W, H, trail_length=400, brightness=0.5)
        elif second < 50:
            segment_frame = frame - (40 * FPS)
            t = segment_frame / (FPS * 10)
            traj_idx = min(int(t * 6), 5)
            trajectory = lorenz_drift[traj_idx]
            frame_idx = segment_frame % trajectory.shape[0]
            img = render_frame(trajectory, frame_idx, trajectory.shape[0], W, H, trail_length=200, brightness=0.5)
        elif second < 55:
            segment_frame = frame - (50 * FPS)
            img = render_frame(particle_cloud, segment_frame, FPS * 10, W, H, trail_length=100, brightness=0.15)
        else:
            img = Image.new('RGB', (W, H), (0, 0, 0))

        print(f"OK - {img.size}")

    except Exception as e:
        print(f"ERROR - {e}")
        import traceback
        traceback.print_exc()

print()
print("Test complete.")
