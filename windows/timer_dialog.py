from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QShortcut, QKeySequence
from PySide6.QtWidgets import (
    QDialog, QLabel, QPushButton, QSpinBox, QWidget,
)

from utils.design import ACCENT, ASSETS, BACKGROUND, SURFACE, TEXT, font


class TwoDigitSpinBox(QSpinBox):
    def textFromValue(self, value: int) -> str:
        return f"{value:02d}"


class TimerDialog(QDialog):
    """The 500×300 'Set the parameters' frame from the design export."""

    def __init__(self, duration: int = 300, parent: QWidget | None = None) -> None:
        super().__init__(None, Qt.WindowType.Window | Qt.WindowType.WindowTitleHint
                         | Qt.WindowType.WindowSystemMenuHint | Qt.WindowType.WindowCloseButtonHint)
        self._owner = parent
        self.setWindowTitle("Set the parameters")
        self.setFixedSize(500, 300)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
        self.setModal(False)
        title = QLabel("Set the parameters", self)
        title.setGeometry(100, 49, 300, 36)
        title.setFont(font(24, True, family="Open Sans"))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {TEXT}; background: transparent;")
        hours, remainder = divmod(duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.fields: list[TwoDigitSpinBox] = []
        for x, label_text, maximum, value in zip(
            (136, 215, 294), ("Hour", "Minute", "Second"), (99, 59, 59),
            (hours, minutes, seconds), strict=True,
        ):
            label = QLabel(label_text, self)
            label.setGeometry(x - 6, 99, 81, 30)
            label.setFont(font(20, True, family="Open Sans"))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(f"color: {TEXT}; background: transparent;")
            field = TwoDigitSpinBox(self)
            field.setGeometry(x, 143, 69, 41)
            field.setRange(0, maximum)
            field.setValue(value)
            field.setFont(font(24, True, family="Open Sans"))
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
        self.set_button = QPushButton("Set", self)
        self.set_button.setIcon(QIcon(str(ASSETS / "set.png")))
        self.set_button.setGeometry(140, 209, 100, 36)
        self.set_button.setDefault(True)
        cancel = QPushButton("Cancel", self)
        cancel.setGeometry(260, 209, 100, 36)
        for button, color in ((self.set_button, ACCENT), (cancel, SURFACE)):
            button.setFont(font(20, True, family="Open Sans"))
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setStyleSheet(
                f"QPushButton {{ background: {color}; color: {TEXT}; border: none;"
                " border-radius: 8px; padding: 0; }"
                f"QPushButton:hover {{ background: {QColor(color).lighter(110).name()}; }}"
                f"QPushButton:focus {{ border: 1px solid {TEXT}; }}"
                "QPushButton:disabled { color: #868686; }"
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
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(BACKGROUND))
        painter.drawRoundedRect(self.rect(), 4, 4)
