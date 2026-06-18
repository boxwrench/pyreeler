#!/usr/bin/env bash
# PyReeler easy installer (macOS / Linux).
#
#   ./install.sh            # installs the Claude Code skill (default)
#   ./install.sh codex      # installs the OpenAI Codex skill
#
# It checks for FFmpeg, installs the core Python deps, and symlinks the skill
# into your assistant's skills directory. Windows users: see README → Installing.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-claude}"

case "$TARGET" in
  claude) SKILL_DIR="$REPO_ROOT/skills/claude"; DEST="$HOME/.claude/skills/pyreeler"; INVOKE="/pyreeler" ;;
  codex)  SKILL_DIR="$REPO_ROOT/skills/codex";  DEST="$HOME/.codex/skills/pyreeler"; INVOKE="\$pyreeler" ;;
  *) echo "Usage: ./install.sh [claude|codex]"; exit 1 ;;
esac

echo "PyReeler installer -> $TARGET"

# 1. FFmpeg is the one hard external dependency.
if command -v ffmpeg >/dev/null 2>&1; then
  echo "  [ok] ffmpeg: $(command -v ffmpeg)"
else
  echo "  [!!] ffmpeg not found. Install it first, then re-run:"
  echo "         macOS:  brew install ffmpeg"
  echo "         Linux:  sudo apt-get install ffmpeg"
  exit 1
fi

# 2. Core Python deps (numpy, pillow).
echo "  Installing core Python deps from requirements.txt ..."
python3 -m pip install -r "$REPO_ROOT/requirements.txt"

# 3. Symlink the skill into place.
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
