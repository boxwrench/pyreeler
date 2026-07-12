#!/usr/bin/env bash
# PyReeler easy installer (macOS / Linux).
#
#   ./install.sh            # installs the Claude Code skill (default)
#   ./install.sh codex      # installs the OpenAI Codex skill
#   ./install.sh cli        # installs the standalone pyreeler CLI/TUI app
#
# It checks for FFmpeg, installs the core Python deps, and symlinks the skill
# into your assistant's skills directory. Windows users: see README → Installing.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-claude}"

case "$TARGET" in
  claude) SKILL_DIR="$REPO_ROOT/skills/claude"; DEST="$HOME/.claude/skills/pyreeler"; INVOKE="/pyreeler" ;;
  codex)  SKILL_DIR="$REPO_ROOT/skills/codex";  DEST="$HOME/.codex/skills/pyreeler"; INVOKE="\$pyreeler" ;;
  cli)
    echo "PyReeler installer -> standalone app"
    echo "  Installing standalone CLI/TUI via pip..."
    if python3 -m pip install -e "$REPO_ROOT[tui]" 2>/dev/null \
       || python3 -m pip install --user -e "$REPO_ROOT[tui]" 2>/dev/null \
       || python3 -m pip install --break-system-packages -e "$REPO_ROOT[tui]" 2>/dev/null; then
      echo "  [ok] Successfully installed pyreeler. Run 'pyreeler' to start the TUI."
    else
      echo "  [!!] Failed to install pyreeler CLI."
      exit 1
    fi
    exit 0
    ;;
  *) echo "Usage: ./install.sh [claude|codex|cli]"; exit 1 ;;
esac

echo "PyReeler installer -> $TARGET"

# 1. Prefer system FFmpeg; the dependency install below provides a fallback.
if command -v ffmpeg >/dev/null 2>&1; then
  echo "  [ok] ffmpeg source: system ($(command -v ffmpeg))"
else
  echo "  [info] system ffmpeg not found; checking the Python fallback"
fi

# 2. Core Python deps, including imageio-ffmpeg.
#    Try the common PEP 668 alternatives before validating the resolver below.
if python3 -c "import numpy, PIL, imageio_ffmpeg" >/dev/null 2>&1; then
  echo "  [ok] core Python deps already available"
else
  echo "  Installing core Python deps from requirements.txt ..."
  if python3 -m pip install -r "$REPO_ROOT/requirements.txt" 2>/dev/null \
     || python3 -m pip install --user -r "$REPO_ROOT/requirements.txt" 2>/dev/null \
     || python3 -m pip install --break-system-packages -r "$REPO_ROOT/requirements.txt" 2>/dev/null; then
    echo "  [ok] installed core Python deps"
  else
    echo "  [warn] could not auto-install numpy/pillow (managed Python?)."
    echo "         Install them yourself, then re-run if needed:"
    echo "           python3 -m pip install -r \"$REPO_ROOT/requirements.txt\""
    echo "         or in a virtualenv:  python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt"
  fi
fi

# 3. Resolve FFmpeg after dependency installation and report the selected source.
if ! command -v ffmpeg >/dev/null 2>&1; then
  IMAGEIO_FFMPEG="$(python3 -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())' 2>/dev/null || true)"
  if [ -n "$IMAGEIO_FFMPEG" ] && [ -x "$IMAGEIO_FFMPEG" ]; then
    echo "  [ok] ffmpeg source: imageio-ffmpeg ($IMAGEIO_FFMPEG)"
  else
    echo "  [!!] Could not resolve FFmpeg from the system PATH or imageio-ffmpeg."
    echo "       Install dependencies with: python3 -m pip install -r \"$REPO_ROOT/requirements.txt\""
    echo "       Or install system FFmpeg, then re-run."
    exit 1
  fi
fi

# 4. Symlink the skill into place.
mkdir -p "$(dirname "$DEST")"
if [ -e "$DEST" ] || [ -L "$DEST" ]; then
  echo "  [skip] $DEST already exists. Remove it and re-run to relink."
else
  ln -s "$SKILL_DIR" "$DEST"
  echo "  [ok] linked $SKILL_DIR -> $DEST"
fi

echo ""
echo "Done. Open your assistant and invoke it with: $INVOKE"
echo "Optional extras (music, voice, scipy filters): pip install -r requirements-extras.txt"
