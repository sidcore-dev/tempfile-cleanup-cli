import os
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tempfile_cleanup_cli.core import (
    delete_files,
    find_old_files,
    format_size,
    parse_duration,
    total_size,
)


class TestParseDuration(unittest.TestCase):
    def test_days(self) -> None:
        self.assertEqual(parse_duration("7d"), 7 * 86400)

    def test_hours(self) -> None:
        self.assertEqual(parse_duration("12h"), 12 * 3600)

    def test_minutes(self) -> None:
        self.assertEqual(parse_duration("30m"), 30 * 60)

    def test_seconds(self) -> None:
        self.assertEqual(parse_duration("45s"), 45)

    def test_bare_number_defaults_to_days(self) -> None:
        self.assertEqual(parse_duration("3"), 3 * 86400)

    def test_invalid_raises(self) -> None:
        with self.assertRaises(ValueError):
            parse_duration("soon")

    def test_invalid_unit_raises(self) -> None:
        with self.assertRaises(ValueError):
            parse_duration("7y")


class TestFindOldFiles(unittest.TestCase):
    def _touch(self, path: Path, age_seconds: float, now: float) -> None:
        path.write_text("data")
        mtime = now - age_seconds
        os.utime(path, (mtime, mtime))

    def test_finds_only_files_older_than_threshold(self) -> None:
        now = time.time()
        with TemporaryDirectory() as tmp:
            old_file = Path(tmp) / "old.log"
            new_file = Path(tmp) / "new.log"
            self._touch(old_file, 10 * 86400, now)
            self._touch(new_file, 1 * 86400, now)

            entries, warnings = find_old_files([tmp], 7 * 86400, now=now)

            self.assertEqual(warnings, [])
            paths = {entry.path for entry in entries}
            self.assertIn(str(old_file), paths)
            self.assertNotIn(str(new_file), paths)

    def test_recurses_into_subdirectories(self) -> None:
        now = time.time()
        with TemporaryDirectory() as tmp:
            sub = Path(tmp) / "nested" / "deeper"
            sub.mkdir(parents=True)
            old_file = sub / "old.bin"
            self._touch(old_file, 10 * 86400, now)

            entries, _warnings = find_old_files([tmp], 7 * 86400, now=now)

            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].path, str(old_file))

    def test_missing_path_produces_warning_not_error(self) -> None:
        entries, warnings = find_old_files(["/no/such/path/xyz"], 86400)
        self.assertEqual(entries, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn("not found", warnings[0])

    def test_single_file_path(self) -> None:
        now = time.time()
        with TemporaryDirectory() as tmp:
            old_file = Path(tmp) / "old.txt"
            self._touch(old_file, 10 * 86400, now)

            entries, _warnings = find_old_files([str(old_file)], 7 * 86400, now=now)

            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].path, str(old_file))


class TestFormatSize(unittest.TestCase):
    def test_bytes(self) -> None:
        self.assertEqual(format_size(500), "500B")

    def test_kilobytes(self) -> None:
        self.assertEqual(format_size(2048), "2.0KB")

    def test_megabytes(self) -> None:
        self.assertEqual(format_size(5 * 1024 * 1024), "5.0MB")


class TestTotalSizeAndDelete(unittest.TestCase):
    def test_total_size_sums_entries(self) -> None:
        now = time.time()
        with TemporaryDirectory() as tmp:
            a = Path(tmp) / "a.txt"
            b = Path(tmp) / "b.txt"
            self._touch(a, 10 * 86400, now)
            self._touch(b, 10 * 86400, now)
            entries, _ = find_old_files([tmp], 7 * 86400, now=now)
            self.assertEqual(total_size(entries), sum(e.size for e in entries))

    def _touch(self, path: Path, age_seconds: float, now: float) -> None:
        path.write_text("hello world")
        mtime = now - age_seconds
        os.utime(path, (mtime, mtime))

    def test_delete_files_removes_and_counts(self) -> None:
        now = time.time()
        with TemporaryDirectory() as tmp:
            a = Path(tmp) / "a.txt"
            self._touch(a, 10 * 86400, now)
            entries, _ = find_old_files([tmp], 7 * 86400, now=now)

            deleted, errors = delete_files(entries)

            self.assertEqual(deleted, 1)
            self.assertEqual(errors, [])
            self.assertFalse(a.exists())


if __name__ == "__main__":
    unittest.main()
