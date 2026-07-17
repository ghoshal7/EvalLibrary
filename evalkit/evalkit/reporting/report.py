"""evalkit.reporting — human-readable run summaries (L0/L1)."""
from __future__ import annotations
from ..core.types import RunReport


def text_summary(report: RunReport) -> str:
    lines = [
        f"Suite: {report.suite}   run={report.run_id}",
        f"Cases: {report.n_cases} x {report.n_attempts} attempt(s)   "
        f"errors={report.aggregates.get('_errors', 0)}",
        "-" * 56,
    ]
    for name, agg in report.aggregates.items():
        if name.startswith("_"):
            continue
        if isinstance(agg, dict):
            lines.append(f"{name:24s} mean={agg['mean']:.3f}  \u00b1{agg['ci95']:.3f} (n={agg['n']})")
        else:
            lines.append(f"{name:24s} {agg}")
    fails = [
        (cr.case_id, m.metric, m.details)
        for cr in report.case_results for m in cr.metrics if m.passed is False
    ]
    if fails:
        lines.append("-" * 56)
        lines.append(f"Failing checks ({len(fails)}):")
        for cid, metric, det in fails[:10]:
            lines.append(f"  {cid} :: {metric} :: {str(det)[:90]}")
    return "\n".join(lines)
