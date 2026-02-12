from __future__ import annotations

import pytest

from ai_paper_trading_agent.core.fail_closed import FailClosedStateMachine, SafetyState
from ai_paper_trading_agent.order_book.sync import BookIntegrityError, BookSyncChecker, DiffRange


def test_staleness_transitions_and_terminal_hard_stop() -> None:
    sm = FailClosedStateMachine(max_safe_mode_exit_staleness_seconds=2.0)
    assert sm.evaluate_staleness(0.5).state is SafetyState.NORMAL
    assert sm.evaluate_staleness(3.0).state is SafetyState.SAFE_MODE
    assert sm.can_attempt_safe_mode_exit(1.5) is True
    assert sm.can_attempt_safe_mode_exit(2.5) is False
    assert sm.state is SafetyState.HARD_STOP
    assert sm.evaluate_staleness(0.1).state is SafetyState.HARD_STOP


def test_book_sync_checker_snapshot_diff_continuity_with_reorder_buffer() -> None:
    checker = BookSyncChecker(snapshot_last_update_id=10, reorder_window_ms=100, max_buffer_events=3)

    assert checker.apply(DiffRange(U=13, u=14, exchange_event_time=1010)) is False
    assert checker.apply(DiffRange(U=11, u=12, exchange_event_time=1020)) is True
    assert checker.last_update_id == 14


def test_book_sync_checker_raises_when_reorder_window_exceeded() -> None:
    checker = BookSyncChecker(snapshot_last_update_id=10, reorder_window_ms=50, max_buffer_events=3)

    checker.apply(DiffRange(U=15, u=16, exchange_event_time=1000))
    with pytest.raises(BookIntegrityError):
        checker.apply(DiffRange(U=18, u=19, exchange_event_time=1060))
