"""Command-line entry point for tempfile-cleanup-cli."""
from __future__ import annotations

import argparse
import sys

from .core import delete_files, find_old_files, format_size, parse_duration, total_size


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tempfile-cleanup-cli",
        description="Find (and optionally delete) files older than a given age in one or more directories.",
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="One or more files/directories to scan (must be given explicitly — nothing is scanned by default)",
    )
    parser.add_argument(
        "--older-than",
        default="7d",
        help="Minimum age for a file to be listed, e.g. '7d', '12h', '30m', '45s' (default: 7d)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete the matched files (default is a dry-run listing only)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        max_age = parse_duration(args.older_than)
    except ValueError as exc:
        print(f"tempfile-cleanup-cli: error: {exc}", file=sys.stderr)
        return 2

    entries, warnings = find_old_files(args.paths, max_age)
    for warning in warnings:
        print(f"tempfile-cleanup-cli: warning: {warning}", file=sys.stderr)

    if not entries:
        print("tempfile-cleanup-cli: no files older than the threshold were found")
        return 0

    entries.sort(key=lambda entry: entry.size, reverse=True)
    for entry in entries:
        print(f"{format_size(entry.size):>8}  {entry.path}")

    print(f"\n{len(entries)} file(s), {format_size(total_size(entries))} reclaimable")

    if not args.apply:
        print("(dry run — pass --apply to delete these files)")
        return 0

    deleted, errors = delete_files(entries)
    for error in errors:
        print(f"tempfile-cleanup-cli: error: {error}", file=sys.stderr)
    print(f"tempfile-cleanup-cli: deleted {deleted} file(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
