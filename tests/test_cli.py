import io
import os
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from tempfile_cleanup_cli.cli import main


def _touch_old(path: Path, age_seconds: float = 10 * 86400) -> None:
    path.write_text("data")
    mtime = time.time() - age_seconds
    os.utime(path, (mtime, mtime))


class TestCli(unittest.TestCase):
    def test_dry_run_lists_and_does_not_delete(self) -> None:
        with TemporaryDirectory() as tmp:
            old_file = Path(tmp) / "old.log"
            _touch_old(old_file)

            out = io.StringIO()
            with redirect_stdout(out):
                code = main([tmp, "--older-than", "7d"])

            self.assertEqual(code, 0)
            self.assertTrue(old_file.exists())
            self.assertIn("dry run", out.getvalue())
            self.assertIn("old.log", out.getvalue())

    def test_apply_deletes_matched_files(self) -> None:
        with TemporaryDirectory() as tmp:
            old_file = Path(tmp) / "old.log"
            _touch_old(old_file)

            out = io.StringIO()
            with redirect_stdout(out):
                code = main([tmp, "--older-than", "7d", "--apply"])

            self.assertEqual(code, 0)
            self.assertFalse(old_file.exists())
            self.assertIn("deleted 1 file", out.getvalue())

    def test_no_matches_reports_nothing_found(self) -> None:
        with TemporaryDirectory() as tmp:
            new_file = Path(tmp) / "fresh.log"
            new_file.write_text("data")

            out = io.StringIO()
            with redirect_stdout(out):
                code = main([tmp, "--older-than", "7d"])

            self.assertEqual(code, 0)
            self.assertIn("no files older", out.getvalue())

    def test_requires_at_least_one_path(self) -> None:
        with self.assertRaises(SystemExit):
            main([])

    def test_invalid_duration_returns_error_code(self) -> None:
        with TemporaryDirectory() as tmp:
            code = main([tmp, "--older-than", "banana"])
            self.assertEqual(code, 2)

    def test_missing_path_warns_but_still_succeeds(self) -> None:
        with TemporaryDirectory() as tmp:
            out = io.StringIO()
            missing = os.path.join(tmp, "does-not-exist")
            with redirect_stdout(out):
                code = main([missing])
            self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
