"""Behavioral tests for ordered canonical frame mapping."""
import pytest

from templates.video import parallel_render


def test_single_worker_is_ordered_and_does_not_create_pool(monkeypatch):
    monkeypatch.setattr(
        parallel_render.mp,
        "Pool",
        lambda **_kwargs: pytest.fail("single-worker path must not create a pool"),
    )

    result = list(parallel_render.ordered_frame_map([2, 0, 1], lambda i: i * 10, 1))

    assert result == [20, 0, 10]


def test_multiworker_uses_ordered_imap_and_computed_chunksize(monkeypatch):
    calls = {}

    class FakePool:
        def __init__(self, processes):
            calls["processes"] = processes

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            calls["closed"] = True

        def imap(self, func, indices, chunksize):
            calls["indices"] = indices
            calls["chunksize"] = chunksize
            return map(func, indices)

    monkeypatch.setattr(parallel_render.mp, "Pool", FakePool)

    result = list(parallel_render.ordered_frame_map(range(4), lambda i: f"f{i}", 2))

    assert result == ["f0", "f1", "f2", "f3"]
    assert calls == {"processes": 2, "indices": [0, 1, 2, 3], "chunksize": 1, "closed": True}


def test_multiworker_propagates_worker_failure_and_closes_pool(monkeypatch):
    calls = {}

    class FakePool:
        def __init__(self, processes):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            calls["closed"] = True

        def imap(self, _func, _indices, chunksize):
            def results():
                yield "frame-0"
                raise RuntimeError("worker failed")
            return results()

    monkeypatch.setattr(parallel_render.mp, "Pool", FakePool)

    iterator = parallel_render.ordered_frame_map([0, 1], str, 2)
    assert next(iterator) == "frame-0"
    with pytest.raises(RuntimeError, match="worker failed"):
        next(iterator)
    assert calls["closed"] is True
