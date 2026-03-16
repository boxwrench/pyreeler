# Hardware Spec Template

Copy this file and rename with your machine (e.g., `ryzen-9-rtx4070.md`).

## Machine
- **CPU:**
- **GPU:**
- **RAM:**
- **OS:**
- **Python:**

## FFmpeg Encoding

### Encoder Performance (fastest to slowest)
1.
2.
3.

### Recommended Settings
| Use Case | Encoder | CRF | Preset | Workers |
|----------|---------|-----|--------|---------|
| Preview (fast) | | | | |
| Preview (quality) | | | | |
| Final | | | | |

## Performance Benchmarks

### Strange Attractors
- 1280×720, 1000 particles: ___ seconds/frame
- 1920×1080, 1000 particles: ___ seconds/frame
- Optimal worker count: ___

### FM Synthesis
- 60s audio @ 48kHz: ___ seconds to generate
- Memory usage: ___ MB

### Reaction-Diffusion
- 256×256 grid: ___ seconds/frame
- 512×512 grid: ___ seconds/frame

## Gotchas
-
-
-

## Optimal Workflow
1. Preview at ___
2. Test render at ___
3. Final render at ___

---
*Created: YYYY-MM-DD*
