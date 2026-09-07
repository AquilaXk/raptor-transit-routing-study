"""Measured lab work, explicit budgets, and no invented deployment counters."""
from dataclasses import dataclass
from time import perf_counter
from typing import Callable
from .timetable import RoutingError, integer

@dataclass(frozen=True)
class ScanMetrics:
    work_units: int = 0
    rounds: int = 0
    routes_scanned: int = 0
    trip_lookups: int = 0
    footpaths_examined: int = 0
    labels_improved: int = 0
    reused_labels: int = 0

class Work:
    """One request-owned meter. Units are operations, not milliseconds."""
    def __init__(self, max_units: int = 1_000_000, *, deadline: float | None = None,
                 cancelled: Callable[[], bool] | None = None):
        integer(max_units, "max_units", 1)
        self.max_units, self.deadline, self.cancelled = max_units, deadline, cancelled
        self.counts = {name: 0 for name in ScanMetrics.__dataclass_fields__}

    def check(self) -> None:
        if self.cancelled is not None and self.cancelled():
            raise RoutingError("CANCELLED", "request cancelled; no partial result")
        if self.deadline is not None and perf_counter() >= self.deadline:
            raise RoutingError("DEADLINE_EXCEEDED", "request deadline exceeded; no partial result")

    def tick(self, field: str | None = None, amount: int = 1) -> None:
        self.check()
        self.counts["work_units"] += amount
        if self.counts["work_units"] > self.max_units:
            raise RoutingError("RAPTOR_WORK_CAPACITY_EXCEEDED", "request work budget exceeded")
        if field:
            self.counts[field] += amount

    def snapshot(self) -> ScanMetrics:
        self.check()
        return ScanMetrics(**self.counts)
