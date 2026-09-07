# 07 — Multicriteria frontiers and extensions

[Previous](06_departure_profiles_and_reverse_search.md) · [Guide](../README.md) · [Next](08_correctness_performance_and_study_plan.md)

## One earlier label can still be the wrong representative

Earliest arrival is useful, but a rider may also care about walking burden, accessible paths, departure time, transfers, and connection slack. Those criteria can disagree.

A label arriving at 08:10 after a long walk might be worse for one rider than an 08:11 label with almost no walking. A connection with ten seconds of remaining slack might be less desirable than one with a comfortable margin. If those distinctions affect a promised representative, discarding the second label at an intermediate stop can destroy the final result.

The local [frontier exercise](../src/pareto.py) makes that a dominance problem: preserve every nondominated objective vector or report insufficient capacity.

## Run a path-loss counterexample

Run `python example_walking_tradeoff.py`, then inspect notebook 03. All numbers
below are invented service seconds; boarding slack is zero.

```text
O --walk 8--> A --fast 10..20--> M --early 20..30--> Z
O --walk 1--> B --low-walk 15..21--> M --later 25..35--> Z
```

At M after one boarding, the scalar row keeps arrival 20 and removes arrival 21.
The final result arrives at 30 with two boardings and eight seconds of walking.
An explicitly enumerated, input-validated alternative arrives at 35 with the same
two boardings and only one second of walking. Neither dominates when walking is
an objective. Sorting the scalar destination results cannot recover that path.

`test_walking_tradeoff.py` checks both witnesses against the raw timetable and
asserts the intermediate label and final objective values. This is one concrete
counterexample, not an unbounded multicriteria oracle or a claim of completeness.

## Dominance follows the direction of each objective

For our standalone `Objective` exercise, later departure and larger minimum slack are better. Earlier arrival, fewer boardings, less walking, and lower accessibility burden are better.

We convert that to a minimizing vector:

```text
(-departure, arrival, boardings, walking, access_burden, -minimum_slack)
```

Candidate A dominates B only if it is no worse on every component and strictly better on at least one. A weighted sum can be a ranking device under an explicit policy, but it is not a substitute for preserving all required nondominated choices.

Hard constraints come first. An inaccessible route doesn't enter the candidate pool and then “win back” feasibility with a good arrival score. The module assumes its inputs are already feasible candidates.

## Capacity is a semantic boundary

`bounded_frontier` removes dominated and equal objective vectors. If the surviving set exceeds capacity, it raises `RAPTOR_FRONTIER_CAPACITY_EXCEEDED` instead of returning a sliced subset.

That is a deliberately conservative teaching policy. The public display count and internal search capacity answer different questions. A future recommendation policy would need to define which alternatives must survive, prove that its pruning preserves them, and fail if capacity prevents that guarantee.

The following shortcut has no such proof:

```python
# Do not use this as an internal frontier policy.
labels = sorted(labels, key=lambda label: label.arrival)[:3]
```

Even if a UI displays three cards, the internal search may need many more labels. Reducing internal state to the public display count mixes two different contracts.

## What full McRAPTOR would add

The basic route scan stores one earliest label per stop and boarding budget. A multicriteria scan generally needs a bag of nondominated labels, a state definition that captures relevant transfer constraints, and dominance checks at each appropriate propagation point.

Adding `bounded_frontier` after the destination search cannot recover alternatives that were already discarded inside the scalar search. That's why this repository labels the module a separate exercise rather than announcing full McRAPTOR support.

To extend the lab properly, start with a tiny counterexample where arrival and walking conflict at an intermediate stop. Build an unbounded multicriteria oracle independent of your bounded production representation. Then introduce the state bag and a named capacity policy. Keep primary and required-representative loss observable.

An independent multicriteria oracle would provide evidence for that extension. The current scalar oracle cannot establish preservation of objectives it does not represent.

## Optimization needs an admission condition

The original [RAPTOR publication](https://www.microsoft.com/en-us/research/publication/round-based-public-transit-routing/) discusses flexible departure times and additional criteria. In this lab, optimization starts with the admitted input model, measured work counters, and an invariant to preserve.

For example, inspect `ScanMetrics` before adding an early-pruning rule. If route scans dominate the measured work, propose a rule that removes specific scans and compare all affected results with the independent oracle. If the counters do not reveal that bottleneck, keep the simpler scan.

This guide does not implement ULTRA, Delay-ULTRA, partitioning, or a new fare objective. Naming an extension is not evidence that its prerequisites or correctness proof hold for the current data.

## Audit a pruning rule before trusting it

For each proposed rule, write down its identifier, the labels it removes, its invariant, the objectives it preserves, its measured count, and the independent oracle comparison. Tie semantic changes to algorithm/frontier identity.

Target-based earliest-arrival pruning can be valid for one objective and invalid for preserving a less-walking or safer alternative. Don't take a pruning rule proved for the basic problem and silently reuse it under a broader product promise.

## Exercise and answer

Create a fast/high-walking objective and a slightly later/low-walking objective in notebook [03](../notebooks/03_frontiers_and_correctness.ipynb). Capacity two should preserve both. Capacity one should fail. Then add an objective worse than the fast one on every axis. It should be removed without using any capacity slot.

Finally, explain why this successful exercise still doesn't prove the route scan is multicriteria. The answer is the intermediate state: the scalar router may already have lost the path that would generate your destination objective.
