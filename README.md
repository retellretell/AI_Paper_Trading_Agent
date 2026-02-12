# AI Paper Trading Agent (Institutional-grade, Paper Only)

This repository implements an institutional-style paper trading research platform based on an L2 order-book (CEX/CLOB) design.

- **Paper trading only** (no real orders, no KYC)
- **Venue assumption**: L2 order-book venues (CEX/CLOB). **AMM venues are out-of-scope.**
- Spec: see `docs/plan_v7_2_2.md`
- Guardrails: see `AGENTS.md`

## M1 collector (paper mode) quick start

Record public L2 events into JSONL (raw event recording format from the plan):

```python
from ai_paper_trading_agent.collector import JsonlRawEventRecorder, L2OrderBookCollector

recorder = JsonlRawEventRecorder("artifacts/raw_events.jsonl")
collector = L2OrderBookCollector(venue="binance", market_type="CEX", recorder=recorder)

collector.ingest(
    message_type="snapshot",
    exchange_event_time=1700000000000,
    raw_payload={"type": "snapshot", "lastUpdateId": 12345},
)
collector.ingest(
    message_type="diff",
    exchange_event_time=1700000000100,
    raw_payload={"type": "diff", "U": 12346, "u": 12347},
)
```

Replay recorded stream deterministically:

```python
from ai_paper_trading_agent.replay.engine import DeterministicEngineSkeleton
from ai_paper_trading_agent.replay.harness import run_replay

outputs = run_replay(
    stream_path="artifacts/raw_events.jsonl",
    seed=7,
    engine=DeterministicEngineSkeleton(),
)
print(outputs)
```

> No order placement is implemented. Execution remains a depth-walk VWAP placeholder only.
