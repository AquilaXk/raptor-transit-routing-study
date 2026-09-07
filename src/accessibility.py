"""Hard feasibility comes before route ranking. No guessed access evidence."""
from dataclasses import dataclass
from math import ceil, isfinite
from .timetable import Footpath, RoutingError, Timetable

@dataclass(frozen=True)
class WalkPolicy:
    strict_step_free: bool = True
    duration_factor: float = 1.0

    def __post_init__(self) -> None:
        if type(self.strict_step_free) is not bool:
            raise RoutingError("INVALID_INPUT", "strict_step_free must be bool")
        if isinstance(self.duration_factor, bool) or not isinstance(self.duration_factor, (int, float)) or not isfinite(self.duration_factor) or self.duration_factor <= 0:
            raise RoutingError("INVALID_INPUT", "duration factor must be finite and positive")

    def seconds(self, edge: Footpath) -> int:
        return ceil(edge.seconds * self.duration_factor)

    def allows(self, edge: Footpath) -> bool:
        return not self.strict_step_free or (edge.verified and edge.step_free is True)

    def admit(self, timetable: Timetable) -> None:
        # Deliberately conservative lab policy: reject an uncertain strict snapshot
        # as a whole. Production admission has a richer, scoped evidence contract.
        if self.strict_step_free and any(not e.verified or e.step_free is None for e in timetable.footpaths):
            raise RoutingError("ACCESSIBILITY_UNAVAILABLE", "strict snapshot contains unverified/unknown walking evidence")
