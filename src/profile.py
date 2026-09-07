"""Event-based, latest-to-earliest rRAPTOR with retained round labels.

Scope: integer-second windows, one admitted service date, static walking,
arrival/boarding objectives, and transit-required O/D pairs. This is not the
complete EasySubway Journey Profile V1 contract or its multicriteria frontier.
"""
from dataclasses import dataclass
from .accessibility import WalkPolicy
from .footpaths import close_footpaths
from .journey import Label, Journey
from .metrics import Work, ScanMetrics
from .round_state import Row, SearchResult, changed, improve, freeze_rows
from .route_index import Compiled, affected_routes, validate_query
from .route_scan import scan_route
from .timetable import RoutingError, integer

@dataclass(frozen=True)
class ProfileSegment:
    ready_from: int
    ready_through: int  # Inclusive, integer seconds.
    result: SearchResult

    @property
    def signature(self) -> tuple[tuple[int, int], ...]:
        return tuple((j.arrival, j.boardings) for j in self.result.journeys())

    def journeys_at(self, ready: int) -> tuple[Journey, ...]:
        if not self.ready_from <= ready <= self.ready_through:
            raise RoutingError("OUTSIDE_WINDOW", "ready time is outside this segment")
        return tuple(Journey(j.origin, j.destination, ready, j.arrival, j.boardings, j.legs)
                     for j in self.result.journeys())

@dataclass(frozen=True)
class Profile:
    segments: tuple[ProfileSegment, ...]
    metrics: ScanMetrics
    departure_events: int

    def at(self, ready: int) -> tuple[Journey, ...]:
        integer(ready, "ready")
        for segment in self.segments:
            if segment.ready_from <= ready <= segment.ready_through:
                return segment.journeys_at(ready)
        raise RoutingError("OUTSIDE_WINDOW", "ready time is outside this profile")

def rraptor(index: Compiled, origin: str, destination: str, start: int, end: int, *,
            max_boardings: int = 4, boarding_slack: int = 0,
            policy: WalkPolicy = WalkPolicy(), work: Work | None = None) -> Profile:
    validate_query(index, origin, destination, start, max_boardings, boarding_slack)
    integer(end, "window end")
    if end < start:
        raise RoutingError("INVALID_WINDOW", "window end precedes start")
    policy.admit(index.timetable)
    meter = work if work is not None else Work()
    access = {origin: Label(0, 0)}
    close_footpaths(index, access, {origin}, policy, meter)
    if destination in access:
        raise RoutingError("UNSUPPORTED_LAB_PROFILE", "walking-only O/D needs affine profile segments; use point/arrive-by")
    thresholds = {end}
    for route in index.timetable.routes:
        for trip in route.trips:
            for position, stop in enumerate(route.stops):
                meter.tick()
                if stop in access and trip.pickup[position]:
                    latest_ready = trip.departures[position] - boarding_slack - access[stop].time
                    if start <= latest_ready <= end:
                        thresholds.add(latest_ready)
    # Catchability changes just AFTER a threshold. A segment is [previous+1, threshold].
    endpoints = sorted(thresholds)
    lower = {right: (start if i == 0 else endpoints[i - 1] + 1) for i, right in enumerate(endpoints)}
    retained: list[Row] = [{} for _ in range(max_boardings + 1)]
    segments: list[ProfileSegment] = []
    for ready in reversed(endpoints):
        if lower[ready] > ready:
            continue
        before = retained
        base: Row = {origin: Label(ready, 0)}
        close_footpaths(index, base, {origin}, policy, meter)
        rows: list[Row] = [base]
        for k in range(1, max_boardings + 1):
            meter.tick("rounds")
            previous = rows[k - 1]
            current = dict(before[k])
            meter.counts["reused_labels"] += len(current)
            touched: set[str] = set()
            for stop, label in previous.items():
                if improve(current, stop, label):
                    touched.add(stop)
            # Compare the SAME round with the later departure, not adjacent rounds.
            marked = changed(before[k - 1], previous)
            for route, position in affected_routes(index, marked).items():
                touched |= scan_route(index, route, position, previous, current, boarding_slack, meter)
            close_footpaths(index, current, touched, policy, meter)
            rows.append(current)
        retained = rows
        result = SearchResult(origin, destination, ready, freeze_rows(rows), meter.snapshot())
        segments.append(ProfileSegment(lower[ready], ready, result))
    ordered = list(reversed(segments))
    compressed: list[ProfileSegment] = []
    for segment in ordered:
        if compressed and compressed[-1].signature == segment.signature:
            earlier = compressed.pop()
            # Keep the later witness: an earlier-ready rider can wait for it.
            compressed.append(ProfileSegment(earlier.ready_from, segment.ready_through, segment.result))
        else:
            compressed.append(segment)
    return Profile(tuple(compressed), meter.snapshot(), len(endpoints))
