"""Path regression checks for shortcuts, protected installs, and legacy data."""

import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from utils.paths import application_directory, resource_path
from utils.timer_store import TimerRecord, TimerStore


class ResourcePathTests(unittest.TestCase):
    def test_source_resources_ignore_cwd(self) -> None:
        original = Path.cwd()
        with TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                self.assertTrue(resource_path("assets/logo.ico").is_file())
                self.assertTrue(resource_path("styles/main.qss").is_file())
            finally:
                os.chdir(original)

    def test_frozen_resources_follow_executable_not_extraction_or_cwd(self) -> None:
        with TemporaryDirectory() as directory, \
                patch.object(sys, "frozen", True, create=True), \
                patch.object(sys, "executable", str(Path(directory) / "ClockIn.exe")), \
                patch.object(sys, "_MEIPASS", "/unrelated/internal", create=True):
            self.assertEqual(application_directory(), Path(directory))
            self.assertEqual(resource_path("assets/logo.ico"), Path(directory) / "assets/logo.ico")

    def test_resource_paths_cannot_escape_root(self) -> None:
        for name in ("../timers.json", str(Path.cwd() / "timers.json")):
            with self.assertRaises(ValueError):
                resource_path(name)

    def test_linux_source_keeps_local_database(self) -> None:
        with patch("utils.timer_store.sys.platform", "linux"), \
                patch("utils.timer_store.is_bundled", return_value=False):
            self.assertEqual(TimerStore().path, resource_path("timers.json"))

    def test_frozen_linux_uses_user_data_and_imports_legacy_once(self) -> None:
        with TemporaryDirectory() as directory:
            base = Path(directory)
            legacy = base / "installation/timers.json"
            TimerStore(legacy).save([TimerRecord("legacy", 40)])
            with patch("utils.timer_store.sys.platform", "linux"), \
                    patch("utils.timer_store.is_bundled", return_value=True), \
                    patch("utils.timer_store.user_data_directory", return_value=base / "user"), \
                    patch("utils.timer_store.DEFAULT_DATABASE", legacy):
                store = TimerStore()
                self.assertEqual(store.path, base / "user/timers.json")
                self.assertEqual(store.load(), [TimerRecord("legacy", 40)])
                store.save([])
                self.assertEqual(TimerStore().load(), [])
                self.assertEqual(TimerStore(legacy).load(), [TimerRecord("legacy", 40)])


if __name__ == "__main__":
    unittest.main()
