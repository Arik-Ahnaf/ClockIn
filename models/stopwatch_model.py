"""Monotonic elapsed time, independent of widgets and refresh frequency."""

from collections.abc import Callable
from time import monotonic

from PySide6.QtCore import QObject, Signal, Slot

from .timer_model import TimerState


class StopwatchModel(QObject):
    changed = Signal()

    def __init__(self, parent: QObject | None = None, *,
                 clock: Callable[[], float] = monotonic) -> None:
        super().__init__(parent)
        self._clock = clock
        self._state = TimerState.IDLE
        self._elapsed_seconds = 0.0
        self._accumulated_seconds = 0.0
        self._started_at: float | None = None

    @property
    def state(self) -> TimerState:
        return self._state

    @property
    def elapsed_seconds(self) -> float:
        """The last published snapshot, shared by all observing views."""
        return self._elapsed_seconds

    @property
    def display_seconds(self) -> int:
        return int(self._elapsed_seconds)

    @Slot()
    def start(self) -> None:
        if self._state is TimerState.RUNNING:
            return
        self._started_at = self._clock()
        self._state = TimerState.RUNNING
        self.changed.emit()

    @Slot()
    def pause(self) -> None:
        if self._state is not TimerState.RUNNING:
            return
        self._elapsed_seconds = self._read_elapsed()
        self._accumulated_seconds = self._elapsed_seconds
        self._started_at = None
        self._state = TimerState.PAUSED
        self.changed.emit()

    @Slot()
    def reset(self) -> None:
        self._started_at = None
        self._elapsed_seconds = 0.0
        self._accumulated_seconds = 0.0
        self._state = TimerState.IDLE
        self.changed.emit()

    @Slot()
    def refresh(self) -> None:
        if self._state is TimerState.RUNNING:
            elapsed = self._read_elapsed()
            if elapsed != self._elapsed_seconds:
                self._elapsed_seconds = elapsed
                self.changed.emit()

    def _read_elapsed(self) -> float:
        assert self._started_at is not None
        return self._accumulated_seconds + self._clock() - self._started_at
