from __future__ import annotations

import time
from typing import Any

from .models import RawCollectorEvent
from .recorder import JsonlRawEventRecorder
from .venue import validate_l2_clob_scope


class L2OrderBookCollector:
    """Paper-only collector for public L2 snapshot/diff events."""

    def __init__(self, *, venue: str, market_type: str, recorder: JsonlRawEventRecorder) -> None:
        validate_l2_clob_scope(venue=venue, market_type=market_type)
        self._venue = venue
        self._market_type = market_type
        self._recorder = recorder

    def ingest(
        self,
        *,
        message_type: str,
        exchange_event_time: int,
        raw_payload: dict[str, Any],
        local_arrival_time_ns: int | None = None,
    ) -> RawCollectorEvent:
        event = RawCollectorEvent(
            message_type=message_type,
            exchange_event_time=exchange_event_time,
            local_arrival_time_ns=time.time_ns() if local_arrival_time_ns is None else local_arrival_time_ns,
            raw_payload=raw_payload,
        )
        self._recorder.append(event)
        return event
