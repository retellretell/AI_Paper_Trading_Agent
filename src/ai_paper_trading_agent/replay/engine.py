from __future__ import annotations

import random

from ai_paper_trading_agent.core.timebase import DecisionClock
from ai_paper_trading_agent.replay.harness import ReplayEvent


class DeterministicEngineSkeleton:
    """Engine skeleton that consumes exchange-event-time events only."""

    def __init__(self) -> None:
        self._clock = DecisionClock()

    def on_event(self, event: ReplayEvent, rng: random.Random) -> dict:
        self._clock.update(event.exchange_event_time)

        return {
            "exchange_event_time": self._clock.current_event_time_ms,
            "message_type": event.message_type,
            "event_type": event.payload.get("type", "unknown"),
            "sample": rng.randint(0, 1_000_000),
        }
