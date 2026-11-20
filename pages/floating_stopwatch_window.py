"""Figma Stopwatch Widget, sharing the timer window's native drag behavior."""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QMenu

from controllers import TimerController
from models import StopwatchModel, TimerState
from pages.floating_timer_window import FloatingTimerWindow, VisualState
from utils.design import BACKGROUND, FLOAT_TEXT, MENU_STYLE, font, time_text


class FloatingStopwatchWindow(FloatingTimerWindow):
    def __init__(self, controller: TimerController) -> None:
        assert isinstance(controller.model, StopwatchModel)
        super().__init__(controller)
        self.setWindowTitle("ClockIn — Floating stopwatch")
        self.reset_button.set_label("Stop and reset stopwatch")
        self.close_button.set_label("Close and reset stopwatch")
        self.close_button.set_asset("stopwatch-close.svg")
        self.remove_requested.connect(self.dismiss_requested)

    def _sync_model(self) -> None:
        running = self.model.state is TimerState.RUNNING
        self.play_button.set_asset("v2-pause.svg" if running else "v2-play.svg")
        self.play_button.set_label("Pause stopwatch" if running else "Start / resume stopwatch")
        self.display_text = time_text(self.model.display_seconds, compact=True)
        self.setAccessibleName(f"Stopwatch {self.display_text}, {self.model.state.name.lower()}")
        self._update_visual_state()

    def _apply_layout(self) -> None:
        self.setFixedSize(*((220, 100) if self._expanded else (200, 60)))
        self.play_button.move(69, 52)
        self.reset_button.move(115, 52)
        self.close_button.setFixedSize(15, 15)
        self.close_button.move(*((196, 8) if self._expanded else (178, 6)))
        self.close_button.setVisible(self._expanded or self.visual_state is VisualState.DEFAULT)

    def contextMenuEvent(self, event) -> None:
        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE)
        menu.addAction("Pause" if self.model.state is TimerState.RUNNING else "Start / resume", self.controller.toggle)
        menu.addAction("Reset", self.controller.reset)
        menu.addSeparator()
        menu.addAction("Hide floating stopwatch", self.close)
        menu.exec(event.globalPos())
        menu.deleteLater()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(BACKGROUND))
        painter.drawRoundedRect(QRectF(self.rect()), 8, 8)
        painter.setPen(QColor(FLOAT_TEXT))
        painter.setFont(font(40, True, family="IBM Plex Sans Condensed"))
        painter.drawText(QRectF(0, 0 if self._expanded else 4, self.width(), 52),
                         Qt.AlignmentFlag.AlignCenter, self.display_text)
