"""Compile immutable positional indexes; do not use a line name as a pattern."""
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping
from .timetable import Timetable, Footpath, RoutingError, integer

@dataclass(frozen=True)
class Compiled:
    timetable: Timetable
    positions: Mapping[str, tuple[tuple[int, int], ...]]
    outgoing: Mapping[str, tuple[Footpath, ...]]
    incoming: Mapping[str, tuple[Footpath, ...]]
    departures: tuple[tuple[tuple[int, ...], ...], ...]
    arrivals: tuple[tuple[tuple[int, ...], ...], ...]

    def first_trip(self, route: int, position: int, ready: int) -> int | None:
        trips = self.timetable.routes[route].trips
        if not trips or not trips[0].pickup[position]:
            return None
        i = bisect_left(self.departures[route][position], ready)
        return i if i < len(trips) else None

    def last_trip(self, route: int, position: int, latest: int) -> int | None:
        trips = self.timetable.routes[route].trips
        if not trips or not trips[0].dropoff[position]:
            return None
        i = bisect_right(self.arrivals[route][position], latest) - 1
        return i if i >= 0 else None

def compile_timetable(timetable: Timetable) -> Compiled:
    positions: dict[str, list[tuple[int, int]]] = {s: [] for s in timetable.stops}
    outgoing: dict[str, list[Footpath]] = {s: [] for s in timetable.stops}
    incoming: dict[str, list[Footpath]] = {s: [] for s in timetable.stops}
    departures, arrivals = [], []
    for r, route in enumerate(timetable.routes):
        for p, stop in enumerate(route.stops):
            positions[stop].append((r, p))  # Keep every occurrence of a loop stop.
        departures.append(tuple(tuple(t.departures[p] for t in route.trips) for p in range(len(route.stops))))
        arrivals.append(tuple(tuple(t.arrivals[p] for t in route.trips) for p in range(len(route.stops))))
    for edge in timetable.footpaths:
        outgoing[edge.source].append(edge)
        incoming[edge.target].append(edge)
    freeze = lambda values: MappingProxyType({k: tuple(v) for k, v in values.items()})
    return Compiled(timetable, freeze(positions), freeze(outgoing), freeze(incoming), tuple(departures), tuple(arrivals))

def affected_routes(index: Compiled, marked: set[str], reverse: bool = False) -> dict[int, int]:
    queue: dict[int, int] = {}
    for stop in sorted(marked):
        for route, position in index.positions[stop]:
            queue[route] = (max if reverse else min)(queue.get(route, position), position)
    return dict(sorted(queue.items()))

def validate_query(index: Compiled, origin: str, destination: str, ready: int,
                   max_boardings: int, boarding_slack: int) -> None:
    if origin not in index.positions or destination not in index.positions:
        raise RoutingError("UNKNOWN_STOP", "use an admitted stop id")
    integer(ready, "ready/deadline")
    integer(max_boardings, "max_boardings")
    integer(boarding_slack, "boarding_slack")
    if max_boardings > 32:
        raise RoutingError("LAB_BOARDING_LIMIT", "the teaching runtime admits at most 32 boardings")
