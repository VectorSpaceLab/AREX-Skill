#!/usr/bin/env python3
"""Print a tiny DataChain nested schema and its flattened columns.

Purpose: demonstrate logical dot-path signals, physical `__` column names, and
internal optional-model sentinel columns without depending on any repository
checkout or external data.

Example:
    python schema_probe.py
    python schema_probe.py --json
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from io import StringIO
from typing import Any


@dataclass
class SchemaProbe:
    tree: str
    user_signals: list[str]
    db_signals: list[str]
    nested_examples: dict[str, str]
    conversions: dict[str, str]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Show how a tiny DataChain DataModel schema flattens into physical "
            "database columns. No input files or network access are used."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a human-readable report.",
    )
    parser.add_argument(
        "--hide-sentinels",
        action="store_true",
        help="Hide internal Optional[DataModel] sentinel columns from db_signals.",
    )
    return parser


def import_datachain_parts():
    try:
        import datachain as dc  # type: ignore
        from datachain.lib.convert.python_to_sql import python_to_sql  # type: ignore
        from datachain.lib.signal_schema import SignalSchema  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise SystemExit(
            "Could not import DataChain schema utilities. Install DataChain in "
            "the active Python environment before running this probe."
        ) from exc
    return dc, SignalSchema, python_to_sql


def sql_type_name(type_obj: Any) -> str:
    if isinstance(type_obj, type):
        return type_obj.__name__
    return type_obj.__class__.__name__


def collect_probe(include_sentinels: bool = True) -> SchemaProbe:
    dc, SignalSchema, python_to_sql = import_datachain_parts()

    class Usage(dc.DataModel):
        prompt_tokens: int
        completion_tokens: int | None = None

    class Response(dc.DataModel):
        text: str
        usage: Usage

    schema = SignalSchema(
        {
            "id": int,
            "response": Response,
            "maybe_response": Response | None,
            "tags": list[str],
        }
    )

    tree_buf = StringIO()
    schema.print_tree(file=tree_buf)

    db_signals = schema.db_signals(include_sentinels=include_sentinels)
    sentinel = schema.model_sentinel("maybe_response")
    nested_examples = {
        "response.usage.prompt_tokens": "response__usage__prompt_tokens",
        "maybe_response.usage.completion_tokens": (
            "maybe_response__usage__completion_tokens"
        ),
    }
    if sentinel is not None:
        nested_examples["maybe_response._type_tag"] = sentinel

    conversions = {
        "int": sql_type_name(python_to_sql(int)),
        "str | None": sql_type_name(python_to_sql(str | None)),
        "dict[str, int]": sql_type_name(python_to_sql(dict[str, int])),
        "list[str]": sql_type_name(python_to_sql(list[str])),
    }

    return SchemaProbe(
        tree=tree_buf.getvalue().strip(),
        user_signals=schema.user_signals(),
        db_signals=[str(col) for col in db_signals],
        nested_examples=nested_examples,
        conversions=conversions,
    )


def print_human(probe: SchemaProbe) -> None:
    print("Logical schema tree:")
    print(probe.tree)
    print("\nUser-facing dot-path leaves:")
    for signal in probe.user_signals:
        print(f"  - {signal}")
    print("\nPhysical database columns:")
    for signal in probe.db_signals:
        print(f"  - {signal}")
    print("\nNested field examples:")
    for logical, physical in probe.nested_examples.items():
        print(f"  - {logical} -> {physical}")
    print("\nPython-to-SQL conversion examples:")
    for py_type, sql_type in probe.conversions.items():
        print(f"  - {py_type} -> {sql_type}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    probe = collect_probe(include_sentinels=not args.hide_sentinels)
    if args.json:
        print(json.dumps(asdict(probe), indent=2))
    else:
        print_human(probe)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
