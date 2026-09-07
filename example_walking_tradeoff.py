"""A source-checked counterexample, not a multicriteria routing implementation."""
from src import Journey, Leg, compile_timetable, raptor
from src.fixtures import walking_tradeoff_timetable


def low_walking_witness() -> Journey:
    # Explicitly enumerate this path independently of scalar labels/frontier code.
    return Journey("O", "Z", 0, 35, 2, (
        Leg("ENTRY", "O", "B", 0, 1),
        Leg("RIDE", "B", "M", 15, 21, "low-walk"),
        Leg("RIDE", "M", "Z", 25, 35, "later"),
    ))


def main() -> None:
    table = walking_tradeoff_timetable()
    result = raptor(compile_timetable(table), "O", "Z", 0, max_boardings=2)
    fast, = result.journeys()
    low_walk = low_walking_witness()
    for name, journey in (("Scalar result", fast), ("Feasible lost alternative", low_walk)):
        journey.validate_against(table)
        print(f"{name}: arrival={journey.arrival}, boardings={journey.boardings}, "
              f"walking={journey.walking_seconds}")
    print(f"At M, round 1 retains arrival {result.rows[1]['M'].time}; "
          "the later low-walking label at 21 is lost.")
    print("Both paths are feasible. Neither dominates on arrival + boardings + walking.")
    print("Sorting scalar destination results cannot recover the discarded path.")


if __name__ == "__main__":
    main()
