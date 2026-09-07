"""Slow independent exact oracle for tiny fixtures. Never use as a fallback.

The search enumerates every boardable trip and every later alighting position
on a state graph (stop, exact boardings). It does NOT call route_scan, RAPTOR,
marked-route collection, binary trip selection, or the walking closure helper.
"""
from heapq import heappop, heappush
from math import inf
from .accessibility import WalkPolicy
from .timetable import Timetable, RoutingError, integer

def oracle_arrivals(timetable: Timetable, origin: str, ready_at: int, *,
                    max_boardings: int = 4, boarding_slack: int = 0,
                    policy: WalkPolicy = WalkPolicy()) -> tuple[dict[str, int], ...]:
    if origin not in timetable.stops:
        raise RoutingError("UNKNOWN_STOP", "unknown oracle origin")
    integer(ready_at, "ready")
    integer(max_boardings, "max_boardings")
    integer(boarding_slack, "slack")
    policy.admit(timetable)
    best: dict[tuple[str, int], int] = {(origin, 0): ready_at}
    queue = [(ready_at, 0, origin)]
    while queue:
        at, boardings, stop = heappop(queue)
        if best[(stop, boardings)] != at:
            continue
        successors: list[tuple[str, int, int]] = []
        for edge in timetable.footpaths:
            if edge.source == stop and policy.allows(edge):
                successors.append((edge.target, boardings, at + policy.seconds(edge)))
        if boardings < max_boardings:
            for route in timetable.routes:
                for position, station in enumerate(route.stops):
                    if station != stop:
                        continue
                    for trip in route.trips:
                        if not trip.pickup[position] or trip.departures[position] < at + boarding_slack:
                            continue
                        for later in range(position + 1, len(route.stops)):
                            if trip.dropoff[later]:
                                successors.append((route.stops[later], boardings + 1, trip.arrivals[later]))
        for target, used, arrival in successors:
            key = (target, used)
            if arrival < best.get(key, inf):
                best[key] = arrival
                heappush(queue, (arrival, used, target))
    rows = []
    for limit in range(max_boardings + 1):
        row = {}
        for stop in timetable.stops:
            value = min((best.get((stop, k), inf) for k in range(limit + 1)), default=inf)
            if value != inf:
                row[stop] = int(value)
        rows.append(row)
    return tuple(rows)

def exact_profile_seconds(timetable: Timetable, origin: str, destination: str, start: int, end: int,
                          **kwargs) -> dict[int, tuple[tuple[int, int], ...]]:
    """Exhaust every integer second for test-only parity, not production range routing."""
    if end < start or end - start > 10_000:
        raise RoutingError("ORACLE_FIXTURE_TOO_LARGE", "use a tiny bounded test window")
    result = {}
    for ready in range(start, end + 1):
        rows = oracle_arrivals(timetable, origin, ready, **kwargs)
        best_arrival = inf
        pairs = []
        for k, row in enumerate(rows):
            arrival = row.get(destination, inf)
            if arrival < best_arrival:
                pairs.append((arrival, k))
                best_arrival = arrival
        result[ready] = tuple(sorted(pairs))
    return result
