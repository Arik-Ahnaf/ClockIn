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
    from PySide6.QtWidgets import QApplication, QMessageBox

    from utils.design import ASSETS, font
    from utils.timer_store import TimerStoreError
    from pages.setter_window import SetterWindow

    app = QApplication(sys.argv)
    app.setApplicationName("ClockIn")
    app.setOrganizationName("ClockIn")
    app.setStyle("Fusion")
    for path in (ASSETS / "fonts").glob("*.ttf"):
        QFontDatabase.addApplicationFont(str(path))
    app.setFont(font(14))
    try:
        window = SetterWindow()
    except TimerStoreError as exc:
        QMessageBox.critical(None, "Unable to load timers", str(exc))
        return 1
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
