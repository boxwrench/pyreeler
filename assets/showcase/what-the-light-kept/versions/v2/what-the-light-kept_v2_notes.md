# What the Light Kept - Execution Log

Use this file to document the benchmark run in a way that other users can inspect quickly.

## Prompt

Original user direction:

> we will use pyreeler to make a short film shocaseing its ability with specical care to emotive narrative
>
> i like 3 and well use the partical effect alot here i think, i thin also a machine voice with simple one word queations a ai tries to remember itself from a delete. i also like to use terminal style text and kinda glitchcore cyberpunk
>
> output to the current show case folder. also well benchmark this for an example. well note the prommpt, execution log time and other stuff people may be interesting in seeing to gage the skill

## Working Title

`What the Light Kept`

## Benchmark Intent

Show a complete prompt-to-film workflow with enough metadata for another person to judge both the creative result and the practical execution path.

## Planned Deliverables

- `what-the-light-kept_preview.mp4`
- `what-the-light-kept_720p.mp4` or `what-the-light-kept_1080p.mp4`
- `what-the-light-kept_poster.png`
- benchmark manifest
- audio timeline

## Execution Tracking

- Start time: 2026-03-14 11:31:09
- End time: 2026-03-14 11:31:24
- Wall-clock duration: 14.73 seconds
- Renderer script: `render_preview.py`
- Preview settings: `960x540 @ 18fps`
- Final settings:
- Encoder selected: `h264_nvenc`
- Worker count: `4`
- Requested worker count: `4`
- Parallel mode: `thread`
- Audio dependencies: `numpy`
- Requested voice pipeline: `edge_tts`
- Voice dependencies: `edge_tts`
- Voice fallback used: `True`
- Output files: `what-the-light-kept_preview.mp4`, `what-the-light-kept_poster.png`, `benchmark_manifest.json`

## Notes During Render

- Preview integrity check: full-duration render completed
- Audio check: audio stem mix muxed into preview
- Early section check: sparse boot residue with first voice prompt
- Midpoint rupture check: corruption phase included
- Final hold check: terminal fade and final question included

## Review After Preview

- What landed:
- What felt too generic:
- What needs structural change before upscale:
