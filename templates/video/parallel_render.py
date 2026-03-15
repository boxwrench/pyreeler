from __future__ import annotations

import multiprocessing as mp
from typing import Callable, Iterable, Iterator, TypeVar


T = TypeVar("T")


def ordered_frame_map(
    frame_indices: Iterable[int],
    render_func: Callable[[int], T],
    workers: int,
    chunksize: int | None = None,
) -> Iterator[T]:
    worker_count = max(1, int(workers))
    if worker_count <= 1:
        for frame_index in frame_indices:
            yield render_func(frame_index)
        return

    indices = list(frame_indices)
    if not indices:
        return
    if chunksize is None:
        chunksize = max(1, len(indices) // (worker_count * 8))

    with mp.Pool(processes=worker_count) as pool:
        for item in pool.imap(render_func, indices, chunksize=chunksize):
            yield item
