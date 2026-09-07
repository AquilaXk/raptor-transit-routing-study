import pytest
from src import *
from src.oracle import exact_profile_seconds
from src.service_time import parse_time as t
from src.metrics import Work

@pytest.fixture
def index():
    return compile_timetable(demo_timetable())

def test_range_reuses_labels_and_covers_window(index):
    start, end = t("07:59:00"), t("08:12:00")
    profile = rraptor(index, "O", "Z", start, end, max_boardings=3, boarding_slack=60)
    assert profile.metrics.reused_labels > 0
    assert profile.segments[0].ready_from == start
    assert profile.segments[-1].ready_through == end
    assert len(profile.segments) == 5
    for left, right in zip(profile.segments, profile.segments[1:]):
        assert left.ready_through + 1 == right.ready_from

def test_range_equals_every_second_independent_oracle(index):
    start, end = t("07:59:50"), t("08:12:10")
    profile = rraptor(index, "O", "Z", start, end, max_boardings=3, boarding_slack=60)
    oracle = exact_profile_seconds(index.timetable, "O", "Z", start, end, max_boardings=3, boarding_slack=60)
    for ready, expected in oracle.items():
        journeys = profile.at(ready)
        assert tuple((j.arrival, j.boardings) for j in journeys) == expected
        for journey in journeys:
            journey.validate(60)

def test_profile_single_second(index):
    ready = t("08:00:00")
    assert rraptor(index, "O", "Z", ready, ready, boarding_slack=60).at(ready)[0].arrival == t("08:22:00")

def test_profile_after_last_event_has_explicit_empty_segment(index):
    profile = rraptor(index, "O", "Z", t("09:00:00"), t("09:00:01"))
    assert len(profile.segments) == 1
    assert not profile.at(t("09:00:00"))

def test_range_rejects_walking_only_domain_instead_of_wrong_constant_segments(index):
    with pytest.raises(RoutingError, match="UNSUPPORTED_LAB_PROFILE"):
        rraptor(index, "O", "A", 0, 100)

def test_profile_outside_window(index):
    profile = rraptor(index, "O", "Z", 0, 100)
    with pytest.raises(RoutingError, match="OUTSIDE_WINDOW"):
        profile.at(101)

def test_invalid_range(index):
    with pytest.raises(RoutingError, match="INVALID_WINDOW"):
        rraptor(index, "O", "Z", 100, 99)

def test_reverse_arrival_deadline_includes_exit(index):
    journey = arrive_by(index, "O", "Z", t("08:22:00"), boarding_slack=60)
    assert journey.ready_at == t("08:00:00")
    assert journey.arrival == t("08:22:00")
    assert arrive_by(index, "O", "Z", t("08:21:59"), boarding_slack=60) is None

def test_reverse_respects_earliest_ready(index):
    assert arrive_by(index, "O", "Z", t("08:22:00"), earliest_ready=t("08:00:01"), boarding_slack=60) is None

def test_reverse_does_not_invent_a_forward_footpath(index):
    assert arrive_by(index, "Z", "O", t("09:00:00")) is None

def test_reverse_can_solve_walking_only(index):
    journey = arrive_by(index, "O", "A", 100)
    assert (journey.ready_at, journey.arrival, journey.boardings) == (40, 100, 0)

def test_last_connection_is_not_midnight(index):
    journey = last_connection(index, "O", "Z", boarding_slack=60)
    assert journey.ready_at == t("08:10:00")
    assert journey.arrival == t("08:38:00")
    journey.validate(60)

def test_last_connection_after_24_hours():
    journey = last_connection(compile_timetable(midnight_timetable()), "A", "B")
    assert journey.ready_at == t("23:59:00")
    assert journey.arrival == t("24:06:00")

def test_cancelled_range_does_not_publish_partial_profile(index):
    with pytest.raises(RoutingError, match="CANCELLED"):
        rraptor(index, "O", "Z", 0, 100, work=Work(cancelled=lambda: True))

def test_reverse_zero_boardings_cannot_ride(index):
    assert arrive_by(index, "O", "Z", t("09:00:00"), max_boardings=0) is None
