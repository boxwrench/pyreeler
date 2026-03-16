# Reaction-Diffusion Sampler Film - Production Notes

## Findings from RD Film Iterations

### v1: Initial Attempt
- Static holds in parameter sequences
- Visuals didn't change much until 20s
- Pattern looked "frozen" during hold periods

### v2: Oscillating Parameters
- Replaced holds with oscillations
- Parameters change every 3-5 seconds
- Better, but still slow to respond visually

### v3: Dramatic Early Changes
- **Big amplitude jumps**: F=0.0545 ↔ 0.040 (coral to fingerprint)
- **Frequent changes**: Every 2 seconds
- **Mode switches early**: V → U at 4s, both at 8s
- **Contrast swings**: 1.0 → 1.8 → 0.8

**Result**: First 10s now visibly dynamic

---

## Key Insights

### RD Pattern "Inertia"
Gray-Scott patterns have temporal momentum. Even with large parameter jumps, the pattern takes time to morph. The simulation needs 10-30 steps to show visible change.

**Implication**: Parameter changes need to be either:
1. **Very large** (regime jumps) to force visible morphing
2. **Combined with post-processing** (mode switches, contrast) for instant feedback

### Effective Techniques
| Technique | Response Time | Visual Impact |
|-----------|---------------|---------------|
| F/k parameter drift | 5-10s | Gradual morphing |
| Mode switches (V/U/both) | Instant | Immediate flip |
| Contrast swings | Instant | Brightness flash |
| Grid size changes | 10-20s | Resolution shift |

### What Works for Early Engagement
- **Contrast pulses**: Immediate brightness variation
- **Mode switches**: Instant visual recontextualization
- **Large parameter jumps**: Force pattern regime changes
- **Frequent small changes**: Better than infrequent large ones

---

## Technical Performance

| Grid Size | FPS | Notes |
|-----------|-----|-------|
| 128×128 | ~1000 | Too small, pixelated |
| 256×256 | ~250 | **Sweet spot** for 60s films |
| 512×512 | ~60 | 4× slower, sharper |

**Pre-warming essential**: 300 steps before filming establishes stable pattern.

---

## Parameter Regimes (Pearson 1993)

| Pattern | F | k | Visual |
|---------|---|---|--------|
| Coral | 0.0545 | 0.062 | Branching, organic |
| Fingerprint | 0.037 | 0.060 | Stripes, labyrinth |
| Spots | 0.025 | 0.060 | Stable dots |
| Chaos | 0.026 | 0.051 | Turbulent |
| Mitosis | 0.022 | 0.051 | Dividing cells |

---

## Render Mode Effects

- **V (activator)**: Black background, white pattern
- **U (inhibitor)**: White background, black pattern (inverse)
- **both (false color)**: Cyan/magenta overlay

Switching modes mid-film creates immediate visual contrast without waiting for pattern evolution.

---

## Next Time

For future RD films:
1. Start with mode switches in first 5s
2. Use contrast pulses as "visual beats"
3. Combine parameter drift + mode switches
4. Consider grid size shifts for dramatic effect
5. Audio should map to visible changes (contrast, mode)

---

## References

- Pearson, J. E. (1993). "Complex Patterns in a Simple System"
- Karl Sims RD Tutorial: https://karlsims.com/rd.html
