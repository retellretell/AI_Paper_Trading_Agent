from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ConfigValidationError(ValueError):
    """Raised when config violates strict schema or allowed values."""


_ALLOWED_VALUES = {
    "raw_event_recording.raw_event_format": {"jsonl"},
    "order_book_reconstruction.reorder_window_ms": {50, 100, 200},
    "order_book_reconstruction.max_buffer_events": {50, 200, 500},
    "safety.max_safe_mode_exit_staleness": {2.0},
    "safety.hard_stop_terminal": {True},
    "safety.hard_stop_open_position_policy": {"terminate_and_exposure_only"},
    "replay.replay_seed_policy": {"match_original_seed"},
}


@dataclass(frozen=True)
class RawEventRecordingConfig:
    raw_event_format: str


@dataclass(frozen=True)
class OrderBookReconstructionConfig:
    reorder_window_ms: int
    max_buffer_events: int


@dataclass(frozen=True)
class SafetyConfig:
    max_safe_mode_exit_staleness: float
    hard_stop_terminal: bool
    hard_stop_open_position_policy: str


@dataclass(frozen=True)
class ReplayConfig:
    replay_seed_policy: str


@dataclass(frozen=True)
class AgentConfig:
    raw_event_recording: RawEventRecordingConfig
    order_book_reconstruction: OrderBookReconstructionConfig
    safety: SafetyConfig
    replay: ReplayConfig


def _check_unknown_keys(raw: dict[str, Any], expected: dict[str, set[str]], scope: str) -> None:
    unknown = set(raw.keys()) - set(expected.keys())
    if unknown:
        raise ConfigValidationError(f"Unknown keys in {scope}: {sorted(unknown)}")


def _require_allowed(path: str, value: Any) -> None:
    allowed = _ALLOWED_VALUES[path]
    if value not in allowed:
        raise ConfigValidationError(f"Invalid value for {path}: {value!r}; allowed={sorted(allowed)}")


def validate_config(raw: dict[str, Any]) -> AgentConfig:
    top_expected = {
        "raw_event_recording": {"raw_event_format"},
        "order_book_reconstruction": {"reorder_window_ms", "max_buffer_events"},
        "safety": {
            "max_safe_mode_exit_staleness",
            "hard_stop_terminal",
            "hard_stop_open_position_policy",
        },
        "replay": {"replay_seed_policy"},
    }
    _check_unknown_keys(raw, top_expected, "root")

    for section, keys in top_expected.items():
        if section not in raw:
            raise ConfigValidationError(f"Missing required section: {section}")
        if not isinstance(raw[section], dict):
            raise ConfigValidationError(f"Section {section} must be a mapping")
        _check_unknown_keys(raw[section], {k: set() for k in keys}, section)

    _require_allowed("raw_event_recording.raw_event_format", raw["raw_event_recording"]["raw_event_format"])
    _require_allowed(
        "order_book_reconstruction.reorder_window_ms",
        raw["order_book_reconstruction"]["reorder_window_ms"],
    )
    _require_allowed(
        "order_book_reconstruction.max_buffer_events",
        raw["order_book_reconstruction"]["max_buffer_events"],
    )
    _require_allowed("safety.max_safe_mode_exit_staleness", raw["safety"]["max_safe_mode_exit_staleness"])
    _require_allowed("safety.hard_stop_terminal", raw["safety"]["hard_stop_terminal"])
    _require_allowed(
        "safety.hard_stop_open_position_policy",
        raw["safety"]["hard_stop_open_position_policy"],
    )
    _require_allowed("replay.replay_seed_policy", raw["replay"]["replay_seed_policy"])

    return AgentConfig(
        raw_event_recording=RawEventRecordingConfig(**raw["raw_event_recording"]),
        order_book_reconstruction=OrderBookReconstructionConfig(**raw["order_book_reconstruction"]),
        safety=SafetyConfig(**raw["safety"]),
        replay=ReplayConfig(**raw["replay"]),
    )
