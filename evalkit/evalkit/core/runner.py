"""evalkit.core.runner — suite execution engine (L0).

Runs: target(case) -> (output, trace) -> scorers -> CaseResult, with
n_attempts repeats per case for reliability stats, then aggregates.
Scorers are callables: (case, output, trace) -> MetricResult.
"""
from __future__ import annotations

import hashlib
import json
import time
import traceback
from typing import Any, Callable, Optional, Sequence

from .stats import mean_ci95, pass_hat_k, pass_at_k
from .types import CanonicalTrace, CaseResult, EvalCase, MetricResult, RunReport

Scorer = Callable[[EvalCase, Any, Optional[CanonicalTrace]], MetricResult]
Target = Callable[[EvalCase], tuple[Any, Optional[CanonicalTrace]]]


def run_suite(
    suite_name: str,
    cases: Sequence[EvalCase],
    target: Target,
    scorers: Sequence[Scorer],
    n_attempts: int = 1,
    pass_metric: Optional[str] = None,
    manifest: Optional[dict[str, Any]] = None,
) -> RunReport:
    results: list[CaseResult] = []
    for case in cases:
        for attempt in range(n_attempts):
            try:
                output, trace = target(case)
                metrics = [s(case, output, trace) for s in scorers]
                results.append(CaseResult(case.case_id, attempt, output, trace, metrics))
            except Exception:
                results.append(CaseResult(
                    case.case_id, attempt, None, None, [],
                    error=traceback.format_exc(limit=3),
                ))

    run_id = hashlib.sha1(f"{suite_name}{time.time()}".encode()).hexdigest()[:10]
    report = RunReport(
        run_id=run_id,
        suite=suite_name,
        n_cases=len(cases),
        n_attempts=n_attempts,
        case_results=results,
        manifest=manifest or {},
    )
    report.aggregates = _aggregate(report, pass_metric)
    return report


def _aggregate(report: RunReport, pass_metric: Optional[str]) -> dict[str, Any]:
    agg: dict[str, Any] = {}
    by_metric: dict[str, list[float]] = {}
    for cr in report.case_results:
        for m in cr.metrics:
            by_metric.setdefault(m.metric, []).append(m.score)
    for name, vals in by_metric.items():
        mean, hw = mean_ci95(vals)
        agg[name] = {"mean": round(mean, 4), "ci95": round(hw, 4), "n": len(vals)}

    err = sum(1 for cr in report.case_results if cr.error)
    agg["_errors"] = err

    if pass_metric and report.n_attempts > 1:
        # per-case pass counts over attempts -> pass@k / pass^k averaged over cases
        per_case: dict[str, int] = {}
        for cr in report.case_results:
            ok = any(m.metric == pass_metric and m.passed for m in cr.metrics)
            per_case[cr.case_id] = per_case.get(cr.case_id, 0) + (1 if ok else 0)
        n = report.n_attempts
        for k in (1, min(2, n), min(4, n)):
            agg[f"pass@{k}"] = round(
                sum(pass_at_k(n, c, k) for c in per_case.values()) / len(per_case), 4)
            agg[f"pass^{k}"] = round(
                sum(pass_hat_k(n, c, k) for c in per_case.values()) / len(per_case), 4)
    return agg


def to_json(report: RunReport) -> str:
    def default(o: Any) -> Any:
        if hasattr(o, "__dict__"):
            return {k: v for k, v in o.__dict__.items() if k != "trace"}
        return str(o)
    return json.dumps(report, default=default, indent=2)
