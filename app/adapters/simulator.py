"""Synthetic source implementing the same contract planned for read-only OT inputs."""
from __future__ import annotations

from ..core import make_simulated_sample
from ..dvr import build_tag_readings
from .contracts import TagSnapshot


class SimulatorAdapter:
    def read_snapshot(self) -> TagSnapshot:
        sample = make_simulated_sample()
        sample["source"] = "simulator"
        return TagSnapshot(sample=sample, readings=build_tag_readings(sample))
