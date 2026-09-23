"""Persistence, validation, and failure safety on isolated JSON databases."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from utils.timer_store import TimerRecord, TimerStore, TimerStoreError


class TimerStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "timers.json"
        self.store = TimerStore(self.path)

    def test_missing_database_creates_empty_file(self) -> None:
        self.assertEqual(self.store.load(), [])
        self.assertEqual(json.loads(self.path.read_text()), {"version": 1, "timers": []})

    def test_round_trip_preserves_order_identity_and_duration(self) -> None:
        records = [TimerRecord("second", 3723), TimerRecord("first", 359999)]
        self.store.save(records)
        self.assertEqual(TimerStore(self.path).load(), records)
        self.assertEqual(list(self.path.parent.glob("*.tmp")), [])

    def test_reads_file_again_instead_of_caching(self) -> None:
        self.store.save([TimerRecord("one", 5)])
        self.assertEqual(self.store.load(), [TimerRecord("one", 5)])
        self.path.write_text('{"version": 1, "timers": [{"timer_id": "manual", "duration_seconds": 9}]}')
        self.assertEqual(self.store.load(), [TimerRecord("manual", 9)])

    def test_invalid_files_are_reported_and_preserved(self) -> None:
        payloads = ["", "{broken", "[]", '{"version": 2, "timers": []}',
                    '{"version": true, "timers": []}', '{"version": 1, "timers": {}}']
        for duration in (0, -1, 360000, True, 2.5, "30", None):
            payloads.append(json.dumps({"version": 1, "timers": [{"timer_id": "one", "duration_seconds": duration}]}))
        for timers in ([None], [{}], [{"timer_id": "", "duration_seconds": 1}],
                       [{"timer_id": "same", "duration_seconds": 1}] * 2):
            payloads.append(json.dumps({"version": 1, "timers": timers}))
        for contents in payloads:
            with self.subTest(contents=contents):
                self.path.write_text(contents)
                with self.assertRaises(TimerStoreError):
                    self.store.load()
                self.assertEqual(self.path.read_text(), contents)

    def test_read_error_does_not_treat_database_as_empty(self) -> None:
        self.store.save([TimerRecord("keep", 5)])
        with patch.object(Path, "read_text", side_effect=PermissionError("Denied")):
            with self.assertRaises(TimerStoreError):
                self.store.load()
        self.assertEqual(self.store.load(), [TimerRecord("keep", 5)])

    def test_failed_atomic_replace_preserves_previous_data(self) -> None:
        self.store.save([TimerRecord("keep", 10)])
        previous = self.path.read_bytes()
        with patch("utils.timer_store.os.replace", side_effect=OSError("Disk failure")):
            with self.assertRaises(TimerStoreError):
                self.store.save([TimerRecord("new", 20)])
        self.assertEqual(self.path.read_bytes(), previous)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_invalid_save_preserves_previous_data(self) -> None:
        self.store.save([TimerRecord("keep", 10)])
        with self.assertRaises(TimerStoreError):
            self.store.save([TimerRecord("bad", 0)])
        self.assertEqual(self.store.load(), [TimerRecord("keep", 10)])

    def windows_store(self) -> TimerStore:
        with patch("utils.timer_store.sys.platform", "win32"), \
                patch("utils.paths.QStandardPaths.writableLocation", return_value=self.directory.name), \
                patch("utils.timer_store.DEFAULT_DATABASE", self.path):
            return TimerStore()

    def test_windows_first_launch_uses_user_data_directory(self) -> None:
        store = self.windows_store()
        self.assertEqual(store.path, Path(self.directory.name) / "ClockIn" / "timers.json")
        self.assertEqual(store.load(), [])
        self.assertTrue(store.path.is_file())
        self.assertFalse(self.path.exists())

    def test_windows_imports_legacy_data_once_without_modifying_source(self) -> None:
        original = [TimerRecord("existing", 125)]
        self.store.save(original)
        before = self.path.read_bytes()
        store = self.windows_store()
        self.assertEqual(store.load(), original)
        self.assertEqual(self.path.read_bytes(), before)
        store.save([])
        self.assertEqual(self.windows_store().load(), [])

    def test_windows_invalid_legacy_database_is_preserved(self) -> None:
        self.path.write_text("{broken", encoding="utf-8")
        store = self.windows_store()
        with self.assertRaises(TimerStoreError):
            store.load()
        self.assertFalse(store.path.exists())
        self.assertEqual(self.path.read_text(), "{broken")

    def test_windows_failed_import_preserves_source(self) -> None:
        records = [TimerRecord("keep", 50)]
        self.store.save(records)
        store = self.windows_store()
        with patch("utils.timer_store.os.replace", side_effect=PermissionError("Denied")):
            with self.assertRaises(TimerStoreError):
                store.load()
        self.assertEqual(self.store.load(), records)
        self.assertFalse(store.path.exists())

    def test_explicit_database_path_is_respected_on_windows(self) -> None:
        with patch("utils.timer_store.sys.platform", "win32"):
            store = TimerStore(self.path)
        self.assertEqual(store.path, self.path)
        self.assertEqual(store.load(), [])


if __name__ == "__main__":
    unittest.main()
