# Windows Desktop Template

**Machine:** Generic Windows workstation
**CPU:** [Your CPU]
**GPU:** [Your GPU if any]
**RAM:** [Amount]
**OS:** Windows 11
**Python:** 3.12

## FFmpeg Path

```python
FFMPEG_PATH = r"C:\path\to\ffmpeg.exe"
```

## Encoder Testing

Run this to find your best encoder:

```python
import subprocess

encoders = ['libx264', 'h264_nvenc', 'h264_qsv', 'h264_amf']
for enc in encoders:
    cmd = ['ffmpeg', '-f', 'lavfi', '-i', 'testsrc=duration=1:size=1280x720:rate=1',
           '-c:v', enc, '-f', 'null', '-']
    result = subprocess.run(cmd, capture_output=True)
    status = "✓" if result.returncode == 0 else "✗"
    print(f"{enc}: {status}")
```

## Typical Results by Hardware

### NVIDIA GPU Present
- **Fastest:** `h264_nvenc` (but larger files)
- **Best quality/size:** `libx264` with `preset=slow, crf=23`
- **Balanced:** `h264_nvenc` with `cq=23`

### Intel Integrated (11th gen+)
- **Fastest:** `h264_qsv`
- **Best quality/size:** `libx264` still wins

### AMD GPU
- **Fastest:** `h264_amf`
- **Quality:** Usually `libx264` is better

### No GPU (CPU only)
- **Only option:** `libx264`
- **Workers:** Set to `os.cpu_count()` or slightly less

## Workers

```python
import os

# Conservative (leave headroom)
workers = max(1, (os.cpu_count() or 4) - 1)

# Aggressive (use all cores)
workers = os.cpu_count() or 4
```

## Memory Limits

If rendering causes swapping:
- Reduce `trail_length` in attractors
- Reduce `n_particles`
- Lower resolution preview first

---
*Template: Fill in your actual measurements*
