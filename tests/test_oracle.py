"""Seeded differential checks. All fixtures are synthetic, tiny, and reproducible."""
from random import Random
import pytest
from src import *
from src.oracle import oracle_arrivals, exact_profile_seconds


def network(seed: int, unrestricted_walks: bool = False) -> Timetable:
    rng = Random(seed)
    stops = ("O", "A", "B", "C", "D", "E", "Z")
    patterns = [("A", "B", "E"), ("A", "C", "D"), ("D", "E"), ("B", "D")]
    # Vary topology as well as time: loops, branches and short turns.
    patterns += [tuple(rng.choices(("A", "B", "C", "D", "E"), k=rng.randint(2, 5)))
                 for _ in range(2)]
    routes = []
    for i, pattern in enumerate(patterns):
        pickup = tuple(rng.random() > 0.2 for _ in pattern)
        dropoff = tuple(rng.random() > 0.2 for _ in pattern)
        trips = []
        for j in range(3):
            arrivals, departures = [], []
            for p in range(len(pattern)):
                lower = departures[-1] + rng.randint(0, 5) if p else rng.randint(2, 12)
                if trips:
                    lower = max(lower, trips[-1].arrivals[p] + rng.randint(1, 9))
                arrivals.append(lower)
                departure = lower + rng.randint(0, 4)
                if trips:
                    departure = max(departure, trips[-1].departures[p] + rng.randint(1, 7))
                departures.append(departure)
            trips.append(Trip(f"t{i}-{j}", tuple(arrivals), tuple(departures), pickup, dropoff))
        routes.append(Route(f"r{i}", pattern, tuple(trips)))
    edges = [Footpath("O", "A", rng.randint(0, 4), "ENTRY"),
             Footpath("E", "Z", rng.randint(0, 4), "EXIT"),
             Footpath("B", "C", rng.randint(0, 4))]
    if unrestricted_walks:
        for _ in range(6):
            a, b = rng.sample(stops, 2)
            edges.append(Footpath(a, b, rng.randint(0, 6), step_free=rng.choice((True, False))))
    return Timetable(stops, tuple(routes), tuple(edges))

@pytest.mark.parametrize("seed", range(120))
def test_all_point_rows_match_independent_oracle(seed):
    table = network(seed, unrestricted_walks=True)
    policy = WalkPolicy(seed % 2 == 0, 1.5 if seed % 3 == 0 else 1.0)
    ready, slack = seed % 20, seed % 4
    result = raptor(compile_timetable(table), "O", "Z", ready, max_boardings=4, boarding_slack=slack, policy=policy)
    expected = oracle_arrivals(table, "O", ready, max_boardings=4, boarding_slack=slack, policy=policy)
    assert tuple({s: label.time for s, label in row.items()} for row in result.rows) == expected
    for journey in result.journeys():
        journey.validate_against(table, slack, policy=policy)

@pytest.mark.parametrize("seed", range(40))
def test_random_range_matches_every_second_oracle(seed):
    table = network(seed)
    slack = seed % 3
    profile = rraptor(compile_timetable(table), "O", "Z", 0, 50, max_boardings=3, boarding_slack=slack)
    expected = exact_profile_seconds(table, "O", "Z", 0, 50, max_boardings=3, boarding_slack=slack)
    for ready, signature in expected.items():
        journeys = profile.at(ready)
        assert tuple((j.arrival, j.boardings) for j in journeys) == signature
        for journey in journeys:
            journey.validate_against(table, slack)

@pytest.mark.parametrize("seed", range(60))
def test_reverse_latest_ready_matches_exhaustive_forward_oracle(seed):
    table = network(seed, unrestricted_walks=True)
    deadline, slack = 35 + seed % 40, seed % 4
    policy = WalkPolicy(seed % 2 == 0)
    reverse = arrive_by(compile_timetable(table), "O", "Z", deadline,
                         max_boardings=3, boarding_slack=slack, policy=policy)
    feasible = []
    for ready in range(deadline + 1):
        row = oracle_arrivals(table, "O", ready, max_boardings=3, boarding_slack=slack, policy=policy)[-1]
        if row.get("Z", float("inf")) <= deadline:
            feasible.append(ready)
    assert (reverse.ready_at if reverse else None) == (max(feasible) if feasible else None)
    if reverse:
        assert reverse.arrival <= deadline
        reverse.validate_against(table, slack, policy=policy)

@pytest.mark.parametrize("seed", range(30))
def test_last_connection_matches_all_feasible_departures(seed):
    table = network(seed)
    index = compile_timetable(table)
    horizon = max(t.arrivals[-1] for r in table.routes for t in r.trips) + sum(e.seconds for e in table.footpaths)
    feasible = []
    for ready in range(horizon + 1):
        if "Z" in oracle_arrivals(table, "O", ready, max_boardings=3)[-1]:
            feasible.append(ready)
    last = last_connection(index, "O", "Z", max_boardings=3)
    assert (last.ready_at if last else None) == (max(feasible) if feasible else None)
    if last:
        last.validate_against(table)


def test_oracle_has_no_import_of_routing_algorithm_or_pruning():
    import inspect
    import src.oracle as oracle
    source = inspect.getsource(oracle)
    for forbidden in ("from .raptor import", "from .route_scan import", "from .footpaths import", "from .profile import"):
        assert forbidden not in source
