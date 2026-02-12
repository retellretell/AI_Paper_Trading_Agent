from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SafetyState(str, Enum):
    NORMAL = "NORMAL"
    SAFE_MODE = "SAFE_MODE"
    HARD_STOP = "HARD_STOP"


@dataclass(frozen=True)
class SafetyDecision:
    state: SafetyState
    reason: str


class FailClosedStateMachine:
    """Fail-closed safety rails for NORMAL/SAFE_MODE/HARD_STOP transitions."""

    def __init__(self, max_safe_mode_exit_staleness_seconds: float = 2.0) -> None:
        self._state = SafetyState.NORMAL
        self._max_safe_mode_exit_staleness_seconds = max_safe_mode_exit_staleness_seconds

    @property
    def state(self) -> SafetyState:
        return self._state

    def evaluate_staleness(self, staleness_seconds: float) -> SafetyDecision:
        if self._state is SafetyState.HARD_STOP:
            return SafetyDecision(self._state, "terminal")

        if staleness_seconds <= 1.0:
            self._state = SafetyState.NORMAL
            return SafetyDecision(self._state, "book_fresh")
        if staleness_seconds <= 5.0:
            self._state = SafetyState.SAFE_MODE
            return SafetyDecision(self._state, "book_stale_safe_mode")

        self._state = SafetyState.HARD_STOP
        return SafetyDecision(self._state, "book_stale_hard_stop")

    def on_integrity_failure(self) -> SafetyDecision:
        self._state = SafetyState.HARD_STOP
        return SafetyDecision(self._state, "integrity_failure")

    def can_attempt_safe_mode_exit(self, last_valid_book_age_seconds: float) -> bool:
        if self._state is not SafetyState.SAFE_MODE:
            return False
        if last_valid_book_age_seconds <= self._max_safe_mode_exit_staleness_seconds:
            return True
        self._state = SafetyState.HARD_STOP
        return False
