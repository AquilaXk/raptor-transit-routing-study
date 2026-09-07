"""A separate frontier exercise, not a claim that the core is full McRAPTOR."""
from dataclasses import dataclass
from .timetable import RoutingError, integer

@dataclass(frozen=True)
class Objective:
    journey_id: str
    departure: int  # Later is better.
    arrival: int
    boardings: int
    walking: int
    access_burden: int
    minimum_slack: int  # Larger is better.

    def __post_init__(self) -> None:
        for field in ("departure", "arrival", "boardings", "walking", "access_burden", "minimum_slack"):
            integer(getattr(self, field), field)
        if self.arrival < self.departure:
            raise RoutingError("INVALID_OBJECTIVE", "arrival precedes departure")

    @property
    def minimizing_key(self) -> tuple[int, ...]:
        return (-self.departure, self.arrival, self.boardings, self.walking,
                self.access_burden, -self.minimum_slack)

def dominates(a: Objective, b: Objective) -> bool:
    x, y = a.minimizing_key, b.minimizing_key
    return all(u <= v for u, v in zip(x, y)) and any(u < v for u, v in zip(x, y))

def bounded_frontier(candidates: tuple[Objective, ...], capacity: int) -> tuple[Objective, ...]:
    """Keep every nondominated objective vector or fail. Never slice to capacity."""
    integer(capacity, "frontier capacity", 1)
    ids: dict[str, Objective] = {}
    for candidate in candidates:
        if candidate.journey_id in ids and candidate != ids[candidate.journey_id]:
            raise RoutingError("DUPLICATE_IDENTITY", "one journey id has conflicting objectives")
        ids[candidate.journey_id] = candidate
    unique = {c.minimizing_key: c for c in sorted(ids.values(), key=lambda c: c.journey_id, reverse=True)}
    survivors = tuple(sorted((c for c in unique.values() if not any(dominates(d, c) for d in unique.values())),
                             key=lambda c: (c.minimizing_key, c.journey_id)))
    if len(survivors) > capacity:
        raise RoutingError("RAPTOR_FRONTIER_CAPACITY_EXCEEDED", "required nondominated labels would be lost")
    return survivors
