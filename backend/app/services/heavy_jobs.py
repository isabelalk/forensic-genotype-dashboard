"""Runs CPU/IO-heavy synchronous work off the event loop with a concurrency cap.

The limiter is per worker process: with `--workers 2` the true ceiling is twice
`max_concurrent_heavy_jobs`. Requests beyond the cap wait in the limiter's queue.
"""

import functools
from typing import Callable, ParamSpec, TypeVar

import anyio
from anyio import CapacityLimiter

from app.core import settings

P = ParamSpec("P")
R = TypeVar("R")

HEAVY_JOB_LIMITER = CapacityLimiter(settings.max_concurrent_heavy_jobs)


async def run_heavy(fn: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> R:
    """Run `fn(*args, **kwargs)` in a worker thread, at most N at a time."""
    return await anyio.to_thread.run_sync(functools.partial(fn, *args, **kwargs), limiter=HEAVY_JOB_LIMITER)
