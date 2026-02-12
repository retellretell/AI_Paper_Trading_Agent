from __future__ import annotations

from pathlib import Path


def test_decision_code_paths_do_not_call_wall_clock_apis() -> None:
    decision_paths = [
        Path(__file__).resolve().parents[1] / "src" / "ai_paper_trading_agent" / "core",
        Path(__file__).resolve().parents[1] / "src" / "ai_paper_trading_agent" / "replay",
    ]

    forbidden_patterns = ("time.time(", "datetime.now(")
    violations: list[str] = []

    for decision_path in decision_paths:
        for py_file in decision_path.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            for pattern in forbidden_patterns:
                if pattern in text:
                    violations.append(f"{py_file}: contains {pattern}")

    assert not violations, "\n".join(violations)
