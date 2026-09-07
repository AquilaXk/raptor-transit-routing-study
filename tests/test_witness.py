"""Validate witnesses against raw input, independently of the routing indexes."""
from dataclasses import replace
import pytest
from src import Journey, Leg, Timetable, Route, Trip, Footpath, WalkPolicy, RoutingError


@pytest.fixture
def table():
    return Timetable(("O", "A", "B", "Z"), (
        Route("r", ("A", "B"), (Trip("train", (10, 20), (12, 22)),)),
    ), (Footpath("O", "A", 3, "ENTRY"), Footpath("B", "Z", 4, "EXIT")))


@pytest.fixture
def journey():
    return Journey("O", "Z", 0, 24, 1, (
        Leg("ENTRY", "O", "A", 0, 3),
        Leg("RIDE", "A", "B", 12, 20, "train"),
        Leg("EXIT", "B", "Z", 20, 24),
    ))


def test_valid_input_witness(table, journey):
    journey.validate_against(table, boarding_slack=2)


@pytest.mark.parametrize("change", [
    {"trip_id": "NONEXISTENT_TRIP"}, {"trip_id": None},
    {"departure": 11}, {"arrival": 19},
])
def test_reject_structurally_valid_but_nonexistent_ride(table, journey, change):
    forged = replace(journey, legs=(journey.legs[0], replace(journey.legs[1], **change), journey.legs[2]))
    forged.validate(2)  # Chronology alone cannot detect this corruption.
    with pytest.raises(RoutingError, match="INVALID_WITNESS"):
        forged.validate_against(table, boarding_slack=2)


@pytest.mark.parametrize("change", [{"kind": "WALK"}, {"arrival": 2}, {"trip_id": "train"}])
def test_reject_invented_walk(table, journey, change):
    forged = replace(journey, legs=(replace(journey.legs[0], **change), *journey.legs[1:]))
    forged.validate(2)
    with pytest.raises(RoutingError, match="INVALID_WITNESS"):
        forged.validate_against(table, boarding_slack=2)


@pytest.mark.parametrize("mask", ["pickup", "dropoff"])
def test_reject_forbidden_board_or_alight(table, journey, mask):
    trip = replace(table.routes[0].trips[0], **{mask: (False, False)})
    restricted = replace(table, routes=(replace(table.routes[0], trips=(trip,)),))
    with pytest.raises(RoutingError, match="INVALID_WITNESS"):
        journey.validate_against(restricted)


def test_strict_walk_policy_and_directed_edges(table, journey):
    stairs = replace(table, footpaths=(replace(table.footpaths[0], step_free=False), table.footpaths[1]))
    with pytest.raises(RoutingError, match="INVALID_WITNESS"):
        journey.validate_against(stairs)
    journey.validate_against(stairs, policy=WalkPolicy(False))
    reversed_edge = replace(table.footpaths[0], source="A", target="O")
    with pytest.raises(RoutingError, match="INVALID_WITNESS"):
        journey.validate_against(replace(table, footpaths=(reversed_edge, table.footpaths[1])))


def test_walk_factor_uses_request_policy(table):
    walk = Journey("O", "A", 0, 5, 0, (Leg("ENTRY", "O", "A", 0, 5),))
    walk.validate_against(table, policy=WalkPolicy(duration_factor=1.5))
    with pytest.raises(RoutingError, match="INVALID_WITNESS"):
        walk.validate_against(table)


def test_repeated_stop_uses_a_matching_ordered_position_pair():
    table = Timetable(("A", "B", "C"), (Route("loop", ("A", "B", "A", "C"), (
        Trip("loop-trip", (1, 2, 3, 4), (1, 2, 3, 4)),)),))
    Journey("A", "C", 3, 4, 1, (Leg("RIDE", "A", "C", 3, 4, "loop-trip"),)).validate_against(table)
    with pytest.raises(RoutingError, match="INVALID_WITNESS"):
        Journey("C", "A", 0, 4, 1, (Leg("RIDE", "C", "A", 1, 4, "loop-trip"),)).validate_against(table)


def test_unknown_empty_journey_is_not_valid(table):
    with pytest.raises(RoutingError, match="INVALID_WITNESS"):
        Journey("missing", "missing", 0, 0, 0, ()).validate_against(table)
