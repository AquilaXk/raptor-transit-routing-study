# 05 — Transfers, accessibility, and identity

[Previous](04_easysubway_end_to_end.md) · [Guide](../README.md) · [Next](06_departure_profiles_and_reverse_search.md)

## Feasible first, preferred second

A strict accessibility constraint is not a preference weight. A stair-only connection doesn't become usable because its travel time is excellent. Similarly, a missing required operational-evidence field doesn't become “probably fine” because an elevator is installed at the station.

Installation evidence and operational verification have different meanings: knowing an elevator exists does not prove it is operating. Likewise, a retrieval timestamp does not establish when its condition was checked. The lab supplies explicit evidence flags rather than attempting to infer either fact.

The lab makes this distinction visible with `step_free` and `verified`. Known stairs are excluded in strict mode. Unknown/unverified edges trigger `ACCESSIBILITY_UNAVAILABLE` under a conservative whole-snapshot admission policy. This is a teaching simplification, not the full production scoping rule.

## Three walks, not one magic transfer number

ENTRY gets the rider from the origin endpoint to the first boarding platform. TRANSFER connects an alighting state to the next boarding state. EXIT gets the rider from the final platform to the destination endpoint.

Our synthetic fixture gives these separate directed edges. It never infers an opposite-direction edge. The duration factor in `WalkPolicy` changes the duration of each permitted edge with an explicit round-up rule. Its default and the example's 60-second boarding slack are lab choices, not universal transit policy values.

A richer state may need the incoming line, platform, transition identity, mobility profile, and path-specific evidence. In this fixture, arriving at `X` is not readiness at `Y`: the directed transfer consumes 120 seconds before boarding slack is added.

## Explain closure with a bad edge order

Suppose the input lists `C -> D`, then `B -> C`, then `A -> B`. Starting at `A`, one pass reaches only `B`. It misses a perfectly valid walk to `D` because the useful earlier edges have already been visited.

`close_footpaths` processes improvements until there are no more better reachable walking labels. Nonnegative costs and strict improvement ensure zero-duration cycles terminate. The heap uses immutable label objects to discard stale queue entries safely.

A negative walking duration is rejected at input construction. We don't “repair” it to zero, because that would hide the malformed input and might invent a feasible transfer.

## Bind once, then calculate

Keep a single input context throughout a calculation. For a profile, mixing one interval's timetable with another interval's realtime or walking policy can create a set of results that never coexisted. The local profile call receives one compiled timetable and one walking policy for its entire window.

[`Snapshot`](../src/realtime.py) demonstrates part of this: bundle and service date must match, validity is checked, unknown trip occurrences are rejected, and the source timetable is not mutated. Its update model is intentionally narrow. Cryptographic verification and a serving endpoint are not implemented.

That boundary matters. A toy hash field isn't a signed descriptor. A frozen Python object isn't an activation receipt. A local test isn't a deployed request observation.

## Failure is part of the API

Different failures answer different rider and operator questions.

| Situation | Lab behavior | Why it must stay distinct |
|---|---|---|
| Bad time or unknown stop | Typed input error | The query wasn't admitted |
| Unknown strict access evidence | `ACCESSIBILITY_UNAVAILABLE` | Feasibility couldn't be established |
| Stale/mismatched realtime | Typed snapshot error | The requested input identity isn't usable |
| No feasible admitted path | Empty result | The search completed without a route |
| Work/frontier capacity exceeded | Typed capacity error | Completeness could not be preserved |
| Deadline/cancellation | Typed failure | Partial or late work must not publish |

The error codes belong to the local Python API. This repository defines no network response schema.

Never catch every exception and return the last successful journey. Never re-run a legacy route service to turn a failed authoritative calculation into success. An explicit user retry is a new request with a new valid context, not permission to relabel the failed request.

## Presentation must preserve the calculation's meaning

The examples print the current result and print `NO_ROUTE` for an admitted point search with no journey. They do not reuse an earlier successful journey. A future UI should likewise distinguish a completed empty search from a rejected or interrupted calculation.

For a profile, use the intervals returned by [`Profile.at`](../src/profile.py). Do not interpolate an invented train between intervals or replace an error with an old interval. A passenger UI and its interaction behavior are outside this lab.

## Exercise and answer

Change a known stair edge to `step_free=None`. Why does the strict result become an admission error instead of simply another slow route? In this lab, the whole strict snapshot must have known evidence. That conservative policy prevents “unknown” from being silently treated as “accessible.”

Then explain what production would need to be more selective: scoped evidence requirements tied to the actual admitted graph/query and complete failure semantics, not a blanket `None -> True` conversion.
