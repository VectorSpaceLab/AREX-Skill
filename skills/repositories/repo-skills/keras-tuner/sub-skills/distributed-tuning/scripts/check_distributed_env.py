#!/usr/bin/env python3
"""Check KerasTuner distributed Oracle env-var completeness safely.

This helper intentionally does not import keras_tuner or grpc, create a tuner,
open a socket, or start OracleServicer. It only checks whether the three
KERASTUNER_* values are absent, complete, or partially populated.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Mapping, Optional, Sequence

ENV_NAMES = (
    "KERASTUNER_ORACLE_IP",
    "KERASTUNER_ORACLE_PORT",
    "KERASTUNER_TUNER_ID",
)


def inspect_environment(env: Optional[Mapping[str, str]] = None):
    """Return a serializable completeness report for ``env``.

    Empty or whitespace-only values count as missing. The report deliberately
    does not validate address syntax, port availability, network reachability,
    or the uniqueness of a tuner ID.
    """
    source = os.environ if env is None else env
    present = [
        name
        for name in ENV_NAMES
        if str(source.get(name, "")).strip()
    ]
    missing = [name for name in ENV_NAMES if name not in present]
    if not present:
        state = "absent"
    elif missing:
        state = "incomplete"
    else:
        state = "complete"
    return {
        "state": state,
        "present": present,
        "missing": missing,
        "distributed": state == "complete",
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check KerasTuner distributed Oracle env vars without starting "
            "a server or making a network request."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the report as JSON",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    report = inspect_environment()
    args = _build_parser().parse_args(argv)

    if args.json:
        print(json.dumps(report, sort_keys=True))
    elif report["state"] == "absent":
        print(
            "Distributed Oracle environment is absent; local mode is "
            "possible."
        )
    elif report["state"] == "complete":
        print(
            "Distributed Oracle environment is complete. "
            "Endpoint reachability and ID uniqueness were not tested."
        )
    else:
        print(
            "Incomplete distributed Oracle environment; missing: "
            + ", ".join(report["missing"])
        )

    # No variables is a valid local-mode state. Any partial set is a
    # configuration error; a complete set is ready for a separate launch.
    return 2 if report["state"] == "incomplete" else 0


if __name__ == "__main__":
    raise SystemExit(main())
