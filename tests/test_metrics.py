from time import perf_counter
import pytest
from src import *
from src.metrics import Work, ScanMetrics

def test_metrics_are_observed_operations_not_claimed_provider_zeros():
    metrics = raptor(compile_timetable(demo_timetable()), "O", "Z", 0).metrics
    assert metrics.routes_scanned > 0 and metrics.trip_lookups > 0
    assert metrics.footpaths_examined > 0 and metrics.work_units > 0
    assert not hasattr(metrics, "provider_calls")

def test_metrics_snapshot_is_immutable():
    from dataclasses import FrozenInstanceError
    with pytest.raises(FrozenInstanceError):
        ScanMetrics().rounds = 3

def test_expired_deadline():
    with pytest.raises(RoutingError, match="DEADLINE_EXCEEDED"):
        raptor(compile_timetable(demo_timetable()), "O", "Z", 0, work=Work(deadline=perf_counter()-1))

def test_cancellation_before_publish():
    work = Work()
    work.cancelled = lambda: True
    with pytest.raises(RoutingError, match="CANCELLED"):
        work.snapshot()

def test_counters_are_request_owned():
    index = compile_timetable(demo_timetable())
    first = raptor(index, "O", "Z", 0)
    second = raptor(index, "O", "Z", 0)
    assert first.metrics == second.metrics

def test_point_queries_do_not_claim_profile_reuse():
    assert raptor(compile_timetable(demo_timetable()), "O", "Z", 0).metrics.reused_labels == 0
