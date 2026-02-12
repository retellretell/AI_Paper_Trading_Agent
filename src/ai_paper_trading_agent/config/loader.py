from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schema import AgentConfig, validate_config


def load_config(path: Path | str) -> AgentConfig:
    """Load config with strict schema validation.

    M0 loader accepts JSON for zero-dependency portability.
    """
    config_path = Path(path)
    raw: Any = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Config root must be a mapping")
    return validate_config(raw)
