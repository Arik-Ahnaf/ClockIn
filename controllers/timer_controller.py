"""Schedule display refreshes without using QTimer as a time source."""

from PySide6.QtCore import QObject, Qt, QTimer, Slot

from models import TimerModel, TimerState


class TimerController(QObject):
    def __init__(self, model: TimerModel, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.model = model
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(50)
        self._refresh_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._refresh_timer.timeout.connect(model.refresh)
        model.changed.connect(self._sync_refresh_timer)
        self._sync_refresh_timer()

    @Slot()
    def start(self) -> None:
        self.model.start()

    @Slot()
    def pause(self) -> None:
        self.model.pause()

    @Slot()
    def toggle(self) -> None:
        if self.model.state is TimerState.RUNNING:
            self.model.pause()
        else:
            self.model.start()

    @Slot()
    def reset(self) -> None:
        self.model.reset()

    @Slot()
    def _sync_refresh_timer(self) -> None:
        if self.model.state is TimerState.RUNNING:
            if not self._refresh_timer.isActive():
                self._refresh_timer.start()
        else:
            self._refresh_timer.stop()
