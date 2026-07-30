"""Core scanning and duration logic for tempfile-cleanup-cli."""
from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass

_DURATION_RE = re.compile(r"^(\d+)([dhms])?$")

_UNIT_SECONDS = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
}


def parse_duration(text: str) -> int:
    """Parse a simple duration string like '7d', '12h', '30m', '45s' into seconds.

    A bare number with no unit suffix is treated as days.
    """
    match = _DURATION_RE.match(text.strip())
    if not match:
        raise ValueError(f"invalid duration: {text!r} (expected e.g. '7d', '12h', '30m', '45s')")
    amount, unit = match.groups()
    unit = unit or "d"
    return int(amount) * _UNIT_SECONDS[unit]


@dataclass
class FileEntry:
    path: str
    size: int
    mtime: float


def find_old_files(
    paths: list[str], max_age_seconds: int, now: float | None = None
) -> tuple[list[FileEntry], list[str]]:
    """Recursively scan `paths` for regular files whose mtime is older than `max_age_seconds`.

    `paths` must be given explicitly by the caller — this function never
    invents a default location to scan. Returns (entries, warnings); a
    top-level path that doesn't exist produces a warning rather than raising.
    """
    if now is None:
        now = time.time()
    cutoff = now - max_age_seconds

    entries: list[FileEntry] = []
    warnings: list[str] = []

    for root_path in paths:
        if not os.path.exists(root_path):
            warnings.append(f"path not found: {root_path}")
            continue
        if os.path.isfile(root_path):
            _maybe_add(root_path, cutoff, entries)
            continue
        for dirpath, _dirnames, filenames in os.walk(root_path):
            for filename in filenames:
                _maybe_add(os.path.join(dirpath, filename), cutoff, entries)

    return entries, warnings


def _maybe_add(path: str, cutoff: float, entries: list[FileEntry]) -> None:
    if not os.path.isfile(path):
        return
    try:
        st = os.stat(path)
    except OSError:
        return
    if st.st_mtime < cutoff:
        entries.append(FileEntry(path=path, size=st.st_size, mtime=st.st_mtime))


def total_size(entries: list[FileEntry]) -> int:
    return sum(entry.size for entry in entries)


def format_size(num_bytes: int) -> str:
    """Format a byte count as a short human-readable string (e.g. '1.5MB')."""
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            if unit == "B":
                return f"{int(size)}{unit}"
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"


def delete_files(entries: list[FileEntry]) -> tuple[int, list[str]]:
    """Delete each entry's file. Returns (deleted_count, error_messages)."""
    deleted = 0
    errors: list[str] = []
    for entry in entries:
        try:
            os.remove(entry.path)
            deleted += 1
        except OSError as exc:
            errors.append(f"{entry.path}: {exc}")
    return deleted, errors
