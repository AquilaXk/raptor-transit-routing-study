from datetime import date
from dataclasses import replace
import pytest
from src import *
from src.realtime import Snapshot, apply_snapshot
from src.metrics import Work

@pytest.mark.parametrize("arrival,departure", [((-1, 2), (0, 2)), ((2, 3), (1, 3)), ((0, 2), (3, 3)), ((True, 2), (1, 2))])
def test_invalid_trip_times(arrival, departure):
    with pytest.raises(RoutingError):
        Trip("x", arrival, departure)

def test_overtaking_rejected():
    with pytest.raises(RoutingError, match="OVERTAKING_PATTERN"):
        Route("r", ("A", "B"), (Trip("a", (1, 20), (1, 20)), Trip("b", (2, 10), (2, 10))))

def test_mixed_pickup_patterns_rejected():
    with pytest.raises(RoutingError, match="INCOMPATIBLE_PATTERN"):
        Route("r", ("A", "B"), (Trip("a", (1, 3), (1, 3)),
                                  Trip("b", (2, 4), (2, 4), pickup=(False, True))))

def test_no_pickup_and_no_dropoff():
    for kwargs in ({"pickup": (False, True)}, {"dropoff": (True, False)}):
        table = Timetable(("A", "B"), (Route("r", ("A", "B"), (Trip("x", (1, 2), (1, 2), **kwargs),)),))
        assert not raptor(compile_timetable(table), "A", "B", 0).journeys()

@pytest.mark.parametrize("seconds", [-1, True, 1.1])
def test_invalid_footpaths(seconds):
    with pytest.raises(RoutingError):
        Footpath("A", "B", seconds)

def test_missing_accessibility_evidence_is_not_no_route():
    table = Timetable(("A", "B"), (), (Footpath("A", "B", 1, step_free=None),))
    with pytest.raises(RoutingError, match="ACCESSIBILITY_UNAVAILABLE"):
        raptor(compile_timetable(table), "A", "B", 0)

def test_known_stairs_are_not_unknown_evidence():
    table = Timetable(("A", "B"), (), (Footpath("A", "B", 1, step_free=False),))
    assert not raptor(compile_timetable(table), "A", "B", 0).journeys()

@pytest.mark.parametrize("kwargs", [{"max_boardings": -1}, {"max_boardings": 33}, {"max_boardings": True}, {"boarding_slack": -1}])
def test_invalid_queries(kwargs):
    with pytest.raises(RoutingError):
        raptor(compile_timetable(demo_timetable()), "O", "Z", 0, **kwargs)

def test_unknown_stop_fails():
    with pytest.raises(RoutingError, match="UNKNOWN_STOP"):
        raptor(compile_timetable(demo_timetable()), "missing", "Z", 0)

def test_budget_failure_never_returns_partial_results():
    with pytest.raises(RoutingError, match="CAPACITY_EXCEEDED"):
        raptor(compile_timetable(demo_timetable()), "O", "Z", 0, work=Work(1))

def snapshot(**kwargs):
    values = dict(identity="toy-rt-1", bundle_id="a"*64, service_date=date(2026, 9, 7), observed_at=100, valid_until=200)
    values.update(kwargs)
    return Snapshot(**values)

@pytest.mark.parametrize("now", [99, 200, 201])
def test_stale_or_future_realtime_rejected(now):
    with pytest.raises(RoutingError, match="REALTIME_STALE"):
        apply_snapshot(demo_timetable(), snapshot(), now)

@pytest.mark.parametrize("kwargs", [{"bundle_id": "b"*64}, {"service_date": date(2026, 9, 8)}])
def test_realtime_identity_is_generation_and_day(kwargs):
    with pytest.raises(RoutingError, match="IDENTITY_MISMATCH"):
        apply_snapshot(demo_timetable(), snapshot(**kwargs), 100)

def test_unknown_trip_realtime_fails():
    with pytest.raises(RoutingError, match="UNKNOWN_OCCURRENCE"):
        apply_snapshot(demo_timetable(), snapshot(delays=(("unknown", 1),)), 100)

def test_cancelled_trip_removed_without_changing_original():
    original = demo_timetable()
    updated = apply_snapshot(original, snapshot(cancelled=frozenset({"R1-0802"})), 100)
    assert len(updated.routes[0].trips) == 1
    assert len(original.routes[0].trips) == 2

def test_delay_can_invalidate_single_trip_scan_assumptions():
    table = Timetable(("A", "B"), (Route("r", ("A", "B"), (
        Trip("a", (0, 20), (0, 20)), Trip("b", (10, 25), (10, 25)))),))
    with pytest.raises(RoutingError, match="OVERTAKING_PATTERN"):
        apply_snapshot(table, snapshot(delays=(("a", 7),)), 100)

def test_duplicate_update_is_rejected():
    with pytest.raises(RoutingError, match="duplicate"):
        snapshot(delays=(("R1-0802", 1), ("R1-0802", 2)))
