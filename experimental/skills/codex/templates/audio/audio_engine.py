from __future__ import annotations

import wave
from pathlib import Path

import numpy as np


def place_stem(stem: np.ndarray, total_samples: int, start_sec: float, sample_rate: int) -> np.ndarray:
    out = np.zeros(total_samples, dtype=np.float32)
    raw_start = int(start_sec * sample_rate)
    stem_offset = max(0, -raw_start)
    start = max(0, raw_start)
    available = max(0, len(stem) - stem_offset)
    end = min(total_samples, start + available)
    if end > start:
        out[start:end] = stem[stem_offset : stem_offset + (end - start)]
    return out


def duck_under_voice(stem: np.ndarray, voice: np.ndarray, amount: float = 0.55, floor: float = 0.35) -> np.ndarray:
    if stem.size == 0 or voice.size == 0:
        return stem
    voice_env = np.abs(voice)
    peak = float(np.max(voice_env)) if voice_env.size else 0.0
    if peak <= 1e-6:
        return stem
    voice_env = voice_env / peak
    gain = np.clip(1.0 - (voice_env * amount), floor, 1.0)
    return stem * gain.astype(np.float32)


def simple_master(signal: np.ndarray, drive: float = 1.12, peak: float = 0.95) -> np.ndarray:
    signal = np.tanh(signal * drive).astype(np.float32)
    max_value = float(np.max(np.abs(signal))) if signal.size else 0.0
    if max_value <= 1e-6:
        return signal
    return signal * (peak / max_value)


def mix_stems(stem_map: dict[str, np.ndarray], gains=None, duck_voice: bool = True) -> np.ndarray:
    gains = gains or {}
    total_samples = max((len(stem) for stem in stem_map.values() if stem is not None), default=0)
    if total_samples == 0:
        return np.zeros(0, dtype=np.float32)

    aligned = {}
    for name, stem in stem_map.items():
        if stem is None:
            continue
        padded = np.zeros(total_samples, dtype=np.float32)
        padded[: len(stem)] = stem.astype(np.float32)
        aligned[name] = padded

    if duck_voice and "voice" in aligned:
        for name in ("score", "ambience", "pulse"):
            if name in aligned:
                aligned[name] = duck_under_voice(aligned[name], aligned["voice"])

    mix = np.zeros(total_samples, dtype=np.float32)
    for name, stem in aligned.items():
        mix += stem * float(gains.get(name, 1.0))

    return simple_master(mix)


def write_mono_wav(path, signal: np.ndarray, sample_rate: int = 44100):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = np.clip(signal, -1.0, 1.0)
    pcm = (pcm * 32767).astype(np.int16)
    with wave.open(str(path), "w") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm.tobytes())
