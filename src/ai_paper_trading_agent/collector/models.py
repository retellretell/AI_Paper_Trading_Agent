from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RawCollectorEvent:
    """Raw event record schema per plan JSONL requirement."""

    message_type: str
    exchange_event_time: int
    local_arrival_time_ns: int
    raw_payload: dict[str, Any]

    def to_json_record(self) -> dict[str, Any]:
        return {
            "message_type": self.message_type,
            "exchange_event_time": self.exchange_event_time,
            "local_arrival_time_ns": self.local_arrival_time_ns,
            "raw_payload": self.raw_payload,
        }
