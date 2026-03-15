# What the Light Kept - Effects Catalog

Running catalog of reusable effects, motifs, and audio behaviors from this piece.

## Robot Talk

- Name: `robot talk`
- Intent: machine speech that feels like a computer trying to form language rather than natural narration
- Used in: the question cues before the ending
- Current implementation:
  - procedural beep-speech generated from short tone units
  - slight harmonic doubling
  - fast envelopes with tiny gaps
  - light delayed smear for electronic character
  - Code references: [render_preview.py](/C:/Github/pyreeler/assets/showcase/what-the-light-kept/render_preview.py#L378), [render_preview.py](/C:/Github/pyreeler/assets/showcase/what-the-light-kept/render_preview.py#L472)
- Notes:
  - this is the `r2d2-like` machine-speaking texture you called out
  - the final `me?` is now intended to use real `edge-tts` voice rather than robot talk

## Rough Particles

- Name: `rough particles`
- Intent: visible memory fragments with grit and signal texture
- Used in: most of the film before the final hold
- Current implementation:
  - deterministic trig-driven particle positions
  - medium particle count
  - point-size variation with occasional horizontal streaks
  - light blur over a crisp particle pass
  - Code references: [render_preview.py](/C:/Github/pyreeler/assets/showcase/what-the-light-kept/render_preview.py#L134), [render_preview.py](/C:/Github/pyreeler/assets/showcase/what-the-light-kept/render_preview.py#L197)
- Notes:
  - this is not a NumPy particle simulation
  - the motion logic is mostly math plus Pillow drawing

## Fine Swirl Trace

- Name: `fine swirl trace`
- Intent: many tiny particles swirling into a shape that hints at a heart or a brain
- Used in: the ending under `LIGHT PATTERN RETAINED`, right before the spoken `me?`
- Current implementation:
  - denser, finer particles than `rough particles`
  - stronger blur and lower alpha
  - hybrid heart/brain silhouette with residual swirl motion
  - Code references: [render_preview.py](/C:/Github/pyreeler/assets/showcase/what-the-light-kept/render_preview.py#L265)
- Notes:
  - this is a first approximation only
  - it is still Pillow-drawn and does not yet match the true emergence-style mist field

## Rupture Glitch

- Name: `rupture glitch`
- Intent: structural failure event, not ambient decoration
- Used in: midpoint collapse
- Current implementation:
  - NumPy-backed row shifting
  - red/cyan channel separation
  - line density tied to rupture intensity
  - Code references: [render_preview.py](/C:/Github/pyreeler/assets/showcase/what-the-light-kept/render_preview.py#L310)
- Notes:
  - this is definitely a NumPy-driven effect

## Misty Particles

- Name: `misty particles`
- Source reference: [pyreeler_emergence.py](C:/Users/wests/Downloads/pyreeler_emergence.py)
- Intent: fine-grain, soft, additive particle haze that can coalesce into a form without looking chunky
- Actual implementation:
  - particle positions and velocities are stored as NumPy arrays
  - particles are accumulated into a float image buffer with `np.add.at`
  - multiple blur radii create glow and softness
  - light film grain keeps the field alive
  - Code references: [pyreeler_emergence.py](C:/Users/wests/Downloads/pyreeler_emergence.py#L165), [pyreeler_emergence.py](C:/Users/wests/Downloads/pyreeler_emergence.py#L207), [pyreeler_emergence.py](C:/Users/wests/Downloads/pyreeler_emergence.py#L297), [pyreeler_emergence.py](C:/Users/wests/Downloads/pyreeler_emergence.py#L308)
- What makes it look different from `rough particles`:
  - much higher particle count
  - additive density instead of individually drawn dots as the main visual impression
  - softer glow stack
  - vectorized motion and target pull
- Reuse guidance:
  - use this when the image should feel like memory vapor, signal mist, or thought-cloud emergence
  - combine with a shape mask when you want particles to imply form rather than draw a hard outline

## Target-Form Emergence

- Name: `target-form emergence`
- Source reference: [pyreeler_emergence.py](C:/Users/wests/Downloads/pyreeler_emergence.py)
- Intent: a diffuse particle field gradually resolves into a chosen shape, symbol, word, or silhouette
- Actual implementation:
  - a target mask is rasterized and sampled into many target points
  - particles are pulled toward those target points over time
  - tangential spiral motion is mixed in early so the convergence feels alive rather than linear
  - Code references: [pyreeler_emergence.py](C:/Users/wests/Downloads/pyreeler_emergence.py#L45), [pyreeler_emergence.py](C:/Users/wests/Downloads/pyreeler_emergence.py#L57), [pyreeler_emergence.py](C:/Users/wests/Downloads/pyreeler_emergence.py#L211), [pyreeler_emergence.py](C:/Users/wests/Downloads/pyreeler_emergence.py#L217)
- What makes it notable:
  - this is the behavior that lets mist become meaning
  - it works for letters, icons, body-like forms, and memory silhouettes
  - it is separate from the visual texture of the particles themselves
- Reuse guidance:
  - pair with `misty particles` for soft emergence
  - pair with `rough particles` for harsher signal-assembly looks
  - use sampled masks whenever the revealed form should feel discovered instead of drawn
