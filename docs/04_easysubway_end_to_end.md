# 04 — EasySubway, end to end

[Previous](03_service_days_and_timetables.md) · [Guide](../README.md) · [Next](05_transfers_accessibility_and_identity.md)

## Use the finished-issue system as the destination

This chapter follows the requested assumption: the relevant EasySubway issues have been implemented. That lets us explain where advanced RAPTOR behavior belongs in the intended product.

It does not let us claim those issues are currently closed, that a feature is active on main, or that deployment evidence exists. We keep a separate record of the source code actually inspected.

## What the reviewed Backend implementation shows

This walkthrough uses the [Backend implementation reviewed on September 7, 2026](https://github.com/AquilaXk/easysubway-backend/tree/1d80b7afc58bf788dd76846ea7dc86fcb8f1cfaa). The source links open that exact version, so you can follow the explanation even after the project changes.

The [algorithm decision record](https://github.com/AquilaXk/easysubway-backend/blob/1d80b7afc58bf788dd76846ea7dc86fcb8f1cfaa/tools/routes/route-algorithm-v2-adr.json) declares `MARKED_SINGLE_DEPARTURE_RAPTOR` active for NOW and DEPART_AT. It declares profile modes inactive until PR #312 is terminal. Even the record's `active-production` status string is a code declaration, not a measurement from a deployed instance.

In the reviewed [route planner](https://github.com/AquilaXk/easysubway-backend/blob/1d80b7afc58bf788dd76846ea7dc86fcb8f1cfaa/backend/src/main/java/com/easysubway/route/application/service/RouteTimetableRaptorPlanner.java), the inspected sections include a thread-local scan workspace, marked-stop/pattern collection, one-round-at-a-time scanning, and Journey access/ride/exit projection. The command type in these paths is still `SearchRouteV2Command`.

The same inspected code contains a fixed `PARETO_LIMIT`. We do not copy that number into a “finished target” policy. [Backend #306](https://github.com/AquilaXk/easysubway-backend/issues/306) and [#307](https://github.com/AquilaXk/easysubway-backend/issues/307) explicitly require separation between Journey-native input, internal state bounds, and the public recommendation cap.

| Main-code idea | Teaching file | Important difference |
|---|---|---|
| Compiled route patterns | `route_index.py` | The lab has a tiny in-memory schema, not the bundle compiler |
| Marked patterns and first position | `raptor.py`, `route_scan.py` | The lab's state is arrival/boardings only |
| ENTRY/TRANSFER/EXIT projection | `journey.py`, `footpaths.py` | Synthetic explicit edges, not the full evidence model |
| Realtime generation association | `realtime.py` | A toy single-day overlay, not a provider adapter |
| Scan operation counts | `metrics.py` | Local operations only, not deployed evidence receipts |

## Follow one request through the target

A rider picks origin, destination, time mode, walking pace, mobility/accessibility settings, transfer bound, and the permitted recommendation count. Mobile validates the local input shape and sends the generated contract. It doesn't decide timetable feasibility or choose a different routing authority when the server fails.

Backend admits the closed request, resolves its service-date span, binds one route generation and the applicable realtime/accessibility identities, and selects the server-owned algorithm/frontier policy. It applies resource admission before expensive profile work, honors cancellation, and prevents late publication.

The router then executes the requested query mode. The resulting journeys include real ENTRY and EXIT semantics, the contract's temporal meanings, and the appropriate representatives. The public projection is a separate step from the internal frontier. A three-card UI does not imply three internal labels.

Platform readiness must expose the capability actually activated. A healthy point-query service is not enough to authorize profile traffic. [Platform #148](https://github.com/AquilaXk/easysubway-platform/issues/148) ties temporal readiness to the relevant identities and resource policy.

## Keep the five owners separate

[Hub #2742](https://github.com/AquilaXk/easysubway/issues/2742) describes the cross-repository ownership boundary. [Hub #1393](https://github.com/AquilaXk/easysubway/issues/1393) distinguishes `server-route-bundle` from `map-pack` and `station-catalog-pack`.

Data owns admitted source inputs and immutable products. Backend owns route calculation. Mobile consumes map/catalog data and server journeys without becoming a local backup planner. Platform owns source-free deployment and activation. Hub coordinates the final evidence and product-identity decisions.

That split is why this learning repository should stay a sixth, non-serving study repository. It must not acquire provider credentials, activate K3s workloads, publish real route bundles, or become a hidden shared runtime package.

## Temporal modes have distinct meanings

The target contract in [Backend #305](https://github.com/AquilaXk/easysubway-backend/issues/305) distinguishes point search from profile search. The point wire vocabulary remains NOW/SCHEDULED, with SCHEDULED interpreted canonically as DEPART_AT; that isn't permission to rename the existing public enum.

DEPART_BETWEEN describes a departure window. ARRIVE_BY maximizes feasible origin readiness subject to a completed-destination-arrival deadline. LAST_CONNECTION finds the latest feasible journey in the applicable service-day scope, not an arbitrary 23:59 query.

Keep ready time, actual journey start, first boarding, platform arrival, and destination arrival separate. The lab's reverse search, for example, can return a latest ready time and an actual arrival earlier than the deadline. Those are not contradictory values.

## Source and assumption register

Reviewed on **September 7, 2026**. Main-code observations are pinned; linked issues are evolving target documents. The relevant open issues across the five repositories were reviewed for curriculum scope. This is not a claim to audit every source file, historical closed issue, or deployed service.

| Source | How this guide uses it |
|---|---|
| [Backend main ADR](https://github.com/AquilaXk/easysubway-backend/blob/1d80b7afc58bf788dd76846ea7dc86fcb8f1cfaa/tools/routes/route-algorithm-v2-adr.json) | Verified active/inactive algorithm declarations |
| [Backend main planner](https://github.com/AquilaXk/easysubway-backend/blob/1d80b7afc58bf788dd76846ea7dc86fcb8f1cfaa/backend/src/main/java/com/easysubway/route/application/service/RouteTimetableRaptorPlanner.java) | Verified scan and Journey projection concepts in inspected sections |
| [Backend #25](https://github.com/AquilaXk/easysubway-backend/issues/25) | Coordinated algorithm-suite target |
| [Backend #305](https://github.com/AquilaXk/easysubway-backend/issues/305), [#306](https://github.com/AquilaXk/easysubway-backend/issues/306) | Temporal contract and native execution boundary |
| [Backend #307](https://github.com/AquilaXk/easysubway-backend/issues/307), [#308](https://github.com/AquilaXk/easysubway-backend/issues/308), [#309](https://github.com/AquilaXk/easysubway-backend/issues/309), [#310](https://github.com/AquilaXk/easysubway-backend/issues/310) | Frontier, forward range, reverse, and controls target |
| [Backend #297](https://github.com/AquilaXk/easysubway-backend/issues/297), [#311](https://github.com/AquilaXk/easysubway-backend/issues/311) | Deployed measurement and conditional pruning |
| [Mobile #316](https://github.com/AquilaXk/easysubway-mobile/issues/316), [#7](https://github.com/AquilaXk/easysubway-mobile/issues/7), [#29](https://github.com/AquilaXk/easysubway-mobile/issues/29), [#45](https://github.com/AquilaXk/easysubway-mobile/issues/45) | Temporal UI, explicit failures, access evidence, and separate static products |
| [Data #454](https://github.com/AquilaXk/easysubway-data/issues/454), [#455](https://github.com/AquilaXk/easysubway-data/issues/455), [#452](https://github.com/AquilaXk/easysubway-data/issues/452), [#478](https://github.com/AquilaXk/easysubway-data/issues/478) | Source-native identity, realtime coverage, and operational accessibility evidence |
| [Platform #148](https://github.com/AquilaXk/easysubway-platform/issues/148), [#117](https://github.com/AquilaXk/easysubway-platform/issues/117), [#17](https://github.com/AquilaXk/easysubway-platform/issues/17) | Capability-aware readiness, deployment, and activation boundaries |
| [Hub #2742](https://github.com/AquilaXk/easysubway/issues/2742), [#1393](https://github.com/AquilaXk/easysubway/issues/1393) | Repository and artifact ownership |

No source in this register is a permission to weaken validation, add a provider fallback, or treat candidate artifacts as actively serving artifacts.
