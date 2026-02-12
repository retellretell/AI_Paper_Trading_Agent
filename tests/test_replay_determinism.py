from __future__ import annotations

import json

from ai_paper_trading_agent.collector.collector import L2OrderBookCollector
from ai_paper_trading_agent.collector.recorder import JsonlRawEventRecorder
from ai_paper_trading_agent.replay.engine import DeterministicEngineSkeleton
from ai_paper_trading_agent.replay.harness import run_replay


def test_recorder_jsonl_stream_replays_deterministically(tmp_path) -> None:
    stream = tmp_path / "events.jsonl"
    recorder = JsonlRawEventRecorder(stream)
    collector = L2OrderBookCollector(venue="binance", market_type="CEX", recorder=recorder)

    collector.ingest(
        message_type="snapshot",
        exchange_event_time=1000,
        local_arrival_time_ns=11,
        raw_payload={"type": "snapshot", "lastUpdateId": 10},
    )
    collector.ingest(
        message_type="diff",
        exchange_event_time=1010,
        local_arrival_time_ns=12,
        raw_payload={"type": "diff", "U": 11, "u": 12},
    )

    rows = [json.loads(line) for line in stream.read_text(encoding="utf-8").splitlines()]
    assert rows[0].keys() == {"message_type", "exchange_event_time", "local_arrival_time_ns", "raw_payload"}

    out_a = run_replay(stream_path=stream, seed=7, engine=DeterministicEngineSkeleton())
    out_b = run_replay(stream_path=stream, seed=7, engine=DeterministicEngineSkeleton())

    assert out_a == out_b
