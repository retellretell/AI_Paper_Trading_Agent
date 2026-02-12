from __future__ import annotations

from pathlib import Path


def test_decision_code_paths_do_not_call_wall_clock_apis() -> None:
    src_root = Path(__file__).resolve().parents[1] / "src" / "ai_paper_trading_agent"
    py_files = [p for p in src_root.rglob("*.py")]

    forbidden_patterns = ("time.time(", "datetime.now(")
    violations: list[str] = []

    for py_file in py_files:
        text = py_file.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            if pattern in text:
                violations.append(f"{py_file}: contains {pattern}")

    assert not violations, "\n".join(violations)
