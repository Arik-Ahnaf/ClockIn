"""Opt-in release diagnostics, usable by the source and frozen launchers."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import traceback

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFontDatabase, QImage
from PySide6.QtWidgets import QApplication

from models import TimerState
from pages.setter_window import SetterWindow
from pages.timer_dialog import TimerDialog
from utils.design import time_text
from utils.paths import application_directory, is_bundled, resource_path, stylesheet
from utils.timer_store import TimerStore


def run_smoke_test(app: QApplication, report_path: str) -> int:
    """Exercise real views and event-loop countdowns without touching user timers."""
    report: dict = {"passed": False, "bundled": is_bundled(),
                    "resource_root": str(application_directory()), "checks": []}
    window = None
    dialog = None
    result = 1
    with TemporaryDirectory(prefix="clockin-smoke-data-") as directory:
        try:
            def check(condition: bool, message: str) -> None:
                if not condition:
                    raise AssertionError(message)
                report["checks"].append(message)

            check(not app.windowIcon().pixmap(32, 32).isNull(), "application icon loads")
            for path in resource_path("assets").glob("*.png"):
                check(not QImage(str(path)).isNull(), f"image loads: {path.name}")
            for path in resource_path("assets/fonts").glob("*.ttf"):
                check(QFontDatabase.addApplicationFont(str(path)) >= 0, f"font loads: {path.name}")
            check("#2A2D34" in stylesheet("main"), "external stylesheet loads")
            check(json.loads(resource_path("defaults/timers.json").read_text())["timers"] == [],
                  "shipped defaults contain no personal timers")
            report["default_database"] = str(TimerStore().path)
            if is_bundled():
                check(not TimerStore().path.is_relative_to(application_directory()),
                      "writable database is outside installation")
            store = TimerStore(Path(directory) / "timers.json")
            window = SetterWindow(store)
            window.show()
            app.processEvents()
            check((window.width(), window.height()) == (500, 500), "setter opens at 500x500")
            check(window.styleSheet() == stylesheet("main"), "setter uses external stylesheet")
            dialog = TimerDialog(1, window)
            check(not dialog.set_button.icon().pixmap(16, 16).isNull(), "dialog icon loads")
            controller = window.add_timer(1)
            timer_id = controller.model.timer_id
            window.show_timer(timer_id)
            floating = window.floating_windows[timer_id]
            check(floating.isVisible(), "floating timer opens")
            check(controller.model.state is TimerState.RUNNING, "timer starts")
            controller.pause()
            remaining = controller.model.remaining_seconds
            time.sleep(0.08)
            controller.model.refresh()
            check(controller.model.remaining_seconds == remaining, "pause preserves remaining time")
            controller.start()
            check(controller.model.state is TimerState.RUNNING, "timer resumes")
            check(TimerStore(store.path).load()[0].timer_id == timer_id, "timer settings save and reload")

            def finish() -> None:
                nonlocal result
                try:
                    check(controller.model.state is TimerState.FINISHED, "event-loop countdown finishes")
                    check(window.timer_items[timer_id].display_text.text() == time_text(0),
                          "setter observes finished countdown")
                    check(floating.display_text == time_text(0, compact=True),
                          "floating view observes same countdown")
                    window.remove_timer(timer_id)
                    check(TimerStore(store.path).load() == [], "timer deletion persists")
                    report["passed"] = True
                    result = 0
                except Exception:
                    report["error"] = traceback.format_exc()
                finally:
                    app.quit()

            QTimer.singleShot(1300, finish)
            app.exec()
        except Exception:
            report["error"] = traceback.format_exc()
        finally:
            if dialog is not None:
                dialog.close()
            if window is not None:
                window.close()
            Path(report_path).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return result
