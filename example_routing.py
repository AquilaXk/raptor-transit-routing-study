"""Start here: trace a step-free journey through a tiny invented network."""
import argparse
from src import compile_timetable, demo_timetable, raptor, parse_time, format_time, WalkPolicy

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ready", default="08:00:00", help="service-day time, HH:MM:SS")
    parser.add_argument("--max-transfers", type=int, default=2)
    parser.add_argument("--allow-stairs", action="store_true")
    args = parser.parse_args()
    if args.max_transfers < 0:
        parser.error("max-transfers must be nonnegative")
    index = compile_timetable(demo_timetable())
    result = raptor(index, "O", "Z", parse_time(args.ready), max_boardings=args.max_transfers + 1,
                    boarding_slack=60, policy=WalkPolicy(not args.allow_stairs))
    print("SYNTHETIC LAB DATA - not a real passenger itinerary\n")
    for k, row in enumerate(result.rows):
        print(f"At most {k} boardings:", {s: format_time(label.time) for s, label in sorted(row.items())})
    for number, journey in enumerate(result.journeys(), 1):
        journey.validate(60)
        print(f"\nOption {number}: arrive {format_time(journey.arrival)}, "
              f"{journey.transfers} transfers, {journey.walking_seconds}s walking")
        for leg in journey.legs:
            print(f"  {leg.kind:8} {leg.source} -> {leg.target}  "
                  f"{format_time(leg.departure)} - {format_time(leg.arrival)}  {leg.trip_id or ''}")
    if not result.journeys():
        print("NO_ROUTE: no feasible journey in this admitted toy timetable.")
    print("\nMeasured lab operations:", result.metrics)

if __name__ == "__main__":
    main()
