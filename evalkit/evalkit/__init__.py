"""evalkit — eval python module library (prototype).

Layers: core (contracts/runner/stats/registry), tracing (vendor adapters ->
CanonicalTrace), inference (targets), metrics (deterministic, judges,
safety), patterns (YAML bundles), reporting.
"""
from .core.types import (CanonicalSpan, CanonicalTrace, CaseResult, EvalCase,
                         MetricResult, RunReport, SpanKind)
from .core.registry import register, resolve, available
from .core.runner import run_suite
from .core import stats
# import for side-effect registration
from .tracing.adapters import vendors as _vendors      # noqa: F401
from .inference import targets as _targets             # noqa: F401
from .metrics import deterministic as _det             # noqa: F401
from .metrics import judges as _judges                 # noqa: F401
from .metrics import safety as _safety                 # noqa: F401
from .metrics import robustness as _rob                 # noqa: F401
from .metrics import scenario as _scen                  # noqa: F401
from .metrics import mas as _mas                        # noqa: F401
