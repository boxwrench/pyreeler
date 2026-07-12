"""Build and exercise the installed PyReeler wheel outside the checkout."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, env=env, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-render", action="store_true", help="do not exercise FFmpeg rendering"
    )
    parser.add_argument(
        "--exercise-fallback",
        action="store_true",
        help="also render with PATH cleared to prove the imageio-ffmpeg fallback",
    )
    args = parser.parse_args()

    repo = Path(__file__).resolve().parent.parent
    with tempfile.TemporaryDirectory(prefix="pyreeler-wheel-") as temporary:
        root = Path(temporary).resolve()
        dist = root / "dist"
        work = root / "work"
        venv = root / "venv"
        dist.mkdir()
        work.mkdir()

        run(
            [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist), str(repo)],
            cwd=root,
        )
        run([sys.executable, "-m", "venv", str(venv)], cwd=root)
        executable = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        wheel = next(dist.glob("pyreeler-*.whl"))
        run([str(executable), "-m", "pip", "install", str(wheel)], cwd=work)

        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        env["PYREELER_SMOKE_CHECKOUT"] = str(repo)
        run([str(executable), "-m", "pyreeler", "list"], cwd=work, env=env)
        run([str(executable), "-m", "pyreeler", "info", "lorenz"], cwd=work, env=env)
        probe = (
            "import importlib.resources as r, os; from pathlib import Path; "
            "import pyreeler, pyreeler.engine; "
            "repo=Path(os.environ['PYREELER_SMOKE_CHECKOUT']).resolve(); "
            "installed=Path(pyreeler.__file__).resolve(); "
            "assert repo not in installed.parents, (repo, installed); "
            "p=r.files('pyreeler.tui').joinpath('styles.tcss'); "
            "assert p.is_file(), p; print(installed); print(p)"
        )
        run([str(executable), "-c", probe], cwd=work, env=env)

        if not args.skip_render:
            source_probe = (
                "import shutil; from pathlib import Path; "
                "from templates.video.ffmpeg_utils import resolve_ffmpeg; "
                "system=shutil.which('ffmpeg'); resolved=resolve_ffmpeg(); "
                "assert not system or Path(resolved).resolve()==Path(system).resolve(); "
                "source='system' if system else 'imageio-ffmpeg'; "
                "print(f'ffmpeg source: {source} ({resolved})')"
            )
            run([str(executable), "-c", source_probe], cwd=work, env=env)

            output = work / "lorenz-smoke.mp4"
            render_command = [
                str(executable), "-m", "pyreeler", "render", "lorenz",
                "--duration", "1", "--width", "160", "--height", "120",
                "--fps", "4", "-o", str(output),
            ]
            run(render_command, cwd=work, env=env)
            if not output.is_file() or output.stat().st_size == 0:
                raise RuntimeError(f"render did not produce a non-empty file: {output}")
            print(f"rendered {output} ({output.stat().st_size} bytes)")

            if args.exercise_fallback:
                fallback_env = env.copy()
                fallback_env["PATH"] = ""
                fallback_probe = (
                    "import shutil, imageio_ffmpeg; "
                    "from templates.video.ffmpeg_utils import resolve_ffmpeg; "
                    "assert shutil.which('ffmpeg') is None; resolved=resolve_ffmpeg(); "
                    "expected=imageio_ffmpeg.get_ffmpeg_exe(); "
                    "assert resolved==expected, (resolved, expected); "
                    "print(f'ffmpeg source: imageio-ffmpeg ({resolved})')"
                )
                run(
                    [str(executable), "-c", fallback_probe],
                    cwd=work,
                    env=fallback_env,
                )
                fallback_output = work / "lorenz-fallback-smoke.mp4"
                fallback_command = [*render_command[:-1], str(fallback_output)]
                run(fallback_command, cwd=work, env=fallback_env)
                if (
                    not fallback_output.is_file()
                    or fallback_output.stat().st_size == 0
                ):
                    raise RuntimeError(
                        "fallback render did not produce a non-empty file: "
                        f"{fallback_output}"
                    )
                print(
                    f"rendered {fallback_output} "
                    f"({fallback_output.stat().st_size} bytes)"
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
