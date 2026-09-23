"""The 500×500 primary window and deterministic owner of all timers."""

from uuid import uuid4

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QDialog, QFrame, QMenu, QMessageBox, QPushButton, QScrollArea, QWidget,
)

from controllers import TimerController
from models import TimerModel
from utils.design import ADD_BUTTON, BACKGROUND, MENU_STYLE, SETTER_SIZE, SURFACE, TEXT, font
from utils.timer_store import TimerRecord, TimerStore, TimerStoreError
from utils.paths import stylesheet
from widgets.asset_button import AssetButton
from widgets.timer_item import TimerItem
from pages.floating_timer_window import FloatingTimerWindow
from pages.timer_dialog import TimerDialog


class SetterWindow(QWidget):
    def __init__(self, store: TimerStore | None = None) -> None:
        super().__init__()
        self.store = store if store is not None else TimerStore()
        saved_timers = self.store.load()
        self.setWindowTitle("ClockIn")
        self.setFixedSize(*SETTER_SIZE)
        self.setStyleSheet(stylesheet("main"))
        self.timers: dict[str, TimerController] = {}
        self.floating_windows: dict[str, FloatingTimerWindow] = {}
        self.timer_items: dict[str, TimerItem] = {}
        self.parameter_windows: dict[str | None, TimerDialog] = {}
        self.edit_mode = False

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setGeometry(0, 30, 500, 400)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet(
            f"QScrollArea, QScrollArea > QWidget > QWidget {{ background: {BACKGROUND};"
            " border: none; }"
            "QScrollBar:vertical { width: 10px; background: transparent; }"
            "QScrollBar::handle:vertical { background: #868686; min-height: 24px; border-radius: 4px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
            "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }"
        )
        self.timer_content = QWidget()
        self.timer_content.setFixedSize(500, 400)
        self.scroll_area.setWidget(self.timer_content)

        self.settings_menu = QMenu(self)
        self.settings_menu.setStyleSheet(MENU_STYLE)
        new_action = QAction("New timer", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._new_timer)
        self.settings_menu.addAction(new_action)
        self.addAction(new_action)
        self.settings_menu.addSeparator()
        self.settings_menu.addAction("Pause all timers", self._pause_all)
        self.settings_menu.addAction("Reset all timers", self._reset_all)
        self.settings_menu.addAction("Hide floating timers", self._hide_floating_timers)
        self.settings_menu.addSeparator()
        self.settings_menu.addAction("Quit", self.close)

        self.settings_button = self._menu_button("Settings", 10, 73)
        self.settings_button.clicked.connect(self._show_settings)
        self.about_button = self._menu_button("About", 104, 55)
        self.about_button.clicked.connect(self._show_about)
        self.help_button = self._menu_button("Help", 178, 43)
        self.help_button.clicked.connect(self._show_help)

        self.button_section = QWidget(self)
        self.button_section.setGeometry(0, 430, 500, 70)
        self.edit_button = AssetButton(
            "edit.png", "Edit timers", (100, 50), self.button_section,
            background=SURFACE, artwork_size=(30, 30),
        )
        self.edit_button.move(140, 10)
        self.edit_button.setCheckable(True)
        self.edit_button.toggled.connect(self._set_edit_mode)
        self.add_button = AssetButton(
            "add.png", "Add timer", (100, 50), self.button_section,
            background=ADD_BUTTON, artwork_size=(30, 30),
        )
        self.add_button.move(260, 10)
        self.add_button.clicked.connect(self._new_timer)
        for record in saved_timers:
            self._create_timer(record)

    def _menu_button(self, text: str, x: int, width: int) -> QPushButton:
        button = QPushButton(text, self)
        button.setGeometry(x, 0, width, 30)
        button.setFont(font(20))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setStyleSheet(
            "QPushButton { color: #FFFFFF; background: transparent; border: none;"
            " padding: 0; text-align: left; }"
            f"QPushButton:focus {{ border-bottom: 1px solid {TEXT}; }}"
        )
        button.raise_()
        return button

    def add_timer(self, duration: int = 300) -> TimerController:
        record = TimerRecord(uuid4().hex, duration)
        self.store.save(self._timer_records() + [record])
        return self._create_timer(record)

    def _timer_records(self) -> list[TimerRecord]:
        return [TimerRecord(timer_id, controller.model.duration_seconds)
                for timer_id, controller in self.timers.items()]

    def _create_timer(self, record: TimerRecord) -> TimerController:
        model = TimerModel(record.duration_seconds, self, timer_id=record.timer_id)
        controller = TimerController(model, self)
        timer_id = model.timer_id
        item = TimerItem(controller, self.timer_content)
        item.play_requested.connect(lambda: self.show_timer(timer_id))
        item.configure_requested.connect(lambda: self.configure_timer(timer_id))
        item.reset_requested.connect(controller.reset)
        item.remove_requested.connect(lambda: self.remove_timer(timer_id))
        item.set_edit_mode(self.edit_mode)
        self.timers[timer_id] = controller
        self.timer_items[timer_id] = item
        self._arrange_items()
        item.show()
        return controller

    def _arrange_items(self) -> None:
        rows = (len(self.timer_items) + 1) // 2
        self.timer_content.setFixedSize(500, max(400, rows * 60 + 10))
        for index, item in enumerate(self.timer_items.values()):
            row, column = divmod(index, 2)
            item.move(27 + column * 210, row * 60)

    def show_timer(self, timer_id: str) -> None:
        controller = self.timers.get(timer_id)
        if controller is None:
            return
        window = self.floating_windows.get(timer_id)
        if window is None:
            window = FloatingTimerWindow(controller, self)
            window.remove_requested.connect(lambda: self.remove_timer(timer_id))
            self.floating_windows[timer_id] = window
            offset = 18 * (len(self.floating_windows) - 1)
            position = self.frameGeometry().topRight() + QPoint(14 + offset, 40 + offset)
            screen = self.screen()
            if screen is not None:
                available = screen.availableGeometry()
                position.setX(max(available.left(), min(position.x(), available.right() - window.width() + 1)))
                position.setY(max(available.top(), min(position.y(), available.bottom() - window.height() + 1)))
            window.move(position)
        controller.start()
        window.restore()

    def remove_timer(self, timer_id: str) -> None:
        if timer_id not in self.timers:
            return
        try:
            self.store.save([record for record in self._timer_records() if record.timer_id != timer_id])
        except TimerStoreError as exc:
            self._message("Unable to save timers", str(exc))
            return
        controller = self.timers.pop(timer_id, None)
        if controller is None:
            return
        controller.reset()
        parameter_window = self.parameter_windows.get(timer_id)
        if parameter_window is not None:
            parameter_window.reject()
        window = self.floating_windows.pop(timer_id, None)
        if window is not None:
            window.close()
            window.deleteLater()
        item = self.timer_items.pop(timer_id)
        item.hide()
        item.deleteLater()
        controller.model.deleteLater()
        controller.deleteLater()
        self._arrange_items()

    def configure_timer(self, timer_id: str) -> None:
        controller = self.timers.get(timer_id)
        if controller is None:
            return
        self._show_parameter_window(timer_id, controller.model.duration_seconds)

    def _new_timer(self) -> None:
        self._show_parameter_window(None, 300)

    def _show_parameter_window(self, timer_id: str | None, duration: int) -> None:
        dialog = self.parameter_windows.get(timer_id)
        if dialog is None:
            dialog = TimerDialog(duration, self)
            self.parameter_windows[timer_id] = dialog
            dialog.finished.connect(
                lambda result: self._finish_parameter_window(timer_id, dialog, result)
            )
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _finish_parameter_window(self, timer_id: str | None, dialog: TimerDialog, result: int) -> None:
        self.parameter_windows.pop(timer_id, None)
        try:
            if result == QDialog.DialogCode.Accepted:
                if timer_id is None:
                    controller = self.add_timer(dialog.duration_seconds)
                    self.scroll_area.ensureWidgetVisible(self.timer_items[controller.model.timer_id])
                elif timer_id in self.timers:
                    records = [TimerRecord(record.timer_id, dialog.duration_seconds)
                               if record.timer_id == timer_id else record for record in self._timer_records()]
                    self.store.save(records)
                    self.timers[timer_id].model.configure(dialog.duration_seconds)
        except TimerStoreError as exc:
            self._message("Unable to save timers", str(exc))
        finally:
            dialog.deleteLater()

    def _set_edit_mode(self, enabled: bool) -> None:
        self.edit_mode = enabled
        self.edit_button.set_label("Finish editing" if enabled else "Edit timers")
        for item in self.timer_items.values():
            item.set_edit_mode(enabled)

    def _show_settings(self) -> None:
        self.settings_menu.exec(self.settings_button.mapToGlobal(QPoint(0, 30)))

    def _pause_all(self) -> None:
        for controller in self.timers.values():
            controller.pause()

    def _reset_all(self) -> None:
        for controller in self.timers.values():
            controller.reset()

    def _hide_floating_timers(self) -> None:
        for window in self.floating_windows.values():
            window.close()

    def _show_about(self) -> None:
        self._message("About ClockIn", "ClockIn\n\nA desktop timer built with Python and PySide6.")

    def _show_help(self) -> None:
        self._message(
            "ClockIn Help",
            "Use the bottom add button or Settings → New timer (Ctrl+N) to add a timer. "
            "The parameter setter opens as a separate window.\n\n"
            "Use the bottom edit button to show timer removal controls; click it again "
            "to leave edit mode.\n\n"
            "Click a timer's time to change its duration. Its play button starts or resumes "
            "the timer and shows the floating window. Right-click a card to edit, reset, or remove it.\n\n"
            "Click the floating timer to expand or collapse its controls. Drag any noninteractive "
            "part to move it; dragging expands the timer immediately. Pause and resume without "
            "losing elapsed time.\n\n"
            "Closing a floating window hides it while the timer continues. Open it again from "
            "its card. Removing a timer stops and deletes that timer. Closing ClockIn stops all timers.",
        )

    def _message(self, title: str, text: str) -> None:
        message = QMessageBox(self)
        message.setWindowTitle(title)
        message.setText(text)
        message.setTextFormat(Qt.TextFormat.PlainText)
        message.setStandardButtons(QMessageBox.StandardButton.Ok)
        message.setFont(font(14))
        message.setStyleSheet(
            f"QMessageBox {{ background: {BACKGROUND}; }}"
            f"QLabel {{ color: {TEXT}; min-width: 320px; }}"
            f"QPushButton {{ color: {TEXT}; background: #13506C; border: none;"
            " border-radius: 4px; padding: 7px 20px; }"
        )
        message.exec()
        message.deleteLater()

    def closeEvent(self, event: QCloseEvent) -> None:
        for dialog in list(self.parameter_windows.values()):
            dialog.reject()
        for controller in self.timers.values():
            controller.pause()
        self._hide_floating_timers()
        super().closeEvent(event)
