#!/usr/bin/env python3
"""Zero-dependency standalone test runner for the RAPTOR study repository.

Runs the entire test suite using only Python's standard library.
No pip packages or virtual environment required.
"""
from __future__ import annotations

import inspect
from pathlib import Path
import re
import sys
import time
from typing import Any, Callable
import importlib


class RaisesContext:
    def __init__(self, expected_exception: type[BaseException], match: str | None = None):
        self.expected = expected_exception
        self.match = match

    def __enter__(self) -> RaisesContext:
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any) -> bool:
        if exc_type is None:
            raise AssertionError(f"Expected {self.expected.__name__} but no exception was raised")
        if not issubclass(exc_type, self.expected):
            return False
        if self.match and not re.search(self.match, str(exc_val)):
            raise AssertionError(f"Exception message '{exc_val}' did not match pattern '{self.match}'")
        return True


class PytestMock:
    """Minimal shim for pytest APIs used across the test suite."""

    @staticmethod
    def raises(expected_exception: type[BaseException], match: str | None = None) -> RaisesContext:
        return RaisesContext(expected_exception, match)

    @staticmethod
    def fixture(func: Callable[..., Any]) -> Callable[..., Any]:
        return func

    class mark:
        @staticmethod
        def parametrize(argnames: str, argvalues: list[Any] | tuple[Any, ...]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
            def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
                func._parametrize = (argnames, argvalues)  # type: ignore[attr-defined]
                return func
            return decorator


# Install pytest shim before importing test modules
sys.modules["pytest"] = PytestMock()  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TEST_MODULES = [
    "tests.test_components",
    "tests.test_invariants",
    "tests.test_metrics",
    "tests.test_structure",
    "tests.test_walking_tradeoff",
    "tests.test_witness",
    "tests.test_raptor",
    "tests.test_profiles",
    "tests.test_oracle",
]


def run() -> int:
    start_time = time.perf_counter()
    total_passed = 0
    total_failed = 0

    print("Running RAPTOR study test suite (Python standard library runner)...")
    print("-" * 72)

    for mod_name in TEST_MODULES:
        mod = importlib.import_module(mod_name)
        fixtures: dict[str, Callable[[], Any]] = {}
        for name, obj in inspect.getmembers(mod):
            if hasattr(obj, "__name__") and name in ("index", "table", "journey"):
                fixtures[name] = obj

        mod_passed = 0
        mod_failed = 0

        for name, func in inspect.getmembers(mod, inspect.isfunction):
            if not name.startswith("test_"):
                continue
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())

            try:
                if hasattr(func, "_parametrize"):
                    argnames, argvalues = func._parametrize  # type: ignore[attr-defined]
                    argnames_list = [a.strip() for a in argnames.split(",")]
                    for val in argvalues:
                        kwargs = {}
                        if len(argnames_list) == 1:
                            kwargs[argnames_list[0]] = val
                        else:
                            for k, v in zip(argnames_list, val):
                                kwargs[k] = v
                        for p in params:
                            if p in fixtures:
                                kwargs[p] = fixtures[p]()
                        func(**kwargs)
                        mod_passed += 1
                else:
                    kwargs = {}
                    for p in params:
                        if p in fixtures:
                            kwargs[p] = fixtures[p]()
                    func(**kwargs)
                    mod_passed += 1
            except Exception as e:
                print(f"FAIL: {mod_name}.{name}: {e}")
                mod_failed += 1

        total_passed += mod_passed
        total_failed += mod_failed
        status = "OK" if mod_failed == 0 else f"FAILED ({mod_failed})"
        print(f"  {mod_name:<28} {mod_passed:>3} passed  [{status}]")

    elapsed = time.perf_counter() - start_time
    print("-" * 72)
    if total_failed == 0:
        print(f"SUCCESS: {total_passed} tests passed in {elapsed:.2f}s")
        return 0
    else:
        print(f"FAILURE: {total_passed} passed, {total_failed} failed in {elapsed:.2f}s")
        return 1


if __name__ == "__main__":
    sys.exit(run())
