# 04 — A journey through the local lab

[Previous](03_service_days_and_timetables.md) · [Guide](../README.md) · [Next](05_transfers_accessibility_and_identity.md)

## Start with an executable request

Run `python example_routing.py --ready 08:00:00 --max-transfers 2` from the repository root. Everything needed to explain this request is in [the example](../example_routing.py) and the local modules below. All station IDs, trips, times, and identity values are invented.

The request starts outside the station at `O`, ends outside the destination at `Z`, allows at most three boardings, and requires step-free walking. Entry, transfer, and exit walks belong to the journey. Boarding slack is 60 seconds for this example.

## Construct and compile the input

[`demo_timetable`](../src/fixtures.py) supplies three patterns: `R1` from `A` to `X`, `R2` from `Y` to `D`, and `DIRECT` from `A` to `D`. It also supplies the directed walking edges.

[`Timetable`, `Route`, and `Trip`](../src/timetable.py) check identifiers, event chronology, stop references, compatible permission masks, and non-overtaking trip order. They reject invalid input instead of guessing a replacement schedule.

[`compile_timetable`](../src/route_index.py) builds stop-occurrence, departure, and walking indexes. Repeated visits to the same stop retain distinct positions. Compilation makes the supplied timetable searchable; it does not establish that the invented data came from an official source.

## Admit the query before scanning

[`raptor`](../src/raptor.py) validates stop IDs, the ready time, boarding bound, and slack. [`WalkPolicy.admit`](../src/accessibility.py) checks the evidence required by the walking policy. In strict mode, a known stair edge is excluded; unknown or unverified evidence rejects the snapshot.

The [`Work` object](../src/metrics.py) checks work limits, deadlines, and cancellation. Such a failure means the calculation could not complete under its constraints. It must not be reported as a successful search with no route.

## Trace the two useful boarding budgets

Round zero starts with readiness at `O` at 08:00. [Walking closure](../src/footpaths.py) takes the 60-second ENTRY edge to `A`, giving 08:01 platform readiness.

In round one, [the scan](../src/route_scan.py) reads only round-zero labels when boarding. With 60 seconds of slack, the 08:02 `R1` departure is catchable at equality. It reaches `X` at 08:10. The same boarding budget can take `DIRECT` at 08:04, reach `D` at 08:29, and complete EXIT at `Z` at 08:30.

The strict transfer from `X` to `Y` takes 120 seconds. That gives 08:12 readiness at `Y`; another 60 seconds of slack makes the 08:13 `R2` departure catchable in round two. It arrives at `D` at 08:21 and completes EXIT at 08:22.

| Boarding budget | Destination arrival | Why retain it? |
|---|---|---|
| One | 08:30 | No transfer |
| Two | 08:22 | Earlier arrival with one transfer |

Neither choice dominates the other in arrival time and boardings. A display preference should not erase this distinction inside the search.

## Extract a result and check its witness

[`SearchResult.journeys`](../src/round_state.py) extracts nondominated arrival/boarding alternatives from immutable rows. Each journey carries the walking and ride legs that explain its arrival.

The command-line example calls [`Journey.validate`](../src/journey.py), which checks internal chronology. For a stronger check, `validate_against` checks the witness against the actual input: trip identity, ordered stop positions, pickup/drop-off permissions, event times, directed walking edges, and policy-adjusted walking duration.

The following can be run from the repository root:

```python
from src import compile_timetable, demo_timetable, raptor, parse_time, WalkPolicy

timetable = demo_timetable()
policy = WalkPolicy(strict_step_free=True)
result = raptor(
    compile_timetable(timetable), "O", "Z", parse_time("08:00:00"),
    max_boardings=3, boarding_slack=60, policy=policy,
)
for journey in result.journeys():
    journey.validate_against(timetable, boarding_slack=60, policy=policy)
```

[Witness tests](../tests/test_witness.py) deliberately corrupt paths in ways chronology alone cannot detect. A valid witness establishes feasibility under the supplied input; optimality is checked separately using [oracle comparisons](../tests/test_oracle.py).

## Follow related calculations without changing the input story

| Question | Local entry point | Scope |
|---|---|---|
| What changes across a ready-time window? | [`rraptor`](../src/profile.py) | One service date, fixed walking, arrival/boarding objectives, transit-required endpoints |
| When can I start and still meet a deadline? | [`arrive_by`](../src/reverse.py) | Native reverse scans over the supplied timetable |
| What is the last feasible connection? | [`last_connection`](../src/reverse.py) | The supplied service day's event horizon; transit-required endpoints |
| How do delays affect the input? | [`apply_snapshot`](../src/realtime.py) | Validated bundle/date identity, whole-trip nonnegative delays and cancellations |
| Which objective vectors survive? | [`bounded_frontier`](../src/pareto.py) | A separate dominance exercise, not a multicriteria route scan |

An admitted point search with no feasible journey returns an empty result. Invalid input, unusable evidence, unsupported profile domains, and exceeded limits raise typed errors. Neither outcome retrieves a previously successful route.

## What is outside this implementation?

The lab does not load or merge multiple service dates, infer exact departures from headways, verify signed data, or integrate a full multicriteria state into the route scan. [Chapter 03](03_service_days_and_timetables.md), [Chapter 06](06_departure_profiles_and_reverse_search.md), and [Chapter 07](07_multicriteria_frontiers_and_extensions.md) explain the missing input and state requirements.

There is no network API, live data provider, passenger UI, or deployment system. The Python examples and tests are the evidence for the behavior described here.

## Exercise and answer

Move readiness from 08:00:00 to 08:00:01. ENTRY plus boarding slack now reaches 08:02:01, missing the first `R1`. The next `R1` reaches `X` at 08:15; transfer and slack permit `R2` at 08:18, and EXIT completes at 08:27. The 08:30 direct journey remains feasible.

This one-second change links the round scan to the exact event boundaries studied in Chapter 06.
