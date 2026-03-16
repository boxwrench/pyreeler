# [Technique Name]

**Status:** Research / Working / Graduated
**Category:** Chaotic Maps / Morphogenesis / Physics / Spatial / Audio
**Dependencies:** NumPy, Pillow, (optional: SciPy)
**Date:** YYYY-MM-DD

## Overview

What this technique does and why it's interesting for code-generated film.

## Algorithm

Brief explanation of the math/algorithm:

```
pseudocode or key equations here
```

## Implementation

```python
# Minimal working example
import numpy as np

def generate(params):
    pass

def render(data, frame_num, width, height):
    pass
```

## Parameters

| Parameter | Range | Default | Effect |
|-----------|-------|---------|--------|
| param_a | 0-1 | 0.5 | Controls primary behavior |
| param_b | 0-100 | 50 | Controls secondary behavior |

## AI Direction Vocabulary

Words/phrases that map to parameters:

| User Says | Parameter Change |
|-----------|------------------|
| "smooth" | param_a *= 0.5 |
| "chaotic" | param_a *= 2 |
| "bright" | param_b += 20 |

## Performance Characteristics

| Metric | Estimate | Notes |
|--------|----------|-------|
| Precompute time | ~5s | Depends on resolution |
| Per-frame time | ~10ms | At 854×480 |
| Memory usage | ~10MB | For typical params |

## Safety Limits

```python
# Recommended max values for real-time rendering
MAX_PARAM_A = 1.0
MAX_RESOLUTION = (1280, 720)
```

## Examples

### Basic Usage
```python
from tools.my_technique import generate, render

data = generate(param_a=0.5, param_b=50)
frame = render(data, frame_num=0, width=854, height=480)
```

### With Audio
```python
# How to sync with audio events
```

## References

- Paper/blog/tutorial that inspired this
- Related techniques in this repo

## Hybrid Compatibility

**Combines well with:**
- [Technique A] - Describe the combination effect
- [Technique B] - Describe the combination effect

**Combination patterns:**
- **Pattern 1:** Brief description of how to integrate
- **Pattern 2:** Another integration approach

## Parameter Sequencing

**Supports automation:**
- [ ] No - Interactive only
- [ ] Yes - Record/playback parameter changes

**Sequence characteristics:**
| Property | Description |
|----------|-------------|
| Keyframeable params | List params that can change over time |
| Interpolation | Linear/smooth/step |
| Real-time | Can params change mid-render? |

**Example sequence:**
```python
# Keyframes: (frame, param, value)
keyframes = [
    (0, 'param_a', 0.5),
    (30, 'param_a', 0.8),
    (60, 'param_b', 100),
]
```

## Rendering Notes

**Buffer strategy:**
- [ ] Clear each frame (standard)
- [ ] Persistent accumulation (trails, motion blur)
- [ ] Dual buffer (feedback effects)

**Spatial indexing needed:**
- [ ] No - O(n) or O(n²) is acceptable
- [ ] Yes - Requires grid/quadtree for real-time

**Performance characteristics:**
| Metric | Estimate | Notes |
|--------|----------|-------|
| Precompute time | ~Xs | Context |
| Per-frame time | ~Xms | At resolution |
| Memory usage | ~XMB | For typical params |

## Known Issues / TODO

- [ ] Issue 1
- [ ] Optimization opportunity

---

*Created: YYYY-MM-DD*
*Last modified: YYYY-MM-DD*
