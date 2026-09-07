# 05 — Transfers, accessibility, and identity

[Previous](04_easysubway_end_to_end.md) · [Guide](../README.md) · [Next](06_departure_profiles_and_reverse_search.md)

## Feasible first, preferred second

A strict accessibility constraint is not a preference weight. A stair-only connection doesn't become usable because its travel time is excellent. Similarly, a missing required operational-evidence field doesn't become “probably fine” because an elevator is installed at the station.

EasySubway's target evidence concerns include [Mobile #29](https://github.com/AquilaXk/easysubway-mobile/issues/29) and [Data #478](https://github.com/AquilaXk/easysubway-data/issues/478). Installation evidence and operational verification have different meanings; retrieval time is not automatically the time a facility's operating status was verified.

The lab makes this distinction visible with `step_free` and `verified`. Known stairs are excluded in strict mode. Unknown/unverified edges trigger `ACCESSIBILITY_UNAVAILABLE` under a conservative whole-snapshot admission policy. This is a teaching simplification, not the full production scoping rule.

## Three walks, not one magic transfer number

ENTRY gets the rider from the origin endpoint to the first boarding platform. TRANSFER connects an alighting state to the next boarding state. EXIT gets the rider from the final platform to the destination endpoint.

Our synthetic fixture gives these separate directed edges. It never infers an opposite-direction edge. The duration factor in `WalkPolicy` changes the duration of each permitted edge with an explicit round-up rule. Its default and the example's 60-second boarding slack are lab choices, not EasySubway policy values.

A real state may also need incoming line, platform, transition identity, mobility profile, and path-specific evidence. The pinned Java planner's access-transition handling is a useful reminder that station arrival and next-platform readiness are not interchangeable.

## Explain closure with a bad edge order

Suppose the input lists `C -> D`, then `B -> C`, then `A -> B`. Starting at `A`, one pass reaches only `B`. It misses a perfectly valid walk to `D` because the useful earlier edges have already been visited.

`close_footpaths` processes improvements until there are no more better reachable walking labels. Nonnegative costs and strict improvement ensure zero-duration cycles terminate. The heap uses immutable label objects to discard stale queue entries safely.

A negative walking duration is rejected at input construction. We don't “repair” it to zero, because that would hide the malformed input and might invent a feasible transfer.

## Bind once, then calculate

The target in [Backend #308](https://github.com/AquilaXk/easysubway-backend/issues/308) binds the route bundle, realtime overlay, accessibility snapshot, algorithm identity, frontier policy, and calculation instant across a profile. A result assembled from different generations isn't a coherent journey just because each component was individually valid at some point.

`Snapshot` demonstrates a small part of this: bundle and service date must match, validity is checked, unknown trip occurrences are rejected, and the source timetable isn't mutated. Its update model is intentionally narrow. The core router takes already-admitted input; this repository does not implement a serving endpoint that cryptographically enforces every target identity field.

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

The production target uses its own closed failure contract. The lab error strings are not advertised as a wire-compatible enum list.

Never catch every exception and return the last successful journey. Never re-run a legacy route service to turn a failed authoritative calculation into success. An explicit user retry is a new request with a new valid context, not permission to relabel the failed request.

## Mobile can stay useful without becoming a router

The target preserves a distinction between verified static map/catalog use and authoritative online journey calculation. If a journey request fails, the app can still show its permitted static content. It cannot present an old route as the successful answer to the new request. See [Mobile #7](https://github.com/AquilaXk/easysubway-mobile/issues/7) and [#45](https://github.com/AquilaXk/easysubway-mobile/issues/45).

For temporal modes, Mobile should present server-selected intervals and representatives instead of locally ranking or approximating the timetable. [Mobile #316](https://github.com/AquilaXk/easysubway-mobile/issues/316) provides the target boundary, including accessible temporal controls and state clearing on failure.

## Exercise and answer

Change a known stair edge to `step_free=None`. Why does the strict result become an admission error instead of simply another slow route? In this lab, the whole strict snapshot must have known evidence. That conservative policy prevents “unknown” from being silently treated as “accessible.”

Then explain what production would need to be more selective: scoped evidence requirements tied to the actual admitted graph/query and complete failure semantics, not a blanket `None -> True` conversion.
