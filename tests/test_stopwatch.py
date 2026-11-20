"""Stopwatch timing and page integration regressions."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtCore import QEvent, QPoint, Qt
from PySide6.QtWidgets import QApplication
from pages.floating_timer_window import VisualState
from PySide6.QtTest import QTest

from models import StopwatchModel, TimerState
from pages.setter_window import SetterWindow
from utils.timer_store import TimerStore
from tests.test_widgets import APP, mouse
from tests.test_timer_model import FakeClock


class StopwatchTests(unittest.TestCase):
    def test_pause_resume_and_delayed_refresh(self):
        clock = FakeClock()
        model = StopwatchModel(clock=clock)
        model.start()
        clock.advance(61.75)
        model.start()  # Repeated start must not lose elapsed time.
        model.refresh()
        self.assertEqual(model.display_seconds, 61)
        clock.advance(.125)
        model.pause()
        self.assertEqual(model.elapsed_seconds, 61.875)
        clock.advance(100)
        model.refresh()
        self.assertEqual(model.elapsed_seconds, 61.875)
        model.start()
        clock.advance(.125)
        model.pause()
        self.assertEqual(model.elapsed_seconds, 62)
        self.assertEqual(model.state, TimerState.PAUSED)

    def test_reset_and_refresh_frequency(self):
        clock = FakeClock()
        a, b = StopwatchModel(clock=clock), StopwatchModel(clock=clock)
        a.start()
        b.start()
        for _ in range(20):
            clock.advance(.25)
            a.refresh()
        b.refresh()
        self.assertEqual(a.elapsed_seconds, b.elapsed_seconds)
        a.reset()
        clock.advance(360000)
        a.refresh()
        b.refresh()
        self.assertEqual((a.state, a.elapsed_seconds), (TimerState.IDLE, 0))
        self.assertEqual(b.elapsed_seconds, 360005)
        a.start()
        clock.advance(1)
        a.refresh()
        self.assertEqual(a.elapsed_seconds, 1)

    def test_page_controls_navigation_and_close(self):
        with TemporaryDirectory() as directory:
            window = SetterWindow(TimerStore(Path(directory) / 'timers.json'))
            window.show()
            try:
                controller = window.stopwatch_controller
                model = controller.model
                clock = FakeClock()
                model._clock = clock
                QTest.mouseClick(window.stopwatch_tab, Qt.MouseButton.LeftButton)
                page = window.stopwatch_page
                self.assertTrue(page.isVisible())
                self.assertFalse(window.scroll_area.isVisible())
                self.assertEqual(page.display.text(), '00:00')
                self.assertEqual(page.play_button.size().width(), 86)
                QTest.mouseClick(page.play_button, Qt.MouseButton.LeftButton)
                QTest.mouseClick(window.timer_tab, Qt.MouseButton.LeftButton)
                clock.advance(62.5)
                model.refresh()
                self.assertEqual(model.state, TimerState.RUNNING)
                QTest.mouseClick(window.stopwatch_tab, Qt.MouseButton.LeftButton)
                self.assertEqual(page.display.text(), '01:02')
                QTest.mouseClick(page.play_button, Qt.MouseButton.LeftButton)
                self.assertEqual(model.state, TimerState.PAUSED)
                self.assertFalse(controller._refresh_timer.isActive())
                self.assertEqual(page.play_button._asset_name, "stopwatch-play.svg")
                QTest.mouseClick(page.play_button, Qt.MouseButton.LeftButton)
                self.assertEqual(page.play_button._asset_name, "stopwatch-pause.svg")
                QTest.mouseClick(page.reset_button, Qt.MouseButton.LeftButton)
                self.assertEqual(model.state, TimerState.IDLE)
                self.assertFalse(controller._refresh_timer.isActive())
                self.assertEqual(page.play_button._asset_name, "stopwatch-play.svg")
                self.assertEqual(page.display.text(), '00:00')
                QTest.mouseClick(page.play_button, Qt.MouseButton.LeftButton)
                self.assertTrue(controller._refresh_timer.isActive())
                window.close()
                self.assertEqual(model.state, TimerState.PAUSED)
                self.assertFalse(controller._refresh_timer.isActive())
            finally:
                window.close()
                window.deleteLater()
                APP.processEvents()


class FloatingStopwatchTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.setter = SetterWindow(TimerStore(Path(self.directory.name) / "timers.json"))
        self.setter.show()
        self.controller = self.setter.stopwatch_controller
        self.controller.model._clock = self.clock = FakeClock()
        self.controller.start()
        self.window = self.setter.stopwatch_window

    def tearDown(self):
        self.setter.close()
        self.setter.deleteLater()
        APP.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.directory.cleanup()

    def test_shared_state_reuse_and_independent_lifetime(self):
        window = self.window
        self.assertTrue(window.isVisible())
        self.assertIs(window.model, self.controller.model)
        self.clock.advance(62.5)
        self.controller.model.refresh()
        self.assertEqual(window.display_text, "0:01:02")
        self.assertEqual(self.setter.stopwatch_page.display.text(), "01:02")
        window._controls_open = True
        window._update_visual_state()
        QTest.mouseClick(window.play_button, Qt.MouseButton.LeftButton)
        self.assertEqual(self.controller.model.state, TimerState.PAUSED)
        self.assertFalse(window.is_dragging)
        window.close()
        self.controller.start()
        self.assertIs(self.setter.stopwatch_window, window)
        self.assertTrue(window.isVisible())
        window.close()
        self.clock.advance(1)
        self.controller.model.refresh()
        self.assertFalse(window.isVisible())  # Refreshes must not reopen it.
        timer = self.setter.add_timer(30)
        self.setter.show_timer(timer.model.timer_id)
        other = self.setter.floating_windows[timer.model.timer_id]
        self.setter._dismiss_stopwatch()
        self.assertEqual(self.controller.model.state, TimerState.IDLE)
        self.assertTrue(other.isVisible())
        self.assertEqual(timer.model.state, TimerState.RUNNING)
        self.controller.start()
        self.assertIs(self.setter.stopwatch_window, window)
        self.assertTrue(window.isVisible())
        self.setter.close()
        self.assertFalse(window.isVisible())

    def test_figma_states_drag_offset_and_controls(self):
        window = self.window
        window.move(300, 200)
        window._is_hovered = False
        window._update_visual_state()
        self.assertEqual((window.width(), window.height()), (200, 60))
        self.assertAlmostEqual(window.windowOpacity(), .7, delta=1/255)
        self.assertEqual(window.close_button.pos(), QPoint(178, 6))
        self.assertFalse(window.close_button.isHidden())
        window._is_hovered = True
        window._update_visual_state()
        self.assertTrue(window.close_button.isHidden())
        self.assertEqual(window.windowOpacity(), 1)
        pointer = window.pos() + QPoint(80, 30)
        mouse(window, QEvent.Type.MouseButtonPress, pointer, held=True)
        self.assertEqual(window.visual_state, VisualState.DRAGGING)
        self.assertEqual((window.width(), window.height()), (220, 100))
        self.assertEqual(window.play_button.pos(), QPoint(69, 52))
        self.assertEqual(window.reset_button.pos(), QPoint(115, 52))
        self.assertEqual(window.close_button.pos(), QPoint(196, 8))
        QApplication.sendEvent(window, QEvent(QEvent.Type.Leave))
        self.assertEqual(window.visual_state, VisualState.DRAGGING)
        destination = pointer + QPoint(130, 90)
        mouse(window, QEvent.Type.MouseMove, destination, held=True)
        self.assertEqual(window.pos(), destination - QPoint(80, 30))
        window._finish_drag(destination)
        self.assertEqual(window.visual_state, VisualState.HOVER)
        mouse(window, QEvent.Type.MouseButtonPress, destination, held=True)
        window._finish_drag(QPoint(-1000, -1000))
        self.assertEqual(window.visual_state, VisualState.DEFAULT)
        window._controls_open = True
        window._update_visual_state()
        QTest.mouseClick(window.reset_button, Qt.MouseButton.LeftButton)
        self.assertEqual(self.controller.model.state, TimerState.IDLE)
        self.assertEqual(window.display_text, "0:00:00")
        self.assertFalse(window.is_dragging)
