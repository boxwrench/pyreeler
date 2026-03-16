# Pixel Sorting

**Status:** Research
**Category:** Image Processing
**Dependencies:** NumPy, Pillow
**Date:** 2026-03-16

## Overview

Pixel sorting is a glitch-art technique that rearranges pixels in an image based on their values, creating streaks, glitch aesthetics, and data corruption beauty. By sorting pixels along rows or columns (contiguously or at intervals) according to a threshold, the algorithm produces striking visual artifacts that bridge generative art and digital decay.

Unlike noise-based glitch (random corruption), pixel sorting is deterministic and controllable—the "glitch" emerges from ordered operations applied to image data.

## Algorithm

The core operation is simple: sort pixels in a line (row, column, or arbitrary angle) based on a criteria (brightness, hue, saturation). The variations come from:

1. **Which pixels participate** - threshold determines inclusion
2. **Sorting direction** - horizontal, vertical, or angled
3. **Interval spacing** - sort every Nth line, creating stripes
4. **Masking** - sort only within specific regions

### Basic Threshold Sort

```python
for each row in image:
    # Find contiguous runs of pixels above threshold
    runs = find_consecutive_pixels(row, lambda p: brightness(p) > threshold)

    for run in runs:
        sort_run_by_brightness(run)
```

### Interval Sort

```python
for row in range(0, height, interval):
    sort_entire_row_by_brightness(row)
```

## Implementation

```python
import numpy as np
from PIL import Image

def brightness_sort_row(row, threshold):
    """Sort contiguous pixels above brightness threshold."""
    # Convert to HSV for brightness channel
    brightness = np.max(row, axis=1)  # Simple approximation

    # Find contiguous regions above threshold
    mask = brightness > threshold
    changes = np.diff(mask.astype(int))
    starts = np.where(changes == 1)[0] + 1
    ends = np.where(changes == -1)[0] + 1

    # Handle edge cases
    if mask[0]:
        starts = np.insert(starts, 0, 0)
    if mask[-1]:
        ends = np.append(ends, len(mask))

    # Sort each contiguous region
    sorted_row = row.copy()
    for start, end in zip(starts, ends):
        if end > start:
            region = sorted_row[start:end]
            # Sort by brightness (sum of RGB)
            brightness_values = np.sum(region, axis=1)
            sort_indices = np.argsort(brightness_values)
            sorted_row[start:end] = region[sort_indices]

    return sorted_row

def pixel_sort(image, threshold=128, direction='horizontal',
               interval=1, angle=0):
    """
    Apply pixel sorting to image.

    Args:
        image: PIL Image or numpy array (H, W, 3)
        threshold: 0-255, pixels above this brightness get sorted
        direction: 'horizontal', 'vertical', 'angle'
        interval: 1 = every row/column, 2 = every other, etc.
        angle: rotation angle in degrees (for direction='angle')

    Returns:
        numpy array of sorted image
    """
    if isinstance(image, Image.Image):
        img_array = np.array(image)
    else:
        img_array = image.copy()

    if direction == 'horizontal':
        for y in range(0, img_array.shape[0], interval):
            img_array[y] = brightness_sort_row(img_array[y], threshold)

    elif direction == 'vertical':
        for x in range(0, img_array.shape[1], interval):
            column = img_array[:, x]
            sorted_col = brightness_sort_row(column.reshape(-1, 3), threshold)
            img_array[:, x] = sorted_col.reshape(-1, 3)

    elif direction == 'angle':
        # Rotate, sort horizontally, rotate back
        from scipy import ndimage
        rotated = ndimage.rotate(img_array, angle, reshape=False)
        for y in range(0, rotated.shape[0], interval):
            rotated[y] = brightness_sort_row(rotated[y], threshold)
        img_array = ndimage.rotate(rotated, -angle, reshape=False)

    return img_array
```

## Parameters

| Parameter | Range | Default | Effect |
|-----------|-------|---------|--------|
| threshold | 0-255 | 128 | Brightness cutoff for sorting participation |
| direction | horiz/vert/angle | horizontal | Axis along which to sort |
| interval | 1-N | 1 | Row/column spacing (1 = all, 2 = every other) |
| angle | 0-360 | 0 | Rotation angle for directional sorting |
| sort_by | brightness/hue/sat | brightness | Which channel determines sort order |

## AI Direction Vocabulary

Words and phrases that map to parameter adjustments:

| User Says | Parameter Change | Visual Result |
|-----------|------------------|---------------|
| "glitch" | threshold = 50-100, direction = horizontal | Corrupted data streaks |
| "streak" | direction = vertical, interval = 1 | Vertical light trails |
| "data corruption" | threshold = 80-120, interval = 2-4 | Striped glitch pattern |
| "motion blur" | direction = angle, angle = 45, interval = 1 | Diagonal streaks |
| "subtle" | threshold = 180-220 | Minimal sorting, faint trails |
| "extreme" | threshold = 0, interval = 1 | Full image sorted chaos |
| "striped" | interval = 3-10 | Banded glitch effect |
| "diagonal" | direction = angle, angle = 30-60 | Angled streaks |
| "rain" | direction = vertical, threshold = 150 | Falling light drops |
| "scan lines" | interval = 2, direction = horizontal | CRT-style artifacts |

## Performance Characteristics

| Metric | Estimate | Notes |
|--------|----------|-------|
| Precompute time | N/A | No precomputation needed |
| Per-frame time | ~50-200ms | Depends on image size and threshold |
| Memory usage | ~3x image size | Original + working buffer + output |

**Optimization notes:**
- Threshold sort is slower than interval sort (contiguous region detection)
- Vertical sort requires column-wise iteration (cache inefficient)
- Angle sort requires rotation (use scipy.ndimage)

## Safety Limits

```python
# Recommended limits for real-time rendering
MAX_IMAGE_SIZE = (1920, 1080)  # Full HD
MAX_INTERVAL = 50  # Larger is meaningless visually
MIN_THRESHOLD = 0  # 0 = sort everything (intense)
MAX_THRESHOLD = 255  # 255 = sort nothing (no effect)

def check_sort_safety(image_shape, interval, n_frames=1):
    """Estimate if sort operation is safe to run."""
    pixels = image_shape[0] * image_shape[1]
    estimated_time = (pixels / (1920*1080)) * 0.2 * n_frames  # seconds

    if estimated_time > 60:  # > 1 minute
        return False, estimated_time, "Reduce resolution or frame count"
    return True, estimated_time, "OK"
```

## Examples

### Basic Glitch Effect
```python
from PIL import Image
import numpy as np

img = Image.open('input.jpg')
result = pixel_sort(img, threshold=100, direction='horizontal')
Image.fromarray(result).save('glitch_output.jpg')
```

### Animated Sort (Threshold Animation)
```python
# Create sequence with changing threshold
for frame in range(60):
    threshold = 50 + int(frame * 3)  # 50 -> 230
    result = pixel_sort(base_image, threshold=threshold)
    save_frame(result, frame)
```

### Multi-Directional Stacking
```python
# Layer multiple sorts with different parameters
layer1 = pixel_sort(img, threshold=100, direction='horizontal')
layer2 = pixel_sort(img, threshold=150, direction='vertical', interval=2)

# Blend layers
blended = (layer1 * 0.6 + layer2 * 0.4).astype(np.uint8)
```

## References

- Original concept popularized by Kim Asendorf's "pixel sorting" experiments
- Reference implementation: https://github.com/davidullmann271/Pixel-Sorting/
- Related techniques: datamoshing, scanline art, glitch aesthetics

## Hybrid Compatibility

**Combines well with:**

- **Reaction-Diffusion** - Use RD output concentration as sort threshold; sort RD patterns directly for organic glitch
- **Particle Systems** - Post-process particle renders for motion streaks; particles create source texture for sorting
- **Strange Attractors** - Use trajectory density as mask; sort along attractor path angles
- **Flow Fields** - Sort angle follows field vectors; creates flowing streaks aligned with field

**Combination patterns:**

- **Pre-process**: Sort source image before using as texture or mask for other techniques. Creates controlled input corruption.

- **Post-process**: Apply pixel sort to rendered output. Adds stylistic glitch to clean generative renders.

- **Mask-driven**: Use another technique's output as the sort threshold or mask. RD concentration creates organic sorting regions.

- **Sequence-driven**: Animate sort parameters based on another technique's state. Particle density drives threshold changes.

## Parameter Sequencing

**Supports automation:**
- [x] Yes - Record/playback parameter changes

**Sequence characteristics:**
| Property | Description |
|----------|-------------|
| Keyframeable params | threshold, interval, angle |
| Interpolation | Linear for threshold/interval, smooth step for angle |
| Real-time | Parameters can change mid-render (no state dependency) |

**Example sequence:**
```python
# Keyframes: (frame, param, value)
keyframes = [
    (0, 'threshold', 200),    # Subtle start
    (30, 'threshold', 100),   # Increase glitch
    (60, 'direction', 'vertical'),  # Switch direction
    (90, 'threshold', 200),   # Fade out
]
```

## Rendering Notes

**Buffer strategy:**
- [x] Clear each frame (standard) - Each frame sorted independently
- [ ] Persistent accumulation - Not applicable
- [ ] Dual buffer - Not applicable

**Spatial indexing needed:**
- [x] No - O(n) per row/column, pixel operations are local

## Known Issues / TODO

- [ ] Implement mask-based sorting (arbitrary regions)
- [ ] Add HSV and LUV color space support
- [ ] Optimize vertical sort with column-wise numpy operations
- [ ] Explore spiral and radial sort patterns
- [ ] Add edge-detection-driven sorting (sort along edges)

---

*Created: 2026-03-16*
*Last modified: 2026-03-16*
