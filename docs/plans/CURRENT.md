# PyReeler Current Working Plan

**Set:** 2026-07-12 after the Ponytail/YAGNI audit
**Status:** Authoritative current plan

This plan supersedes the ordered, infrastructure-first backlog in
`2026-06-17-remaining-roadmap-implementation.md`. That document is retained as
planning history, not committed scope.

## Milestone: Dependable PyReeler v0.1 Local Renderer

Freeze feature expansion until the existing CLI/TUI works from a built artifact
outside the repository checkout and renders without retaining a whole film in memory.

### Definition of done

- A wheel builds and installs in a clean environment outside the checkout.
- The artifact contains runtime helpers and `pyreeler/tui/styles.tcss`.
- `pyreeler list` and `pyreeler info lorenz` work after installation.
- A representative one-second recipe renders to a valid MP4.
- The no-argument TUI launches with its stylesheet.
- FFmpeg fallback behavior, dependencies, installers, and README agree.
- Ordered frames stream into FFmpeg instead of accumulating for the full film.
- Provider sync and focused behavioral tests remain green.
- CI includes an installed-wheel smoke test, not only source-tree tests.

### Immediate next task

Add an artifact-install smoke test first, observe its failures, and make the
smallest packaging corrections needed. Do not add a plugin or packaging abstraction.

Validation should build a wheel, install it into a temporary environment outside
the checkout, run `list`, `info`, and a one-second low-resolution render, then
launch the TUI. Verify the documented PyInstaller path separately.

### Milestone sequence

1. Prove and correct the wheel's package/module/data boundary.
2. Align FFmpeg fallback dependencies, installer behavior, and documentation.
3. Stream `ordered_frame_map()` results directly to FFmpeg while preserving order,
   progress, cleanup, and useful stderr.
4. Validate the milestone in a clean environment and record the result.

Keep the streaming refactor isolated. Validate a real short render, broken-pipe and
FFmpeg-error behavior, and approximately steady memory on a longer render.

## Evaluate After v0.1

These are candidates, not an automatic queue:

- Consolidate the duplicate package/template banner.
- Decide whether `graduation_check.py` merits a required CI gate; preserve
  `sync.py --check` and behavioral tests.
- Prototype FFmpeg-smoke-test-first encoder selection and compare it across actual
  platforms before replacing vendor detection.
- Replace duplicate experimental copies of canonical references with links.
- Add direct behavioral tests where runtime helpers have only sync coverage.
- Add recipes or templates only for a specific film the current set cannot express.

## Triggered Later

| Idea | Revisit only when |
|---|---|
| 2D contact sheets / parallel variants | A real tuning task repeatedly needs two changing parameters. |
| Band envelopes / beat detection | A film needs behavior the RMS envelope cannot express. |
| Multi-layer helper | Two films duplicate substantially the same composition logic. |
| Visual regression | Deterministic regressions recur or manual smoke renders become inadequate. |
| WGPU/shader v2 | A measured film requirement fails and a benchmark proves shaders solve it. |
| Real-time preview | Low-fidelity preview renders repeatedly exceed acceptable iteration time. |
| Provider wrappers | A third provider arrives or wrapper prose repeatedly drifts. |
| Render farm | One machine remains inadequate after multiprocessing and streaming are exhausted. |

## Parking Lot

Differential growth, space colonization, DLA, full boids controls, L-systems,
granular synthesis, retro overlays, hybrid pipelines, neuroevolution, and additional
attractor modes are creative options, not a queue.

Research and experiments remain valuable retained knowledge. They do not assign work
to the product.

## Protect

Keep the compact recipe/parameter model, centralized validation, no-clobber output,
`sync.py`, self-contained provider distributions, the experimental/product
boundary, encoder smoke tests and software fallback, optional dependency tiers,
completed films, research, benchmarks, and compressed showcase media.

## Planning Rule

A new abstraction must be paid for by a current film, a demonstrated installation
failure, or repeated duplicated implementation - not merely by an interesting idea.
