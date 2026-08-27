#!/usr/bin/env python3
"""Build safe E5 MTEB/BEIR evaluation commands without running them."""

from __future__ import annotations

import argparse
import shlex
import sys
from dataclasses import dataclass
from typing import Sequence


MODEL_CONFIG = {
    "e5-small": ("avg", "query_or_passage"),
    "e5-base": ("avg", "query_or_passage"),
    "e5-large": ("avg", "query_or_passage"),
    "e5-small-unsupervised": ("avg", "query_or_passage"),
    "e5-base-unsupervised": ("avg", "query_or_passage"),
    "e5-large-unsupervised": ("avg", "query_or_passage"),
    "e5-small-v2": ("avg", "query_or_passage"),
    "e5-base-v2": ("avg", "query_or_passage"),
    "e5-large-v2": ("avg", "query_or_passage"),
    "multilingual-e5-small": ("avg", "query_or_passage"),
    "multilingual-e5-base": ("avg", "query_or_passage"),
    "multilingual-e5-large": ("avg", "query_or_passage"),
    "multilingual-e5-large-instruct": ("avg", "instruction"),
    "e5-mistral-7b-instruct": ("last", "instruction"),
}

DEFAULT_MTEB_TASK_TYPES = [
    "STS",
    "Summarization",
    "PairClassification",
    "Classification",
    "Reranking",
    "Clustering",
    "BitextMining",
]


@dataclass(frozen=True)
class Plan:
    command: list[str]
    warnings: list[str]
    pool_type: str
    prefix_type: str


def model_basename(model: str) -> str:
    return model.rstrip("/").split("/")[-1]


def detect_model_config(model: str, pool_type: str | None, prefix_type: str | None) -> tuple[str, str, list[str]]:
    base_name = model_basename(model)
    detected_pool, detected_prefix = MODEL_CONFIG.get(base_name, (None, None))
    warnings: list[str] = []

    if detected_pool is None:
        warnings.append(
            f"Unknown E5 model basename {base_name!r}; using explicit/default pool and prefix settings."
        )

    final_pool = pool_type or detected_pool or "avg"
    final_prefix = prefix_type or detected_prefix or "query_or_passage"

    if final_pool not in {"cls", "avg", "last", "weightedavg"}:
        raise SystemExit("--pool-type must be one of: cls, avg, last, weightedavg")
    if final_prefix not in {"query_or_passage", "instruction"}:
        raise SystemExit("--prefix-type must be one of: query_or_passage, instruction")

    if pool_type and detected_pool and pool_type != detected_pool:
        warnings.append(
            f"Explicit --pool-type {pool_type!r} overrides source default {detected_pool!r} for {base_name}."
        )
    if prefix_type and detected_prefix and prefix_type != detected_prefix:
        warnings.append(
            f"Explicit --prefix-type {prefix_type!r} overrides source default {detected_prefix!r} for {base_name}."
        )
    if base_name == "e5-mistral-7b-instruct":
        warnings.append("Mistral E5 requires transformers>=4.34 and is much heavier than encoder E5 models.")

    return final_pool, final_prefix, warnings


def build_beir(args: argparse.Namespace) -> Plan:
    pool_type, prefix_type, warnings = detect_model_config(args.model, args.pool_type, args.prefix_type)
    if args.multilingual:
        raise SystemExit("BEIR mode does not accept --multilingual; use mteb mode for non-retrieval multilingual MTEB.")

    command = [
        "python",
        "-u",
        "mteb_beir_eval.py",
        "--model-name-or-path",
        args.model,
        "--output-dir",
        args.output_dir,
        "--pool-type",
        pool_type,
        "--prefix-type",
        prefix_type,
    ]
    if args.doc_as_query:
        command.append("--doc-as-query")
    if args.dry_run:
        command.append("--dry-run")
    command.extend(args.extra_args)

    warnings.append("BEIR evaluation may download benchmark corpora/model weights and can take hours on full corpora.")
    if prefix_type == "query_or_passage":
        warnings.append("Use query/passage prefixes: queries get 'query: ', corpus gets 'passage: ' unless --doc-as-query applies.")
    else:
        warnings.append("Instruction models use task-specific 'Instruct: ...\\nQuery: ' prompts for queries.")
    return Plan(command=command, warnings=warnings, pool_type=pool_type, prefix_type=prefix_type)


def build_mteb(args: argparse.Namespace) -> Plan:
    pool_type, prefix_type, warnings = detect_model_config(args.model, args.pool_type, args.prefix_type)
    base_name = model_basename(args.model)
    is_multilingual_model = base_name.startswith("multilingual-")

    if args.multilingual and not is_multilingual_model:
        warnings.append("--multilingual was set for a non-multilingual model name; confirm this broad task selection is intended.")
    if is_multilingual_model and not args.multilingual:
        warnings.append("Multilingual E5 model without --multilingual will be restricted to English MTEB tasks by the upstream script.")

    task_types = args.task_types or DEFAULT_MTEB_TASK_TYPES
    command = [
        "python",
        "-u",
        "mteb_except_retrieval_eval.py",
        "--model-name-or-path",
        args.model,
        "--task-types",
        *task_types,
        "--output-dir",
        args.output_dir,
        "--pool-type",
        pool_type,
        "--prefix-type",
        prefix_type,
    ]
    if args.multilingual:
        command.append("--multilingual")
    if args.dry_run:
        command.append("--dry-run")
    command.extend(args.extra_args)

    warnings.append("Non-retrieval MTEB may download datasets/model weights; dry-run narrows tasks but still runs code if executed.")
    if "Classification" in task_types:
        warnings.append("The upstream evaluator disables L2 normalization for Classification tasks.")
    return Plan(command=command, warnings=warnings, pool_type=pool_type, prefix_type=prefix_type)


def shell_join(parts: Sequence[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def print_plan(plan: Plan) -> None:
    print("# Safe E5 evaluation command plan")
    print(f"# pool_type: {plan.pool_type}")
    print(f"# prefix_type: {plan.prefix_type}")
    for warning in plan.warnings:
        print(f"# warning: {warning}")
    print(shell_join(plan.command))


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        description=(
            "Print a validated E5 BEIR or MTEB evaluation command. "
            "This helper never downloads data, loads models, or runs benchmarks."
        )
    )
    subparsers = root.add_subparsers(dest="mode", required=True)

    def add_common(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--model", required=True, help="Hugging Face model id or local model path to place in the command.")
        subparser.add_argument("--output-dir", default="tmp-outputs/", help="Output directory argument for the evaluator.")
        subparser.add_argument("--pool-type", choices=["cls", "avg", "last", "weightedavg"], help="Override detected pooling.")
        subparser.add_argument("--prefix-type", choices=["query_or_passage", "instruction"], help="Override detected prefix mode.")
        subparser.add_argument("--dry-run", action="store_true", help="Append the upstream evaluator's dry-run flag.")
        subparser.add_argument(
            "extra_args",
            nargs=argparse.REMAINDER,
            help="Additional evaluator arguments after --, appended verbatim to the printed command.",
        )

    beir = subparsers.add_parser("beir", help="Build a command for mteb_beir_eval.py retrieval evaluation.")
    add_common(beir)
    beir.add_argument("--doc-as-query", action="store_true", help="Append --doc-as-query for symmetric retrieval tasks.")
    beir.add_argument("--multilingual", action="store_true", help=argparse.SUPPRESS)
    beir.set_defaults(builder=build_beir)

    mteb = subparsers.add_parser("mteb", help="Build a command for non-retrieval MTEB evaluation.")
    add_common(mteb)
    mteb.add_argument("--multilingual", action="store_true", help="Append --multilingual for multilingual MTEB task selection.")
    mteb.add_argument("--task-types", nargs="+", help="Task types to pass after --task-types; defaults match UniLM E5 script.")
    mteb.set_defaults(builder=build_mteb, doc_as_query=False)

    return root


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.extra_args and args.extra_args[0] == "--":
        args.extra_args = args.extra_args[1:]
    plan = args.builder(args)
    print_plan(plan)
    return 0


if __name__ == "__main__":
    sys.exit(main())
