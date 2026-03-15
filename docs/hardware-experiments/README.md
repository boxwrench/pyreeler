# Local NVIDIA Runtime

This folder is intentionally local-only. It is not part of the portable `pyreeler`
skill package.

Purpose:

- use the discrete NVIDIA GPU directly for expensive full-frame effects
- keep the portable package conservative and machine-agnostic
- prototype shader-backed preview rendering for this specific machine

Current stack:

- `wgpu` for explicit adapter selection and offscreen rendering
- Vulkan or D3D12 backend chosen by the driver stack
- `h264_nvenc` via the existing PyReeler runtime helper when available

Files:

- `wgpu_runtime.py`: local adapter/runtime helpers for the discrete GPU path
- `render_shader_terminal_preview.py`: local shader-backed cyber terminal demo

Notes:

- This runtime is meant for local tuning on the Acer Predator / RTX 5070 Ti machine.
- It can assume `wgpu` is installed and that the machine has a working discrete adapter.
- The demo keeps encoding piped through FFmpeg but moves the heavy full-frame look
  generation onto the GPU.
