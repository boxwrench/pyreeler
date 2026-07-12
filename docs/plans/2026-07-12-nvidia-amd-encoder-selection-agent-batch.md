# NVIDIA/AMD Encoder Selection Agent Batch

**Set:** 2026-07-12  
**Status:** Completed post-v0.1 maintenance batch

## Goal

Choose video encoders by proving that they can initialize on the current host,
not by inferring support from a GPU vendor name, platform string, or FFmpeg's
encoder listing.

The intentionally narrow selection order is:

1. smoke-test NVIDIA NVENC;
2. smoke-test AMD AMF;
3. use `libx264` with the `veryfast` preset as the dependable CPU safety
   fallback.

Intel Quick Sync Video (QSV), Apple VideoToolbox, and Linux VAAPI are parked.
They may be added through focused pull requests or demonstrated user requests
with hardware on which their behavior can be validated.

## Why This Boundary

FFmpeg can advertise a hardware encoder even when the corresponding device,
driver, or runtime cannot initialize it. Vendor detection has the inverse
problem: recognizing a GPU does not prove that the selected FFmpeg binary can
use its encoder. A tiny real encode is the useful capability check.

The CPU fallback remains required. It is slower than hardware encoding, but a
fast `libx264` preset keeps short PyReeler previews practical and prevents a
driver or probe failure from turning into a failed render.

## Implementation Tasks

### Task 1: Capability-first selection

- Define the supported candidates in the fixed order NVENC, AMF, then
  `libx264`.
- Run a bounded, minimal FFmpeg encode smoke test for each accelerated
  candidate before selecting it.
- Treat a missing encoder, non-zero exit, timeout, or initialization failure as
  an unavailable candidate and continue to the next one.
- Do not inspect GPU vendor names, device strings, operating-system branding,
  or FFmpeg's static encoder list to choose the encoder.
- Preserve the existing FFmpeg binary resolution order, including explicit
  `PYREEL_FFMPEG`, system FFmpeg, and the `imageio-ffmpeg` fallback.

### Task 2: Dependable software fallback

- Retain `libx264` as the final candidate.
- Use the `veryfast` preset for the CPU fallback.
- Surface the selected encoder clearly enough for users and tests to identify
  the active path.
- If even `libx264` cannot encode, raise a clear error naming every attempted
  candidate rather than silently selecting an unusable encoder.

### Task 3: Tests and validation

- Add deterministic unit tests for NVENC success, NVENC failure followed by AMF
  success, both accelerated candidates failing, probe timeout/failure, and
  complete failure including `libx264`.
- Prove that vendor/platform detection does not control selection.
- Keep CI independent of physical NVIDIA or AMD hardware by mocking probe
  outcomes.
- Run a real short render with the encoder available on the development host and
  verify that the resulting MP4 is valid.
- Confirm the installed-wheel smoke and full test suite remain green.

### Task 4: Documentation and handoff

- Update user-facing hardware-encoding claims to match the NVIDIA/AMD boundary.
- Record the selected encoder and validation results in the batch handoff.
- Leave QSV, VideoToolbox, and VAAPI explicitly parked rather than adding
  speculative branches.

## Acceptance Criteria

- Encoder selection always attempts NVENC, then AMF, then `libx264`.
- NVENC or AMF is selected only after a successful bounded encode smoke test.
- No GPU-vendor or platform-name detection participates in encoder selection.
- A failed accelerated probe cannot prevent the next candidate from being
  tested.
- The CPU safety path uses `libx264` with `-preset veryfast` and completes a
  representative short render.
- Selection exposes enough information to diagnose which encoder was used.
- Total probe failure produces a clear error naming all attempted candidates.
- Unit tests require no particular GPU, and existing wheel/render validation
  remains green.
- QSV, VideoToolbox, and VAAPI remain out of scope pending a focused PR or a
  demonstrated request.

## Non-goals

- Benchmarking or automatically ranking encoders by performance or quality.
- Adding Intel, Apple, or VAAPI support in this batch.
- Detecting installed GPU vendors or maintaining a hardware-profile database.
- Removing the portable FFmpeg resolver or the software fallback.
- Changing frame synthesis, recipe behavior, or output defaults unrelated to
  encoder initialization.
## Completion

Completed on 2026-07-12. The runtime now smoke-tests `h264_nvenc`,
`h264_amf`, and `libx264` in that order, with five-second bounded probes and a
clear total-failure error naming every attempted candidate. The development
host selected NVENC with system FFmpeg 8.1.1. Deterministic tests cover AMF,
CPU fallback, timeouts, launch failures, and total failure without requiring
specific GPU hardware.

Validation: 122 tests passed; `python graduation_check.py`,
`python sync.py --check`, and `git diff --check` passed; the clean installed
wheel rendered successfully with both system FFmpeg and the imageio-ffmpeg
fallback.