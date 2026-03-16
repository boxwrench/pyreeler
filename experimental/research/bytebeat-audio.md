# Bytebeat Audio

Extreme minimalism: C expressions that generate 8-bit audio. No samples, no oscillators—just bitwise math on time.

## Overview

Bytebeat originated from the demoscene. The formula is the waveform. Change the formula, change the sound entirely.

## The Formula

```
sample(t) = expression(t) & 255
```

Output is 8-bit unsigned (0-255). Center at 128 for signed.

## Python Implementation

```python
import numpy as np

def bytebeat(formula, duration, sample_rate=8000):
    """Generate audio from bytebeat formula.

    Args:
        formula: Lambda taking t (int) returning int
        duration: Length in seconds
        sample_rate: Usually 8000 for authentic bytebeat

    Returns:
        numpy array float32 (-1 to 1)
    """
    t = np.arange(int(duration * sample_rate))
    # Vectorize the formula
    samples = np.array([formula(ti) for ti in t], dtype=np.int32)
    samples = samples & 255  # 8-bit mask
    # Convert to float -1 to 1
    return ((samples - 128) / 128).astype(np.float32)

# Classic formulas
def formula1(t):
    return t * (t >> 12 & (t >> 8 | t >> 14) & 63 | t >> 4)

def formula2(t):
    return (t * (t >> 5 | t >> 8)) >> (t >> 16)

# Generate
audio = bytebeat(formula1, 10.0, 8000)
```

## Classic Formulas

| Formula | Description |
|---------|-------------|
| `t*(t>>12&((t>>8\|t>>14)&63\|t>>4))` | Rhythmic, industrial |
| `(t*(t>>5\|t>>8))>>(t>>16)` | Evolving melody |
| `t*((t>>12\|t>>8)&63&4)` | Simple drone |
| `t*(0xCA98>>(t>>9&14)&15)\|t>>8` | Arpeggio-like |
| `(t*5&t>>7)\|(t*3&t>>10)` | Glitchy percussion |

## Evolving Formulas

Crossfade between formulas over time:

```python
def morph_bytebeat(t, formulas, weights):
    """Blend multiple formulas."""
    result = 0
    for f, w in zip(formulas, weights):
        result += f(t) * w
    return int(result / sum(weights))

# Fade from formula1 to formula2
weights = [1 - t/max_t, t/max_t]
```

## Filtering

Raw bytebeat is harsh. Soften with simple lowpass:

```python
def simple_lowpass(signal, factor=0.5):
    """Simple exponential moving average filter."""
    result = np.zeros_like(signal)
    result[0] = signal[0]
    for i in range(1, len(signal)):
        result[i] = result[i-1] * factor + signal[i] * (1 - factor)
    return result
```

## When to Use

**Good for:**
- Retro/computer aesthetic
- Rhythmic industrial textures
- Surprising emergent melodies
- Very small file sizes (formula is bytes, not samples)

**Not good for:**
- Traditional musical harmony
- Smooth timbres
- Predictable composition

## AI Direction

Bytebeat is hard to direct musically. Better approach:

1. Generate 10-20 random formulas with structure
2. Human picks promising ones
3. AI sequences/crossfades the selected formulas

Or treat it as texture layer rather than lead element.

## Performance

- Generation: extremely fast (just math)
- Sample rate: typically 8000 Hz (not CD quality—that's the point)
- File size: tiny (just store the formula string)

## Integration with PyReeler

```python
from experimental.tools.bytebeat import bytebeat, formula_rhythmic

# As glitchy texture layer
beat_layer = bytebeat(formula_rhythmic, duration=60, sample_rate=8000)
beat_layer = simple_lowpass(beat_layer, 0.3)  # Soften
beat_layer *= 0.2  # Mix quietly under main audio
```

## Dependencies

- NumPy only

## References

- [Bytebeat: Algorithmic Symphonies](http://canonical.org/~kragen/bytebeat/)
- Vihart's YouTube explainer

---

*Status: Documented, ready to implement*
