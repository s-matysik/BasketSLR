"""
basketslr.utils
===============
Small deterministic helpers shared across modules.
"""
from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterable


def itemset_to_str(itemset: Iterable[str], joiner: str = " + ") -> str:
    """Canonical, sorted string form of an itemset ('a + b + c')."""
    return joiner.join(sorted(itemset))


@contextmanager
def timer(label: str = "step"):
    """Context manager printing elapsed wall-clock time of a step."""
    t0 = time.perf_counter()
    try:
        yield
    finally:
        print(f"[t] {label}: {time.perf_counter() - t0:.2f}s")
