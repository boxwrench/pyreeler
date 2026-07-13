# Changelog

Notable user-facing changes are recorded here. PyReeler follows semantic
versioning for published releases.

## 0.1.0 - 2026-07-12

Initial dependable local-renderer milestone:

- Added an offline recipe CLI and interactive Textual TUI with typed,
  range-checked controls and no-clobber output paths.
- Added built-in attractor recipes and ordered, streaming frame delivery to
  FFmpeg so complete films do not accumulate in memory.
- Added capability-tested NVIDIA NVENC and AMD AMF encoding with a conservative
  `libx264` CPU fallback and an `imageio-ffmpeg` binary fallback.
- Added portable Codex and Claude skill distributions backed by synchronized
  canonical templates and reference material.
- Added installed-wheel smoke validation, provider-sync checks, template
  graduation checks, and focused behavioral coverage for critical helpers.

PyInstaller binaries, macOS validation, Intel QSV, Apple VideoToolbox, and VAAPI
are not part of the 0.1.0 support boundary.