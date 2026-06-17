"""Audio-reactive parameter mapping helpers.

Convert mono audio signals into normalized per-frame envelopes so visual
parameters can react to stems or mixes while still being driven by a shared
timeline such as `arc_state(t)`.
"""
from __future__ import annotations

import numpy as np


def rms_envelope(
    signal: np.ndarray,
    sample_rate: int,
    fps: float,
    frame_count: int,
    *,
    window_sec: float = 0.05,
    attack: float = 0.45,
    release: float = 0.12,
) -> np.ndarray:
    """Return a normalized 0..1 RMS envelope, one value per video frame."""
    if sample_rate <= 0:
        raise ValueError("sample_rate must be > 0")
    if fps <= 0:
        raise ValueError("fps must be > 0")
    if frame_count <= 0:
        raise ValueError("frame_count must be > 0")
    if window_sec <= 0:
        raise ValueError("window_sec must be > 0")

    audio = np.asarray(signal, dtype=np.float32)
    if audio.ndim != 1:
        raise ValueError("signal must be mono")

    if audio.size == 0:
        return np.zeros(frame_count, dtype=np.float32)

    half_window = max(1, int(round(window_sec * sample_rate / 2.0)))
    values = np.zeros(frame_count, dtype=np.float32)
    for frame_idx in range(frame_count):
        center = int(round(frame_idx * sample_rate / fps))
        start = max(0, center - half_window)
        end = min(audio.size, center + half_window)
        if end > start:
            segment = audio[start:end]
            values[frame_idx] = float(np.sqrt(np.mean(segment * segment)))

    peak = float(np.max(values)) if values.size else 0.0
    if peak <= 1e-12:
        return values

    values = np.clip(values / peak, 0.0, 1.0)
    attack = float(np.clip(attack, 0.0, 1.0))
    release = float(np.clip(release, 0.0, 1.0))
    smoothed = np.zeros_like(values)
    last = 0.0
    for idx, value in enumerate(values):
        coeff = attack if value > last else release
        last = last + (float(value) - last) * coeff
        smoothed[idx] = last
    return smoothed


def map_range(
    values: np.ndarray,
    out_min: float,
    out_max: float,
    *,
    curve: float = 1.0,
) -> np.ndarray:
    """Map normalized envelope values into a target parameter range."""
    if curve <= 0:
        raise ValueError("curve must be > 0")
    normalized = np.clip(np.asarray(values, dtype=np.float32), 0.0, 1.0)
    shaped = normalized ** float(curve)
    return (float(out_min) + shaped * (float(out_max) - float(out_min))).astype(np.float32)


def reactive_value(
    base: float,
    amount: float,
    envelope_value: float,
    *,
    mode: str = "add",
) -> float:
    """Apply one envelope sample to a scalar base parameter."""
    env = float(np.clip(envelope_value, 0.0, 1.0))
    if mode == "add":
        return float(base) + float(amount) * env
    if mode == "multiply":
        return float(base) * (1.0 + float(amount) * env)
    raise ValueError(f"unknown reactive mode: {mode}")
