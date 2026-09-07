# 02 — Marked-route scanning

**English** | [한국어](02_marked_route_scanning.ko.md)

[Previous](01_rounds_labels_and_pareto.md) · [Guide](../README.md) · [Next](03_service_days_and_timetables.md)

## Find the work that actually changed

After a round, some stops have improved labels and most do not. A route that touches no improved boarding state has no new opportunity to discover in the next round. So collect only affected routes.

For each affected route, remember the earliest marked position in a forward scan. If `A` and `C` both mark the same `A-B-C-D` pattern, scanning from `A` covers both opportunities. Don't scan the same route twice just because two stops marked it.

The lab's [`affected_routes`](../src/route_index.py) returns one position per route: the earliest occurrence touched by an improved stop. [`raptor`](../src/raptor.py) passes that position to [`scan_route`](../src/route_scan.py), so each affected pattern is scanned once per round.

## The active trip is the heart of the scan

Walk along the route's stop positions. When a trip is active, first consider alighting from it. Then look at the previous-round label at this stop. Perhaps reaching this stop independently allows boarding an earlier trip than the one you're currently following.

Here's a tiny counterintuitive example. You can reach `A` at time 10, so you initially board the trip leaving `A` at 15. But a separate walk reaches `B` at time 1. The earlier trip that left `A` at 5 reaches `B` at 20, and you can catch it there. A scan that never switches trips would miss its arrival at `C` at 25.

The test `test_can_board_an_earlier_trip_at_a_later_position` captures this. Read it before reading the implementation; the fixture tells you what the scan must accomplish.

## The assumptions are executable

This implementation admits a group only when all trips share the same stop sequence and pickup/drop-off masks, and are ordered without overtaking in arrivals or departures. Binary search then finds the earliest catchable trip at a position.

Mixed pickup permissions can break a simplistic active-trip scan even when times are sorted. Overtaking can break it too: the earliest departing trip may not be the earliest arriving one downstream. Our `Route` constructor rejects those patterns. A real compiler can partition them, or an alternative scan can explicitly handle them, but ignoring the issue is not an acceptable shortcut.

Realtime can invalidate an otherwise safe static group. After applying a toy overlay, we reconstruct and validate routes again. If the order crosses, the operation fails. It does not secretly switch to a different planner.

## Platform identity and repeated stops

The fixture gives transfer platforms different IDs (`X` and `Y`). That lets the walking edge carry the transfer duration rather than pretending all transfers within a station take the same time.

For a loop pattern such as `A-B-A-C`, both positions of `A` belong in the index. The forward queue uses the minimum marked position; a reverse queue uses the maximum. The route scan still visits each position, so reaching the second occurrence can matter even if the first departure is already gone.

Stop sequence and stable identity are input requirements. Never infer sequence from arbitrary row order or join stops only because their display names look alike. In [timetable.py](../src/timetable.py), a `Route` supplies its ordered stop tuple explicitly; the index retains each occurrence of a repeated stop.

## Walking closure is a separate step

Ride scans produce new alighting labels. Walking closure propagates them across permitted directed edges in the same round. This lab uses a shortest-path heap because its input footpaths need not be transitively closed.

The [paper](https://www.microsoft.com/en-us/research/wp-content/uploads/2012/01/raptor_alenex.pdf) uses its own transfer-model assumptions. Don't copy a single transfer-relaxation pass into an arbitrary graph and assume it remains equivalent. A chain of three edges supplied in reverse order is a simple failing fixture.

## Cost model, without marketing numbers

In one round, the transit work depends on the positions of affected patterns and their trip lookups. The code compiles departure arrays so each lookup is a binary search instead of sorting or constructing the entire array inside the scan. It still copies path tuples for clarity, which can cost much more than compact production predecessor records.

Walking closure has its own graph-search cost. Profile processing multiplies some work by relevant event iterations but can reuse labels. None of this implies a deployed service's latency percentile. Use measured operation counts here, and deployed request-bound evidence for production.

## Read the files in this order

Start with `Compiled` and `affected_routes` in `route_index.py`. Then read `scan_route` in `route_scan.py`. Finish with `raptor.py`, whose job is mostly to preserve the round invariant and orchestrate walking closure.

Before changing the scan, name the assumption you are changing. Then add a fixture that would have failed under the old assumption. “It looked faster” is not a correctness argument.
