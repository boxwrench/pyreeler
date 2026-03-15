---
name: pyreeler
description: Design and deliver sub-60-second code-generated films, loops, and experimental motion pieces with a final-product-first workflow. Use when Claude needs to turn a loose idea into a preview, iterate with artistic judgment, export the final piece to the Videos folder, offer upscale options, and keep the production process clean and repeatable without becoming formulaic. Claude can read rendered PNG frames directly for visual review during the preview stage.
---

# PyReeler

## Overview
Use this skill to make short code-generated films that prioritize the final piece over attachment to any one template, effect list, or toolchain.
Keep only the workflow rules that reliably improve the result: make a full-duration preview first, judge the piece on its own terms, deliver the final export to `~/Videos`, offer upscale after preview approval, and delete intermediates unless they are needed for debugging.

## Core Workflow

1. Convert the user's idea into a concrete brief with runtime, format, perceived genre or artistic mode, tone, and desired deliverable.
2. Read `references/creative-lenses.md` before locking structure. Decide what would make this specific kind of piece compelling.
3. Read `references/vocabulary-map.md` when choosing or inventing visual, audio, temporal, textual, or transition strategies.
4. Read `references/audio-pipeline.md` before implementation when the piece has meaningful sound design, score, voice, or sync requirements.
5. Read `references/workflow.md` before implementation and follow the production rules exactly.
6. For Python-based video renders, prefer `templates/video/render_runtime.py` to obtain the ffmpeg path, validated encoder choice, and conservative worker count. Do not hardcode `h264_nvenc`, `h264_qsv`, or fixed worker pools in portable scripts when the runtime helper can be used instead.
7. Before implementation, verify that the chosen renderer or template actually supports the brief fields and behaviors you plan to rely on. Patch the implementation or narrow the brief before rendering if there is a mismatch.
8. Build the fastest credible full-duration preview first. Do not jump straight to a high-resolution final.
9. Review the preview with the user. Read rendered PNG frames directly to make visual judgments about arc, composition, contrast, motif development, and pacing. If the piece is flat, repetitive, or off-mode, change structure or behavior before raising fidelity.
10. After preview approval, offer an upscale choice instead of assuming final resolution.
11. Export approved final outputs to `~/Videos`.

## Creative Standard

- Let perceived genre or artistic mode shape what is appealing, effective, and surprising.
- Treat repetition as a tool. Use it when it establishes, transforms, or recontextualizes a motif.
- Do not optimize for novelty per shot. Optimize for a coherent arc with at least one strong memorable move.
- Use effects, systems, and motifs as tools in service of the piece, not as a preset menu to satisfy.
- If a known pattern feels too familiar, mutate it or invent a new one instead of reusing it by habit.

## Production Rules

- `Preview` means a full-duration piece intended for artistic judgment.
- `Test pass` means a non-user-facing technical check for debugging render speed, scene behavior, or pipeline correctness.
- Always make a preview version first.
- Never present a partial-duration render to the user as the preview.
- If speed is a concern, reduce preview fidelity before reducing runtime: lower resolution, lower fps, cached overlays, simpler passes, lighter effects.
- Always surface the preview to the user before committing to an upscale.
- After preview approval, explicitly offer an upscale option such as `720p`, `1080p`, or `keep preview`.
- Write user-facing deliverables to `~/Videos` unless the user asks for another location.
- Clean up intermediate frames, audio stems, and temporary videos after a successful final render unless the user asks to keep them.
- Keep intermediates when debugging, recompositing, or when the user wants source materials.
- Prefer the simplest toolchain that can achieve the piece. Escalate only when the concept benefits materially.
- After each preview render, verify duration and basic output integrity before presenting it.

### Hardware-Aware Rendering
- In portable Python scripts, prefer `from templates.video.render_runtime import detect_render_runtime` and use the returned `ffmpeg_path`, `video_args`, and `workers` instead of script-local encoder assumptions.
- Prefer hardware encoders only after validation. Treat `h264_qsv`, `h264_nvenc`, `h264_videotoolbox`, or `h264_amf` as optional accelerators, not assumptions. Fall back to `libx264` automatically if the smoke test fails.
- Prefer a dynamic worker cap such as `min(4, os.cpu_count() or 1)` over fixed pool sizes. Tune more aggressively only in local installed copies that target a known machine.
- Prefer streaming frames directly into FFmpeg when practical. Keep on-disk intermediates when caching, debugging, or recomposition is more useful than a pipe.
- For local override of worker count, set `PYREEL_WORKERS_OVERRIDE` in the environment. For local FFmpeg candidates, set `PYREEL_LOCAL_FFMPEG_CANDIDATES` (path-separator-delimited list).

### Pre-Render Hardware Gate
- Before the first full preview render for any portable Python renderer, inspect the generated script and verify all of the following from the code itself:
  - `detect_render_runtime()` is used
  - encoder selection comes from the runtime helper rather than a hardcoded hardware encoder
  - `runtime.workers` is used for actual frame generation, not only for FFmpeg arguments, logging, or unused configuration
  - frames are streamed to FFmpeg instead of writing a temporary frame tree when piping is practical
- Before the first full preview render, run a short worker-path smoke test whenever `runtime.workers > 1` and the script intends to use multiprocessing.
- Treat the worker path as passing only if it starts cleanly on the current machine. If Windows multiprocessing setup fails, patch first and re-check before the full render.
- If any item fails, patch the script first and re-check before rendering.
- Do not proceed to the first full preview render until this verification passes.
- When verifying worker usage, require a concrete code path such as `ordered_frame_map(..., workers=runtime.workers)` or an equivalent worker-backed frame-generation path. Merely printing `runtime.workers`, storing it, or passing it only to FFmpeg does not satisfy this requirement.
- For Windows-safe multiprocessing, prefer top-level worker functions, picklable frame inputs, and a main-guarded entry point. Use `if __name__ == "__main__":` and add `multiprocessing.freeze_support()` when needed for portable scripts.

### Smart Preview Fidelity
- For the "fastest credible preview," start with a modest resolution and frame rate that preserves the piece's arc and readability, then adjust to the work. Increase fps for motion-sensitive pieces, or increase resolution for text or detail-sensitive pieces before committing to a higher-fidelity upscale.

## When To Extend Rather Than Reuse

- The current vocabulary does not match the piece's mode.
- The motif needs a new visual or audio behavior to develop meaningfully.
- The preview is technically competent but emotionally obvious.
- The same scene/effect combination would repeat prior work without adding meaning.
- A reusable shortcut would become the creative premise instead of serving the piece.

## References

- `references/workflow.md`: production loop, export rules, preview/upscale policy, and cleanup behavior.
- `references/creative-lenses.md`: genre-sensitive decision making, motif logic, repetition, rupture, and surprise.
- `references/vocabulary-map.md`: broader creative vocabulary across image, sound, time, text, materiality, transition, and narrative function.
- `references/audio-pipeline.md`: guidance for procedural foley, stem design, SoundFont scoring, mixing, and FFmpeg handoff.
- `templates/audio/`: starter modules for procedural foley, optional scoring, optional voice, and stem mixing.
- `templates/video/`: starter modules for portable render-runtime selection, encoder validation, and worker defaults.
