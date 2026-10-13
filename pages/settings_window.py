"""The 300×300 Settings Page from Figma, with staged Save/Exit choices."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QCheckBox, QDialog, QPushButton, QWidget

from utils.design import ACCENT, ASSETS, BACKGROUND, font


class SettingsWindow(QDialog):
    def __init__(
        self, transparent_background: bool, timers_stay_on_top: bool, parent: QWidget,
    ) -> None:
        super().__init__(parent, Qt.WindowType.Window | Qt.WindowType.WindowTitleHint
                         | Qt.WindowType.WindowSystemMenuHint | Qt.WindowType.WindowCloseButtonHint
                         | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle("Settings")
        self.setFixedSize(300, 300)
        self.setModal(False)
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
        self.setStyleSheet(f"SettingsWindow {{ background: {BACKGROUND}; }}")

        self.transparent_background_checkbox = self._checkbox(
            "Transparent Background", 20, transparent_background,
        )
        self.stay_on_top_checkbox = self._checkbox("Timers stay on top", 64, timers_stay_on_top)
        self.exit_button = self._button("Exit", 50, "#8E8E93")
        self.save_button = self._button("Save", 160, ACCENT)
        self.save_button.setDefault(True)
        self.exit_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self.accept)
        self.move(parent.geometry().center() - self.rect().center())

    def _checkbox(self, text: str, y: int, checked: bool) -> QCheckBox:
        checkbox = QCheckBox(text, self)
        checkbox.setGeometry(30, y, 240, 44)
        checkbox.setFont(font(16, family="Arimo"))
        checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        checkbox.setChecked(checked)
        checkbox.setStyleSheet(
            "QCheckBox { color: #DDDDDD; background: transparent; spacing: 8px; }"
            "QCheckBox::indicator { width: 16px; height: 16px; border: 3px solid #575957;"
            " border-radius: 4px; background: transparent; }"
            f'QCheckBox::indicator:checked {{ image: url("{(ASSETS / "check.png").as_posix()}"); }}'
            f"QCheckBox::indicator:focus {{ border-color: {ACCENT}; }}"
        )
        return checkbox

    def _button(self, text: str, x: int, color: str) -> QPushButton:
        button = QPushButton(text, self)
        button.setGeometry(x, 250, 90, 30)
        button.setFont(font(20, True, family="Inter"))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setAutoDefault(False)
        button.setStyleSheet(
            f"QPushButton {{ background: {color}; color: #FFFFFF; border: none;"
            " border-radius: 8px; padding: 0; }"
            f"QPushButton:hover {{ background: {QColor(color).lighter(110).name()}; }}"
            "QPushButton:focus { border: 1px solid #FFFFFF; }"
        )
        return button
