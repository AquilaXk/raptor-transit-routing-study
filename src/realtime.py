"""A small frozen overlay contract, not a realtime provider or signature verifier."""
from dataclasses import dataclass, replace
from datetime import date
from .timetable import Timetable, Route, Trip, RoutingError, integer

@dataclass(frozen=True)
class Snapshot:
    identity: str
    bundle_id: str
    service_date: date
    observed_at: int
    valid_until: int
    delays: tuple[tuple[str, int], ...] = ()
    cancelled: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        object.__setattr__(self, "delays", tuple(tuple(x) for x in self.delays))
        object.__setattr__(self, "cancelled", frozenset(self.cancelled))
        integer(self.observed_at, "observed_at")
        integer(self.valid_until, "valid_until")
        if not self.identity or self.valid_until <= self.observed_at:
            raise RoutingError("INVALID_REALTIME", "invalid realtime identity or validity interval")
        if len({key for key, _ in self.delays}) != len(self.delays):
            raise RoutingError("INVALID_REALTIME", "duplicate occurrence update")
        for _, delay in self.delays:
            integer(delay, "delay")

def apply_snapshot(timetable: Timetable, snapshot: Snapshot, now: int) -> Timetable:
    integer(now, "now")
    if (snapshot.bundle_id, snapshot.service_date) != (timetable.bundle_id, timetable.service_date):
        raise RoutingError("REALTIME_IDENTITY_MISMATCH", "overlay does not belong to this generation/day")
    if not snapshot.observed_at <= now < snapshot.valid_until:
        raise RoutingError("REALTIME_STALE", "overlay is stale or observed in the future")
    known = {t.id for r in timetable.routes for t in r.trips}
    delays = dict(snapshot.delays)
    if not (set(delays) | snapshot.cancelled) <= known:
        raise RoutingError("UNKNOWN_OCCURRENCE", "overlay names a trip outside this admitted service date")
    routes = []
    for route in timetable.routes:
        trips = []
        for trip in route.trips:
            if trip.id in snapshot.cancelled:
                continue
            delay = delays.get(trip.id, 0)  # Explicit unchanged-trip semantics inside a valid snapshot.
            trips.append(Trip(trip.id, tuple(t + delay for t in trip.arrivals),
                              tuple(t + delay for t in trip.departures), trip.pickup, trip.dropoff))
        trips.sort(key=lambda t: (t.departures, t.arrivals, t.id))
        routes.append(Route(route.id, route.stops, tuple(trips)))  # Recheck no-overtaking.
    return replace(timetable, routes=tuple(routes))
