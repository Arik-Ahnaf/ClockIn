"""Shared timer data and lifecycle."""

from .timer_model import MAX_DURATION_SECONDS, TimerModel, TimerState
from .stopwatch_model import StopwatchModel

__all__ = ["MAX_DURATION_SECONDS", "TimerModel", "TimerState", "StopwatchModel"]
