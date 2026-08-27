#!/usr/bin/env python3
"""Dry-run-first Hail Table pipeline template.

By default this script prints a JSON execution plan and does not import Hail,
initialize a backend, read inputs, or write outputs. Use --emit-code to print a
runnable Python pipeline skeleton. Use --execute only after adapting the plan and
choosing a backend in the surrounding environment.
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from typing import Any

TYPE_NAME_TO_CODE = {
    "str": "hl.tstr",
    "string": "hl.tstr",
    "int": "hl.tint32",
    "int32": "hl.tint32",
    "int64": "hl.tint64",
    "float": "hl.tfloat64",
    "float32": "hl.tfloat32",
    "float64": "hl.tfloat64",
    "bool": "hl.tbool",
    "boolean": "hl.tbool",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a safe Hail Table pipeline plan. Default mode is dry-run and "
            "does not import Hail or execute backend actions."
        )
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Print a JSON plan without importing Hail or executing a backend action (default).",
    )
    mode.add_argument(
        "--emit-code",
        action="store_true",
        help="Print a runnable Python Hail pipeline skeleton for adaptation.",
    )
    mode.add_argument(
        "--print-template",
        action="store_true",
        help="Print a short annotated template with common Table operations.",
    )
    mode.add_argument(
        "--execute",
        action="store_true",
        help="Execute the simple import/key/preview/write/export pipeline. Requires a working Hail backend.",
    )

    parser.add_argument("--input", nargs="+", help="Input text table path(s) for hl.import_table.")
    parser.add_argument("--read-table", help="Read an existing native .ht table instead of importing text.")
    parser.add_argument("--output", help="Native .ht output path for Table.write.")
    parser.add_argument("--export", help="Text output path for Table.export.")
    parser.add_argument("--key", nargs="*", default=[], help="Field name(s) to key by after import/read.")
    parser.add_argument("--delimiter", default="\t", help="Text import/export delimiter. Default: tab.")
    parser.add_argument("--missing", default="NA", help="Missing token for hl.import_table. Default: NA.")
    parser.add_argument("--types-json", default="{}", help="JSON map of field name to type name, e.g. '{\"id\": \"str\"}'.")
    parser.add_argument("--impute", action="store_true", help="Pass impute=True to hl.import_table; review inferred identifier types.")
    parser.add_argument("--no-header", action="store_true", help="Pass no_header=True to hl.import_table.")
    parser.add_argument("--quote", help="Quote character for delimited text, commonly '\"'.")
    parser.add_argument("--comment", nargs="*", default=[], help="Comment prefixes for hl.import_table.")
    parser.add_argument("--preview", type=int, default=5, help="Number of rows for bounded preview. Default: 5.")
    parser.add_argument("--overwrite", action="store_true", help="Allow overwriting native output when --execute is used.")
    return parser.parse_args()


def parse_types_json(raw: str) -> dict[str, str]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"--types-json must be valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise SystemExit("--types-json must be a JSON object mapping field names to type names")
    result = {}
    for field, type_name in parsed.items():
        if not isinstance(field, str) or not isinstance(type_name, str):
            raise SystemExit("--types-json keys and values must be strings")
        result[field] = type_name
    return result


def type_code(type_name: str) -> str:
    return TYPE_NAME_TO_CODE.get(type_name.lower(), f"hl.dtype({type_name!r})")


def types_code(types: dict[str, str]) -> str:
    if not types:
        return "{}"
    parts = [f"{field!r}: {type_code(type_name)}" for field, type_name in sorted(types.items())]
    return "{" + ", ".join(parts) + "}"


def build_plan(args: argparse.Namespace, types: dict[str, str]) -> dict[str, Any]:
    source = "read_table" if args.read_table else "import_table"
    warnings = []
    if args.read_table and args.input:
        warnings.append("--read-table is set; --input paths will be ignored")
    if not args.read_table and not args.input:
        warnings.append("no --input or --read-table supplied; emitted code will contain a placeholder input path")
    if args.impute:
        warnings.append("impute=True can infer unsafe numeric types for identifiers; prefer explicit --types-json")
    if args.preview > 100:
        warnings.append("preview is large for a driver-local action; keep preview small unless the data is tiny")
    if not args.output and not args.export:
        warnings.append("no --output or --export supplied; plan performs import/read, optional keying, and preview only")
    return {
        "mode": "dry-run" if not args.emit_code and not args.print_template and not args.execute else "selected",
        "source": source,
        "input": args.input or [],
        "read_table": args.read_table,
        "key": args.key,
        "import_options": {
            "delimiter": args.delimiter,
            "missing": args.missing,
            "types": types,
            "impute": args.impute,
            "no_header": args.no_header,
            "quote": args.quote,
            "comment": args.comment,
        },
        "preview_rows": args.preview,
        "write_output": args.output,
        "export_output": args.export,
        "overwrite": args.overwrite,
        "warnings": warnings,
        "backend_note": "No Hail backend is initialized in dry-run or emit-code mode.",
    }


def source_code_expr(args: argparse.Namespace, types: dict[str, str]) -> str:
    if args.read_table:
        return f"hl.read_table({args.read_table!r})"
    input_expr = repr(args.input[0]) if args.input and len(args.input) == 1 else repr(args.input or ["input.tsv.bgz"])
    options = [
        f"delimiter={args.delimiter!r}",
        f"missing={args.missing!r}",
        f"types={types_code(types)}",
        f"impute={args.impute!r}",
        f"no_header={args.no_header!r}",
    ]
    if args.quote is not None:
        options.append(f"quote={args.quote!r}")
    if args.comment:
        options.append(f"comment={tuple(args.comment)!r}")
    formatted_options = ",\n        ".join(options)
    return f"hl.import_table(\n        {input_expr},\n        {formatted_options},\n    )"


def emit_code(args: argparse.Namespace, types: dict[str, str]) -> str:
    lines = [
        "import hail as hl",
        "",
        "# Initialize Hail before executing, e.g. hl.init(backend=\"local\") or another configured backend.",
        f"ht = {source_code_expr(args, types)}",
    ]
    if args.key:
        key_args = ", ".join(repr(key) for key in args.key)
        lines.append(f"ht = ht.key_by({key_args})")
    lines.extend(
        [
            "",
            "ht.describe()",
            f"ht.head({args.preview}).show(width=120, truncate=80)",
            "",
            "# Add row transformations here, rebinding ht after each table-returning operation.",
            "# ht = ht.annotate(clean_field=...) ",
            "# ht = ht.filter((ht.some_field == value) & hl.is_defined(ht.other_field))",
            "# summary = ht.aggregate(hl.struct(n=hl.agg.count()))",
        ]
    )
    if args.output:
        lines.append(f"ht.write({args.output!r}, overwrite={args.overwrite!r})")
    if args.export:
        lines.append(f"ht.export({args.export!r}, delimiter={args.delimiter!r}, header=True)")
    return "\n".join(lines).rstrip() + "\n"


def print_template() -> None:
    print(
        textwrap.dedent(
            """
            # Hail Table pipeline template
            import hail as hl

            # Choose backend outside this template, then initialize Hail.
            # hl.init(backend="local")

            ht = hl.import_table(
                "samples.tsv.bgz",
                delimiter="\t",
                missing="NA",
                types={"sample_id": hl.tstr, "score": hl.tfloat64},
            )
            ht = ht.key_by("sample_id")
            ht.describe()
            ht.head(5).show(width=120, truncate=80)

            ht = ht.annotate(
                pass_qc=hl.is_defined(ht.score) & (ht.score >= 0),
                score_bucket=hl.case().when(ht.score < 10, "low").default("high"),
            )

            summary = ht.aggregate(hl.struct(
                n=hl.agg.count(),
                mean_score=hl.agg.mean(ht.score),
            ))

            by_bucket = ht.group_by(bucket=ht.score_bucket).aggregate(n=hl.agg.count())

            # Prefer native .ht for Hail intermediates; use export for downstream text.
            # ht.write("prepared_samples.ht", overwrite=True)
            # ht.select("sample_id", "score", "score_bucket").export("scores.tsv.bgz")
            """
        ).strip()
    )


def execute_plan(args: argparse.Namespace, types: dict[str, str]) -> None:
    import hail as hl  # Imported only in explicit execution mode.

    if args.read_table:
        ht = hl.read_table(args.read_table)
    else:
        if not args.input:
            raise SystemExit("--execute requires --input or --read-table")
        hail_types = {field: getattr(hl, TYPE_NAME_TO_CODE[name.lower()].split(".")[1]) for field, name in types.items() if name.lower() in TYPE_NAME_TO_CODE}
        unsupported = {field: name for field, name in types.items() if name.lower() not in TYPE_NAME_TO_CODE}
        if unsupported:
            raise SystemExit(f"--execute supports simple type aliases only; unsupported: {unsupported}")
        ht = hl.import_table(
            args.input[0] if len(args.input) == 1 else args.input,
            delimiter=args.delimiter,
            missing=args.missing,
            types=hail_types,
            impute=args.impute,
            no_header=args.no_header,
            quote=args.quote,
            comment=tuple(args.comment),
        )
    if args.key:
        ht = ht.key_by(*args.key)
    ht.describe()
    ht.head(args.preview).show(width=120, truncate=80)
    if args.output:
        ht.write(args.output, overwrite=args.overwrite)
    if args.export:
        ht.export(args.export, delimiter=args.delimiter, header=True)


def main() -> int:
    args = parse_args()
    types = parse_types_json(args.types_json)
    if args.print_template:
        print_template()
        return 0
    if args.emit_code:
        sys.stdout.write(emit_code(args, types))
        return 0
    if args.execute:
        execute_plan(args, types)
        return 0
    print(json.dumps(build_plan(args, types), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
