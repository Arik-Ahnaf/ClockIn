"""Figma pixels are Qt logical pixels; never multiply these by the DPR."""

from pathlib import Path

from PySide6.QtGui import QFont

ASSETS = Path(__file__).resolve().parents[1] / "assets"
BACKGROUND = "#2A2D34"
SURFACE = "#1A1A1A"
TEXT = "#FFFFF3"
FLOAT_TEXT = "#F2F2F2"
MUTED = "#868686"
ACCENT = "#13506C"
ADD_BUTTON = "#009DDC"
FONT_FAMILY = "Roboto"
SETTER_SIZE = (500, 500)
CARD_SIZE = (200, 50)
FLOAT_SIZE = (200, 60)
FLOAT_HOVER_SIZE = (200, 58)
EXPANDED_SIZE = (270, 130)


def font(pixels: int, bold: bool = False, *, family: str = FONT_FAMILY) -> QFont:
    result = QFont(family)
    result.setFamilies([family, "Adwaita Sans", "Noto Sans"])
    result.setPixelSize(pixels)
    result.setWeight(QFont.Weight.Bold if bold else QFont.Weight.Normal)
    return result


def time_text(seconds: int, *, compact: bool = False) -> str:
    hours, remainder = divmod(max(0, seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    hours_text = str(hours) if compact else f"{hours:02d}"
    return f"{hours_text}:{minutes:02d}:{seconds:02d}"


MENU_STYLE = f"""
QMenu {{ background: {BACKGROUND}; color: {TEXT}; border: 1px solid #868686;
         padding: 5px; font-family: '{FONT_FAMILY}'; font-size: 14px; }}
QMenu::item {{ padding: 7px 20px; }}
QMenu::item:selected {{ background: {ACCENT}; }}
QMenu::item:disabled {{ color: {MUTED}; }}
QMenu::separator {{ height: 1px; background: #464646; margin: 4px; }}
"""
