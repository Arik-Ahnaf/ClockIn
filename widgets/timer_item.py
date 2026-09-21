"""A fixed-size setter card observing a shared timer controller."""

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QColor, QContextMenuEvent, QKeyEvent, QMouseEvent
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QLabel, QMenu, QWidget

from controllers import TimerController
from models import TimerState
from utils.design import BACKGROUND, MENU_STYLE, TEXT, font, time_text
from widgets.asset_button import AssetButton


class TimerItem(QWidget):
    play_requested = Signal()
    configure_requested = Signal()
    reset_requested = Signal()
    remove_requested = Signal()

    def __init__(self, controller: TimerController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = controller
        self.model = controller.model
        self._text_pressed = False
        self._edit_mode = False
        self.setFixedSize(220, 70)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.card = QFrame(self)
        self.card.setGeometry(10, 10, 200, 50)
        self.card.setMouseTracking(True)
        self.card.setStyleSheet(
            f"QFrame {{ background: {BACKGROUND}; border: 1px solid {TEXT};"
            " border-radius: 4px; }"
        )
        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setOffset(0, 4)
        shadow.setBlurRadius(4)
        shadow.setColor(QColor(0, 0, 0, 64))
        self.card.setGraphicsEffect(shadow)
        self._shadow = shadow
        self._shadow.setEnabled(False)
        self.card.installEventFilter(self)

        self.display_text = QLabel(self.card)
        self.display_text.setGeometry(18, 10, 135, 32)
        self.display_text.setFont(font(24, True, family="Adwaita Sans"))
        self.display_text.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.display_text.setStyleSheet("background: transparent; color: #FFFFFF; border: none;")
        self.display_text.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.display_text.setToolTip("Click to edit this timer")

        self.play_button = AssetButton("play-card.png", "Start timer", 24, self.card)
        self.play_button.move(162, 14)
        self.play_button.clicked.connect(self.play_requested)
        self.remove_button = AssetButton("remove.png", "Remove timer", 20, self)
        self.remove_button.move(0, 0)
        self.remove_button.clicked.connect(self.remove_requested)
        self.remove_button.hide()
        self.remove_button.raise_()
        self.model.changed.connect(self._sync_model)
        self._sync_model()

    def _sync_model(self) -> None:
        text = time_text(self.model.display_seconds)
        self.display_text.setText(text)
        self.setAccessibleName(f"Timer {text}")
        if self.model.state is TimerState.RUNNING:
            label = "Show floating timer"
        elif self.model.state is TimerState.PAUSED:
            label = "Resume timer"
        else:
            label = "Start timer"
        self.play_button.set_label(label)

    def set_edit_mode(self, enabled: bool) -> None:
        self._edit_mode = enabled
        self.remove_button.setVisible(enabled)
        if enabled:
            self.remove_button.raise_()

    def eventFilter(self, watched, event) -> bool:
        if watched is self.card:
            if event.type() == QEvent.Type.Enter:
                self._shadow.setEnabled(True)
            elif event.type() in (QEvent.Type.Leave, QEvent.Type.Hide):
                self._shadow.setEnabled(False)
        return super().eventFilter(watched, event)

    def _over_text(self, event: QMouseEvent) -> bool:
        position = self.display_text.mapFrom(self, event.position().toPoint())
        return self.display_text.rect().contains(position)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._over_text(event):
            self._text_pressed = True
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            pressed = self._text_pressed
            self._text_pressed = False
            if pressed and self._over_text(event):
                self.configure_requested.emit()
                event.accept()
                return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.configure_requested.emit()
            event.accept()
        else:
            super().keyPressEvent(event)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE)
        menu.addAction("Edit timer", self.configure_requested.emit)
        menu.addAction("Reset timer", self.reset_requested.emit)
        menu.addSeparator()
        menu.addAction("Remove timer", self.remove_requested.emit)
        menu.exec(event.globalPos())
        menu.deleteLater()
        event.accept()
