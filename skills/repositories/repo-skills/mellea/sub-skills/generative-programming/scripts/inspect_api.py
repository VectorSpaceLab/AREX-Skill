#!/usr/bin/env python3
"""Safely inspect the public generative-programming API.

This helper performs no model call, network access, credential lookup, file
mutation, or backend startup. It is intended for an installed Mellea package.
Example: python inspect_api.py --help
"""

from __future__ import annotations

import argparse
import inspect
from collections.abc import Iterable


def _public_signature(target: object) -> str:
    """Return a stable signature string, or a useful inspection failure."""
    try:
        return str(inspect.signature(target))
    except (TypeError, ValueError) as exc:
        return f"<signature unavailable: {exc}>"


def _targets() -> Iterable[tuple[str, object]]:
    """Yield the public objects needed by this route."""
    from mellea import MelleaSession, generative, start_session
    from mellea.core import ModelOutputThunk, Requirement
    from mellea.stdlib.components import Instruction, Message, SimpleComponent, mify
    from mellea.stdlib.context import ChatContext, SimpleContext
    from mellea.stdlib.functional import aact, act, ainstruct, instruct
    from mellea.stdlib.streaming import stream

    return (
        ("mellea.start_session", start_session),
        ("mellea.generative", generative),
        ("mellea.MelleaSession", MelleaSession),
        ("MelleaSession.instruct", MelleaSession.instruct),
        ("MelleaSession.ainstruct", MelleaSession.ainstruct),
        ("MelleaSession.act", MelleaSession.act),
        ("MelleaSession.aact", MelleaSession.aact),
        ("functional.instruct", instruct),
        ("functional.ainstruct", ainstruct),
        ("functional.act", act),
        ("functional.aact", aact),
        ("Instruction", Instruction),
        ("SimpleComponent", SimpleComponent),
        ("Message", Message),
        ("mify", mify),
        ("SimpleContext", SimpleContext),
        ("ChatContext", ChatContext),
        ("Requirement", Requirement),
        ("ModelOutputThunk", ModelOutputThunk),
        ("stream", stream),
    )


def main() -> int:
    """Parse options and print signatures without invoking generation."""
    parser = argparse.ArgumentParser(
        description="Inspect Mellea generative-programming API signatures safely."
    )
    parser.add_argument(
        "--names-only",
        action="store_true",
        help="Print object names without importing inspect signatures.",
    )
    args = parser.parse_args()

    import mellea

    print(f"mellea {mellea.__version__}")
    for name, target in _targets():
        if args.names_only:
            print(name)
        else:
            print(f"{name}{_public_signature(target)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
