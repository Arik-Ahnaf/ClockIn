"""Fixed Figma Stopwatch Page content; the setter owns the shared toolbar."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import QLabel, QWidget

from controllers import TimerController
from models import StopwatchModel, TimerState
from utils.design import TEXT, font
from widgets.asset_button import AssetButton


class StopwatchPage(QWidget):
    def __init__(self, controller: TimerController, parent: QWidget) -> None:
        super().__init__(parent)
        self.controller = controller
        self.model = controller.model
        assert isinstance(self.model, StopwatchModel)
        # Content begins below the existing 66px toolbar.
        self.setGeometry(0, 66, 500, 434)
        self.display = QLabel(self)
        self.display.setGeometry(0, 122, 500, 125)
        display_font = font(96)
        display_font.setVariableAxis(QFont.Tag("wght"), 600)
        self.display.setFont(display_font)
        self.display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.display.setStyleSheet(f"color: {TEXT}; background: transparent;")
        self.display.setAccessibleName("Stopwatch elapsed time")
        self.play_button = AssetButton("stopwatch-play.svg", "Start or resume stopwatch", 86, self)
        self.play_button.move(149, 307)
        self.play_button.clicked.connect(controller.toggle)
        self.reset_button = AssetButton("reset-btn.svg", "Stop and reset stopwatch", 86, self)
        self.reset_button.move(265, 307)
        self.reset_button.clicked.connect(controller.reset)

        reset_action = QAction("Reset stopwatch", self)
        reset_action.setShortcut("Ctrl+R")
        reset_action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        reset_action.triggered.connect(controller.reset)
        self.addAction(reset_action)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setToolTip("Reset stopwatch: Ctrl+R or right-click")
        self.model.changed.connect(self._sync)
        self._sync()

    def _sync(self) -> None:
        running = self.model.state is TimerState.RUNNING
        self.play_button.set_asset("stopwatch-pause.svg" if running else "stopwatch-play.svg")
        self.play_button.set_label("Pause stopwatch" if running else "Start or resume stopwatch")
        minutes, seconds = divmod(self.model.display_seconds, 60)
        self.display.setText(f"{minutes:02d}:{seconds:02d}")
