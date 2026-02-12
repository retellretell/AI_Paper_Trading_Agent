from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class ReplayEvent:
    message_type: str
    exchange_event_time: int
    local_arrival_time_ns: int
    payload: dict[str, Any]


class ReplayEngine(Protocol):
    def on_event(self, event: ReplayEvent, rng: random.Random) -> dict | None: ...


def _load_recorded_stream(stream_path: Path) -> list[ReplayEvent]:
    events: list[ReplayEvent] = []
    with stream_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            payload = row.get("raw_payload", row.get("payload", {}))
            events.append(
                ReplayEvent(
                    message_type=row.get("message_type", payload.get("type", "unknown")),
                    exchange_event_time=row["exchange_event_time"],
                    local_arrival_time_ns=row.get("local_arrival_time_ns", 0),
                    payload=payload,
                )
            )
    return events


def run_replay(*, stream_path: Path | str, seed: int, engine: ReplayEngine) -> list[dict]:
    """Deterministic replay skeleton: recorded stream -> engine outputs."""
    rng = random.Random(seed)
    events = _load_recorded_stream(Path(stream_path))

    outputs: list[dict] = []
    for event in sorted(events, key=lambda x: x.exchange_event_time):
        maybe = engine.on_event(event, rng)
        if maybe is not None:
            outputs.append(maybe)
    return outputs
