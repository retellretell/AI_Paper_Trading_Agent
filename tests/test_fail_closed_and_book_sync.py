from __future__ import annotations

from ai_paper_trading_agent.core.fail_closed import FailClosedStateMachine, SafetyState
from ai_paper_trading_agent.order_book.sync import BookSyncChecker, DiffRange


def test_staleness_transitions_and_terminal_hard_stop() -> None:
    sm = FailClosedStateMachine(max_safe_mode_exit_staleness_seconds=2.0)
    assert sm.evaluate_staleness(0.5).state is SafetyState.NORMAL
    assert sm.evaluate_staleness(3.0).state is SafetyState.SAFE_MODE
    assert sm.can_attempt_safe_mode_exit(1.5) is True
    assert sm.can_attempt_safe_mode_exit(2.5) is False
    assert sm.state is SafetyState.HARD_STOP
    assert sm.evaluate_staleness(0.1).state is SafetyState.HARD_STOP


def test_book_sync_checker_handles_bridge_duplicate_and_continuity() -> None:
    checker = BookSyncChecker(snapshot_last_update_id=10)

    assert checker.apply(DiffRange(U=10, u=10)) is False  # duplicate/old
    assert checker.apply(DiffRange(U=11, u=12)) is True  # initial bridge
    assert checker.apply(DiffRange(U=13, u=14)) is True  # continuity
    assert checker.apply(DiffRange(U=16, u=17)) is False  # gap
