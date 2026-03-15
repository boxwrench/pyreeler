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
- Status: referenced from earlier work, not yet traced to its source file here
- Working understanding:
  - likely more particles, much smaller size, lower alpha, slower motion, and stronger blur
  - NumPy may help, but the look mainly comes from those rendering choices
- Next step:
  - identify the earlier source file and add exact code notes
