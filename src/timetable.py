"""Immutable, already-admitted teaching data. This is not a GTFS importer."""
from dataclasses import dataclass
from datetime import date
import re

class RoutingError(ValueError):
    """A typed failure; callers must not turn it into an old successful route."""
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")

def integer(value: int, name: str, minimum: int = 0) -> None:
    if type(value) is not int or value < minimum:
        raise RoutingError("INVALID_INPUT", f"{name} must be an integer >= {minimum}")

def identifier(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise RoutingError("INVALID_INPUT", f"{name} must be a nonempty string")

@dataclass(frozen=True)
class Trip:
    id: str
    arrivals: tuple[int, ...]
    departures: tuple[int, ...]
    pickup: tuple[bool, ...] = ()
    dropoff: tuple[bool, ...] = ()

    def __post_init__(self) -> None:
        identifier(self.id, "trip id")
        for field in ("arrivals", "departures", "pickup", "dropoff"):
            object.__setattr__(self, field, tuple(getattr(self, field)))
        n = len(self.arrivals)
        if n < 2 or len(self.departures) != n:
            raise RoutingError("INVALID_TIMETABLE", "a trip needs matching times at >= 2 positions")
        for field in ("pickup", "dropoff"):
            if not getattr(self, field):
                object.__setattr__(self, field, (True,) * n)
            if len(getattr(self, field)) != n or any(type(x) is not bool for x in getattr(self, field)):
                raise RoutingError("INVALID_TIMETABLE", f"invalid {field} mask")
        for i, (arrival, departure) in enumerate(zip(self.arrivals, self.departures)):
            integer(arrival, "arrival")
            integer(departure, "departure")
            if arrival > departure or (i and self.departures[i - 1] > arrival):
                raise RoutingError("INVALID_TIMETABLE", "trip time moves backward")

@dataclass(frozen=True)
class Route:
    """A scan pattern, not a passenger-facing line name. Position matters."""
    id: str
    stops: tuple[str, ...]
    trips: tuple[Trip, ...]

    def __post_init__(self) -> None:
        identifier(self.id, "route id")
        object.__setattr__(self, "stops", tuple(self.stops))
        object.__setattr__(self, "trips", tuple(self.trips))
        if len(self.stops) < 2:
            raise RoutingError("INVALID_TIMETABLE", "a pattern needs >= 2 positions")
        for trip in self.trips:
            if len(trip.arrivals) != len(self.stops):
                raise RoutingError("INVALID_TIMETABLE", "trip/pattern length mismatch")
        for earlier, later in zip(self.trips, self.trips[1:]):
            if earlier.pickup != later.pickup or earlier.dropoff != later.dropoff:
                raise RoutingError("INCOMPATIBLE_PATTERN", "split different pickup/dropoff patterns first")
            if any(a > b for a, b in zip(earlier.arrivals, later.arrivals)) or any(
                a > b for a, b in zip(earlier.departures, later.departures)
            ):
                raise RoutingError("OVERTAKING_PATTERN", "split overtaking trips before a single-trip scan")

@dataclass(frozen=True)
class Footpath:
    source: str
    target: str
    seconds: int
    kind: str = "TRANSFER"
    step_free: bool | None = True
    verified: bool = True

    def __post_init__(self) -> None:
        integer(self.seconds, "footpath seconds")
        if self.kind not in {"ENTRY", "TRANSFER", "EXIT", "WALK"}:
            raise RoutingError("INVALID_INPUT", "unknown walking leg kind")
        if self.step_free is not None and type(self.step_free) is not bool:
            raise RoutingError("INVALID_INPUT", "step_free must be bool or None")
        if type(self.verified) is not bool:
            raise RoutingError("INVALID_INPUT", "verified must be bool")

@dataclass(frozen=True)
class Timetable:
    stops: tuple[str, ...]
    routes: tuple[Route, ...]
    footpaths: tuple[Footpath, ...] = ()
    service_date: date = date(2026, 9, 7)
    bundle_id: str = "a" * 64

    def __post_init__(self) -> None:
        for field in ("stops", "routes", "footpaths"):
            object.__setattr__(self, field, tuple(getattr(self, field)))
        for stop in self.stops:
            identifier(stop, "stop")
        if not self.stops or len(set(self.stops)) != len(self.stops):
            raise RoutingError("INVALID_TIMETABLE", "stop ids must be unique")
        route_ids = [route.id for route in self.routes]
        trip_ids = [trip.id for route in self.routes for trip in route.trips]
        if len(set(route_ids)) != len(route_ids) or len(set(trip_ids)) != len(trip_ids):
            raise RoutingError("INVALID_TIMETABLE", "route and trip ids must be unique")
        stops = set(self.stops)
        if any(stop not in stops for route in self.routes for stop in route.stops):
            raise RoutingError("INVALID_TIMETABLE", "pattern refers to an unknown stop")
        if any(edge.source not in stops or edge.target not in stops for edge in self.footpaths):
            raise RoutingError("INVALID_TIMETABLE", "footpath refers to an unknown stop")
        if type(self.service_date) is not date or not re.fullmatch(r"[0-9a-f]{64}", self.bundle_id):
            raise RoutingError("INVALID_IDENTITY", "expected a service date and lowercase SHA-256-shaped id")
