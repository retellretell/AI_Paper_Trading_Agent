from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class ReplayEvent:
    exchange_event_time: int
    payload: dict


class ReplayEngine(Protocol):
    def on_event(self, event: ReplayEvent, rng: random.Random) -> dict | None: ...


def _load_recorded_stream(stream_path: Path) -> list[ReplayEvent]:
    events: list[ReplayEvent] = []
    with stream_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            events.append(
                ReplayEvent(
                    exchange_event_time=row["exchange_event_time"],
                    payload=row["payload"],
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
