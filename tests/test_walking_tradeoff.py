from src import compile_timetable, raptor
from src.fixtures import walking_tradeoff_timetable
from example_walking_tradeoff import low_walking_witness


def test_scalar_intermediate_label_loses_a_feasible_low_walking_alternative():
    table = walking_tradeoff_timetable()
    result = raptor(compile_timetable(table), "O", "Z", 0, max_boardings=2)
    assert (result.rows[1]["M"].time, result.rows[1]["M"].boardings) == (20, 1)
    fast, = result.journeys()
    low_walk = low_walking_witness()
    fast.validate_against(table)
    low_walk.validate_against(table)
    assert (fast.arrival, fast.boardings, fast.walking_seconds) == (30, 2, 8)
    assert (low_walk.arrival, low_walk.boardings, low_walk.walking_seconds) == (35, 2, 1)
    assert fast.arrival < low_walk.arrival and fast.walking_seconds > low_walk.walking_seconds
    assert low_walk not in result.journeys()
