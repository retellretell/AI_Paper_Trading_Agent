from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_paper_trading_agent.config import ConfigValidationError, load_config


def test_config_validation_rejects_unknown_keys(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "raw_event_recording": {"raw_event_format": "jsonl", "unknown_key": "nope"},
                "order_book_reconstruction": {"reorder_window_ms": 100, "max_buffer_events": 200},
                "safety": {
                    "max_safe_mode_exit_staleness": 2.0,
                    "hard_stop_terminal": True,
                    "hard_stop_open_position_policy": "terminate_and_exposure_only",
                },
                "replay": {"replay_seed_policy": "match_original_seed"},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigValidationError):
        load_config(config_path)
