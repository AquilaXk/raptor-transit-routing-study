"""Invented data only. These ids, times, and hashes are not real transit data."""
from datetime import date
from .service_time import parse_time as t
from .timetable import Timetable, Route, Trip, Footpath

def demo_timetable() -> Timetable:
    def trip(name: str, *times: str) -> Trip:
        seconds = tuple(t(value) for value in times)
        return Trip(name, seconds, seconds)
    return Timetable(
        stops=("O", "A", "X", "Y", "D", "Z", "U"),
        routes=(
            Route("R1", ("A", "X"), (trip("R1-0802", "08:02:00", "08:10:00"),
                                         trip("R1-0807", "08:07:00", "08:15:00"))),
            Route("R2", ("Y", "D"), (trip("R2-0812", "08:12:00", "08:20:00"),
                                         trip("R2-0813", "08:13:00", "08:21:00"),
                                         trip("R2-0818", "08:18:00", "08:26:00"))),
            Route("DIRECT", ("A", "D"), (trip("D-0804", "08:04:00", "08:29:00"),
                                              trip("D-0812", "08:12:00", "08:37:00"))),
        ),
        footpaths=(Footpath("O", "A", 60, "ENTRY"),
                   Footpath("X", "Y", 120, "TRANSFER"),
                   Footpath("X", "Y", 30, "TRANSFER", step_free=False),
                   Footpath("D", "Z", 60, "EXIT")),
        service_date=date(2026, 9, 7), bundle_id="a" * 64,
    )

def midnight_timetable() -> Timetable:
    seconds = (t("23:59:00"), t("24:06:00"))
    return Timetable(("A", "B"), (Route("NIGHT", ("A", "B"), (Trip("night-1", seconds, seconds),)),))


def walking_tradeoff_timetable() -> Timetable:
    """At M, arrival-only dominance discards the one-second-walking path.

    All times are tiny synthetic service seconds. Equal boarding counts isolate
    walking as the missing objective; no production timetable is implied.
    """
    return Timetable(("O", "A", "B", "M", "Z"), (
        Route("fast-feeder", ("A", "M"), (Trip("fast", (10, 20), (10, 20)),)),
        Route("low-walk-feeder", ("B", "M"), (Trip("low-walk", (15, 21), (15, 21)),)),
        Route("onward", ("M", "Z"), (
            Trip("early", (20, 30), (20, 30)), Trip("later", (25, 35), (25, 35)))),
    ), (Footpath("O", "A", 8, "ENTRY"), Footpath("O", "B", 1, "ENTRY")))
