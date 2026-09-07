# 06 — Departure profiles and reverse search

[Previous](05_transfers_accessibility_and_identity.md) · [Guide](../README.md) · [Next](07_multicriteria_frontiers_and_extensions.md)

## A range is not a pile of minute samples

The rider asks, “What changes if I leave between 07:59 and 08:12?” A loop that queries 07:59, 08:00, 08:01, and so on can miss second-level catchability. Even querying many exact times independently doesn't demonstrate the retained-label range algorithm required by the EasySubway target.

[Backend #308](https://github.com/AquilaXk/easysubway-backend/issues/308) asks for actual departure events, latest-to-earliest processing, marked scans, and safe round-label reuse. The runnable `rraptor` follows those mechanics for the lab's restricted model.

## Derive the actual origin-ready events

First compute the shortest allowed walk from the origin to each potential boarding stop. For a trip departure at time `d`, access duration `w`, and boarding slack `b`, the last catchable origin-ready time is:

$$e = d - w - b.$$

Those are thresholds in the origin's clock, not just raw train-departure timestamps. For integer-second queries, catchability changes just after a threshold. An interval ending at `e` includes `e`; the next starts at `e + 1`.

The implementation adds the window end, builds these interval endpoints, then processes them in descending order. It never calls the point router to produce a profile.

## Reuse the right rows

At an earlier ready time, every journey feasible at a later ready time is still feasible: the rider can wait. That lets the earlier iteration start with retained labels rather than an empty state.

The subtle part is the marking comparison. For row `k-1`, compare the new earlier-departure row with **row `k-1` from the previous, later-departure iteration**. Those improvements reveal new boarding opportunities. This is different from comparing adjacent boarding rounds within a single point query.

Current rows still carry the previous boarding-budget row, and boarding still reads only the previous round. Retained labels never authorize an extra same-round boarding.

The code copies dictionaries and immutable path tuples for clarity. It reports reused-label counts, but those counts don't prove production speed. They prove that the implementation actually retains state rather than disguising independent point calls.

## Compress only what you've promised to preserve

Our profile's observable signature is the nondominated set of arrival-time/boarding-count pairs. Adjacent intervals with the same signature can merge. We retain a later feasible witness so an earlier-ready rider can wait for it.

That is narrower than retaining every distinct physical journey, accessibility preference, safety representative, or walking tradeoff. The full target's breakpoint equivalence must follow its complete frontier semantics. A pair of intervals that look equal to the scalar lab might differ under a least-walking or safest-connection objective.

Walking-only arrivals are another trap. If you can walk directly from origin to destination in 300 seconds, arrival is `ready + 300`, not a constant step function. This lab rejects walking-only O/D profiles with `UNSUPPORTED_LAB_PROFILE` rather than claiming constant segments are exact. A full profile engine can represent the necessary affine pieces.

## Arrive-by is a native reverse problem

Start from the destination deadline. Reverse walking closure subtracts the duration of an existing forward edge. Scan each affected pattern from its latest relevant position toward earlier positions. Select the latest trip that can alight in time; at an earlier boarding position, subtract boarding slack to obtain latest platform readiness.

The reverse index doesn't create a physical walkway. If the forward graph contains `X -> Y`, backward feasibility can propagate from `Y` to `X` using that same edge. It cannot conclude that a rider can physically walk from `Y` to `X`.

`arrive_by` returns the latest feasible origin ready time within the admitted lower bound. We then tighten unnecessary waits before walking while retaining the exact chosen rides. This makes the witness's actual destination arrival clear and avoids confusing the deadline with an obligatory arrival time.

## Last connection follows the schedule, not the clock face

The lab finds a conservative finite horizon from the latest admitted trip arrival and a bound on useful walking. A native reverse query then finds the latest feasible origin readiness. Its scope is one supplied service date and transit-required O/D pairs.

This is why the demo's last departure can be 08:10 in a tiny morning-only fixture, and the overnight fixture can arrive at 24:06. Neither result is tied to 23:59 or an arbitrary service-day cutoff.

The completed-issue target in [Backend #309](https://github.com/AquilaXk/easysubway-backend/issues/309) must also handle multi-date occurrence semantics, active calendars, exact frequency treatment, accessibility, realtime applicability, and the full frontier. Those are not silently supplied by the toy horizon calculation.

## The oracle is allowed to be slow

For small windows, the tests evaluate every integer second with the independent state-graph oracle. Reverse tests enumerate all feasible ready times and compare the maximum with the native reverse answer. This is deliberately wasteful and structurally different from the production-style scan.

An exact oracle is a verification tool. It is not a recovery path when the router fails. Never route user traffic through it to hide capacity loss, identity errors, or incomplete implementation.

## Exercise and answer

Why do we inspect `e+1`, not just `e`, when checking boundaries? Equality is boardable at `e`; the change appears immediately after it. Why can a merged interval retain its later witness? Every earlier-ready rider in that interval can wait for the same departure under the lab's fixed, time-independent constraints.

Run [the profile example](../example_journey_profiles.py), then compare `profile.at(08:00:00)` with `profile.at(08:00:01)` in notebook 02.
