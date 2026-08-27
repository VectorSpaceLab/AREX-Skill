#!/usr/bin/env python3
"""Inspect MTEB task and benchmark selections without downloading datasets.

This helper imports the installed public ``mteb`` package, applies task and
benchmark selection filters, and prints metadata summaries as JSON or Markdown.
It does not call ``load_data()``, instantiate models, or run ``mteb.evaluate``.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from collections.abc import Iterable, Sequence
from typing import Any


def _split_csv(values: Sequence[str] | None) -> list[str] | None:
    if not values:
        return None
    parsed: list[str] = []
    for value in values:
        parsed.extend(part.strip() for part in value.split(",") if part.strip())
    return parsed or None


def _task_summary(task: Any) -> dict[str, Any]:
    metadata = task.metadata
    return {
        "name": metadata.name,
        "type": metadata.type,
        "category": getattr(metadata, "category", None),
        "languages": sorted(getattr(metadata, "languages", []) or []),
        "scripts": sorted(getattr(metadata, "scripts", []) or []),
        "domains": sorted(getattr(metadata, "domains", []) or []),
        "modalities": sorted(getattr(metadata, "modalities", []) or []),
        "eval_splits": list(getattr(task, "eval_splits", []) or []),
        "hf_subsets": list(getattr(task, "hf_subsets", []) or []),
        "is_public": getattr(metadata, "is_public", None),
        "is_beta": getattr(metadata, "is_beta", None),
        "superseded_by": getattr(metadata, "superseded_by", None),
    }


def _markdown_table(rows: list[dict[str, Any]]) -> str:
    headers = [
        "name",
        "type",
        "languages",
        "scripts",
        "domains",
        "modalities",
        "eval_splits",
        "is_beta",
        "superseded_by",
    ]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        cells = []
        for header in headers:
            value = row.get(header)
            if isinstance(value, list):
                value = ", ".join(str(item) for item in value[:5]) + (", ..." if len(value) > 5 else "")
            cells.append(str(value).replace("|", "\\|"))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _counts(rows: Iterable[dict[str, Any]], key: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        value = row.get(key)
        if isinstance(value, list):
            counter.update(str(item) for item in value)
        elif value is not None:
            counter[str(value)] += 1
    return dict(sorted(counter.items()))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", help="Benchmark name or alias, such as 'MTEB(eng, v2)'.")
    parser.add_argument("--names", nargs="*", help="Task names to select; comma-separated values are accepted.")
    parser.add_argument("--languages", nargs="*", help="ISO 639-3 language codes, such as eng deu.")
    parser.add_argument("--scripts", nargs="*", help="ISO 15924 script codes, such as Latn Cyrl.")
    parser.add_argument("--domains", nargs="*", help="Task domains, such as Legal or Medical.")
    parser.add_argument("--task-types", nargs="*", help="Task types, such as Retrieval or Classification.")
    parser.add_argument("--categories", nargs="*", help="Task categories.")
    parser.add_argument("--modalities", nargs="*", help="Modalities, such as text image audio video.")
    parser.add_argument("--eval-splits", nargs="*", help="Evaluation splits to keep, such as test validation.")
    parser.add_argument("--exclusive-language-filter", action="store_true", help="Keep only multilingual subsets matching the requested languages/scripts exclusively.")
    parser.add_argument("--exclusive-modality-filter", action="store_true", help="Require task modalities to exactly match --modalities.")
    parser.add_argument("--include-superseded", action="store_true", help="Include superseded tasks.")
    parser.add_argument("--include-private", action="store_true", help="Include private or closed tasks in discovery/filtering.")
    parser.add_argument("--include-beta", action="store_true", help="Include beta tasks in discovery/filtering.")
    parser.add_argument("--exclude-aggregate", action="store_true", help="Exclude aggregate tasks.")
    parser.add_argument("--leaderboard", choices=["true", "false", "all"], default="all", help="When listing benchmarks without --benchmark, filter by leaderboard visibility.")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--limit", type=int, default=50, help="Maximum task rows to print; use 0 for no limit.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        import mteb
    except Exception as exc:  # pragma: no cover - depends on user environment
        print(f"Failed to import mteb: {exc}", file=sys.stderr)
        return 2

    names = _split_csv(args.names)
    languages = _split_csv(args.languages)
    scripts = _split_csv(args.scripts)
    domains = _split_csv(args.domains)
    task_types = _split_csv(args.task_types)
    categories = _split_csv(args.categories)
    modalities = _split_csv(args.modalities)
    eval_splits = _split_csv(args.eval_splits)

    try:
        benchmark_info = None
        if args.benchmark:
            benchmark = mteb.get_benchmark(args.benchmark)
            source_tasks = list(benchmark)
            selected_tasks = mteb.filter_tasks(
                source_tasks,
                languages=languages,
                script=scripts,
                domains=domains,
                task_types=task_types,
                categories=categories,
                modalities=modalities,
                exclusive_modality_filter=args.exclusive_modality_filter,
                exclude_superseded=not args.include_superseded,
                exclude_aggregate=args.exclude_aggregate,
                exclude_private=not args.include_private,
                exclude_beta=not args.include_beta,
            )
            benchmark_info = {
                "requested": args.benchmark,
                "name": benchmark.name,
                "aliases": list(benchmark.aliases or []),
                "display_on_leaderboard": benchmark.display_on_leaderboard,
                "total_tasks": len(source_tasks),
            }
        elif names or any([languages, scripts, domains, task_types, categories, modalities, eval_splits]):
            selected_tasks = list(
                mteb.get_tasks(
                    tasks=names,
                    languages=languages,
                    script=scripts,
                    domains=domains,
                    task_types=task_types,
                    categories=categories,
                    exclude_superseded=not args.include_superseded,
                    eval_splits=eval_splits,
                    exclusive_language_filter=args.exclusive_language_filter,
                    modalities=modalities,
                    exclusive_modality_filter=args.exclusive_modality_filter,
                    exclude_aggregate=args.exclude_aggregate,
                    exclude_private=not args.include_private,
                    exclude_beta=not args.include_beta,
                )
            )
        else:
            display_on_leaderboard = None
            if args.leaderboard != "all":
                display_on_leaderboard = args.leaderboard == "true"
            benchmarks = mteb.get_benchmarks(display_on_leaderboard=display_on_leaderboard)
            payload = {
                "mteb_version": getattr(mteb, "__version__", None),
                "benchmark_count": len(benchmarks),
                "benchmarks": [
                    {
                        "name": benchmark.name,
                        "aliases": list(benchmark.aliases or []),
                        "task_count": len(benchmark),
                        "display_on_leaderboard": benchmark.display_on_leaderboard,
                    }
                    for benchmark in benchmarks
                ],
            }
            if args.format == "markdown":
                rows = payload["benchmarks"]
                print("| name | aliases | task_count | display_on_leaderboard |")
                print("| --- | --- | --- | --- |")
                for row in rows:
                    print(
                        f"| {row['name']} | {', '.join(row['aliases'])} | {row['task_count']} | {row['display_on_leaderboard']} |"
                    )
            else:
                print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
    except Exception as exc:
        print(f"Selection failed: {exc}", file=sys.stderr)
        return 1

    rows = [_task_summary(task) for task in selected_tasks]
    limited_rows = rows if args.limit == 0 else rows[: args.limit]
    payload = {
        "mteb_version": getattr(mteb, "__version__", None),
        "benchmark": benchmark_info,
        "selected_count": len(rows),
        "printed_count": len(limited_rows),
        "filters": {
            "names": names,
            "languages": languages,
            "scripts": scripts,
            "domains": domains,
            "task_types": task_types,
            "categories": categories,
            "modalities": modalities,
            "eval_splits": eval_splits,
            "exclusive_language_filter": args.exclusive_language_filter,
            "exclusive_modality_filter": args.exclusive_modality_filter,
            "include_superseded": args.include_superseded,
            "include_private": args.include_private,
            "include_beta": args.include_beta,
            "exclude_aggregate": args.exclude_aggregate,
        },
        "counts": {
            "types": _counts(rows, "type"),
            "languages": _counts(rows, "languages"),
            "scripts": _counts(rows, "scripts"),
            "modalities": _counts(rows, "modalities"),
        },
        "tasks": limited_rows,
    }

    if args.format == "markdown":
        if benchmark_info:
            print(f"# {benchmark_info['name']}\n")
            print(f"Selected {len(rows)} of {benchmark_info['total_tasks']} benchmark tasks.\n")
        else:
            print(f"# MTEB Task Selection\n\nSelected {len(rows)} tasks.\n")
        print(_markdown_table(limited_rows))
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
