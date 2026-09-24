"""Native utility window; pointer interaction is independent of timer state."""

from enum import Enum, auto

from PySide6.QtCore import QEvent, QPoint, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QCursor, QKeySequence, QMouseEvent, QPainter, QShortcut
from PySide6.QtWidgets import QApplication, QMenu, QWidget

from controllers import TimerController
from models import TimerState
from utils.design import (
    BACKGROUND, EXPANDED_SIZE, FLOAT_HOVER_SIZE, FLOAT_SIZE, FLOAT_TEXT,
    MENU_STYLE, MUTED, SURFACE, font, time_text,
)
from widgets.asset_button import AssetButton


class VisualState(Enum):
    DEFAULT = auto()
    HOVER = auto()
    DRAGGING = auto()


class FloatingTimerWindow(QWidget):
    remove_requested = Signal()
    closed = Signal()

    def __init__(self, controller: TimerController) -> None:
        # X11 window managers can hide all utility windows when the main window
        # is minimized, even without a parent. Use an independent normal window
        # on X11/XWayland; retain taskbar-free tool windows on other platforms.
        window_type = (Qt.WindowType.Window if QApplication.platformName() == "xcb"
                       else Qt.WindowType.Tool)
        super().__init__(None, window_type | Qt.WindowType.FramelessWindowHint
                         | Qt.WindowType.WindowStaysOnTopHint)
        self.controller = controller
        self.model = controller.model
        self.setWindowTitle("ClockIn — Floating timer")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
        self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._is_hovered = False
        self._is_dragging = False
        self._controls_open = False
        self._drag_offset = QPoint()
        self._press_global = QPoint()
        self._moved = False
        self.visual_state = VisualState.DEFAULT
        self.display_text = ""
        self._expanded = False

        self.pause_button = AssetButton(
            "pause.png", "Pause timer", 50, self,
            circle=BACKGROUND, artwork_size=(26, 25),
        )
        self.pause_button.move(65, 68)
        self.pause_button.clicked.connect(controller.toggle)
        self.remove_button = AssetButton(
            "trash.png", "Delete timer", 50, self,
            circle=BACKGROUND, artwork_size=(25, 25),
        )
        self.remove_button.move(155, 68)
        self.remove_button.clicked.connect(self.remove_requested)
        self.model.changed.connect(self._sync_model)
        QShortcut(QKeySequence("Space"), self, activated=controller.toggle)
        QShortcut(QKeySequence("Delete"), self, activated=self.remove_requested.emit)
        QShortcut(QKeySequence("Escape"), self, activated=self._escape)
        self._sync_model()
        self._update_visual_state()

    @property
    def is_dragging(self) -> bool:
        return self._is_dragging

    @property
    def controls_open(self) -> bool:
        return self._controls_open

    def set_stay_on_top(self, enabled: bool) -> None:
        flag = Qt.WindowType.WindowStaysOnTopHint
        if bool(self.windowFlags() & flag) == enabled:
            return
        was_visible = self.isVisible()
        geometry = self.geometry()
        # Changing QWidget window flags hides/recreates the native window.
        # Restore only windows that were visible; hidden timers stay hidden.
        self.setWindowFlag(flag, enabled)
        self.setGeometry(geometry)
        if was_visible:
            self.show()
            self._is_hovered = self.geometry().contains(QCursor.pos())
            self._update_visual_state()

    def restore(self) -> None:
        self.show()
        self.raise_()
        self._is_hovered = self.geometry().contains(QCursor.pos())
        self._update_visual_state()

    def _sync_model(self) -> None:
        self.display_text = time_text(self.model.display_seconds, compact=True)
        running = self.model.state is TimerState.RUNNING
        self.pause_button.set_asset("pause.png" if running else "play.png")
        self.pause_button.set_label("Pause timer" if running else "Start / resume timer")
        self.setAccessibleName(f"Timer {self.display_text}, {self.model.state.name.lower()}")
        self.update()

    def _update_visual_state(self) -> None:
        """The only place that resolves appearance, geometry, and cursors."""
        if self._is_dragging:
            self.visual_state = VisualState.DRAGGING
        elif self._is_hovered:
            self.visual_state = VisualState.HOVER
        else:
            self.visual_state = VisualState.DEFAULT
        self._expanded = self._is_dragging or self._controls_open
        # The hover export has a 58px painted surface. Retaining the 60px hit
        # area avoids enter/leave oscillation in its two transparent bottom rows.
        self.setFixedSize(*(EXPANDED_SIZE if self._expanded else FLOAT_SIZE))
        self.pause_button.setVisible(self._expanded)
        self.remove_button.setVisible(self._expanded)
        self.setCursor(Qt.CursorShape.ClosedHandCursor if self._is_dragging
                       else Qt.CursorShape.OpenHandCursor)
        self.update()

    def enterEvent(self, event) -> None:
        self._is_hovered = True
        self._update_visual_state()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._is_hovered = False
        self._update_visual_state()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return
        # Child buttons consume their presses; all painted text/background is
        # one continuous draggable surface without decorative child dead zones.
        self._press_global = event.globalPosition().toPoint()
        self._drag_offset = self._press_global - self.pos()
        self._moved = False
        self._is_dragging = True
        self._update_visual_state()
        if QApplication.platformName() not in ("offscreen", "minimal"):
            self.grabMouse()
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not self._is_dragging:
            super().mouseMoveEvent(event)
            return
        if not event.buttons() & Qt.MouseButton.LeftButton:
            self._finish_drag(QCursor.pos(), toggle_controls=False)
            event.accept()
            return
        global_position = event.globalPosition().toPoint()
        if (global_position - self._press_global).manhattanLength() >= QApplication.startDragDistance():
            self._moved = True
        # Always use the INITIAL offset; never accumulate local deltas.
        self.move(global_position - self._drag_offset)
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._is_dragging:
            if (event.globalPosition().toPoint() - self._press_global).manhattanLength() >= QApplication.startDragDistance():
                self._moved = True
            self._finish_drag(QCursor.pos(), toggle_controls=not self._moved)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def _finish_drag(self, global_position: QPoint, *, toggle_controls: bool = False) -> None:
        self._is_dragging = False
        if QWidget.mouseGrabber() is self:
            self.releaseMouse()
        if toggle_controls:
            self._controls_open = not self._controls_open
        self._update_visual_state()
        # Resolve against the CURRENT geometry, including any compact resize.
        self._is_hovered = self.geometry().contains(global_position)
        self._update_visual_state()

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.UngrabMouse and getattr(self, "_is_dragging", False):
            self._finish_drag(QCursor.pos())
        return super().event(event)

    def _escape(self) -> None:
        if self._is_dragging:
            self._finish_drag(QCursor.pos())
        if self._controls_open:
            self._controls_open = False
            self._update_visual_state()
            self._is_hovered = self.geometry().contains(QCursor.pos())
            self._update_visual_state()
        else:
            self.close()

    def hideEvent(self, event) -> None:
        if self._is_dragging:
            self._finish_drag(QCursor.pos())
        self._is_hovered = False
        self._update_visual_state()
        super().hideEvent(event)

    def closeEvent(self, event) -> None:
        if self._is_dragging:
            self._finish_drag(QCursor.pos())
        self.closed.emit()
        event.accept()

    def contextMenuEvent(self, event) -> None:
        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE)
        running = self.model.state is TimerState.RUNNING
        menu.addAction("Pause" if running else "Start / resume", self.controller.toggle)
        menu.addAction("Reset", self.controller.reset)
        menu.addSeparator()
        menu.addAction("Hide floating timer", self.close)
        menu.addAction("Delete timer", self.remove_requested.emit)
        menu.exec(event.globalPos())
        menu.deleteLater()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        surface = self.rect()
        if not self._expanded and self.visual_state is VisualState.HOVER:
            surface.setHeight(FLOAT_HOVER_SIZE[1])
        painter.fillRect(surface, QColor(SURFACE))
        active = self._expanded or self.visual_state is not VisualState.DEFAULT
        painter.setPen(QColor(FLOAT_TEXT if active else MUTED))
        painter.setFont(font(48 if self._expanded else 40, True, family="Noto Sans"))
        text_rect = QRectF(0, 9, 270, 56) if self._expanded else QRectF(0, 0, 200, 60)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.display_text)
