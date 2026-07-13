# PyReeler Current Working Plan

**Set:** 2026-07-12 after the Ponytail/YAGNI audit
**Status:** v0.1 milestone complete; TUI banner canonicalized

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

### Milestone result

Completed on 2026-07-12. Packaging, fallback alignment, ordered frame streaming,
and clean-artifact validation are recorded in the
[v0.1 milestone validation](2026-07-12-v0.1-milestone-validation.md).

All four milestone steps are complete. The first post-v0.1 maintenance batch also
restored a cross-platform green baseline: 110 tests pass, provider sync passes,
and the graduation manifest remains a required CI gate.

## Completed Batch: Capability-first NVIDIA/AMD Encoding

Replace vendor-name inference with bounded FFmpeg encode smoke tests. Selection
tries NVIDIA NVENC, then AMD AMF, and retains `libx264 -preset veryfast` as the
CPU safety fallback. Intel QSV, Apple VideoToolbox, and VAAPI are parked for a
focused pull request or demonstrated request with suitable validation hardware.

The batch tasks and acceptance criteria are recorded in the
[NVIDIA/AMD encoder selection agent batch](2026-07-12-nvidia-amd-encoder-selection-agent-batch.md).

Completed on 2026-07-12 with 122 tests passing, both repository gates green,
and installed-wheel renders passing with system and imageio FFmpeg sources.

## Completed Batch: Canonical TUI Banner

The polished non-AI banner in `pyreeler/tui/banner.py` is now the canonical
implementation. The existing sync pipeline copies it into the reusable template
and both provider distributions, preserving the animation and static fallback
without maintaining a second implementation.

The boundary and validation are recorded in the
[TUI banner consolidation report](2026-07-12-tui-banner-consolidation.md).

## Evaluate After v0.1

These are candidates, not an automatic queue:

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
