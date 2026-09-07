"""Marked-route, single-departure RAPTOR for arrival time and boardings."""
from .accessibility import WalkPolicy
from .footpaths import close_footpaths
from .journey import Label
from .metrics import Work
from .round_state import SearchResult, freeze_rows, changed
from .route_index import Compiled, affected_routes, validate_query
from .route_scan import scan_route

def raptor(index: Compiled, origin: str, destination: str, ready_at: int, *,
           max_boardings: int = 4, boarding_slack: int = 0,
           policy: WalkPolicy = WalkPolicy(), work: Work | None = None) -> SearchResult:
    validate_query(index, origin, destination, ready_at, max_boardings, boarding_slack)
    policy.admit(index.timetable)
    meter = work if work is not None else Work()
    meter.check()
    first = {origin: Label(ready_at, 0)}
    close_footpaths(index, first, {origin}, policy, meter)
    rows = [first]
    marked = set(first)
    for _ in range(max_boardings):
        meter.tick("rounds")
        previous = rows[-1]
        current = dict(previous)
        touched: set[str] = set()
        for route, start in affected_routes(index, marked).items():
            touched |= scan_route(index, route, start, previous, current, boarding_slack, meter)
        close_footpaths(index, current, touched, policy, meter)
        marked = changed(previous, current)
        rows.append(current)
        if not marked:
            # Preserve row indexing without spending empty scan rounds.
            rows.extend(dict(current) for _ in range(max_boardings + 1 - len(rows)))
            break
    return SearchResult(origin, destination, ready_at, freeze_rows(rows), meter.snapshot())
