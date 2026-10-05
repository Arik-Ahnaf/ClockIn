"""Play the operating system's alarm sound without blocking the Qt event loop."""

import logging
import sys

from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, Slot
from PySide6.QtWidgets import QApplication


logger = logging.getLogger(__name__)


class AlarmService(QObject):
    """One sound per completion; Linux players live until playback finishes."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._players: set[QProcess] = set()

    @Slot()
    def play(self) -> None:
        if sys.platform == "win32":
            try:
                import winsound

                # Resolve the user's Windows sound scheme, with the system
                # default sound as PlaySound's fallback for a missing alias.
                winsound.PlaySound(
                    "Notification.Looping.Alarm",
                    winsound.SND_ALIAS | winsound.SND_ASYNC | winsound.SND_SYSTEM,
                )
            except (ImportError, RuntimeError, OSError) as exc:
                self._fallback(str(exc))
        elif sys.platform.startswith("linux"):
            self._play_linux()
        else:
            self._fallback("No alarm backend for this operating system")

    def _play_linux(self) -> None:
        player = QProcess(self)
        environment = QProcessEnvironment.systemEnvironment()
        # PyInstaller prepends bundled libraries. A system executable must use
        # the original library path, or GTK can load incompatible bundled libs.
        if getattr(sys, "frozen", False):
            if environment.contains("LD_LIBRARY_PATH_ORIG"):
                environment.insert("LD_LIBRARY_PATH", environment.value("LD_LIBRARY_PATH_ORIG"))
            else:
                environment.remove("LD_LIBRARY_PATH")
        player.setProcessEnvironment(environment)
        player.setProgram("canberra-gtk-play")
        player.setArguments([
            "--id", "alarm-clock-elapsed",
            "--description", "ClockIn timer finished",
            "--property", "application.name=ClockIn",
        ])
        player.finished.connect(lambda code, status: self._finished(player, code, status))
        player.errorOccurred.connect(lambda error: self._failed(player, error))
        self._players.add(player)
        player.start()

    def _finished(self, player: QProcess, code: int, status: QProcess.ExitStatus) -> None:
        if player not in self._players:
            return
        if code != 0 or status != QProcess.ExitStatus.NormalExit:
            detail = bytes(player.readAllStandardError()).decode(errors="replace").strip()
            self._fallback(detail or "System alarm player failed")
        self._players.remove(player)
        player.deleteLater()

    def _failed(self, player: QProcess, error: QProcess.ProcessError) -> None:
        # Crashes also emit finished; only handle startup failure here.
        if error == QProcess.ProcessError.FailedToStart and player in self._players:
            self._fallback(player.errorString())
            self._players.remove(player)
            player.deleteLater()

    @staticmethod
    def _fallback(reason: str) -> None:
        logger.warning("Unable to play system alarm: %s; using system bell", reason)
        QApplication.beep()

    @Slot()
    def stop(self) -> None:
        """Reap active players when the application closes."""
        for player in tuple(self._players):
            self._players.remove(player)
            player.kill()
            player.waitForFinished(1000)
            player.deleteLater()

