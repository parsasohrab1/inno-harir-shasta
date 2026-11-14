"""Contracts shared by simulator and future read-only OT adapters."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class TagSnapshot:
    sample: dict[str, Any]
    readings: list[dict[str, Any]]


class ReadOnlyTagAdapter(Protocol):
    """Only a snapshot read is permitted; no write/control operation is defined."""

    def read_snapshot(self) -> TagSnapshot:
        """Return one timestamped tag snapshot and its source metadata."""
        ...
