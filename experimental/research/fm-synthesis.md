# FM Synthesis from Scratch

Frequency Modulation synthesis using pure NumPy. No SoundFont files, no FluidSynth binaries—just math.

## Overview

FM synthesis creates complex timbres by modulating the frequency of a carrier wave with a modulator wave. The modulator's amplitude (index) determines how much the carrier's frequency deviates, creating sidebands that form the harmonic content.

## Basic Formula

```
output(t) = sin(2π × carrier_freq × t + index × sin(2π × mod_freq × t))
```

## Python Implementation

```python
import numpy as np

def fm_wave(duration, sample_rate, carrier, modulator, index):
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

# Example: Bell-like tone
tone = fm_wave(2.0, 48000, 440, 440, 2.0)  # C:A ratio 1:1
```

## Musical Ratios (Carrier:Modulator)

| Ratio | Character | Use Case |
|-------|-----------|----------|
| 1:1 | Hollow, metallic | Bells, chimes |
| 2:1 | Bright, brassy | Trumpets, horns |
| 3:1 | Reedy, woody | Clarinets, woodwinds |
| 1:2 | Inharmonic, clangorous | Gongs, cymbals |
| 3:2 | Warm, organ-like | Pads, organs |
| 5:4 | Mellow, vocal | Vowel sounds |

## Index Ranges

| Index | Effect |
|-------|--------|
| 0-1 | Sine-like, few harmonics |
| 1-3 | Clear timbre, moderate harmonics |
| 3-5 | Bright, rich harmonics |
| 5-10 | Complex, potentially noisy |
| 10+ | Chaotic, inharmonic |

## Envelopes

FM sounds lifeless without envelopes. Use ADSR:

```python
def adsr_envelope(duration, sample_rate, attack, decay, sustain, release):
    """Generate ADSR envelope (0-1 range)."""
    samples = int(duration * sample_rate)
    env = np.zeros(samples)

    attack_s = int(attack * sample_rate)
    decay_s = int(decay * sample_rate)
    release_s = int(release * sample_rate)
    sustain_s = samples - attack_s - decay_s - release_s

    # Attack
    env[:attack_s] = np.linspace(0, 1, attack_s)
    # Decay
    env[attack_s:attack_s+decay_s] = np.linspace(1, sustain, decay_s)
    # Sustain
    env[attack_s+decay_s:attack_s+decay_s+sustain_s] = sustain
    # Release
    env[-release_s:] = np.linspace(sustain, 0, release_s)

    return env

# Bell: quick attack, no sustain, long release
bell_env = adsr_envelope(2.0, 48000, 0.01, 0.1, 0.0, 1.5)
tone = fm_wave(2.0, 48000, 440, 440, 2.0) * bell_env
```

## Chaining Operators (DX7-style)

Multiple FM operators in series or parallel:

```python
def fm_cascade(t, freq, ratios, indices):
    """Series FM: modulator modulates modulator modulates carrier."""
    phase = 0
    for ratio, index in zip(reversed(ratios), reversed(indices)):
        phase = index * np.sin(2 * np.pi * freq * ratio * t + phase)
    return np.sin(2 * np.pi * freq * t + phase)

# 3-operator chain: mod2 → mod1 → carrier
# freq=220, ratios=[1, 2, 3], indices=[2, 1.5, 1]
```

## AI Direction Prompts

**Useful parameter vocabularies for AI direction:**

- "metallic" → 1:1 ratio, medium index (2-4)
- "brassy" → 2:1 ratio, high index (4-6)
- "wooden/reedy" → 3:1 or 3:2 ratio
- "bell" → 1:1, quick decay, no sustain
- "drone" → long attack, long sustain
- "percussive" → quick attack, no sustain
- "bright" → increase index
- "muffled" → decrease index, lower ratio

## Performance Notes

- Single FM wave: negligible compute
- 1000 simultaneous voices: still fast (vectorized NumPy)
- Bottleneck is usually writing to disk, not generation
- For real-time preview, use lower sample rate (22050)

## Integration with PyReeler

```python
# In your film script
from experimental.tools.fm_synth import fm_wave, adsr_envelope

def make_hit_sound(frame, fps):
    """Generate a percussion hit synchronized to visual event."""
    time = frame / fps
    # Trigger on beat
    if abs(time % 0.5) < 0.01:  # Every half second
        tone = fm_wave(0.3, 48000, 200, 200, 3.0)
        env = adsr_envelope(0.3, 48000, 0.001, 0.1, 0.0, 0.2)
        return tone * env
    return None
```

## Dependencies

- NumPy only

## References

- Chowning, J. (1973). "The Synthesis of Complex Audio Spectra by Means of Frequency Modulation"
- DX7 manual for algorithm diagrams

---

*Status: Ready to implement*
