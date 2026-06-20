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
  - Code references: `assets/showcase/what-the-light-kept/render_preview.py` lines 378, 472
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
  - Code references: `assets/showcase/what-the-light-kept/render_preview.py` lines 134, 197
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
  - Code references: `assets/showcase/what-the-light-kept/render_preview.py` line 265
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
  - Code references: `assets/showcase/what-the-light-kept/render_preview.py` line 310
- Notes:
  - this is definitely a NumPy-driven effect

## Misty Particles

- Name: `misty particles`
- Source reference: `pyreeler_emergence.py` (historical external prototype, not committed)
- Intent: fine-grain, soft, additive particle haze that can coalesce into a form without looking chunky
- Actual implementation:
  - particle positions and velocities are stored as NumPy arrays
  - particles are accumulated into a float image buffer with `np.add.at`
  - multiple blur radii create glow and softness
  - light film grain keeps the field alive
  - Code references: `pyreeler_emergence.py` lines 165, 207, 297, 308
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
- Source reference: `pyreeler_emergence.py` (historical external prototype, not committed)
- Intent: a diffuse particle field gradually resolves into a chosen shape, symbol, word, or silhouette
- Actual implementation:
  - a target mask is rasterized and sampled into many target points
  - particles are pulled toward those target points over time
  - tangential spiral motion is mixed in early so the convergence feels alive rather than linear
  - Code references: `pyreeler_emergence.py` lines 45, 57, 211, 217
- What makes it notable:
  - this is the behavior that lets mist become meaning
  - it works for letters, icons, body-like forms, and memory silhouettes
  - it is separate from the visual texture of the particles themselves
- Reuse guidance:
  - pair with `misty particles` for soft emergence
  - pair with `rough particles` for harsher signal-assembly looks
  - use sampled masks whenever the revealed form should feel discovered instead of drawn
