from __future__ import annotations

import random

from ai_paper_trading_agent.order_book.sync import BookSyncChecker, DiffRange


def test_book_sync_fuzz_like_ranges_never_regress_last_update_id() -> None:
    rng = random.Random(123)
    checker = BookSyncChecker(snapshot_last_update_id=100, reorder_window_ms=200, max_buffer_events=500)
    previous = checker.last_update_id

    for i in range(200):
        start = rng.randint(90, 130)
        end = rng.randint(start, start + 3)
        event_time = 1000 + i
        try:
            checker.apply(DiffRange(U=start, u=end, exchange_event_time=event_time))
        except Exception:
            pass
        assert checker.last_update_id >= previous
        previous = checker.last_update_id
