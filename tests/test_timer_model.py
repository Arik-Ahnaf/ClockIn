"""Deterministic lifecycle checks; no real-time sleeps or display required."""

import unittest

from PySide6.QtCore import QCoreApplication, QTimer

from controllers import TimerController
from models import MAX_DURATION_SECONDS, TimerModel, TimerState


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class TimerModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = FakeClock()
        self.model = TimerModel(60, clock=self.clock)

    def test_delayed_refresh_catches_up_using_elapsed_time(self) -> None:
        self.model.start()
        self.clock.advance(17.75)
        self.model.refresh()
        self.assertEqual(self.model.state, TimerState.RUNNING)
        self.assertEqual(self.model.remaining_seconds, 42.25)
        self.assertEqual(self.model.display_seconds, 43)
        self.clock.advance(40)
        self.model.refresh()
        self.assertEqual(self.model.remaining_seconds, 2.25)

    def test_pause_accounts_for_time_since_last_refresh(self) -> None:
        self.model.start()
        self.clock.advance(8.125)
        self.model.pause()
        self.assertEqual(self.model.state, TimerState.PAUSED)
        self.assertEqual(self.model.remaining_seconds, 51.875)
        self.clock.advance(700)
        self.model.refresh()
        self.assertEqual(self.model.remaining_seconds, 51.875)
        self.model.start()
        self.clock.advance(1.375)
        self.model.refresh()
        self.assertEqual(self.model.remaining_seconds, 50.5)

    def test_refresh_frequency_does_not_change_result(self) -> None:
        other = TimerModel(60, clock=self.clock)
        self.model.start()
        other.start()
        for _ in range(21):
            self.clock.advance(0.25)
            self.model.refresh()
        other.refresh()
        self.assertEqual(self.model.remaining_seconds, other.remaining_seconds)
        self.assertEqual(self.model.remaining_seconds, 54.75)

    def test_finish_at_exact_deadline_and_emit_once(self) -> None:
        states_at_finish = []
        self.model.finished.connect(lambda: states_at_finish.append(self.model.state))
        self.model.start()
        self.clock.advance(59.875)
        self.model.refresh()
        self.assertEqual(self.model.display_seconds, 1)
        self.assertEqual(states_at_finish, [])
        self.clock.advance(0.125)
        self.model.refresh()
        self.assertEqual(self.model.remaining_seconds, 0)
        self.assertEqual(self.model.display_seconds, 0)
        self.assertEqual(states_at_finish, [TimerState.FINISHED])
        self.clock.advance(100)
        self.model.refresh()
        self.model.pause()
        self.assertEqual(states_at_finish, [TimerState.FINISHED])

    def test_pause_after_deadline_finishes_instead(self) -> None:
        finishes = []
        self.model.finished.connect(lambda: finishes.append(True))
        self.model.start()
        self.clock.advance(200)
        self.model.pause()
        self.assertEqual(self.model.state, TimerState.FINISHED)
        self.assertEqual(self.model.remaining_seconds, 0)
        self.assertEqual(finishes, [True])

    def test_restart_finished_timer_emits_for_each_run(self) -> None:
        finishes = []
        self.model.finished.connect(lambda: finishes.append(True))
        for _ in range(2):
            self.model.start()
            self.assertEqual(self.model.remaining_seconds, 60)
            self.clock.advance(60)
            self.model.refresh()
        self.assertEqual(finishes, [True, True])

    def test_start_running_timer_preserves_deadline(self) -> None:
        self.model.start()
        self.clock.advance(20)
        self.model.start()
        self.model.refresh()
        self.assertEqual(self.model.remaining_seconds, 40)

    def test_reset_stops_running_timer_and_restores_duration(self) -> None:
        self.model.start()
        self.clock.advance(20)
        self.model.reset()
        self.clock.advance(100)
        self.model.refresh()
        self.assertEqual(self.model.state, TimerState.IDLE)
        self.assertEqual(self.model.remaining_seconds, 60)

    def test_configuration_publishes_one_consistent_snapshot(self) -> None:
        self.model.start()
        observations = []
        self.model.changed.connect(
            lambda: observations.append(
                (self.model.state, self.model.duration_seconds, self.model.remaining_seconds)
            )
        )
        self.model.configure(125)
        self.assertEqual(observations, [(TimerState.IDLE, 125, 125.0)])

    def test_invalid_configuration_preserves_active_timer(self) -> None:
        self.model.start()
        with self.assertRaises(ValueError):
            self.model.configure(0)
        self.clock.advance(1)
        self.model.refresh()
        self.assertEqual(self.model.duration_seconds, 60)
        self.assertEqual(self.model.state, TimerState.RUNNING)
        self.assertEqual(self.model.remaining_seconds, 59)

    def test_duration_validation(self) -> None:
        for invalid in (True, False, 1.5, "60", None):
            with self.subTest(duration=invalid), self.assertRaises(TypeError):
                TimerModel(invalid)  # type: ignore[arg-type]
        for invalid in (0, -1, MAX_DURATION_SECONDS + 1):
            with self.subTest(duration=invalid), self.assertRaises(ValueError):
                TimerModel(invalid)
        self.assertEqual(TimerModel(1).duration_seconds, 1)
        self.assertEqual(TimerModel(MAX_DURATION_SECONDS).duration_seconds, 359999)

    def test_timers_run_independently(self) -> None:
        other = TimerModel(120, clock=self.clock)
        self.assertNotEqual(other.timer_id, self.model.timer_id)
        self.model.start()
        self.clock.advance(20)
        other.start()
        self.model.pause()
        self.clock.advance(60)
        other.refresh()
        self.assertEqual(self.model.remaining_seconds, 40)
        self.assertEqual(self.model.state, TimerState.PAUSED)
        self.assertEqual(other.remaining_seconds, 60)
        self.assertEqual(other.state, TimerState.RUNNING)


class TimerControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self) -> None:
        self.clock = FakeClock()
        self.model = TimerModel(10, clock=self.clock)
        self.controller = TimerController(self.model)
        self.refresh_timer = self.controller.findChild(QTimer)
        assert self.refresh_timer is not None

    def tearDown(self) -> None:
        self.controller.reset()

    def test_refresh_runs_only_while_model_is_running(self) -> None:
        self.assertFalse(self.refresh_timer.isActive())
        self.controller.start()
        self.assertTrue(self.refresh_timer.isActive())
        self.controller.toggle()
        self.assertEqual(self.model.state, TimerState.PAUSED)
        self.assertFalse(self.refresh_timer.isActive())
        self.controller.toggle()
        self.assertTrue(self.refresh_timer.isActive())
        self.clock.advance(10)
        self.model.refresh()
        self.assertEqual(self.model.state, TimerState.FINISHED)
        self.assertFalse(self.refresh_timer.isActive())

    def test_direct_model_changes_also_stop_refresh(self) -> None:
        self.controller.start()
        self.model.configure(20)
        self.assertFalse(self.refresh_timer.isActive())
        self.model.start()
        self.assertTrue(self.refresh_timer.isActive())
        self.model.reset()
        self.assertFalse(self.refresh_timer.isActive())


if __name__ == "__main__":
    unittest.main()
