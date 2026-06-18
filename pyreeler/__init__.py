"""PyReeler CLI/TUI package — make code-generated films without an AI.

Ensures the repository root is importable so the sibling namespace packages
`experimental.tools.*` and `templates.video.*` resolve regardless of the current
working directory (they have no __init__.py; PEP 420 namespace import covers them).
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
