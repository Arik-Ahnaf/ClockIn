from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QAbstractButton, QWidget

from utils.design import ASSETS, TEXT


class AssetButton(QAbstractButton):
    """Clickable Figma raster artwork; no font glyph substitutions."""

    def __init__(
        self, asset: str, label: str, size: int | tuple[int, int], parent: QWidget,
        *, circle: str | None = None, artwork_size: tuple[int, int] | None = None,
        background: str | None = None, radius: int = 8,
    ) -> None:
        super().__init__(parent)
        self._circle = circle
        self._background = background
        self._radius = radius
        self._hovered = False
        self._artwork_size = artwork_size
        self.setFixedSize(*(size if isinstance(size, tuple) else (size, size)))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(label)
        self.setToolTip(label)
        self.set_asset(asset)

    def set_asset(self, asset: str) -> None:
        if getattr(self, "_asset_name", None) == asset:
            return
        self._asset_name = asset
        self._pixmap = QPixmap(str(ASSETS / asset))
        # Some exported icons include their colored backing circle. Preserve
        # that artwork while applying the same 10% brightness rule on hover.
        hover_image = self._pixmap.toImage()
        for y in range(hover_image.height()):
            for x in range(hover_image.width()):
                hover_image.setPixelColor(x, y, hover_image.pixelColor(x, y).lighter(110))
        self._hover_pixmap = QPixmap.fromImage(hover_image)
        self.update()

    def enterEvent(self, event) -> None:
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def set_label(self, label: str) -> None:
        self.setAccessibleName(label)
        self.setToolTip(label)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        backing = self._circle or self._background
        if backing:
            painter.setPen(Qt.PenStyle.NoPen)
            color = QColor(backing)
            painter.setBrush(color.lighter(110) if self._hovered else color)
            if self._circle:
                painter.drawEllipse(QRectF(self.rect()))
            else:
                painter.drawRoundedRect(QRectF(self.rect()), self._radius, self._radius)
        target = QRectF(self.rect())
        if self._artwork_size:
            width, height = self._artwork_size
            target = QRectF((self.width() - width) / 2, (self.height() - height) / 2, width, height)
        artwork = self._hover_pixmap if self._hovered and not backing else self._pixmap
        painter.drawPixmap(target, artwork, QRectF(artwork.rect()))
        if self.hasFocus() or self.isChecked():
            painter.setPen(QPen(QColor(TEXT), 1, Qt.PenStyle.SolidLine if self.isChecked() else Qt.PenStyle.DotLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            outline = QRectF(self.rect()).adjusted(1, 1, -1, -1)
            if self._background:
                painter.drawRoundedRect(outline, self._radius, self._radius)
            else:
                painter.drawEllipse(outline)
