#!/usr/bin/env python3
"""Generate a Potpie graph/agent-surface Markdown reference from the installed package.

Run this after upgrading Potpie when you need to compare the generated skill's
read/write guidance with the live context-core contract. The helper is read-only
and does not contact the daemon or graph backend.
"""

from __future__ import annotations

import sys
from typing import TextIO

from potpie_context_core.agent_context_port import (
    CONTEXT_RESOLVE_RECIPES,
    context_port_manifest,
)
from potpie_context_core.context_records import (
    PREFERENCE_AUDIENCES,
    PREFERENCE_STRENGTHS,
    SCOPE_KINDS,
    VERIFICATION_OUTCOMES,
)


def emit(stream: TextIO) -> None:
    print("# Potpie Agent Surface (generated)\n", file=stream)
    print(
        "_Generated from the installed `potpie_context_core` package. "
        "Use this as a staleness check for graph-read and graph-write guidance._\n",
        file=stream,
    )

    print("## Intents\n", file=stream)
    print("| Intent | When | Default Includes |", file=stream)
    print("|---|---|---|", file=stream)
    for intent in sorted(CONTEXT_RESOLVE_RECIPES):
        recipe = CONTEXT_RESOLVE_RECIPES[intent]
        when = recipe.get("when", "")
        includes = ", ".join(recipe.get("include", ()))
        print(f"| `{intent}` | {when} | {includes} |", file=stream)
    print(file=stream)

    print("## Includes\n", file=stream)
    families = context_port_manifest()["include_families"]
    for tier, label in (
        ("reader_backed", "Reader-backed"),
        ("planned", "Planned or best-effort"),
    ):
        keys = families.get(tier, [])
        print(f"### {label}\n", file=stream)
        print(", ".join(f"`{key}`" for key in keys) if keys else "_(none)_", file=stream)
        print(file=stream)

    print("## Record-type vocabularies\n", file=stream)
    print("### Scope kinds\n", file=stream)
    print(", ".join(f"`{value}`" for value in sorted(SCOPE_KINDS)), file=stream)
    print(file=stream)
    print("### Preference strengths\n", file=stream)
    print(", ".join(f"`{value}`" for value in sorted(PREFERENCE_STRENGTHS)), file=stream)
    print(file=stream)
    print("### Preference audiences\n", file=stream)
    print(", ".join(f"`{value}`" for value in sorted(PREFERENCE_AUDIENCES)), file=stream)
    print(file=stream)
    print("### Verification outcomes\n", file=stream)
    print(", ".join(f"`{value}`" for value in sorted(VERIFICATION_OUTCOMES)), file=stream)
    print(file=stream)


def main() -> int:
    emit(sys.stdout)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
