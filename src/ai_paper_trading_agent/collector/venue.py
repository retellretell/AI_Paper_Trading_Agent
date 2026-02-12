from __future__ import annotations


def validate_l2_clob_scope(*, venue: str, market_type: str) -> None:
    """Enforce explicit venue scope: L2 order-book (CEX/CLOB) only."""
    if market_type.upper() == "AMM":
        raise ValueError("AMM venues are out-of-scope. Use L2 order-book CEX/CLOB venues only.")

    if venue.lower() == "polymarket" and market_type.upper() != "CLOB":
        raise ValueError("Polymarket must use CLOB endpoints only; AMM-only markets are excluded.")

    if market_type.upper() not in {"CLOB", "CEX"}:
        raise ValueError("market_type must be CEX or CLOB for this paper-trading collector.")
