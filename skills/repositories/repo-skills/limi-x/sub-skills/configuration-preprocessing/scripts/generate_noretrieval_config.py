#!/usr/bin/env python3
"""Generate standalone LimiX no-retrieval inference config JSON.

The default preset mirrors the repository helper named
``generate_infenerce_config(args)`` without importing LimiX. A catalog preset is
also provided for agents that want task-shaped defaults matching the observed
non-retrieval config families.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any


HELPER_RETRIEVAL_CONFIG: dict[str, Any] = {
    "use_retrieval": False,
    "retrieval_before_preprocessing": False,
    "calculate_feature_attention": False,
    "calculate_sample_attention": False,
    "subsample_ratio": 1,
    "subsample_type": None,
    "use_type": None,
}

CATALOG_NORETRIEVAL_CONFIG: dict[str, Any] = {
    "use_retrieval": False,
    "retrieval_before_preprocessing": False,
    "calculate_feature_attention": False,
    "calculate_sample_attention": False,
    "subsample_ratio": 0.7,
    "subsample_type": "sample",
    "use_type": "mixed",
}


def pipeline(
    *,
    worker_tags: list[Any],
    discrete_flag: bool,
    original_flag: bool,
    svd_tag: str | None,
    encoding_strategy: str,
    retrieval_config: dict[str, Any],
) -> dict[str, Any]:
    """Build one LimiX pipeline item with safe deep-copied values."""
    return {
        "RebalanceFeatureDistribution": {
            "worker_tags": copy.deepcopy(worker_tags),
            "discrete_flag": discrete_flag,
            "original_flag": original_flag,
            "svd_tag": svd_tag,
        },
        "CategoricalFeatureEncoder": {
            "encoding_strategy": encoding_strategy,
        },
        "FeatureShuffler": {
            "mode": "shuffle",
        },
        "retrieval_config": copy.deepcopy(retrieval_config),
    }


def helper_templates(_task: str) -> list[dict[str, Any]]:
    """Templates equivalent to generate_infenerce_config(args)."""
    return [
        pipeline(
            worker_tags=["quantile"],
            discrete_flag=False,
            original_flag=True,
            svd_tag="svd",
            encoding_strategy="ordinal_strict_feature_shuffled",
            retrieval_config=HELPER_RETRIEVAL_CONFIG,
        ),
        pipeline(
            worker_tags=[None],
            discrete_flag=True,
            original_flag=False,
            svd_tag=None,
            encoding_strategy="numeric",
            retrieval_config=HELPER_RETRIEVAL_CONFIG,
        ),
    ]


def catalog_templates(task: str, *, mvi_compatible: bool) -> list[dict[str, Any]]:
    """Templates matching observed non-retrieval catalog families."""
    if task == "classification":
        return [
            pipeline(
                worker_tags=["quantile_uniform_10"],
                discrete_flag=False,
                original_flag=True,
                svd_tag="svd",
                encoding_strategy="ordinal_strict_feature_shuffled",
                retrieval_config=CATALOG_NORETRIEVAL_CONFIG,
            ),
            pipeline(
                worker_tags=[None],
                discrete_flag=True,
                original_flag=False,
                svd_tag=None,
                encoding_strategy="numeric",
                retrieval_config=CATALOG_NORETRIEVAL_CONFIG,
            ),
        ]

    second_worker = [None] if mvi_compatible else ["power"]
    second_discrete_flag = True if mvi_compatible else False
    return [
        pipeline(
            worker_tags=["quantile_uniform_all_data"],
            discrete_flag=False,
            original_flag=True,
            svd_tag="svd",
            encoding_strategy="ordinal_strict_feature_shuffled",
            retrieval_config=CATALOG_NORETRIEVAL_CONFIG,
        ),
        pipeline(
            worker_tags=second_worker,
            discrete_flag=second_discrete_flag,
            original_flag=False,
            svd_tag=None,
            encoding_strategy="onehot",
            retrieval_config=CATALOG_NORETRIEVAL_CONFIG,
        ),
    ]


def default_repeats(task: str, preset: str) -> int:
    if preset == "helper":
        return 2
    return 2 if task == "classification" else 4


def expand_templates(
    templates: list[dict[str, Any]],
    *,
    repeats: int | None,
    pipelines_count: int | None,
    task: str,
    preset: str,
) -> list[dict[str, Any]]:
    if not templates:
        raise ValueError("internal error: no templates available")

    if pipelines_count is not None:
        if pipelines_count <= 0:
            raise ValueError("--pipelines must be greater than 0")
        base: list[dict[str, Any]] = []
        for template in templates:
            for _ in range(default_repeats(task, preset)):
                base.append(copy.deepcopy(template))
        return [copy.deepcopy(base[i % len(base)]) for i in range(pipelines_count)]

    repeats = default_repeats(task, preset) if repeats is None else repeats
    if repeats <= 0:
        raise ValueError("--repeats must be greater than 0")

    expanded: list[dict[str, Any]] = []
    for template in templates:
        for _ in range(repeats):
            expanded.append(copy.deepcopy(template))
    return expanded


def build_config(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.mvi_compatible and args.task != "regression":
        raise ValueError("--mvi-compatible is only valid with --task regression")
    if args.mvi_compatible and args.preset != "catalog":
        raise ValueError("--mvi-compatible requires --preset catalog")

    templates = (
        helper_templates(args.task)
        if args.preset == "helper"
        else catalog_templates(args.task, mvi_compatible=args.mvi_compatible)
    )
    return expand_templates(
        templates,
        repeats=args.repeats,
        pipelines_count=args.pipelines,
        task=args.task,
        preset=args.preset,
    )


def write_json(data: list[dict[str, Any]], output: str, *, overwrite: bool, indent: int) -> None:
    if output == "-":
        json.dump(data, sys.stdout, indent=indent)
        sys.stdout.write("\n")
        return

    path = Path(output)
    if path.exists() and not overwrite:
        raise FileExistsError(f"output exists: {path}; pass --overwrite to replace it")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=indent)
        handle.write("\n")


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a standalone LimiX JSON inference config with retrieval disabled.",
    )
    parser.add_argument(
        "--task",
        choices=("classification", "regression"),
        required=True,
        help="Task intent. Helper preset uses the same source-helper templates for both tasks; catalog preset selects task-shaped observed defaults.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output JSON path, or '-' for stdout.",
    )
    parser.add_argument(
        "--preset",
        choices=("helper", "catalog"),
        default="helper",
        help="'helper' mirrors generate_infenerce_config(args); 'catalog' emits observed task-specific no-retrieval presets.",
    )
    parser.add_argument(
        "--pipelines",
        type=int,
        default=None,
        help="Total number of pipeline entries to write. Overrides --repeats and cycles through the selected preset order.",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=None,
        help="Repeat each selected template this many times. Defaults: helper=2; catalog classification=2; catalog regression=4.",
    )
    parser.add_argument(
        "--mvi-compatible",
        action="store_true",
        help="With --task regression --preset catalog, emit the MVI-style no-power second template.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing an existing output path.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation spaces.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    try:
        config = build_config(args)
        write_json(config, args.output, overwrite=args.overwrite, indent=args.indent)
    except Exception as exc:  # noqa: BLE001 - CLI should show concise failure messages.
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.output != "-":
        print(f"wrote {len(config)} no-retrieval pipeline(s) to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
