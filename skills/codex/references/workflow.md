# Workflow

## 1. Frame the piece

- Define duration, format, tone, and perceived genre or artistic mode.
- Decide whether the piece is primarily narrative, poetic, atmospheric, ritual, confrontational, or loop-based.
- Keep the brief lightweight. Only lock the decisions needed to build a useful preview.
- Distinguish early between artistic intent and implementation assumptions. If the brief depends on specific text, per-beat metadata, effect toggles, or audio logic, verify the renderer supports them before you render.
- If audio carries meaning in the piece, decide early what it must do: establish space, provide propulsion, punctuate transitions, or carry the final landing.

## 2. Plan the audio architecture

- If the film needs more than a simple bed, plan audio as stems rather than one monolithic soundtrack.
- Prefer a small reusable structure such as ambience, pulse, impacts, score, and voice.
- Keep audio timing tied to the same scene or beat structure that drives the visuals.
- Prefer procedural foley and algorithmic composition before introducing heavy sample libraries.
- If instrumental timbre matters, use a small SoundFont workflow rather than ad hoc downloaded assets.

## 3. Build the preview first

- `Preview` means a full-duration piece for artistic review.
- `Test pass` means a technical or debugging render and must not be presented as the preview.
- For portable Python renderers, perform a script-level hardware gate before the first full preview render.
- Confirm `detect_render_runtime()` is used, encoder selection comes from the runtime helper, `runtime.workers` drives actual frame generation, and FFmpeg piping is used when practical.
- If `runtime.workers > 1`, run a short worker-path smoke test before the first full preview render.
- Require the multiprocessing path to start successfully on the current machine before you count worker support as passing.
- If any hardware-gate item fails, patch and re-check before rendering. Do not spend a full preview render on a known-failing runtime path.
- Make the fastest credible full-duration preview before investing in high resolution or heavy passes.
- Default preview target: low-resolution, fast-turnaround, enough fidelity to judge arc, pacing, contrast, motif, and tone.
- If the request is experimental, prefer speed of iteration over polish on the first pass, but preserve the full runtime.
- Reduce fidelity before reducing duration: lower resolution, lower fps, lighter passes, cached static overlays, and simplified compositing.
- For audio, simplify layers before deleting the structural cues that make the film readable.
- In portable Python renderers, prefer `templates/video/render_runtime.py` for ffmpeg path, validated encoder selection, and default worker count rather than script-local codec defaults.

## 4. Review the preview

- Judge the preview on its own terms, not against a generic checklist.
- Ask whether the piece has a clear internal logic.
- Ask whether repetition is doing useful work.
- Ask whether motifs evolve rather than merely recur.
- Ask whether pacing across the full runtime supports the intended emotional mode.
- Ask whether the peak, rupture, or transformation actually lands.
- Ask whether the sound and image reinforce the same arc rather than telling competing stories.
- If the preview is merely competent, change the structure or motif behavior before increasing fidelity.

## 5. Verify before presenting

- Check that the preview duration matches the brief.
- Check that the output opens correctly and includes expected audio.
- Spot-check representative frames or moments from early, middle, and late sections before showing the piece to the user.

## 6. Offer upscale only after approval

- Do not assume the preview should become the final.
- Once the preview is approved, offer a concrete upscale decision:
  - `720p` for faster final output
  - `1080p` for a cleaner final output
  - `keep preview` if the preview resolution already suits the piece

## 7. Deliver cleanly

- Write final user-facing outputs to `~/Videos` unless the user requests a different path.
- Name outputs clearly and avoid burying the final in a temporary render tree if a cleaner copy should live in `~/Videos`.

## 8. Clean up intermediates

- After a successful final render, delete frame directories, temporary audio, and temporary video artifacts unless:
  - the user asked to keep them
  - you are still debugging
  - they are needed for recomposition or alternate exports

- Intermediate files to consider removing:
  - extracted or rendered frame directories
  - temporary WAV stems
  - temporary video-only mux files
  - preview artifacts that are no longer needed once the final is approved

## 9. Preserve flexibility

- Use an existing template only when it helps the piece.
- If a bespoke structure will produce a better film, build the bespoke structure.
- The process is repeatable; the results should not feel templated.
- Reuse compositional behaviors or workflow patterns when useful, but do not let named scene shortcuts become the default creative answer.

## 10. Audio implementation notes

- Prefer modular helpers or macros over embedding all DSP directly in the main film script.
- Keep stems in memory when practical and hand the final mix to `ffmpeg`.
- Use small, controllable dependencies. `numpy` is the baseline. Add `scipy`, `pedalboard`, `midiutil`, or `pyfluidsynth` only when they materially improve the result.
- If voice is present, prioritize intelligibility over score density.
- If the piece needs silence, give it real negative space instead of leaving low-level noise under everything.

## 11. Portable hardware-aware defaults

- Assume many users have modern hardware, but do not assume they know which encoder to request.
- Prefer a lightweight host probe with standard-library tools such as `platform`, `subprocess`, `shutil`, and `os`.
- Validate candidate encoders with a short FFmpeg smoke test before selecting them.
- Prefer a conservative worker cap for CPU-bound frame generation. A good portable default is profile-aware with a ceiling such as `min(4, os.cpu_count() or 1)`.
- Keep `libx264` as the stable fallback path when acceleration is unavailable or fails validation.
- Separate portable-safe detection from machine-specific tuning. The shared package should auto-help most people; local installs can still push harder.
- Treat `detect_render_runtime()` as the preferred portable entry point when generating new Python video scripts from this skill.

## 12. Local Hardware Profile Example: N150

Use this as a local-install tuning example, not as a portable-skill default. On an N150-powered NucBox G2 Plus, prefer a piped FFmpeg workflow and treat Quick Sync as an optimization to validate, not a requirement to assume.

### Implementation Example
```python
# Hardware-Optimized for N150
import multiprocessing as mp
from pathlib import Path
import subprocess

def render_worker(frame_data):
    # Logic to draw the frame
    pass

output_path = Path.home() / "Videos" / "preview.mp4"
workers = min(4, mp.cpu_count() or 1)

def pick_video_encoder():
    smoke_test = [
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=15",
        "-t", "0.25",
        "-c:v", "h264_qsv",
        "-f", "null", "-"
    ]
    result = subprocess.run(smoke_test, capture_output=True, text=True)
    return "h264_qsv" if result.returncode == 0 else "libx264"

video_encoder = pick_video_encoder()

# The 'N150-Fast' FFmpeg Pipe
cmd = [
    "ffmpeg", "-y",
    "-f", "image2pipe", "-vcodec", "png", "-i", "-",
    "-c:v", video_encoder,
    "-preset", "veryfast",
    str(output_path),
]

# Stream frames to stdin instead of writing a temporary frame tree when practical.
ffmpeg = subprocess.Popen(cmd, stdin=subprocess.PIPE)
```

Treat `runtime.workers` as satisfied only when it is wired into actual frame production, such as `ordered_frame_map(..., workers=runtime.workers)` or an equivalent worker-backed render path. Using it only for FFmpeg settings does not count.
On Windows, structure worker-backed scripts so the parallel path can actually launch: prefer top-level worker functions, picklable frame payloads, and a guarded entry point under `if __name__ == "__main__":`. Add `multiprocessing.freeze_support()` when the startup path needs it.
