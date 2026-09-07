from dataclasses import replace
import pytest
from src import *
from src.service_time import parse_time as t
from src.fixtures import demo_timetable

@pytest.fixture
def index():
    return compile_timetable(demo_timetable())

def test_round_zero_and_each_boarding(index):
    result = raptor(index, "O", "Z", t("08:00:00"), max_boardings=3, boarding_slack=60)
    assert "Z" not in result.rows[0]
    assert result.rows[1]["Z"].time == t("08:30:00")
    assert result.rows[2]["Z"].time == t("08:22:00")
    assert [(j.arrival, j.transfers) for j in result.journeys()] == [(t("08:22:00"), 1), (t("08:30:00"), 0)]
    for j in result.journeys():
        j.validate(60)

def test_exactly_catchable_is_allowed(index):
    assert raptor(index, "O", "Z", t("08:00:00"), boarding_slack=60).journeys()[0].arrival == t("08:22:00")

def test_one_second_late_changes_trip(index):
    assert raptor(index, "O", "Z", t("08:00:01"), boarding_slack=60).journeys()[0].arrival == t("08:27:00")

def test_zero_boardings_allows_walk_but_not_ride(index):
    assert raptor(index, "O", "A", t("08:00:00"), max_boardings=0).journeys()[0].arrival == t("08:01:00")
    assert not raptor(index, "O", "Z", t("08:00:00"), max_boardings=0).journeys()

def test_no_route(index):
    assert not raptor(index, "O", "U", 0).journeys()

def test_source_is_destination(index):
    journey = raptor(index, "O", "O", 10).journeys()[0]
    assert (journey.arrival, journey.boardings, journey.legs) == (10, 0, ())
    journey.validate()

def test_exit_is_part_of_destination_arrival(index):
    journey = raptor(index, "O", "Z", t("08:00:00"), boarding_slack=60).journeys()[0]
    assert journey.legs[-1].kind == "EXIT"
    assert journey.arrival - journey.legs[-2].arrival == 60

def test_stairs_are_a_hard_filter_not_a_time_penalty(index):
    strict = raptor(index, "O", "Z", t("08:00:00"), boarding_slack=60)
    open_ = raptor(index, "O", "Z", t("08:00:00"), boarding_slack=60, policy=WalkPolicy(False))
    assert strict.journeys()[0].arrival == t("08:22:00")
    assert open_.journeys()[0].arrival == t("08:21:00")

def test_direction_is_not_invented(index):
    assert not raptor(index, "Z", "O", 0).journeys()

def test_service_times_do_not_wrap_at_midnight():
    j = raptor(compile_timetable(midnight_timetable()), "A", "B", t("23:58:00")).journeys()[0]
    assert j.arrival == t("24:06:00")

def test_round_rows_do_not_mutate(index):
    result = raptor(index, "O", "Z", t("08:00:00"), boarding_slack=60)
    assert result.rows[1]["Z"].time == t("08:30:00")
    with pytest.raises(TypeError):
        result.rows[1]["Z"] = result.rows[2]["Z"]

def test_labels_never_get_worse_with_more_boardings(index):
    result = raptor(index, "O", "Z", t("08:00:00"), max_boardings=8, boarding_slack=60)
    for previous, current in zip(result.rows, result.rows[1:]):
        for stop in previous:
            assert current[stop].key <= previous[stop].key
    assert result.metrics.rounds < 8

def test_route_order_does_not_allow_two_boardings_in_one_round():
    a = Route("a", ("A", "B"), (Trip("t1", (10, 20), (10, 20)),))
    b = Route("b", ("B", "C"), (Trip("t2", (21, 30), (21, 30)),))
    for routes in ((a, b), (b, a)):
        index = compile_timetable(Timetable(("A", "B", "C"), routes))
        assert not raptor(index, "A", "C", 0, max_boardings=1).journeys()
        assert raptor(index, "A", "C", 0, max_boardings=2).journeys()[0].arrival == 30

def test_multiple_walking_edges_are_closed():
    table = Timetable(("A", "B", "C", "D"), (),
                      (Footpath("C", "D", 2), Footpath("B", "C", 2), Footpath("A", "B", 2)))
    assert raptor(compile_timetable(table), "A", "D", 0, max_boardings=0).journeys()[0].arrival == 6

def test_zero_duration_walking_cycle_terminates():
    table = Timetable(("A", "B", "C"), (),
                      (Footpath("A", "B", 0), Footpath("B", "A", 0), Footpath("B", "C", 1)))
    assert raptor(compile_timetable(table), "A", "C", 0).journeys()[0].arrival == 1

def test_can_board_an_earlier_trip_at_a_later_position():
    route = Route("r", ("A", "B", "C"), (Trip("early", (5, 20, 25), (5, 20, 25)),
                                           Trip("late", (15, 30, 35), (15, 30, 35))))
    table = Timetable(("O", "A", "B", "C"), (route,),
                      (Footpath("O", "A", 10), Footpath("O", "B", 1)))
    j = raptor(compile_timetable(table), "O", "C", 0, max_boardings=1).journeys()[0]
    assert j.arrival == 25
    assert j.legs[-1].trip_id == "early"

def test_immutable_input_detaches_caller_lists():
    stops = ["A", "B"]
    table = Timetable(stops, [])
    stops.append("C")
    assert table.stops == ("A", "B")
