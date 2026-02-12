from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DiffRange:
    U: int
    u: int


class BookSyncChecker:
    """Minimal continuity checker scaffold for snapshot/diff sequencing."""

    def __init__(self, snapshot_last_update_id: int) -> None:
        self.last_update_id = snapshot_last_update_id
        self._initialized = False

    def apply(self, diff: DiffRange) -> bool:
        # Discard duplicates / old updates.
        if diff.u <= self.last_update_id:
            return False

        # Initial bridge from snapshot.
        if not self._initialized:
            if diff.U <= self.last_update_id + 1 <= diff.u:
                self.last_update_id = diff.u
                self._initialized = True
                return True
            return False

        # Steady-state strict continuity skeleton.
        if diff.U == self.last_update_id + 1:
            self.last_update_id = diff.u
            return True

        return False
