"""A monotonic countdown with no dependency on widgets or refresh frequency."""

from collections.abc import Callable
from enum import Enum, auto
from math import ceil
from time import monotonic
from uuid import uuid4

from PySide6.QtCore import QObject, Signal, Slot


MAX_DURATION_SECONDS = 99 * 3600 + 59 * 60 + 59


class TimerState(Enum):
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    FINISHED = auto()


class TimerModel(QObject):
    """Own the countdown observed by every view of one timer.

    ``remaining_seconds`` is the last published snapshot, so all receivers of
    ``changed`` see the same value. While running, the deadline is authoritative:
    refresh and pause calculate the remaining time from the clock, never ticks.
    """

    changed = Signal()
    finished = Signal()

    def __init__(
        self,
        duration_seconds: int = 300,
        parent: QObject | None = None,
        *,
        clock: Callable[[], float] = monotonic,
        timer_id: str | None = None,
    ) -> None:
        super().__init__(parent)
        self._validate_duration(duration_seconds)
        self.timer_id = timer_id if timer_id is not None else uuid4().hex
        self._duration_seconds = duration_seconds
        self._remaining_seconds = float(duration_seconds)
        self._state = TimerState.IDLE
        self._clock = clock
        self._deadline: float | None = None

    @property
    def duration_seconds(self) -> int:
        return self._duration_seconds

    @property
    def remaining_seconds(self) -> float:
        return self._remaining_seconds

    @property
    def display_seconds(self) -> int:
        return ceil(self._remaining_seconds)

    @property
    def state(self) -> TimerState:
        return self._state

    @Slot()
    def start(self) -> None:
        """Start a full countdown or resume the exact paused remainder."""
        if self._state is TimerState.RUNNING:
            return
        if self._state in (TimerState.IDLE, TimerState.FINISHED):
            self._remaining_seconds = float(self._duration_seconds)
        self._deadline = self._clock() + self._remaining_seconds
        self._state = TimerState.RUNNING
        self.changed.emit()

    @Slot()
    def pause(self) -> None:
        """Account for elapsed time even if the last refresh was delayed."""
        if self._state is not TimerState.RUNNING:
            return
        self._remaining_seconds = self._read_remaining()
        self._deadline = None
        if self._remaining_seconds <= 0:
            self._finish()
            return
        self._state = TimerState.PAUSED
        self.changed.emit()

    @Slot()
    def reset(self) -> None:
        self._deadline = None
        self._remaining_seconds = float(self._duration_seconds)
        self._state = TimerState.IDLE
        self.changed.emit()

    @Slot(int)
    def configure(self, duration_seconds: int) -> None:
        """Replace the duration and return the timer to its idle state."""
        self._validate_duration(duration_seconds)
        self._duration_seconds = duration_seconds
        self.reset()

    @Slot()
    def refresh(self) -> None:
        if self._state is not TimerState.RUNNING:
            return
        remaining = self._read_remaining()
        if remaining <= 0:
            self._finish()
        elif remaining != self._remaining_seconds:
            self._remaining_seconds = remaining
            self.changed.emit()

    def _read_remaining(self) -> float:
        assert self._deadline is not None
        return max(0.0, self._deadline - self._clock())

    def _finish(self) -> None:
        self._deadline = None
        self._remaining_seconds = 0.0
        self._state = TimerState.FINISHED
        self.changed.emit()
        self.finished.emit()

    @staticmethod
    def _validate_duration(duration_seconds: int) -> None:
        if isinstance(duration_seconds, bool) or not isinstance(duration_seconds, int):
            raise TypeError("Timer duration must be a whole number of seconds.")
        if not 1 <= duration_seconds <= MAX_DURATION_SECONDS:
            raise ValueError("Timer duration must be between 00:00:01 and 99:59:59.")
