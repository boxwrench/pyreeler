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

## Encoding vs. Frame Synthesis

PyReeler's portable "GPU mode" means hardware-assisted video encoding through
FFmpeg when a host encoder is available. Visual frames are still usually generated
on the CPU with Python, NumPy, and Pillow.

The files in this folder prototype **GPU frame synthesis**: shader code generates
the pixels for each frame on the GPU, then the resulting frames are encoded through
the normal FFmpeg path. This is hardware-specific and remains outside the portable
skill until the dependency and platform story is stable.

Files:

- `wgpu_runtime.py`: local adapter/runtime helpers for the discrete GPU path
- `render_shader_terminal_preview.py`: local shader-backed cyber terminal demo

Notes:

- This runtime is meant for local tuning on the Acer Predator / RTX 5070 Ti machine.
- It can assume `wgpu` is installed and that the machine has a working discrete adapter.
- The demo keeps encoding piped through FFmpeg but moves the heavy full-frame look
  generation onto the GPU.
- `wgpu_runtime.py` is import-safe without `wgpu` so CI can test selection behavior,
  but running a shader preview still requires installing `wgpu` and having working
  GPU drivers.

Example local run:

```bash
python docs/hardware-experiments/render_shader_terminal_preview.py --duration 12
```
