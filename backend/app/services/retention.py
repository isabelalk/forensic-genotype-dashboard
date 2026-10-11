"""Retention and quota handling for uploads and STRUCTURE artifacts.

Timestamps carry the state so every worker process and restart agree:
- upload mtime = time of upload (never changed after the write)
- upload atime = last use, set explicitly in `touch_last_use`
- artifact directory mtime = time of generation
"""

import logging
import os
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class SweepResult:
    uploads_removed: int
    artifacts_removed: int


def directory_bytes(path: Path) -> int:
    """Total size of regular files under `path` (recursive)."""
    total = 0
    if not path.exists():
        return 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += (Path(root) / name).stat().st_size
            except FileNotFoundError:
                continue
    return total


def touch_last_use(path: Path, now: float | None = None) -> None:
    """Record a use of the file: atime <- now, mtime unchanged."""
    try:
        stat = path.stat()
        os.utime(path, ns=(int((now if now is not None else time.time()) * 1e9), stat.st_mtime_ns))
    except FileNotFoundError:
        return


def sweep_uploads(upload_dir: Path, idle_ttl_seconds: float, max_age_seconds: float, now: float | None = None) -> int:
    """Delete uploads idle longer than `idle_ttl_seconds` or older than `max_age_seconds`."""
    if not upload_dir.exists():
        return 0
    current = now if now is not None else time.time()
    removed = 0
    for entry in list(upload_dir.iterdir()):
        if not entry.is_file():
            continue
        try:
            stat = entry.stat()
        except FileNotFoundError:
            continue
        idle_for = current - stat.st_atime
        age = current - stat.st_mtime
        if idle_for > idle_ttl_seconds or age > max_age_seconds:
            if _remove_file(entry):
                removed += 1
    return removed


def sweep_artifacts(
    artifact_dir: Path,
    max_age_seconds: float,
    max_count: int,
    max_bytes: int,
    now: float | None = None,
    reserve_bytes: int = 0,
) -> int:
    """Remove artifact directories by age, then oldest-first until count and byte quotas hold.

    `reserve_bytes` makes room for an artifact about to be written.
    """
    if not artifact_dir.exists():
        return 0
    current = now if now is not None else time.time()
    removed = 0

    entries = []
    for entry in list(artifact_dir.iterdir()):
        if not entry.is_dir():
            continue
        try:
            mtime = entry.stat().st_mtime
        except FileNotFoundError:
            continue
        if current - mtime > max_age_seconds:
            if _remove_tree(entry):
                removed += 1
            continue
        entries.append((mtime, entry))

    entries.sort(key=lambda item: item[0], reverse=True)  # newest first
    sizes = {entry: directory_bytes(entry) for _mtime, entry in entries}
    total = sum(sizes.values()) + reserve_bytes

    while entries and (len(entries) > max_count or total > max_bytes):
        _mtime, oldest = entries.pop()
        total -= sizes[oldest]
        if _remove_tree(oldest):
            removed += 1
    return removed


def sweep_all(settings) -> SweepResult:
    """Run both sweeps with the configured limits. Safe to call from any worker at any time."""
    uploads_removed = sweep_uploads(
        settings.get_upload_dir(),
        idle_ttl_seconds=settings.upload_idle_ttl_seconds,
        max_age_seconds=settings.upload_max_age_seconds,
    )
    artifacts_removed = sweep_artifacts(
        settings.get_artifact_dir(),
        max_age_seconds=settings.max_artifact_age_seconds,
        max_count=settings.max_artifact_count,
        max_bytes=settings.max_artifact_dir_bytes,
    )
    if uploads_removed or artifacts_removed:
        logger.info("Retention sweep removed %d upload(s) and %d artifact(s)", uploads_removed, artifacts_removed)
    return SweepResult(uploads_removed=uploads_removed, artifacts_removed=artifacts_removed)


def _remove_file(path: Path) -> bool:
    try:
        path.unlink()
        return True
    except FileNotFoundError:
        return False
    except OSError as error:
        logger.warning("Could not remove upload %s: %s", path.name, error)
        return False


def _remove_tree(path: Path) -> bool:
    if not path.exists():
        return False
    shutil.rmtree(path, ignore_errors=True)
    return True
