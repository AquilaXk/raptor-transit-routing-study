# 08 — Correctness, performance, and a study plan

**English** | [한국어](08_correctness_performance_and_study_plan.ko.md)

[Previous](07_multicriteria_frontiers_and_extensions.md) · [Back to the guide](../README.md)

## Build a failure before building an optimization

A useful regression fixture is small enough to explain on a whiteboard. For this lab, that includes a train caught at equality, the same train missed one second later, two routes that must not chain in one round, and a walking chain listed in an inconvenient order.

The tests also cover midnight rollover, repeated stop positions, pickup/drop-off restrictions, rejected overtaking, hard accessibility admission, immutable rows, stale and mismatched realtime, capacity failures, cancellation, and reverse-direction mistakes.

These are observable obligations. A comment saying “fail closed” is not a substitute for a test that forces the failure and checks that no successful result is returned.

## Keep the oracle independent

[`oracle.py`](../src/oracle.py) searches states `(stop, exact_boardings)` using a priority queue. It explicitly enumerates every boardable trip and every permitted later alighting position. It walks edges one at a time. It never calls the production-style route scan, marked-route collector, binary trip selection, range engine, or walking-closure helper.

It shares immutable input types and the declared walking policy because both algorithms must solve the same problem. It does not share the route-search representation or pruning. Tests compare all stop arrivals for every boarding budget, not just the first destination answer.

Seeded random fixtures broaden coverage without making failures irreproducible. Range parity uses every integer second of small windows. Reverse parity finds the latest feasible forward ready time by exhaustive enumeration.

The generator varies repeated-stop patterns, branching and short turns, dwell
times, unequal headways and pickup/drop-off masks while constructing non-overtaking
trips. A fixed seed count is not a measure of input diversity. Differential tests
also validate returned witnesses against raw input with `validate_against`, so a
correct arrival value cannot conceal a nonexistent ride or walking edge. Hand-built
negative witnesses test this checker independently of the route generator.

These checks establish confidence in the restricted lab model. They do not prove multi-date profile semantics, real-source completeness, or full multicriteria representative preservation.

## Measure the thing you actually ran

`ScanMetrics` records local work units, rounds, routes scanned, trip lookups, footpaths examined, label improvements, and retained-label reuse. They are counters produced by this implementation.

There are no synthetic `provider_calls=0`, `fallback_calls=0`, or “production p95” fields. The lab cannot observe those deployed behaviors. An unobservable quantity is not zero.

For a benchmark, distinguish input compilation and the first query from repeated queries on an existing index. Bind the reported counters to the exact fixture and query. [`Work`](../src/metrics.py) also exposes local work limits, deadlines, and cancellation; these are checks in the calculation, not measurements of a deployed service.

If you benchmark this lab, report the Python version, hardware, fixture seed, number of stops/trips, query corpus, and exact command. A faster run on a seven-stop fixture does not predict a production service-level objective.

## A practical learning sequence

**Pass 1: explain it.** Read chapters 00–02 and run `example_routing.py`. Explain why the two destination alternatives survive and why another route cannot board from a label written in the same round.

**Pass 2: break it safely.** In a scratch branch, replace `previous` with `current` in boarding readiness, remove walking closure, or allow an overtaking pattern. Add the smallest regression fixture that exposes each bug. Restore the correct code before proceeding.

**Pass 3: follow time.** Read chapters 03 and 06 and execute notebook 02. Explain a `24:xx` occurrence, an exact-second profile breakpoint, retained rows across departures, and the difference between latest ready time and destination deadline.

**Pass 4: follow the input.** Read chapters 04–05. Trace the fixture through compilation, admission, scanning, and witness validation. Explain why a hash-shaped field is not a signature, and why chronology alone cannot prove a ride exists.

**Pass 5: challenge the frontier.** Read chapter 07 and execute notebook 03. Produce a case where one scalar intermediate label loses a least-walking candidate. Explain which oracle and state representation would be needed before claiming full McRAPTOR.

You understand the lab's boundaries when you can separate algorithm correctness, input admission, witness validity, and measured work without using one as a proxy for the others.

## Settings and contribution policy

The directory layout is a curriculum baseline, not a maximum file count.
Structure checks protect the required learning resources and local links while
allowing new examples, tests and tooling. `.github/workflows/ci.yml` runs tests,
examples and fresh-kernel notebook execution on Python 3.11.14 and 3.14.6.
Check actual GitHub run results before describing a revision as passing CI.

For contributions, make a small feature branch, add a failing fixture, implement
the fix, run affected tests, execute `python tools/verify_notebooks.py` when notebook
behavior changes, and check `git diff --check`. CI runs the full suite. Treat an
unsupported input or algorithm domain as a visible boundary, not an invitation
to fabricate a successful route.

## Learning resource map

| Learning goal | Read | Run or inspect |
|---|---|---|
| Choose the right query model | Chapter 00 application decision table | Point, profile and tradeoff examples |
| Preserve round and scan invariants | Chapters 01–02 | `tests/test_raptor.py`, notebook 01 |
| Resolve service-day semantics | Chapter 03 | `src/service_time.py`, notebook 02 |
| Follow the local calculation | Chapter 04 | `example_routing.py`, `src/raptor.py`, `tests/test_witness.py` |
| Validate accessible path witnesses | Chapter 05 | `tests/test_witness.py`, `Journey.validate_against` |
| Understand range and reverse scans | Chapter 06 | `tests/test_profiles.py`, `tests/test_oracle.py` |
| Expose scalar frontier loss | Chapter 07 | `example_walking_tradeoff.py`, notebook 03 |
| Reproduce verification | This chapter | `.github/workflows/ci.yml`, `tools/verify_notebooks.py` |

Add a resource when it teaches a distinct invariant or supplies independent
verification. Preserve existing learning links; no fixed file count is required.
