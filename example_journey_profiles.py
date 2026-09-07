"""Explore actual label-reusing range scans and native reverse scans."""
from src import compile_timetable, demo_timetable, rraptor, arrive_by, last_connection, parse_time as t, format_time as f

def main() -> None:
    index = compile_timetable(demo_timetable())
    profile = rraptor(index, "O", "Z", t("07:59:00"), t("08:12:00"), max_boardings=3, boarding_slack=60)
    print("SYNTHETIC DATA / one service date / arrival + boarding objectives\n")
    for segment in profile.segments:
        choices = [(f(a), b) for a, b in segment.signature]
        print(f"Ready {f(segment.ready_from)} through {f(segment.ready_through)}: {choices or 'NO_ROUTE'}")
    print("\nRetained-label reuse:", profile.metrics.reused_labels)
    arrival = arrive_by(index, "O", "Z", t("08:22:00"), earliest_ready=t("07:50:00"),
                         max_boardings=3, boarding_slack=60)
    last = last_connection(index, "O", "Z", max_boardings=3, boarding_slack=60)
    for title, journey in (("Arrive by 08:22", arrival), ("Last connection in this input service day", last)):
        print(f"{title}: " + (f"be ready {f(journey.ready_at)}, arrive {f(journey.arrival)}" if journey else "NO_ROUTE"))
        if journey:
            journey.validate(60)

if __name__ == "__main__":
    main()
