from datetime import date
import pytest
from src import *
from src.service_time import service_instant, service_active
from src.route_index import affected_routes
from src.pareto import Objective, bounded_frontier, dominates

@pytest.mark.parametrize("text,seconds", [("0:00:00", 0), ("08:00:01", 28801), ("24:06:00", 86760), ("27:00:00", 97200)])
def test_time_roundtrip(text, seconds):
    assert parse_time(text) == seconds
    assert parse_time(format_time(seconds)) == seconds

@pytest.mark.parametrize("text", ["8:0:0", "08:60:00", "-1:00:00", "08:00", "2026-09-07", "08:00:00Z", "eight", ""])
def test_invalid_time(text):
    with pytest.raises(RoutingError):
        parse_time(text)

def test_seoul_service_day_rollover():
    value = service_instant(date(2026, 9, 7), parse_time("24:06:00"))
    assert value.isoformat() == "2026-09-08T00:06:00+09:00"

def test_calendar_exceptions_override_weekly_schedule():
    day = date(2026, 9, 7)
    assert not service_active(day, day, day, frozenset({0}), {day: False})
    assert service_active(day, day, day, frozenset(), {day: True})

def test_loop_stop_positions_are_preserved():
    table = Timetable(("A", "B", "C"), (Route("r", ("A", "B", "A", "C"), (
        Trip("t", (1, 2, 3, 4), (1, 2, 3, 4)),)),))
    index = compile_timetable(table)
    assert index.positions["A"] == ((0, 0), (0, 2))
    assert affected_routes(index, {"A"}) == {0: 0}
    assert affected_routes(index, {"A"}, reverse=True) == {0: 2}
    assert raptor(index, "A", "C", 3).journeys()[0].arrival == 4

def test_walk_factor_is_rounded_up():
    assert WalkPolicy(duration_factor=1.1).seconds(Footpath("A", "B", 3)) == 4

@pytest.mark.parametrize("factor", [0, -1, float('inf'), float('nan'), True])
def test_invalid_walk_factor(factor):
    with pytest.raises(RoutingError):
        WalkPolicy(duration_factor=factor)

def objective(name, arrival=100, walking=10, slack=30):
    return Objective(name, 0, arrival, 1, walking, 0, slack)

def test_multicriteria_dominance_not_weighted_sum():
    fast, less_walk = objective("fast", 100, 30), objective("walk", 110, 10)
    assert not dominates(fast, less_walk) and not dominates(less_walk, fast)
    assert len(bounded_frontier((fast, less_walk), 2)) == 2

def test_required_frontier_cannot_be_silently_truncated():
    with pytest.raises(RoutingError, match="RAPTOR_FRONTIER_CAPACITY_EXCEEDED"):
        bounded_frontier((objective("fast", 100, 30), objective("walk", 110, 10)), 1)

def test_dominated_and_equal_vectors_are_deduplicated():
    a, b, c = objective("a"), objective("b", 101), objective("c")
    assert bounded_frontier((a, b, c), 1) == (a,)

def test_conflicting_journey_identity_fails():
    with pytest.raises(RoutingError, match="DUPLICATE_IDENTITY"):
        bounded_frontier((objective("a"), objective("a", 101)), 2)

def test_safety_slack_is_maximized():
    assert dominates(objective("safe", slack=31), objective("tight", slack=30))
