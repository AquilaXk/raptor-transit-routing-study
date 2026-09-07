"""Native reverse scans. Incoming edges are a search index, not new walkways."""
from .accessibility import WalkPolicy
from .footpaths import close_footpaths
from .journey import Label, Journey, tighten_walks
from .metrics import Work
from .round_state import changed
from .route_index import Compiled, affected_routes, validate_query
from .route_scan import scan_route
from .timetable import RoutingError, integer

def arrive_by(index: Compiled, origin: str, destination: str, deadline: int, *,
              earliest_ready: int = 0, max_boardings: int = 4, boarding_slack: int = 0,
              policy: WalkPolicy = WalkPolicy(), work: Work | None = None) -> Journey | None:
    validate_query(index, origin, destination, deadline, max_boardings, boarding_slack)
    integer(earliest_ready, "earliest_ready")
    if earliest_ready > deadline:
        raise RoutingError("INVALID_WINDOW", "earliest ready is after deadline")
    policy.admit(index.timetable)
    meter = work if work is not None else Work()
    current = {destination: Label(deadline, 0)}
    close_footpaths(index, current, {destination}, policy, meter, reverse=True)
    marked = set(current)
    for _ in range(max_boardings):
        meter.tick("rounds")
        previous = current
        current = dict(previous)
        touched: set[str] = set()
        for route, start in affected_routes(index, marked, reverse=True).items():
            touched |= scan_route(index, route, start, previous, current, boarding_slack, meter, reverse=True)
        close_footpaths(index, current, touched, policy, meter, reverse=True)
        marked = changed(previous, current, reverse=True)
        if not marked:
            break
    meter.check()
    label = current.get(origin)
    if label is None or label.time < earliest_ready:
        return None
    arrival = label.legs[-1].arrival if label.legs else label.time
    journey = Journey(origin, destination, label.time, arrival, label.boardings, label.legs)
    journey = tighten_walks(journey)
    journey.validate(boarding_slack)
    return journey

def last_connection(index: Compiled, origin: str, destination: str, *,
                    earliest_ready: int = 0, max_boardings: int = 4, boarding_slack: int = 0,
                    policy: WalkPolicy = WalkPolicy(), work: Work | None = None) -> Journey | None:
    validate_query(index, origin, destination, earliest_ready, max_boardings, boarding_slack)
    policy.admit(index.timetable)
    meter = work if work is not None else Work()
    walking = {origin: Label(0, 0)}
    close_footpaths(index, walking, {origin}, policy, meter)
    if destination in walking:
        raise RoutingError("UNSUPPORTED_LAB_LAST_CONNECTION", "this lab requires at least one ride and no walking-only O/D")
    arrivals = [time for route in index.timetable.routes for trip in route.trips for time in trip.arrivals]
    if not arrivals:
        meter.check()
        return None
    # Every useful nonnegative shortest walk has a simple path, bounded by this sum.
    horizon = max(arrivals) + sum(policy.seconds(edge) for edge in index.timetable.footpaths if policy.allows(edge))
    if earliest_ready > horizon:
        meter.check()
        return None
    return arrive_by(index, origin, destination, horizon, earliest_ready=earliest_ready,
                     max_boardings=max_boardings, boarding_slack=boarding_slack, policy=policy, work=meter)
