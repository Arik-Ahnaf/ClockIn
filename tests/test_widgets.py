"""Model/view integration and input regressions; native checks are in scripts/."""

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import unittest
from unittest.mock import patch

from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QCursor, QFontDatabase, QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog

from controllers import TimerController
from models import TimerModel, TimerState
from utils.design import ASSETS
from windows.floating_timer_window import FloatingTimerWindow, VisualState
from windows.setter_window import SetterWindow
from windows.timer_dialog import TimerDialog

# Created while discovery imports modules, before any QCoreApplication-only tests.
APP = QApplication.instance() or QApplication([])
APP.setStyle("Fusion")
APP.setQuitOnLastWindowClosed(False)
for path in (ASSETS / "fonts").glob("*.ttf"):
    QFontDatabase.addApplicationFont(str(path))


def mouse(window, kind: QEvent.Type, position: QPoint, *, held: bool = False) -> None:
    button = Qt.MouseButton.NoButton if kind is QEvent.Type.MouseMove else Qt.MouseButton.LeftButton
    buttons = Qt.MouseButton.LeftButton if held else Qt.MouseButton.NoButton
    event = QMouseEvent(kind, QPointF(window.mapFromGlobal(position)), QPointF(position),
                        button, buttons, Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(window, event)


class FloatingInteractionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = TimerModel(18605)
        self.controller = TimerController(self.model)
        self.window = FloatingTimerWindow(self.controller)
        self.window.move(300, 200)

    def tearDown(self) -> None:
        self.controller.reset()
        self.window.close()
        self.window.deleteLater()
        APP.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_drag_priority_and_initial_global_offset(self) -> None:
        window = self.window
        pointer = window.pos() + QPoint(80, 30)
        mouse(window, QEvent.Type.MouseButtonPress, pointer, held=True)
        self.assertEqual(window.visual_state, VisualState.DRAGGING)
        self.assertEqual((window.width(), window.height()), (270, 130))
        QApplication.sendEvent(window, QEvent(QEvent.Type.Leave))
        self.assertEqual(window.visual_state, VisualState.DRAGGING)
        for delta in (QPoint(40, 20), QPoint(-90, 80), QPoint(120, -70)):
            target = pointer + delta
            mouse(window, QEvent.Type.MouseMove, target, held=True)
            self.assertEqual(window.pos(), target - QPoint(80, 30))
        with patch.object(QCursor, "pos", return_value=target):
            mouse(window, QEvent.Type.MouseButtonRelease, target)
        self.assertEqual(window.visual_state, VisualState.HOVER)
        self.assertFalse(window.controls_open)

    def test_release_outside_current_geometry_resolves_default(self) -> None:
        window = self.window
        pointer = window.pos() + QPoint(40, 20)
        mouse(window, QEvent.Type.MouseButtonPress, pointer, held=True)
        mouse(window, QEvent.Type.MouseMove, pointer + QPoint(30, 0), held=True)
        outside = window.pos() + QPoint(400, 250)
        with patch.object(QCursor, "pos", return_value=outside):
            mouse(window, QEvent.Type.MouseButtonRelease, outside)
        self.assertEqual(window.visual_state, VisualState.DEFAULT)
        self.assertFalse(window.is_dragging)

    def test_click_toggles_controls_and_buttons_do_not_drag(self) -> None:
        window = self.window
        window.show()
        APP.processEvents()
        pointer = window.pos() + QPoint(30, 20)
        for expected in (True, False, True):
            mouse(window, QEvent.Type.MouseButtonPress, pointer, held=True)
            with patch.object(QCursor, "pos", return_value=pointer):
                mouse(window, QEvent.Type.MouseButtonRelease, pointer)
            self.assertEqual(window.controls_open, expected)
        self.controller.start()
        old_position = window.pos()
        QTest.mouseClick(window.pause_button, Qt.MouseButton.LeftButton)
        self.assertEqual(self.model.state, TimerState.PAUSED)
        self.assertFalse(window.is_dragging)
        self.assertEqual(window.pos(), old_position)
        QTest.mouseClick(window.pause_button, Qt.MouseButton.LeftButton)
        self.assertEqual(self.model.state, TimerState.RUNNING)
        removed = []
        window.remove_requested.connect(lambda: removed.append(True))
        QTest.mouseClick(window.remove_button, Qt.MouseButton.LeftButton)
        self.assertEqual(removed, [True])
        self.assertFalse(window.is_dragging)

    def test_lost_left_button_and_hide_end_drag(self) -> None:
        pointer = self.window.pos() + QPoint(10, 10)
        mouse(self.window, QEvent.Type.MouseButtonPress, pointer, held=True)
        mouse(self.window, QEvent.Type.MouseMove, pointer, held=False)
        self.assertFalse(self.window.is_dragging)
        self.window.show()
        mouse(self.window, QEvent.Type.MouseButtonPress, pointer, held=True)
        self.window.hide()
        self.assertFalse(self.window.is_dragging)

    def test_native_flags_and_fixed_size_constraints(self) -> None:
        flags = self.window.windowFlags()
        self.assertTrue(flags & Qt.WindowType.FramelessWindowHint)
        self.assertTrue(flags & Qt.WindowType.WindowStaysOnTopHint)
        self.assertEqual(flags & Qt.WindowType.WindowType_Mask, Qt.WindowType.Tool)
        self.assertFalse(self.window.testAttribute(Qt.WidgetAttribute.WA_QuitOnClose))
        self.window.resize(500, 500)
        self.assertEqual((self.window.width(), self.window.height()), (200, 60))

    def test_hover_surface_matches_export_without_resizing_hit_area(self) -> None:
        self.window._is_hovered = True
        self.window._update_visual_state()
        image = self.window.grab().toImage()
        self.assertEqual(image.pixelColor(0, 0).name(), "#1a1a1a")
        self.assertEqual(image.pixelColor(0, 57).alpha(), 255)
        self.assertEqual(image.pixelColor(0, 59).alpha(), 0)


class SetterIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.window = SetterWindow()
        self.window.show()
        APP.processEvents()

    def tearDown(self) -> None:
        self.window.close()
        self.window.deleteLater()
        APP.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_design_dimensions_and_card_positions(self) -> None:
        self.assertEqual((self.window.width(), self.window.height()), (500, 500))
        for item, expected in zip(self.window.timer_items.values(),
                                  (QPoint(37, 40), QPoint(247, 40), QPoint(37, 100)), strict=True):
            self.assertEqual(item.card.mapTo(self.window, QPoint()), expected)
            self.assertEqual((item.card.width(), item.card.height()), (200, 50))
            self.assertEqual(item.display_text.text(), "00:05:00")

    def test_start_shares_model_and_reopening_reuses_window(self) -> None:
        timer_id = next(iter(self.window.timers))
        item = self.window.timer_items[timer_id]
        QTest.mouseClick(item.play_button, Qt.MouseButton.LeftButton)
        floating = self.window.floating_windows[timer_id]
        model = self.window.timers[timer_id].model
        self.assertIs(floating.model, item.model)
        self.assertEqual(model.state, TimerState.RUNNING)
        model.pause()
        model.configure(3670)
        self.assertEqual(item.display_text.text(), "01:01:10")
        self.assertEqual(floating.display_text, "1:01:10")
        floating.close()
        self.assertTrue(self.window.isVisible())
        self.window.show_timer(timer_id)
        self.assertIs(self.window.floating_windows[timer_id], floating)

    def test_removal_and_floating_close_do_not_affect_other_timers(self) -> None:
        first, second, _ = self.window.timers
        self.window.show_timer(first)
        self.window.show_timer(second)
        self.window.floating_windows[first].close()
        self.assertTrue(self.window.floating_windows[second].isVisible())
        self.assertEqual(self.window.timers[first].model.state, TimerState.RUNNING)
        self.window.remove_timer(first)
        APP.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.assertNotIn(first, self.window.timers)
        self.assertNotIn(first, self.window.floating_windows)
        self.assertEqual(self.window.timers[second].model.state, TimerState.RUNNING)
        self.assertTrue(self.window.floating_windows[second].isVisible())

    def test_more_timers_scroll_without_changing_card_size(self) -> None:
        for _ in range(16):
            self.window.add_timer(10)
        APP.processEvents()
        self.assertGreater(self.window.scroll_area.verticalScrollBar().maximum(), 0)
        self.assertTrue(all(item.card.width() == 200 for item in self.window.timer_items.values()))

    def test_edit_mode_controls_removal_independently_of_hover(self) -> None:
        first_id = next(iter(self.window.timer_items))
        item = self.window.timer_items[first_id]
        self.assertFalse(item.remove_button.isVisible())
        QTest.mouseMove(item.card, QPoint(50, 20))
        self.assertFalse(item.remove_button.isVisible())
        QTest.mouseClick(self.window.edit_button, Qt.MouseButton.LeftButton)
        self.assertTrue(self.window.edit_mode)
        self.assertTrue(all(item.remove_button.isVisible() for item in self.window.timer_items.values()))
        QTest.mouseMove(self.window, QPoint(480, 420))
        self.assertTrue(item.remove_button.isVisible())
        added = self.window.add_timer(120)
        self.assertTrue(self.window.timer_items[added.model.timer_id].remove_button.isVisible())
        QTest.mouseClick(item.remove_button, Qt.MouseButton.LeftButton)
        self.assertNotIn(first_id, self.window.timers)
        QTest.mouseClick(self.window.edit_button, Qt.MouseButton.LeftButton)
        self.assertFalse(self.window.edit_mode)
        self.assertTrue(all(not item.remove_button.isVisible() for item in self.window.timer_items.values()))

    def test_parameter_windows_save_cancel_reuse_and_close_with_owner(self) -> None:
        initial_count = len(self.window.timers)
        QTest.mouseClick(self.window.add_button, Qt.MouseButton.LeftButton)
        dialog = self.window.parameter_windows[None]
        self.assertIsNone(dialog.parentWidget())
        self.assertTrue(dialog.isWindow())
        self.assertFalse(dialog.isModal())
        self.assertFalse(dialog.windowFlags() & Qt.WindowType.FramelessWindowHint)
        self.window._new_timer()
        self.assertIs(self.window.parameter_windows[None], dialog)
        for field, value in zip(dialog.fields, (0, 2, 15), strict=True):
            field.setValue(value)
        QTest.mouseClick(dialog.set_button, Qt.MouseButton.LeftButton)
        self.assertNotIn(None, self.window.parameter_windows)
        self.assertEqual(len(self.window.timers), initial_count + 1)
        added_id = next(reversed(self.window.timers))
        self.assertEqual(self.window.timers[added_id].model.duration_seconds, 135)
        self.window.configure_timer(added_id)
        edit = self.window.parameter_windows[added_id]
        edit.fields[1].setValue(3)
        edit.reject()
        self.assertEqual(self.window.timers[added_id].model.duration_seconds, 135)
        self.window.configure_timer(added_id)
        self.window.remove_timer(added_id)
        self.assertNotIn(added_id, self.window.parameter_windows)
        self.window._new_timer()
        self.window.close()
        self.assertFalse(self.window.parameter_windows)

    def test_dialog_rejects_zero_and_returns_exact_duration(self) -> None:
        dialog = TimerDialog(0, self.window)
        self.assertFalse(dialog.set_button.isEnabled())
        dialog.accept()
        self.assertEqual(dialog.result(), QDialog.DialogCode.Rejected)
        for field, value in zip(dialog.fields, (2, 3, 4), strict=True):
            field.setValue(value)
        self.assertTrue(dialog.set_button.isEnabled())
        self.assertEqual(dialog.duration_seconds, 7384)
        dialog.accept()
        self.assertEqual(dialog.result(), QDialog.DialogCode.Accepted)


if __name__ == "__main__":
    unittest.main()
