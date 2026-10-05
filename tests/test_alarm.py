"""Native sound requests and completion wiring without audible unit tests."""

import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QProcess
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from pages.setter_window import SetterWindow
from utils.alarm import AlarmService
from utils.timer_store import TimerStore


APP = QApplication.instance() or QApplication([])
APP.setQuitOnLastWindowClosed(False)


class AlarmTests(unittest.TestCase):
    def setUp(self) -> None:
        self.alarm = AlarmService()
        self.fallback = patch.object(self.alarm, "_fallback").start()
        self.addCleanup(patch.stopall)

    def tearDown(self) -> None:
        self.alarm.stop()
        self.alarm.deleteLater()
        APP.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_windows_uses_async_system_alarm_and_handles_failure(self) -> None:
        sound = SimpleNamespace(PlaySound=Mock(), SND_ALIAS=65536, SND_ASYNC=1, SND_SYSTEM=2097152)
        with patch("utils.alarm.sys.platform", "win32"), patch.dict(sys.modules, winsound=sound):
            self.alarm.play()
            sound.PlaySound.assert_called_once_with("Notification.Looping.Alarm", 2162689)
            self.fallback.assert_not_called()
            sound.PlaySound.side_effect = RuntimeError("No audio device")
            self.alarm.play()
        self.fallback.assert_called_once()

    def test_linux_requests_theme_alarm_and_restores_frozen_library_path(self) -> None:
        for original in (None, "/system/libraries"):
            with self.subTest(original=original), patch("utils.alarm.sys.platform", "linux"), \
                    patch("utils.alarm.sys.frozen", True, create=True), \
                    patch.dict(os.environ, {"LD_LIBRARY_PATH": "/bundled"}, clear=True), \
                    patch.object(QProcess, "start"):
                if original is not None:
                    os.environ["LD_LIBRARY_PATH_ORIG"] = original
                self.alarm.play()
                player = next(iter(self.alarm._players))
                self.assertEqual(player.program(), "canberra-gtk-play")
                self.assertEqual(player.arguments()[:2], ["--id", "alarm-clock-elapsed"])
                env = player.processEnvironment()
                self.assertEqual(env.value("LD_LIBRARY_PATH"), original or "")
                self.assertEqual(os.environ["LD_LIBRARY_PATH"], "/bundled")
                self.alarm.stop()

    def test_linux_player_success_failure_crash_and_missing_executable(self) -> None:
        real_start = QProcess.start
        for script in ("pass", "raise SystemExit(1)", "import os; os.abort()", None):
            with self.subTest(script=script):
                self.fallback.reset_mock()

                def start(player):
                    player.setProgram(sys.executable if script is not None else "/missing-clockin-player")
                    player.setArguments(["-c", script] if script is not None else [])
                    real_start(player)

                with patch("utils.alarm.sys.platform", "linux"), patch.object(QProcess, "start", start):
                    self.alarm.play()
                    for _ in range(200):
                        if not self.alarm._players:
                            break
                        QTest.qWait(10)
                self.assertFalse(self.alarm._players)
                self.assertEqual(self.fallback.call_count, 0 if script == "pass" else 1)

    def test_stop_reaps_an_active_player_without_fallback(self) -> None:
        player = QProcess(self.alarm)
        self.alarm._players.add(player)
        player.start(sys.executable, ["-c", "import time; time.sleep(30)"])
        self.assertTrue(player.waitForStarted())
        self.alarm.stop()
        self.assertEqual(player.state(), QProcess.ProcessState.NotRunning)
        self.assertFalse(self.alarm._players)
        self.fallback.assert_not_called()

    def test_each_timer_alarms_once_per_run_even_with_hidden_views(self) -> None:
        with TemporaryDirectory() as directory, patch.object(AlarmService, "play") as play:
            window = SetterWindow(TimerStore(Path(directory) / "timers.json"))
            try:
                now = [100.0]
                first = window.add_timer(1)
                second = window.add_timer(2)
                for controller in (first, second):
                    controller.model._clock = lambda: now[0]
                    window.show_timer(controller.model.timer_id)
                window._hide_floating_timers()
                window.hide()
                now[0] += 1
                first.model.refresh()
                first.model.refresh()
                second.model.refresh()
                self.assertEqual(play.call_count, 1)
                now[0] += 1
                second.pause()  # Deadline reached between UI refreshes.
                self.assertEqual(play.call_count, 2)
                first.start()
                now[0] += 1
                first.model.refresh()
                self.assertEqual(play.call_count, 3)
                first.reset()
                first.start()
                first.pause()
                second.model.configure(10)
                window.remove_timer(first.model.timer_id)
                self.assertEqual(play.call_count, 3)
            finally:
                window.close()
                window.deleteLater()
                APP.sendPostedEvents(None, QEvent.Type.DeferredDelete)
