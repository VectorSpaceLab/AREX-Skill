#!/usr/bin/env python3
"""Smoke-check Potpie's public context-core/context-engine API imports.

This bundled helper is adapted from Potpie's repo-owned mypy smoke target. It is
safe to run against any installed Potpie environment and does not contact the
daemon or a graph backend.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import Mapping

from potpie_context_core.api import GraphDefinition
from potpie_context_engine.api import Candidate


def definition_metadata(definition: GraphDefinition) -> Mapping[str, object]:
    """Return status metadata from a public graph definition."""
    return definition.status_metadata()


def candidate_key(candidate: Candidate) -> str:
    """Return the public candidate key field used by context-engine."""
    return candidate.candidate_key


def _safe_version(dist: str) -> str:
    try:
        return version(dist)
    except PackageNotFoundError:
        return "not-installed"


def main() -> int:
    print("Potpie public context API import smoke: ok")
    for dist in ("potpie", "potpie-context-core", "potpie-context-engine"):
        print(f"{dist}: {_safe_version(dist)}")
    print("GraphDefinition:", GraphDefinition.__module__ + "." + GraphDefinition.__qualname__)
    print("Candidate:", Candidate.__module__ + "." + Candidate.__qualname__)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
