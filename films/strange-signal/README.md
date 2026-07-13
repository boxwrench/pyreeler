# Strange Signal

Status: AI-workflow experiment, not a showcase film.

This experiment tested the intended PyReeler boundary after v0.1:

- the non-AI CLI/TUI remains a simple, fully offline attractor renderer;
- the AI skill can build a bespoke film with structured motion, procedural
  audio, multiprocessing, and capability-tested encoding.

## Brief

A 20-second atmospheric/techno signal study. A contained orbital form develops,
a second field intrudes, both collapse near the midpoint, and the combined
signal returns before resolving to one pulse.

## Render

From the repository root:

```powershell
python films/strange-signal/render_preview.py "$HOME\Videos\strange-signal-ai-preview.mp4"
```

Use `--frames 4` for a short worker/encoder smoke test. The renderer obtains its
FFmpeg path, encoder arguments, and worker count from the canonical runtime
helper; frames stream directly to FFmpeg and procedural audio is muxed as AAC.

## Result

The technical workflow passed on Windows with four workers and NVIDIA NVENC:
400 H.264 frames at 480x270 and 20 fps, plus 48 kHz mono AAC audio, for exactly
20 seconds.

The artistic result was serviceable but only a loose interpretation of the
brief. It demonstrated a visible structural connection without reaching
showcase quality. Keep it as workflow evidence and a prompt-to-structure
learning example; do not treat its visual choices as a reusable house style.

One implementation seam appeared: directly executed film scripts need an
explicit repository-root bootstrap before importing canonical `templates.*`
helpers. Do not generalize a launcher until another film repeats that need.
