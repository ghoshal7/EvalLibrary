"""evalkit.core.stats — reliability and agreement statistics (L0)."""
from __future__ import annotations

import math
import statistics
from math import comb


def pass_at_k(n: int, c: int, k: int) -> float:
    """P(at least one of k sampled attempts passes), given c of n passed."""
    if n <= 0 or k <= 0:
        return 0.0
    k = min(k, n)
    if c >= n:
        return 1.0
    return 1.0 - comb(n - c, k) / comb(n, k)


def pass_hat_k(n: int, c: int, k: int) -> float:
    """tau-bench pass^k: P(all k independent attempts pass) = C(c,k)/C(n,k)."""
    if n <= 0 or k <= 0 or k > n:
        return 0.0
    if c < k:
        return 0.0
    return comb(c, k) / comb(n, k)


def mean_ci95(values: list[float]) -> tuple[float, float]:
    """(mean, half-width of 95% CI). Normal approximation; fine for n>=5."""
    if not values:
        return 0.0, 0.0
    m = statistics.fmean(values)
    if len(values) < 2:
        return m, 0.0
    sd = statistics.stdev(values)
    return m, 1.96 * sd / math.sqrt(len(values))


def cohen_kappa(a: list[int], b: list[int]) -> float:
    """Agreement between two raters over categorical labels."""
    assert len(a) == len(b) and a, "need equal, non-empty label lists"
    n = len(a)
    cats = sorted(set(a) | set(b))
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pe = sum(
        (a.count(c) / n) * (b.count(c) / n) for c in cats
    )
    return 0.0 if pe == 1 else (po - pe) / (1 - pe)
