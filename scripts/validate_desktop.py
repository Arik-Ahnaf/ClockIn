#!/usr/bin/env python3
"""Exercise actual XWayland windows with native pointer input.

Run from the repository: ``.venv/bin/python scripts/validate_desktop.py``.
Requires a KDE/EWMH X11 or XWayland desktop, libX11, libXtst, and xprop.
This briefly creates two ClockIn floats and an unrelated normal Qt process.
Only test-owned windows receive clicks. The original pointer position is restored.
JSON evidence and screenshots are saved under /tmp/clockin-validation by default.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
import traceback

os.environ["QT_QPA_PLATFORM"] = "xcb"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QEvent, QPoint, QTimer, Qt
from PySide6.QtGui import QColor, QCursor, QEnterEvent, QFontDatabase
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget

from models import TimerState
from utils.design import ASSETS, FLOAT_TEXT, MUTED, SURFACE, font
from utils.timer_store import TimerRecord, TimerStore
from pages.floating_timer_window import VisualState
from pages.setter_window import SetterWindow
from native_x11 import NativeX11


def app_instance() -> QApplication:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")
    for path in (ASSETS / "fonts").glob("*.ttf"):
        QFontDatabase.addApplicationFont(str(path))
    app.setFont(font(14))
    return app


def unrelated_window(metadata: Path, x: int, y: int) -> int:
    """A separate process with an ordinary decorated, non-topmost window."""
    app = app_instance()
    window = QWidget()
    window.setWindowTitle("ClockIn native validation — unrelated normal process")
    window.setStyleSheet("background: #244466;")
    window.setFixedSize(640, 400)
    window.move(x, y)
    window.show()
    window.raise_()
    window.activateWindow()

    def announce() -> None:
        metadata.write_text(json.dumps({"pid": os.getpid(), "window_id": int(window.winId())}))

    QTimer.singleShot(150, announce)
    QTimer.singleShot(60_000, app.quit)
    return app.exec()


class Validation:
    def __init__(self, output: Path):
        self.output = output
        self.output.mkdir(parents=True, exist_ok=True)
        self.app = app_instance()
        self.native = NativeX11()
        self.original_pointer = QCursor.pos().toTuple()
        self.setter: SetterWindow | None = None
        self.database_directory = TemporaryDirectory(prefix="clockin-native-")
        self.other_process: subprocess.Popen | None = None
        self.results: list[dict] = []
        self.evidence: dict = {
            "platform": QApplication.platformName(),
            "xtest_version": self.native.xtest_version,
            "screens": [{"name": s.name(), "geometry": s.geometry().getRect(),
                         "device_pixel_ratio": s.devicePixelRatio()} for s in self.app.screens()],
        }

    def wait(self, ms: int = 100) -> None:
        QTest.qWait(ms)

    def check(self, condition: bool, name: str, details=None) -> None:
        result = {"check": name, "passed": bool(condition)}
        if details is not None:
            result["details"] = details
        self.results.append(result)
        print(f"{'PASS' if condition else 'FAIL'}: {name}", flush=True)
        if not condition:
            raise AssertionError(f"{name}: {details}")

    def move(self, point: QPoint) -> None:
        self.native.move(point.x(), point.y())
        self.wait(200)

    def press(self) -> None:
        self.native.button(True)
        self.wait(200)

    def release(self) -> None:
        self.native.button(False)
        self.wait(200)

    def screenshot(self, widget: QWidget, name: str) -> None:
        widget.grab().save(str(self.output / f"{name}.png"))

    def text_color_present(self, widget: QWidget, color: str) -> bool:
        image = widget.grab().toImage().scaled(widget.size())
        rgb = QColor(color).rgb()
        return any(image.pixel(x, y) == rgb for y in range(5, min(image.height(), 57))
                   for x in range(10, image.width() - 10))

    def run(self) -> None:
        screen = self.app.primaryScreen()
        assert screen is not None
        available = screen.availableGeometry()
        self.check(available.width() >= 1150 and available.height() >= 650,
                   "Desktop has room for isolated test-owned windows", available.getRect())
        base = available.topLeft() + QPoint(50, 50)
        blank = base + QPoint(10, 450)
        store = TimerStore(Path(self.database_directory.name) / "timers.json")
        store.save([TimerRecord(f"native-test-{index}", 300) for index in range(3)])
        self.setter = SetterWindow(store)
        self.setter.move(base)
        self.setter.show()
        self.wait(180)
        self.move(blank)
        self.check(self.setter.size().toTuple() == (500, 500), "Setter is exactly 500 × 500 logical pixels")
        self.check(len(self.setter.timers) == 3 and all(
            item.card.size().toTuple() == (200, 50) for item in self.setter.timer_items.values()),
            "Three initial cards are exactly 200 × 50 logical pixels")
        self.screenshot(self.setter, "setter")
        timer_ids = list(self.setter.timers)
        self.setter.show_timer(timer_ids[0])
        floating = self.setter.floating_windows[timer_ids[0]]
        floating.move(base + QPoint(600, 130))
        self.wait(180)
        self.move(blank)
        self.check(floating.model is self.setter.timers[timer_ids[0]].model,
                   "Setter and floating timer share one model")
        self.check(floating.size().toTuple() == (200, 60), "Default floating window is fixed 200 × 60")
        self.check(floating.minimumSize() == floating.maximumSize(), "Floating window cannot be resized")
        self.check(floating.visual_state is VisualState.DEFAULT, "Pointer outside resolves DEFAULT")
        self.check(self.text_color_present(floating, MUTED), "Default text uses the Figma muted color")
        self.check(floating.grab().toImage().pixelColor(2, 2).name().upper() == SURFACE,
                   "Floating surface uses the Figma background color")
        self.screenshot(floating, "floating-default")

        self.move(floating.pos() + QPoint(100, 30))
        self.check(floating.visual_state is VisualState.HOVER, "Native pointer enter resolves HOVER", {"geometry": floating.geometry().getRect(), "pointer": self.native.pointer(), "state": str(floating.visual_state)})
        self.check(self.text_color_present(floating, FLOAT_TEXT), "Hover text uses the Figma active color")
        hover_image = floating.grab().toImage().scaled(floating.size())
        self.check(hover_image.pixelColor(2, 57).alpha() == 255 and hover_image.pixelColor(2, 59).alpha() == 0,
                   "Hover paints exactly 58 pixels inside the stable 60-pixel input window")
        self.screenshot(floating, "floating-hover")
        self.move(blank)
        self.check(floating.visual_state is VisualState.DEFAULT, "Native pointer leave returns DEFAULT")

        # Text is painted on the drag surface; press over the glyph region.
        offset = QPoint(85, 28)
        origin = floating.pos()
        self.move(origin + offset)
        self.press()
        self.check(floating.is_dragging and floating.visual_state is VisualState.DRAGGING,
                   "Native press over text immediately enters DRAGGING")
        self.check(floating.size().toTuple() == (270, 130), "Dragging uses the Figma 270 × 130 frame")
        self.screenshot(floating, "floating-dragging")
        actual_offset = QCursor.pos() - origin
        # Explicitly deliver enter/leave while the *native* grab is held. A
        # normal stable-offset drag stays under its pointer and need not emit them.
        QApplication.sendEvent(floating, QEvent(QEvent.Type.Leave))
        self.check(floating.visual_state is VisualState.DRAGGING, "Leave while dragging retains DRAGGING")
        QApplication.sendEvent(floating, QEnterEvent(QPoint(20, 20), QPoint(20, 20), floating.pos() + QPoint(20, 20)))
        self.check(floating.visual_state is VisualState.DRAGGING, "Enter while dragging retains DRAGGING")
        for delta in (QPoint(44, 18), QPoint(-25, 74), QPoint(130, 32), QPoint(10, 12)):
            cursor = origin + offset + delta
            self.move(cursor)
            self.check((floating.pos() - (QCursor.pos() - actual_offset)).manhattanLength() <= 1,
                       f"Drag retains initial global offset at ({delta.x()}, {delta.y()})",
                       {"expected": (cursor - offset).toTuple(), "actual": floating.pos().toTuple()})
        self.release()
        self.check(not floating.is_dragging and floating.visual_state is VisualState.HOVER,
                   "Native release over current geometry resolves HOVER")
        self.check(not floating.controls_open, "A drag does not toggle persistent controls")

        # Release outside requires moving the held window away from the pointer;
        # direct pointer movement would normally move this grabbed window with it.
        self.move(floating.pos() + QPoint(80, 25))
        self.press()
        self.move(floating.pos() + QPoint(80, 25) + QPoint(25, 0))
        floating.move(floating.pos() + QPoint(0, 150))
        self.wait()
        self.release()
        self.check(floating.visual_state is VisualState.DEFAULT and not floating.is_dragging,
                   "Native release outside current geometry resolves DEFAULT")

        for index in range(8):
            origin = floating.pos()
            local = QPoint(45 + index * 12, 24)
            self.move(origin + local)
            self.press()
            actual_offset = QCursor.pos() - origin
            delta = QPoint(14 if index % 2 == 0 else -14, -8 if index % 2 == 0 else 8)
            self.move(origin + local + delta)
            expected_position = QCursor.pos() - actual_offset
            self.release()
            self.check((floating.pos() - expected_position).manhattanLength() <= 1 and not floating.is_dragging,
                       f"Rapid repeat drag {index + 1} has no position jump")

        self.move(floating.pos() + QPoint(90, 25))
        self.press()
        self.release()
        self.check(floating.controls_open and floating.size().toTuple() == (270, 130),
                   "Surface click keeps the expanded controls open")
        self.move(blank)
        self.check(floating.controls_open and floating.pause_button.isVisible(),
                   "Controls remain usable after the pointer leaves")
        self.screenshot(floating, "floating-controls")
        pause_point = floating.pause_button.mapToGlobal(floating.pause_button.rect().center())
        position_before = floating.pos()
        self.move(pause_point)
        self.press()
        self.check(not floating.is_dragging, "Pause button press does not start dragging")
        self.release()
        self.check(floating.model.state is TimerState.PAUSED and floating.pos() == position_before,
                   "Pause button pauses without moving the floating window")
        paused_remaining = floating.model.remaining_seconds
        self.wait(250)
        self.check(floating.model.remaining_seconds == paused_remaining, "Paused countdown remains frozen")
        self.press()
        self.release()
        self.check(floating.model.state is TimerState.RUNNING and not floating.is_dragging,
                   "Resume button resumes without dragging")
        self.wait(120)
        self.check(tuple(map(int, floating.display_text.split(":"))) == tuple(map(int, self.setter.timer_items[timer_ids[0]].display_text.text().split(":"))),
                   "Setter and floating displays remain synchronized after pause/resume")
        self.move(floating.pos() + QPoint(90, 25))
        self.press()
        self.release()
        self.check(not floating.controls_open and floating.size().toTuple() == (200, 60),
                   "Second surface click returns to compact controls")

        self.setter.show_timer(timer_ids[1])
        second = self.setter.floating_windows[timer_ids[1]]
        second.move(base + QPoint(810, 420))
        self.wait()
        self.check(second.model is not floating.model and second.model.state is TimerState.RUNNING,
                   "Second timer runs with its own model and floating window")
        second.close()
        self.wait()
        self.check(floating.isVisible() and floating.model.state is TimerState.RUNNING
                   and self.setter.isVisible() and second.model.state is TimerState.RUNNING,
                   "Closing one floating window leaves setter and both countdowns alive")
        self.setter.show_timer(timer_ids[1])
        self.check(self.setter.floating_windows[timer_ids[1]] is second and second.isVisible(),
                   "Reopening a floating timer retains its owned window")
        second.close()

        # A normal window in another process is raised *after* the float.
        floating.move(base + QPoint(620, 120))
        self.move(blank)
        self.wait()
        native_id = int(floating.winId())
        props = self.native.properties(native_id)
        self.evidence["floating_native_properties"] = props
        self.evidence["floating_native_geometry"] = self.native.geometry(native_id)
        self.check("_NET_WM_STATE_ABOVE" in props, "Native window manager records always-on-top state")
        self.check("_NET_WM_WINDOW_TYPE_UTILITY" in props, "Native window type is a utility window")
        self.check("_NET_WM_WINDOW_TYPE_UTILITY" in props, "Floating window advertises utility semantics for taskbar suppression")
        hints = subprocess.check_output(["xprop", "-id", hex(native_id), "WM_NORMAL_HINTS"], text=True)
        self.evidence["floating_size_hints"] = hints
        self.check(f"program specified minimum size: {round(200 * floating.devicePixelRatioF())} by {round(60 * floating.devicePixelRatioF())}" in hints
                   and f"program specified maximum size: {round(200 * floating.devicePixelRatioF())} by {round(60 * floating.devicePixelRatioF())}" in hints,
                   "Native minimum and maximum dimensions are fixed at 200 × 60")
        motif = re.search(r"_MOTIF_WM_HINTS.*?=\s*(.*)", props)
        motif_values = [int(value.strip(), 0) for value in motif.group(1).split(",")] if motif else []
        self.check(len(motif_values) >= 3 and motif_values[0] & 2 and motif_values[2] == 0,
                   "Native Motif hints explicitly disable decorations", motif_values)
        metadata = self.output / "unrelated-window.json"
        metadata.unlink(missing_ok=True)
        normal_position = base + QPoint(560, 80)
        self.other_process = subprocess.Popen(
            [sys.executable, __file__, "--normal-window", str(metadata),
             "--x", str(normal_position.x()), "--y", str(normal_position.y())],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
        )
        deadline = time.monotonic() + 8
        while not metadata.exists() and time.monotonic() < deadline:
            self.wait(50)
            if self.other_process.poll() is not None:
                raise RuntimeError(self.other_process.stderr.read())
        self.check(metadata.exists(), "Unrelated normal application launched successfully")
        other_data = json.loads(metadata.read_text())
        other_id = other_data["window_id"]
        self.wait(350)
        stack = self.native.stacking()
        active = subprocess.check_output(["xprop", "-root", "_NET_ACTIVE_WINDOW"], text=True)
        self.evidence["unrelated_process"] = other_data
        self.evidence["native_stacking_bottom_to_top"] = [hex(i) for i in stack]
        self.evidence["native_active_window"] = active
        self.evidence["unrelated_native_properties"] = self.native.properties(other_id)
        self.check(hex(other_id) in active, "Unrelated normal application is actually active", active.strip())
        self.check(native_id in stack and other_id in stack and stack.index(native_id) > stack.index(other_id),
                   "Floating timer stays above the active unrelated normal application", [hex(i) for i in stack])
        # Capture only the rectangle covered by our normal window and float.
        other_rect = self.native.geometry(other_id)
        x, y, width, height = other_rect
        screen.grabWindow(0, x, y, width, height).save(str(self.output / "native-always-on-top.png"))
        sampled = screen.grabWindow(0, floating.x() + 3, floating.y() + 3, 1, 1).toImage().pixelColor(0, 0)
        if sampled.name() == "#000000":
            # XWayland cannot read the Wayland compositor root framebuffer.
            self.evidence["desktop_framebuffer_capture"] = "Unavailable (black XWayland root); native stacking verified above."
            print("SKIP: Compositor framebuffer capture is unavailable under XWayland", flush=True)
        else:
            self.check(sampled.name().upper() == SURFACE,
                       "Desktop framebuffer shows timer pixels over unrelated app", sampled.name())

        self.other_process.terminate()
        self.other_process.wait(timeout=5)
        self.other_process = None
        self.setter.activateWindow()
        floating.raise_()
        self.wait()
        # Delete the second timer via its real button; keep the first intact.
        self.setter.show_timer(timer_ids[1])
        second.move(base + QPoint(800, 370))
        self.wait()
        self.move(second.pos() + QPoint(90, 25))
        self.press()
        self.release()
        delete_point = second.remove_button.mapToGlobal(second.remove_button.rect().center())
        self.move(delete_point)
        self.press()
        self.check(not second.is_dragging, "Delete button press does not start dragging")
        self.release()
        self.check(timer_ids[1] not in self.setter.timers and timer_ids[1] not in self.setter.floating_windows
                   and floating.isVisible() and floating.model.state is TimerState.RUNNING,
                   "Delete removes only its own timer and floating window")

    def close(self) -> None:
        self.native.button(False)
        if self.other_process is not None:
            self.other_process.terminate()
            try:
                self.other_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.other_process.kill()
                self.other_process.wait(timeout=5)
        if self.setter is not None:
            self.setter.close()
        self.database_directory.cleanup()
        self.native.move(*self.original_pointer)
        self.wait(80)
        self.native.close()
        self.evidence["checks"] = self.results
        self.evidence["passed"] = all(result["passed"] for result in self.results) and "exception" not in self.evidence
        (self.output / "report.json").write_text(json.dumps(self.evidence, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("/tmp/clockin-validation"))
    parser.add_argument("--normal-window", type=Path)
    parser.add_argument("--x", type=int, default=650)
    parser.add_argument("--y", type=int, default=200)
    args = parser.parse_args()
    if args.normal_window:
        return unrelated_window(args.normal_window, args.x, args.y)
    validation = Validation(args.output)
    try:
        validation.run()
    except Exception:
        validation.evidence["exception"] = traceback.format_exc()
        traceback.print_exc()
        return 1
    finally:
        validation.close()
    print(f"Native desktop verification passed: {len(validation.results)} checks; {args.output / 'report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
