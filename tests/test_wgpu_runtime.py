"""CI-safe tests for the local-only WGPU runtime helper."""
import importlib.util
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
WGPU_RUNTIME = REPO_ROOT / "docs" / "hardware-experiments" / "wgpu_runtime.py"


def load_wgpu_runtime():
    spec = importlib.util.spec_from_file_location("wgpu_runtime_under_test", WGPU_RUNTIME)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_module_imports_without_wgpu_installed():
    module = load_wgpu_runtime()

    assert module.LocalShaderRuntime


def test_is_wgpu_available_returns_bool():
    module = load_wgpu_runtime()

    assert isinstance(module.is_wgpu_available(), bool)


def test_pick_discrete_adapter_without_wgpu_has_clear_error():
    module = load_wgpu_runtime()

    with pytest.raises(RuntimeError, match="Install wgpu to use local shader rendering"):
        module.pick_discrete_adapter(wgpu_module=None)
