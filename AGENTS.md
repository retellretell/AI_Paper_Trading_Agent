# AGENTS.md — Project Guardrails

- Source of truth: docs/plan_v7_2_2.md (do not contradict it).
- Venue: L2 order-book (CEX/CLOB). AMM is out of scope.
- If Polymarket is used: use CLOB endpoints only; AMM-only markets excluded.
- Determinism: decisions use Exchange Event Time only; wall-clock is monitoring only.
- Fills: depth-walk VWAP only; no mid-price assumptions.
- Fail-closed: respect NORMAL/SAFE_MODE/HARD_STOP transitions.
- Parameters: never invent; must be in config/appendix.
- Always add tests for: book sync edge cases, staleness transitions, replay determinism, fuzz inputs.
