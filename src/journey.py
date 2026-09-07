"""Immutable path witnesses. Waiting is implicit between consecutive legs."""
from dataclasses import dataclass
from .timetable import RoutingError, Timetable, integer
from .accessibility import WalkPolicy

@dataclass(frozen=True)
class Leg:
    kind: str
    source: str
    target: str
    departure: int
    arrival: int
    trip_id: str | None = None

@dataclass(frozen=True)
class Label:
    time: int
    boardings: int
    legs: tuple[Leg, ...] = ()

    @property
    def key(self) -> tuple[int, int]:
        return self.time, self.boardings

@dataclass(frozen=True)
class Journey:
    origin: str
    destination: str
    ready_at: int
    arrival: int
    boardings: int
    legs: tuple[Leg, ...]

    @property
    def transfers(self) -> int:
        return max(0, self.boardings - 1)

    @property
    def walking_seconds(self) -> int:
        return sum(leg.arrival - leg.departure for leg in self.legs if leg.kind != "RIDE")

    @property
    def first_board_at(self) -> int | None:
        return next((leg.departure for leg in self.legs if leg.kind == "RIDE"), None)

    def validate(self, boarding_slack: int = 0) -> None:
        at, clock, boardings = self.origin, self.ready_at, 0
        for leg in self.legs:
            required = clock + (boarding_slack if leg.kind == "RIDE" else 0)
            if leg.source != at or leg.departure < required or leg.arrival < leg.departure:
                raise RoutingError("INVALID_WITNESS", "path continuity, time, or boarding slack failed")
            if leg.kind == "RIDE":
                boardings += 1
            at, clock = leg.target, leg.arrival
        if at != self.destination or clock != self.arrival or boardings != self.boardings:
            raise RoutingError("INVALID_WITNESS", "destination/arrival/boarding count mismatch")

    def validate_against(self, timetable: Timetable, boarding_slack: int = 0, *,
                         policy: WalkPolicy = WalkPolicy()) -> None:
        """Check raw admitted input; do not reuse routing indexes or trip selection.

        Supply the exact post-overlay timetable and walking policy used by the
        query. This proves feasibility in that input, not optimality or provenance.
        Repeated stops match an ordered pair of positions, never a stop-id lookup.
        """
        integer(boarding_slack, "boarding_slack")
        integer(self.ready_at, "ready_at")
        integer(self.arrival, "arrival")
        integer(self.boardings, "boardings")
        policy.admit(timetable)
        self.validate(boarding_slack)
        if self.origin not in timetable.stops or self.destination not in timetable.stops:
            raise RoutingError("INVALID_WITNESS", "endpoint is outside the supplied timetable")
        for leg in self.legs:
            integer(leg.departure, "leg departure")
            integer(leg.arrival, "leg arrival")
            if leg.kind == "RIDE":
                exists = any(
                    route.stops[i] == leg.source and route.stops[j] == leg.target
                    and trip.pickup[i] and trip.dropoff[j]
                    and trip.departures[i] == leg.departure
                    and trip.arrivals[j] == leg.arrival
                    for route in timetable.routes for trip in route.trips
                    if trip.id == leg.trip_id
                    for i in range(len(route.stops))
                    for j in range(i + 1, len(route.stops))
                )
            else:
                exists = leg.trip_id is None and any(
                    (edge.source, edge.target, edge.kind) == (leg.source, leg.target, leg.kind)
                    and policy.allows(edge)
                    and policy.seconds(edge) == leg.arrival - leg.departure
                    for edge in timetable.footpaths
                )
            if not exists:
                raise RoutingError("INVALID_WITNESS", "leg is not permitted by the supplied input")

def to_journey(label: Label, origin: str, destination: str, ready_at: int) -> Journey:
    return Journey(origin, destination, ready_at, label.time, label.boardings, label.legs)

def tighten_walks(journey: Journey) -> Journey:
    """Keep the chosen rides, but remove unnecessary waiting before walking."""
    clock = journey.ready_at
    legs = []
    for leg in journey.legs:
        if leg.kind != "RIDE":
            duration = leg.arrival - leg.departure
            leg = Leg(leg.kind, leg.source, leg.target, clock, clock + duration, leg.trip_id)
        legs.append(leg)
        clock = leg.arrival
    return Journey(journey.origin, journey.destination, journey.ready_at, clock, journey.boardings, tuple(legs))
