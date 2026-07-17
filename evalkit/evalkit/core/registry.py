"""evalkit.core.registry — name -> implementation resolution (L0).

Skills and suite YAMLs reference scorers, judges, targets, and adapters by
registered name; nothing above L0 imports implementations directly.
"""
from __future__ import annotations

from typing import Any, Callable

_REGISTRIES: dict[str, dict[str, Any]] = {
    "scorer": {}, "judge": {}, "target": {}, "adapter": {}, "harness": {},
}


def register(kind: str, name: str) -> Callable:
    def deco(obj: Any) -> Any:
        _REGISTRIES[kind][name] = obj
        return obj
    return deco


def resolve(kind: str, name: str) -> Any:
    try:
        return _REGISTRIES[kind][name]
    except KeyError:
        raise KeyError(
            f"No {kind} registered as '{name}'. "
            f"Available: {sorted(_REGISTRIES[kind])}"
        )


def available(kind: str) -> list[str]:
    return sorted(_REGISTRIES[kind])
