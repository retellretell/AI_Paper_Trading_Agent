from __future__ import annotations

from dataclasses import dataclass


class BookIntegrityError(RuntimeError):
    """Raised when bounded reordering cannot restore continuity."""


@dataclass(frozen=True)
class DiffRange:
    U: int
    u: int
    exchange_event_time: int


class BookSyncChecker:
    """Continuity checker with bounded reorder buffer per plan M1."""

    def __init__(self, *, snapshot_last_update_id: int, reorder_window_ms: int, max_buffer_events: int) -> None:
        self.last_update_id = snapshot_last_update_id
        self.reorder_window_ms = reorder_window_ms
        self.max_buffer_events = max_buffer_events
        self._initialized = False
        self._buffer: dict[int, DiffRange] = {}

    def apply(self, diff: DiffRange) -> bool:
        # Discard duplicates / old updates.
        if diff.u <= self.last_update_id:
            return False

        # Initial bridge from snapshot.
        if not self._initialized:
            if diff.U <= self.last_update_id + 1 <= diff.u:
                self.last_update_id = diff.u
                self._initialized = True
                self._try_drain_buffer(reference_exchange_event_time=diff.exchange_event_time)
                return True
            self._buffer_event(diff)
            self._try_drain_buffer(reference_exchange_event_time=diff.exchange_event_time)
            return False

        # Steady-state: strict continuity if next in chain; otherwise buffer and bounded wait.
        if diff.U == self.last_update_id + 1:
            self.last_update_id = diff.u
            self._try_drain_buffer(reference_exchange_event_time=diff.exchange_event_time)
            return True

        self._buffer_event(diff)
        self._try_drain_buffer(reference_exchange_event_time=diff.exchange_event_time)
        return False

    def _buffer_event(self, diff: DiffRange) -> None:
        if len(self._buffer) >= self.max_buffer_events and diff.U not in self._buffer:
            raise BookIntegrityError("Reorder buffer exceeded max_buffer_events")
        self._buffer[diff.U] = diff

    def _try_drain_buffer(self, *, reference_exchange_event_time: int) -> None:
        progressed = True
        while progressed:
            progressed = False
            expected_U = self.last_update_id + 1
            candidate = self._buffer.get(expected_U)
            if candidate is not None:
                self.last_update_id = candidate.u
                del self._buffer[expected_U]
                progressed = True

        if not self._buffer:
            return

        oldest = min(item.exchange_event_time for item in self._buffer.values())
        age_ms = reference_exchange_event_time - oldest
        if age_ms > self.reorder_window_ms:
            raise BookIntegrityError("Unable to restore continuity within reorder_window_ms")
