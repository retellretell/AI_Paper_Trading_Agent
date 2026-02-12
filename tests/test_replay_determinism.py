from __future__ import annotations

import json
from pathlib import Path

from ai_paper_trading_agent.replay.engine import DeterministicEngineSkeleton
from ai_paper_trading_agent.replay.harness import run_replay


def test_replay_determinism_same_seed_same_stream_identical_outputs(tmp_path: Path) -> None:
    stream = tmp_path / "events.jsonl"
    rows = [
        {"exchange_event_time": 1000, "payload": {"type": "snapshot"}},
        {"exchange_event_time": 1010, "payload": {"type": "diff"}},
        {"exchange_event_time": 1020, "payload": {"type": "diff"}},
    ]
    stream.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    out_a = run_replay(stream_path=stream, seed=7, engine=DeterministicEngineSkeleton())
    out_b = run_replay(stream_path=stream, seed=7, engine=DeterministicEngineSkeleton())

    assert out_a == out_b
