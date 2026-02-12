from __future__ import annotations

import json
from pathlib import Path

from .models import RawCollectorEvent


class JsonlRawEventRecorder:
    """JSON Lines recorder: one raw event object per line."""

    def __init__(self, output_path: Path | str) -> None:
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: RawCollectorEvent) -> None:
        with self.output_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_json_record(), separators=(",", ":")) + "\n")
