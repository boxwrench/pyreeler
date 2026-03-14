from __future__ import annotations

import math

import numpy as np

try:
    from scipy.signal import butter, lfilter
except ImportError:  # pragma: no cover - optional dependency
    butter = None
    lfilter = None


def _rng(seed=None):
    return np.random.default_rng(seed)


def normalize(signal: np.ndarray, peak: float = 0.95) -> np.ndarray:
    signal = np.asarray(signal, dtype=np.float32)
    max_value = float(np.max(np.abs(signal))) if signal.size else 0.0
    if max_value <= 1e-6:
        return signal
    return signal * (peak / max_value)


def _lowpass(signal: np.ndarray, cutoff_hz: float, sample_rate: int) -> np.ndarray:
    if len(signal) == 0:
        return np.asarray(signal, dtype=np.float32)
    if butter is not None and lfilter is not None:
        b, a = butter(2, cutoff_hz / (sample_rate / 2.0), btype="low")
        return lfilter(b, a, signal).astype(np.float32)

    # Fallback one-pole filter when scipy is unavailable.
    alpha = math.exp(-2.0 * math.pi * cutoff_hz / float(sample_rate))
    out = np.empty_like(signal, dtype=np.float32)
    out[0] = signal[0]
    for index in range(1, len(signal)):
        out[index] = (1.0 - alpha) * signal[index] + alpha * out[index - 1]
    return out


def gen_wind(duration_sec: float, sample_rate: int = 44100, intensity: float = 0.5, seed=None) -> np.ndarray:
    num_samples = int(duration_sec * sample_rate)
    rng = _rng(seed)
    white = rng.normal(0.0, 1.0, num_samples).astype(np.float32)
    brown = np.cumsum(white).astype(np.float32)
    brown = normalize(brown)

    t = np.linspace(0.0, duration_sec, num_samples, dtype=np.float32)
    swell = 0.6 + 0.4 * np.sin(2.0 * np.pi * 0.09 * t + 0.3)
    cutoff = 240.0 + 700.0 * intensity
    wind = _lowpass(brown, cutoff_hz=cutoff, sample_rate=sample_rate)
    return normalize(wind * swell, peak=0.55)


def gen_impact(
    duration_sec: float = 0.35,
    fundamental_hz: float = 62.0,
    sample_rate: int = 44100,
    noise_amount: float = 0.1,
    seed=None,
) -> np.ndarray:
    num_samples = int(duration_sec * sample_rate)
    rng = _rng(seed)
    t = np.linspace(0.0, duration_sec, num_samples, dtype=np.float32)

    body = np.sin(2.0 * np.pi * fundamental_hz * t) * np.exp(-8.0 * t)
    body += 0.35 * np.sin(2.0 * np.pi * fundamental_hz * 2.0 * t) * np.exp(-11.0 * t)
    transient = rng.normal(0.0, noise_amount, num_samples).astype(np.float32) * np.exp(-55.0 * t)
    return normalize(body + transient, peak=0.9)


def gen_shimmer(duration_sec: float, sample_rate: int = 44100, seed=None) -> np.ndarray:
    num_samples = int(duration_sec * sample_rate)
    rng = _rng(seed)
    t = np.linspace(0.0, duration_sec, num_samples, dtype=np.float32)

    partials = (
        0.12 * np.sin(2.0 * np.pi * 3520.0 * t)
        + 0.08 * np.sin(2.0 * np.pi * 4400.0 * t + 0.2)
        + 0.05 * np.sin(2.0 * np.pi * 5280.0 * t + 0.4)
    )
    air = rng.normal(0.0, 0.02, num_samples).astype(np.float32)
    envelope = np.exp(-0.45 * t)
    return normalize((partials + air) * envelope, peak=0.4)
