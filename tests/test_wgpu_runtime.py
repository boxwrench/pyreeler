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


class FakeAdapter:
    def __init__(self, **info):
        self.info = info


class FakeGpu:
    def __init__(self, adapters):
        self._adapters = adapters

    def enumerate_adapters_sync(self):
        return self._adapters


class FakeWgpu:
    def __init__(self, adapters):
        self.gpu = FakeGpu(adapters)


def test_resolve_local_ffmpeg_candidates_filters_missing_paths(tmp_path):
    module = load_wgpu_runtime()
    existing = tmp_path / "ffmpeg"
    existing.write_text("fake", encoding="utf-8")
    missing = tmp_path / "missing"

    candidates = module.resolve_local_ffmpeg_candidates(extra_candidates=[existing, missing])

    assert str(existing) in candidates
    assert str(missing) not in candidates


def test_pick_discrete_adapter_prefers_nvidia_discrete_adapter():
    module = load_wgpu_runtime()
    amd = FakeAdapter(adapter_type="DiscreteGPU", vendor="AMD", device="Radeon")
    nvidia = FakeAdapter(adapter_type="DiscreteGPU", vendor="NVIDIA", device="RTX")

    chosen = module.pick_discrete_adapter(wgpu_module=FakeWgpu([amd, nvidia]))

    assert chosen is nvidia


def test_pick_discrete_adapter_falls_back_to_any_discrete_adapter():
    module = load_wgpu_runtime()
    discrete = FakeAdapter(adapter_type="DiscreteGPU", vendor="AMD", device="Radeon")

    chosen = module.pick_discrete_adapter(wgpu_module=FakeWgpu([discrete]))

    assert chosen is discrete


def test_pick_discrete_adapter_can_fall_back_to_any_adapter():
    module = load_wgpu_runtime()
    integrated = FakeAdapter(adapter_type="IntegratedGPU", vendor="Intel", device="Arc")

    chosen = module.pick_discrete_adapter(
        wgpu_module=FakeWgpu([integrated]),
        require_discrete=False,
    )

    assert chosen is integrated
