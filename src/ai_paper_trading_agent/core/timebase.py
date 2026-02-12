from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExchangeEventTime:
    """Event time in milliseconds, sourced only from exchange events."""

    event_time_ms: int

    def age_seconds_from(self, newer_event_time_ms: int) -> float:
        if newer_event_time_ms < self.event_time_ms:
            raise ValueError("Event time must be monotonic for age calculations")
        return (newer_event_time_ms - self.event_time_ms) / 1000.0


class DecisionClock:
    """Decision clock that only advances via exchange event time."""

    def __init__(self) -> None:
        self._current_event_time_ms: int | None = None

    def update(self, exchange_event_time_ms: int) -> None:
        if self._current_event_time_ms is not None and exchange_event_time_ms < self._current_event_time_ms:
            raise ValueError("Exchange event time regressed")
        self._current_event_time_ms = exchange_event_time_ms

    @property
    def current_event_time_ms(self) -> int:
        if self._current_event_time_ms is None:
            raise RuntimeError("Decision clock is unset")
        return self._current_event_time_ms
