"""Application entry point: a single QApplication owned by the setter."""

import os
import sys


def main() -> int:
    # Wayland intentionally prevents client-chosen absolute window positions.
    # XWayland allows the required global-offset drag behavior on Linux/KDE.
    # Respect explicit backend overrides (including offscreen test runs).
    if sys.platform.startswith("linux") and os.environ.get("DISPLAY"):
        os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

    from PySide6.QtGui import QFontDatabase
    from PySide6.QtWidgets import QApplication

    from utils.design import ASSETS, font
    from windows.setter_window import SetterWindow

    app = QApplication(sys.argv)
    app.setApplicationName("ClockIn")
    app.setOrganizationName("ClockIn")
    app.setStyle("Fusion")
    for path in (ASSETS / "fonts").glob("*.ttf"):
        QFontDatabase.addApplicationFont(str(path))
    app.setFont(font(14))
    window = SetterWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
