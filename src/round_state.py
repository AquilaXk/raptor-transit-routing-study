"""At-most-k labels, immutable result rows, and time/boarding dominance."""
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping
from .journey import Label, Journey, to_journey
from .metrics import ScanMetrics

Row = dict[str, Label]

def improve(row: Row, stop: str, label: Label, *, reverse: bool = False) -> bool:
    old = row.get(stop)
    key = lambda value: ((-value.time if reverse else value.time), value.boardings)
    if old is None or key(label) < key(old):
        row[stop] = label
        return True
    return False

def changed(before: Mapping[str, Label], after: Mapping[str, Label], *, reverse: bool = False) -> set[str]:
    key = lambda value: ((-value.time if reverse else value.time), value.boardings)
    return {s for s, label in after.items() if s not in before or key(label) < key(before[s])}

@dataclass(frozen=True)
class SearchResult:
    origin: str
    destination: str
    ready_at: int
    rows: tuple[Mapping[str, Label], ...]
    metrics: ScanMetrics

    def journeys(self) -> tuple[Journey, ...]:
        labels = [row[self.destination] for row in self.rows if self.destination in row]
        unique = {(x.time, x.boardings): x for x in labels}
        survivors = [x for x in unique.values() if not any(
            y.time <= x.time and y.boardings <= x.boardings and y.key != x.key
            for y in unique.values())]
        return tuple(to_journey(x, self.origin, self.destination, self.ready_at)
                     for x in sorted(survivors, key=lambda x: x.key))

def freeze_rows(rows: list[Row]) -> tuple[Mapping[str, Label], ...]:
    return tuple(MappingProxyType(dict(row)) for row in rows)
