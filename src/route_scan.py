"""One active trip per admitted pattern. Read previous; write current."""
from typing import Mapping
from .journey import Label, Leg
from .metrics import Work
from .round_state import Row, improve
from .route_index import Compiled

def scan_route(index: Compiled, route_number: int, start: int, previous: Mapping[str, Label],
               current: Row, slack: int, work: Work, *, reverse: bool = False) -> set[str]:
    work.tick("routes_scanned")
    route = index.timetable.routes[route_number]
    touched: set[str] = set()
    active: int | None = None
    parent: Label | None = None
    connection_position = -1
    positions = range(start, -1, -1) if reverse else range(start, len(route.stops))
    for position in positions:
        work.tick()
        stop = route.stops[position]
        if active is not None and parent is not None:
            trip = route.trips[active]
            permitted = trip.pickup[position] if reverse else trip.dropoff[position]
            if permitted:
                if reverse:
                    leg = Leg("RIDE", stop, route.stops[connection_position],
                              trip.departures[position], trip.arrivals[connection_position], trip.id)
                    label = Label(trip.departures[position] - slack, parent.boardings + 1,
                                  (leg,) + parent.legs)
                else:
                    leg = Leg("RIDE", route.stops[connection_position], stop,
                              trip.departures[connection_position], trip.arrivals[position], trip.id)
                    label = Label(trip.arrivals[position], parent.boardings + 1, parent.legs + (leg,))
                if improve(current, stop, label, reverse=reverse):
                    work.tick("labels_improved")
                    touched.add(stop)
        ready = previous.get(stop)  # Never current: that would hide an extra boarding.
        if ready is None:
            continue
        work.tick("trip_lookups")
        candidate = (index.last_trip(route_number, position, ready.time) if reverse else
                     index.first_trip(route_number, position, ready.time + slack))
        if candidate is not None and (
            active is None or (candidate > active if reverse else candidate < active)
            or (candidate == active and parent is not None and ready.boardings < parent.boardings)
        ):
            active, parent, connection_position = candidate, ready, position
    return touched
