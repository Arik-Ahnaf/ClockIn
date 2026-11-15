"""Figma pixels are Qt logical pixels; never multiply these by the DPR."""

from PySide6.QtGui import QFont

import json

from utils.paths import resource_path

THEME = json.loads(resource_path("themes/dracula.json").read_text(encoding="utf-8"))["Dracula"]

ASSETS = resource_path("assets")
BACKGROUND = THEME["bg-color"]
SURFACE = THEME["neutral-color"]
TEXT = THEME["fg-color"]
FLOAT_TEXT = THEME["fg-color"]
MUTED = THEME["neutral-color"]
ERROR = THEME["error-color"]
ACCENT = THEME["primary-color"]
ADD_BUTTON = ACCENT
FONT_FAMILY = "IBM Plex Sans"
OBJECTIVE = "Add Stopwatch Feature"
OBJECTIVE_COLOR = THEME["off-white"]
SETTER_SIZE = (500, 500)
CARD_SIZE = (200, 50)
FLOAT_SIZE = (270, 80)
FLOAT_HOVER_SIZE = (270, 80)
EXPANDED_SIZE = (300, 120)


def font(pixels: int, bold: bool = False, *, family: str = FONT_FAMILY) -> QFont:
    result = QFont(family)
    result.setFamilies([family, "Adwaita Sans", "Noto Sans"])
    result.setPixelSize(pixels)
    result.setWeight(QFont.Weight.Bold if bold else QFont.Weight.Normal)
    if family == "IBM Plex Sans":
        # The variable font exposes only Regular to Qt; avoid synthetic bold.
        result.setWeight(QFont.Weight.Normal)
        result.setVariableAxis(QFont.Tag("wght"), 700 if bold else 400)
        result.setVariableAxis(QFont.Tag("wdth"), 100)
    return result


def time_text(seconds: int, *, compact: bool = False) -> str:
    hours, remainder = divmod(max(0, seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    hours_text = str(hours) if compact else f"{hours:02d}"
    return f"{hours_text}:{minutes:02d}:{seconds:02d}"


MAIN_STYLE = f"SetterWindow {{ background: {BACKGROUND}; }}"
MENU_STYLE = f'''QMenu {{ background: {BACKGROUND}; color: {TEXT}; border: 1px solid {MUTED};
        padding: 5px; font-family: '{FONT_FAMILY}'; font-size: 14px; }}
QMenu::item {{ padding: 7px 20px; }}
QMenu::item:selected {{ background: {SURFACE}; }}
QMenu::item:disabled {{ color: {MUTED}; }}
QMenu::indicator {{ width: 14px; height: 14px; left: 15px; }}
QMenu::indicator:checked {{ image: url("{(ASSETS / 'check.png').as_posix()}"); }}
QMenu::indicator:unchecked {{ image: none; }}
QMenu::separator {{ height: 1px; background: {SURFACE}; margin: 4px; }}
'''
