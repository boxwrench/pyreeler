"""FM Synthesis module for PyReeler experimental.

Pure NumPy implementation of Frequency Modulation synthesis.
No SoundFont or FluidSynth required.

Usage:
    from experimental.tools.fm_synth import fm_wave, adsr_envelope

    tone = fm_wave(duration=2.0, sample_rate=48000, carrier=440, modulator=440, index=2.0)
    env = adsr_envelope(duration=2.0, sample_rate=48000, attack=0.01, decay=0.1, sustain=0.0, release=1.5)
    bell = tone * env
"""
import numpy as np


def fm_wave(duration: float, sample_rate: int, carrier: float, modulator: float, index: float) -> np.ndarray:
    """Generate FM synthesized audio.

    Args:
        duration: Length in seconds
        sample_rate: Samples per second (e.g., 48000)
        carrier: Carrier frequency in Hz (fundamental pitch)
        modulator: Modulator frequency in Hz (harmonic ratio)
        index: Modulation index (0-10+, higher = more harmonics)

    Returns:
        numpy array of float32 samples (-1 to 1)
    """
    t = np.linspace(0, duration, int(duration * sample_rate), False)
    mod = index * np.sin(2 * np.pi * modulator * t)
    carrier_wave = np.sin(2 * np.pi * carrier * t + mod)
    return carrier_wave.astype(np.float32)


def adsr_envelope(
    duration: float,
    sample_rate: int,
    attack: float,
    decay: float,
    sustain: float,
    release: float
) -> np.ndarray:
    """Generate ADSR envelope (0-1 range).

    Args:
        duration: Total envelope length in seconds
        sample_rate: Samples per second
        attack: Attack time in seconds
        decay: Decay time in seconds
        sustain: Sustain level (0-1)
        release: Release time in seconds

    Returns:
        numpy array of float32 samples (0 to 1)
    """
    samples = int(duration * sample_rate)
    env = np.zeros(samples, dtype=np.float32)

    attack_s = int(attack * sample_rate)
    decay_s = int(decay * sample_rate)
    release_s = int(release * sample_rate)
    sustain_s = max(0, samples - attack_s - decay_s - release_s)

    # Attack
    if attack_s > 0:
        env[:attack_s] = np.linspace(0, 1, attack_s, dtype=np.float32)

    # Decay
    if decay_s > 0:
        end_decay = min(attack_s + decay_s, samples)
        env[attack_s:end_decay] = np.linspace(1, sustain, end_decay - attack_s, dtype=np.float32)

    # Sustain
    if sustain_s > 0:
        end_sustain = min(attack_s + decay_s + sustain_s, samples)
        env[attack_s + decay_s:end_sustain] = sustain

    # Release
    if release_s > 0:
        start_release = max(0, samples - release_s)
        env[start_release:] = np.linspace(sustain, 0, samples - start_release, dtype=np.float32)

    return env


def bell_tone(
    duration: float = 2.0,
    sample_rate: int = 48000,
    freq: float = 440,
    index: float = 2.0
) -> np.ndarray:
    """Generate a bell-like tone using FM synthesis.

    Args:
        duration: Length in seconds
        sample_rate: Samples per second
        freq: Fundamental frequency
        index: Modulation index (higher = more metallic)

    Returns:
        Audio samples as float32 array
    """
    tone = fm_wave(duration, sample_rate, freq, freq, index)
    env = adsr_envelope(duration, sample_rate, attack=0.01, decay=0.1, sustain=0.0, release=duration - 0.11)
    return tone * env


def brass_tone(
    duration: float = 1.0,
    sample_rate: int = 48000,
    freq: float = 440,
    index: float = 4.0
) -> np.ndarray:
    """Generate a brass-like tone using FM synthesis.

    Args:
        duration: Length in seconds
        sample_rate: Samples per second
        freq: Fundamental frequency
        index: Modulation index (higher = brighter)

    Returns:
        Audio samples as float32 array
    """
    tone = fm_wave(duration, sample_rate, freq, freq * 2, index)
    env = adsr_envelope(duration, sample_rate, attack=0.1, decay=0.2, sustain=0.7, release=0.3)
    return tone * env


def woodwind_tone(
    duration: float = 1.0,
    sample_rate: int = 48000,
    freq: float = 440,
    index: float = 1.5
) -> np.ndarray:
    """Generate a woodwind-like tone using FM synthesis.

    Args:
        duration: Length in seconds
        sample_rate: Samples per second
        freq: Fundamental frequency
        index: Modulation index (lower = mellower)

    Returns:
        Audio samples as float32 array
    """
    tone = fm_wave(duration, sample_rate, freq, freq * 3, index)
    env = adsr_envelope(duration, sample_rate, attack=0.15, decay=0.1, sustain=0.8, release=0.2)
    return tone * env


if __name__ == "__main__":
    # Demo: generate test tones
    import subprocess
    from pathlib import Path

    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)

    sample_rate = 48000

    # Generate various tones
    tones = {
        "bell_440Hz": bell_tone(2.0, sample_rate, 440),
        "bell_880Hz": bell_tone(2.0, sample_rate, 880),
        "brass_220Hz": brass_tone(1.0, sample_rate, 220),
        "woodwind_330Hz": woodwind_tone(1.5, sample_rate, 330),
    }

    print("FM Synthesis Demo")
    print("=" * 40)

    for name, samples in tones.items():
        # Convert float32 (-1 to 1) to int16 for WAV
        samples_int16 = (samples * 32767).astype(np.int16)

        wav_path = output_dir / f"{name}.wav"

        # Write raw PCM and convert with FFmpeg
        raw_path = wav_path.with_suffix('.raw')
        raw_path.write_bytes(samples_int16.tobytes())

        cmd = [
            "ffmpeg", "-y",
            "-f", "s16le",
            "-ar", str(sample_rate),
            "-ac", "1",
            "-i", str(raw_path),
            str(wav_path)
        ]

        result = subprocess.run(cmd, capture_output=True)
        raw_path.unlink()

        if result.returncode == 0:
            print(f"Generated: {wav_path}")
        else:
            print(f"Failed to generate {name}: {result.stderr.decode()[:100]}")

    print("=" * 40)
    print(f"Test files in: {output_dir}")
