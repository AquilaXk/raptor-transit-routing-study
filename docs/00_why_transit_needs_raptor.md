# 00 — Why transit needs RAPTOR

[Back to the guide](../README.md) · [Next: rounds and labels](01_rounds_labels_and_pareto.md)

## Start with the rider, not the acronym

Imagine a rider standing outside a station at 08:00. They need a step-free journey, and they can tolerate one transfer. A useful answer must include the walk to the first platform, the train they can actually board, the transfer path, and the exit at the destination.

The “shortest line on the map” can't answer all of that. It doesn't say whether the first train has left. It doesn't know that a short stairway is unusable for this request. It doesn't tell you whether the arrival time means “train reaches the platform” or “rider completes the exit.”

That's the setting for this repository. The fixture is small on purpose, but the questions match the completed-issue EasySubway target.

## What the round buys you

The starting point is simple: separate journeys by boarding budget. Round zero lets us walk. The next round lets us add one vehicle. Another round lets us add another vehicle.

This gives us a useful invariant and a natural way to expose transfer tradeoffs. In the fixture, one boarding reaches the destination at 08:30; two boardings reach it at 08:22. Calling one universally “best” would throw away the rider's preference before we've represented it.

The [original RAPTOR paper](https://www.microsoft.com/en-us/research/publication/round-based-public-transit-routing/) uses route-oriented scans rather than a Dijkstra-based transit search. Keep the distinction precise: the implementation can still compile indexes, validate a timetable, and run a walking-closure algorithm. “Not Dijkstra-based” is a statement about the transit-routing approach, not a ban on every heap anywhere in a service.

## Decide which RAPTOR model the request needs

Use this table to connect product requirements to executable learning evidence.
Algorithm choice does not establish that the required input is available.

| Request or input condition | Model or admission decision | Lab evidence | EasySubway target |
|---|---|---|---|
| One origin-ready instant; arrival/boarding tradeoff | Point RAPTOR | `example_routing.py`, `test_raptor.py` | Backend #306 |
| Every change across an origin-ready window | Event-driven rRAPTOR | `test_profiles.py`, notebook 02 | Backend #308 |
| Completed arrival deadline or latest connection | Reverse scans plus admitted service-date scope | `reverse.py`, `test_oracle.py` | Backend #309 |
| Preserve low walking, accessibility burden or safe connections | Richer intermediate state and versioned representative policy | `example_walking_tradeoff.py`; full McRAPTOR remains unimplemented | Backend #307 |
| Trips overtake or differ in pickup/drop-off masks | Split compatible patterns before this scan; reject incompatible input | `test_invariants.py` | Data admission and Backend compilation |
| Calendar, occurrence or required access evidence is unresolved | Typed admission failure before claiming a journey | Chapters 03 and 05; multi-date admission remains unimplemented | Backend #310 and Data contracts |

The [source register](04_easysubway_end_to_end.md#source-and-assumption-register)
links these issue targets. The table is a selection guide, not a claim of feature activation.

## A line, a pattern, and a trip are different things

A passenger-facing line name is presentation. A scan pattern is an ordered list of stops that compatible trips share. A trip is one scheduled vehicle run over that pattern.

An express and an all-stop service may share a line name but not a stop pattern. Two trips with different pickup permissions may also need separate scan groups. Our compiler keeps the teaching scan honest by rejecting a group it can't safely scan with one active trip.

That rejection is useful. It turns an implicit assumption into an executable boundary. A production importer may split or compile such services more intelligently, but it must not silently pretend the assumption holds.

## Read EasySubway as two layers

At the inspected Backend main commit, [`RouteTimetableRaptorPlanner.java`](https://github.com/AquilaXk/easysubway-backend/blob/1d80b7afc58bf788dd76846ea7dc86fcb8f1cfaa/backend/src/main/java/com/easysubway/route/application/service/RouteTimetableRaptorPlanner.java) is a concrete code-reading anchor. Its marked-stop collection and pattern scan help make the algorithm tangible.

The completed-issue architecture is the second layer: Journey-native commands, forward and reverse profiles, versioned frontier policy, and request-bound operational evidence. [Backend #25](https://github.com/AquilaXk/easysubway-backend/issues/25) coordinates that target. We assume it is implemented when discussing the intended product, but we do not relabel inactive code as active production.

This distinction prevents two learning mistakes. One is treating a toy algorithm as an entire deployed system. The other is treating every detail of a transitional adapter as an enduring algorithm requirement.

## Try this before reading more

Run `python example_routing.py` from the root. Hide the printed answer and sketch the path yourself. Starting at 08:00, you need 60 seconds for entry and another 60 seconds of boarding slack. Can you board the 08:02 train? Yes: equality is allowed.

At `X`, you arrive at 08:10. The strict transfer takes 120 seconds, followed by 60 seconds of boarding slack. You can catch the 08:13 departure. It arrives at `D` at 08:21, and EXIT adds another minute. The destination arrival is therefore 08:22.

Now add one second to the origin ready time. The first train becomes unreachable. This tiny change is why minute-sampled routing is not an exact departure-profile algorithm.

## Check yourself

Why isn't round two the same as two transfers? Because the first boarding isn't a transfer. What makes `Z` different from `D`? `Z` includes the exit walk; `D` is platform-side. Why not use a real station name for the fixture? These times and paths are invented, and we don't want a teaching example to look like an official itinerary.

You're ready for the next chapter when you can explain those three points without looking at the code.
