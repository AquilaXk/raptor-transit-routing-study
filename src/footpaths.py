"""Directed shortest-walk closure. The heap belongs to walking, not route scans."""
from heapq import heappop, heappush
from itertools import count
from .accessibility import WalkPolicy
from .journey import Label, Leg
from .metrics import Work
from .round_state import Row, improve
from .route_index import Compiled

def close_footpaths(index: Compiled, row: Row, seeds: set[str], policy: WalkPolicy,
                    work: Work, *, reverse: bool = False) -> set[str]:
    touched: set[str] = set()
    serial = count()
    sign = -1 if reverse else 1
    heap: list[tuple[int, int, int, str, Label]] = []
    for stop in sorted(seeds):
        label = row[stop]
        heappush(heap, (sign * label.time, label.boardings, next(serial), stop, label))
    while heap:
        _, _, _, stop, label = heappop(heap)
        work.tick()
        if row.get(stop) is not label:
            continue
        edges = index.incoming[stop] if reverse else index.outgoing[stop]
        for edge in edges:
            work.tick("footpaths_examined")
            if not policy.allows(edge):
                continue
            duration = policy.seconds(edge)
            target = edge.source if reverse else edge.target
            if reverse:
                leg = Leg(edge.kind, edge.source, edge.target, label.time - duration, label.time)
                candidate = Label(label.time - duration, label.boardings, (leg,) + label.legs)
            else:
                leg = Leg(edge.kind, edge.source, edge.target, label.time, label.time + duration)
                candidate = Label(label.time + duration, label.boardings, label.legs + (leg,))
            if improve(row, target, candidate, reverse=reverse):
                work.tick("labels_improved")
                touched.add(target)
                heappush(heap, (sign * candidate.time, candidate.boardings, next(serial), target, candidate))
    return touched
