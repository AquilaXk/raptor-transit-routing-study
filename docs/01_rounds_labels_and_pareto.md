# 01 — Rounds, labels, and Pareto choices

**English** | [한국어](01_rounds_labels_and_pareto.ko.md)

[Previous](00_why_transit_needs_raptor.md) · [Guide](../README.md) · [Next](02_marked_route_scanning.md)

## Give every label a sentence

For the point-query lab, `row[k][s]` means: “This is the earliest arrival we've found at stop `s` with at most `k` boardings.” The label also carries the actual boarding count and an immutable tuple of path legs.

The “at most” part explains why a round begins as a copy of the previous one. If a one-boarding journey was feasible, allowing two boardings doesn't invalidate it. More budget must never make the earliest-arrival label worse.

Unreached stops are absent from a row. There is no magic timestamp standing for success, and we never fill an absent label from a cached earlier request.

## The recurrence, one operation at a time

Start with the origin's ready time. Close all allowed walking paths to form round zero. For round `k`, carry round `k-1`, collect routes affected by its improvements, and scan those routes using only round `k-1` for boarding readiness. Write arrival improvements into round `k`. Finally, close walking paths again without increasing the boarding count.

Let $d(t,i)$ and $a(t,i)$ denote trip $t$'s departure and arrival times at
position $i$. For a boardable trip at that position, the condition is:

$$\tau_{k-1}(s_i) + b \le d(t,i).$$

The alighting update at a later permitted position `j` is:

$$\tau_k(s_j) = \min(\tau_k(s_j), a(t,j)).$$

This describes the lab's recurrence. It assumes fixed request-specific walking durations and boarding slack, allowed waiting, admitted trips, and a state that captures the transfer distinctions that matter. It is not a proof that one scalar label handles every mobility or fare rule.

## Read one row; write another

Consider two routes, `A -> B` and `B -> C`. The first arrives at `B` at 08:10, and the second leaves at 08:11.

If the second route reads the `B` label just written in the same round, it can reach `C` while the code still claims one boarding. Reversing route iteration order may then change the answer. That's a serious semantic bug, not an optimization problem.

`test_route_order_does_not_allow_two_boardings_in_one_round` catches it directly. Read [`scan_route`](../src/route_scan.py) and find the line that reads `previous.get(stop)`. That line is part of the correctness argument.

## Keep witnesses stable

A label's path should mean the same thing tomorrow as it meant when the label was created. If a later round overwrites a shared predecessor slot, an old destination label may suddenly reconstruct a different path.

The lab takes an intentionally simple approach: labels and legs are frozen dataclasses, and each improved label stores a tuple of complete legs. This copies more than a compact production predecessor structure would, but it makes aliasing mistakes easy to avoid and inspect. Result rows are read-only mapping views over detached dictionaries.

A production implementation can use immutable predecessor records, arena offsets tied to a generation, or another efficient representation. The obligation is the same: reconstruction must preserve the witness for the label actually selected.

`Journey.validate()` checks chronology and continuity only. Use
`journey.validate_against(timetable, boarding_slack=60, policy=policy)` to check
the witness against the exact admitted, post-overlay input used by the query.
It enumerates raw trip positions and footpaths without using the compiled scan
indexes. Ride IDs, ordered boarding/alighting positions, exact event times,
pickup/drop-off permissions, directed walking kinds and policy-adjusted durations
must all match. This proves input feasibility, not optimality or source provenance.

## Pareto means “not beaten on every relevant axis”

For the basic lab, compare arrival time and boarding count. A journey dominates another when it is no later, uses no more boardings, and is strictly better on at least one of those axes.

| Journey | Destination arrival | Boardings | Keep it? |
|---|---:|---:|---|
| A | 08:22 | 2 | Yes |
| B | 08:30 | 1 | Yes |
| C | 08:35 | 2 | No: A dominates it |
| D | 08:22 | 3 | No: A dominates it |

Boardings are used internally so round zero stays natural. The display transfer count is `max(0, boardings - 1)`.

We intentionally retain one witness for equal arrival/boarding objectives. That's not a promise to retain every physically distinct itinerary. It also doesn't preserve a least-walking or safest-connection representative; those need more state and a broader dominance relation, discussed in [chapter 07](07_multicriteria_frontiers_and_extensions.md).

## Why the scalar label is safe here

Under the lab's assumptions, arriving earlier at the same stop with no more boardings lets you wait for every departure available to a later label. Fixed walking costs preserve that ordering. This is the local reason an earlier label can replace a later one.

Now change the problem. Suppose one label arrived on a platform with a short transfer and another on a different platform with a long transfer. If you collapse both into a single station ID, earlier station arrival may no longer imply better boarding readiness. You must represent the platform or incoming-line state explicitly, not patch the result after the search.

## Exercise and answer

Delete the carry-forward copy in a scratch branch. What invariant fails? Labels can disappear or get worse when the boarding budget increases. Then read the no-improvement stop condition: if a completed round produces no new better state under these assumptions, another identical round cannot introduce a useful new boarding opportunity.

Use the notebook [01 — rounds and journeys](../notebooks/01_rounds_labels_and_journeys.ipynb) to inspect each row. The exercise is complete when you can reconstruct both nondominated journeys and explain why `D`'s time differs from `Z`'s time.

Algorithm background: [Delling, Pajor, and Werneck, 2012](https://www.microsoft.com/en-us/research/publication/round-based-public-transit-routing/). The worked table and implementation choices here are original lab examples.
