import sys

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QShortcut, QKeySequence
from PySide6.QtWidgets import (
    QDialog, QLabel, QPushButton, QSpinBox, QWidget,
)

from utils.design import ACCENT, ASSETS, BACKGROUND, SURFACE, TEXT, font


class TwoDigitSpinBox(QSpinBox):
    def textFromValue(self, value: int) -> str:
        return f"{value:02d}"


class TimerDialog(QDialog):
    """The 400×300 'Set the parameters' frame from the design export."""

    def __init__(self, duration: int = 300, parent: QWidget | None = None) -> None:
        super().__init__(None, Qt.WindowType.Window | Qt.WindowType.WindowTitleHint
                         | Qt.WindowType.WindowSystemMenuHint | Qt.WindowType.WindowCloseButtonHint)
        self._owner = parent
        self.setWindowTitle("Set the parameters")
        self.setFixedSize(400, 300)
        # Qt only supports translucent top-level Windows widgets when frameless.
        # Keep this dialog's native title bar and use an opaque client background.
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, sys.platform != "win32")
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
        self.setModal(False)
        title = QLabel("Set the parameters", self)
        title.setGeometry(91, 50, 217, 31)
        title.setFont(font(24, True, family="IBM Plex Sans"))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {TEXT}; background: transparent;")
        hours, remainder = divmod(duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.fields: list[TwoDigitSpinBox] = []
        for x, label_text, maximum, value in zip(
            (86, 165, 244), ("Hour", "Minute", "Second"), (99, 59, 59),
            (hours, minutes, seconds), strict=True,
        ):
            label = QLabel(label_text, self)
            label.setGeometry({86: 90, 165: 156, 244: 240}[x], 99,
                              {86: 46, 165: 64, 244: 69}[x], 26)
            label_font = font(20, family="IBM Plex Sans")
            label_font.setVariableAxis(QFont.Tag("wght"), 600)
            label.setFont(label_font)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(f"color: {TEXT}; background: transparent;")
            field = TwoDigitSpinBox(self)
            field.setGeometry(x, 141, 69, 41)
            field.setRange(0, maximum)
            field.setValue(value)
            field.setFont(font(24, True, family="IBM Plex Sans"))
            field.setAlignment(Qt.AlignmentFlag.AlignCenter)
            field.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
            field.setKeyboardTracking(True)
            field.setAccessibleName(label_text)
            field.setStyleSheet(
                f"QSpinBox {{ background: {SURFACE}; color: {TEXT}; border: none;"
                " border-radius: 8px; padding: 0; }"
                f"QSpinBox:focus {{ border: 1px solid {ACCENT}; }}"
            )
            label.setBuddy(field)
            field.valueChanged.connect(self._validate)
            self.fields.append(field)
        self.set_button = QPushButton(self)
        self.set_button.setIcon(QIcon(str(ASSETS / "dialog-save-button.svg")))
        self.set_button.setAccessibleName("Set timer")
        self.set_button.setGeometry(85, 209, 110, 46)
        self.set_button.setDefault(True)
        cancel = QPushButton(self)
        cancel.setIcon(QIcon(str(ASSETS / "dialog-cancel-button.svg")))
        cancel.setAccessibleName("Cancel")
        cancel.setToolTip("Cancel")
        cancel.setGeometry(205, 209, 110, 46)
        for button in (self.set_button, cancel):
            button.setIconSize(QSize(110, 46))
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setStyleSheet(
                "QPushButton { background: transparent; border: none; padding: 0; }"
                f"QPushButton:focus {{ border: 1px dotted {TEXT}; border-radius: 8px; }}"
            )
        self.set_button.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        QShortcut(QKeySequence("Escape"), self, activated=self.reject)
        self._validate()

    @property
    def duration_seconds(self) -> int:
        return sum(field.value() * factor for field, factor in zip(
            self.fields, (3600, 60, 1), strict=True,
        ))

    def _validate(self) -> None:
        if hasattr(self, "set_button"):
            self.set_button.setEnabled(self.duration_seconds > 0)
            self.set_button.setToolTip("Set timer" if self.duration_seconds else "Enter a duration above zero")

    def accept(self) -> None:
        for field in self.fields:
            field.interpretText()
        if self.duration_seconds > 0:
            super().accept()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self._owner:
            self.move(self._owner.geometry().center() - self.rect().center())

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground):
            painter.fillRect(self.rect(), QColor(BACKGROUND))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(BACKGROUND))
        painter.drawRoundedRect(self.rect(), 8, 8)
