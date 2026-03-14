# PyReeler Devlog

## Current Repo State

`C:\Github\pyreeler` has been cleaned down to the current skill packages only:

- `pyreeler`
- `pyreeler-claude`

Previous render outputs, frame dumps, smoke artifacts, temp skill copies, and scratch scripts were moved out of the working folder to:

- `C:\Github\pyreeler_archive_20260313`

## Portable Package Source

The repo copy at `C:\Github\pyreeler\pyreeler` was rebuilt from the current portable package source:

- `C:\Users\wests\Downloads\pyreeler`

## Installed Skill Sync

After rebuilding the repo copy, these files were synced from the installed Codex skill so the guidance matches current behavior:

- `C:\Users\wests\.codex\skills\pyreeler\SKILL.md`
- `C:\Users\wests\.codex\skills\pyreeler\references\workflow.md`

Applied to:

- `C:\Github\pyreeler\pyreeler\SKILL.md`
- `C:\Github\pyreeler\pyreeler\references\workflow.md`

## Current Guidance Added

The current portable and installed guidance now requires:

- a pre-render hardware gate for portable Python renderers
- `detect_render_runtime()` for runtime selection
- validated encoder selection instead of hardcoded hardware encoder assumptions
- `runtime.workers` to drive actual frame generation, not just FFmpeg settings
- piped FFmpeg when practical
- a short worker-path smoke test before the first full render when `runtime.workers > 1`
- Windows-safe multiprocessing structure
  - top-level worker functions
  - picklable worker inputs
  - `if __name__ == "__main__":`
  - `multiprocessing.freeze_support()` when needed

## Benchmark Interpretation

Recent clean-room testing suggests:

- helper adoption is now happening by default
- worker-backed rendering can be selected and verified before full render
- some scenes may still render slowly because the frame function itself is expensive
- heavy full-frame procedural fields and bloom are a separate performance problem from worker-path correctness
