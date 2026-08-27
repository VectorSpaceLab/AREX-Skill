#!/usr/bin/env python3
"""Validate the dataset files referenced by an H2O LLM Studio config."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from llm_studio.src.datasets.conversation_chain_handler import ConversationChainHandler
from llm_studio.src.utils.config_utils import load_config_yaml
from llm_studio.src.utils.data_utils import is_valid_data_frame, load_train_valid_data

NONE_STRINGS = {"", "none", "null"}
CLASSIFICATION_PROBLEM = "text_causal_classification_modeling"
REGRESSION_PROBLEM = "text_causal_regression_modeling"
DPO_PROBLEM = "text_dpo_modeling"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Load an H2O LLM Studio YAML config and validate the referenced "
            "train/validation dataframes without starting training."
        )
    )
    parser.add_argument("--config", required=True, help="Path to a YAML config file.")
    parser.add_argument(
        "--root",
        default=".",
        help=(
            "Project/runtime root used to resolve relative paths and local assets "
            "while loading the config. Defaults to the current directory."
        ),
    )
    parser.add_argument(
        "--expect-problem-type",
        help="Fail if the resolved config problem_type differs from this value.",
    )
    parser.add_argument(
        "--preview-rows",
        type=int,
        default=0,
        help="Print this many rows from required columns after validation. Defaults to 0.",
    )
    return parser.parse_args()


def resolve_under_root(root_arg: str, path_arg: str) -> tuple[Path, Path]:
    root = Path(root_arg).expanduser().resolve()
    raw_path = Path(path_arg).expanduser()
    path = raw_path if raw_path.is_absolute() else root / raw_path
    return root, path.resolve()


def is_none_like(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in NONE_STRINGS
    return False


def as_columns(value: Any) -> list[str]:
    if is_none_like(value):
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if not is_none_like(item)]
    return [str(value)]


def configured_paths(cfg: Any) -> list[tuple[str, str]]:
    paths = [("train", cfg.dataset.train_dataframe)]
    validation = getattr(cfg.dataset, "validation_dataframe", None)
    if getattr(cfg.dataset, "validation_strategy", None) == "custom" and not is_none_like(validation):
        paths.append(("validation", validation))
    return paths


def check_files(cfg: Any) -> None:
    for split, path in configured_paths(cfg):
        if is_none_like(path):
            raise ValueError(f"{split} dataframe path is missing")
        if not is_valid_data_frame(str(path)):
            raise ValueError(
                f"{split} dataframe is not a readable CSV or Parquet file: {path}"
            )


def normalize_deprecated_answer_column(cfg: Any) -> list[str]:
    warnings: list[str] = []
    if cfg.problem_type in {CLASSIFICATION_PROBLEM, REGRESSION_PROBLEM} and isinstance(
        cfg.dataset.answer_column, str
    ):
        warnings.append(
            "answer_column was provided as a string for a classification/regression "
            "config; treating it as a single-column list."
        )
        cfg.dataset.answer_column = [cfg.dataset.answer_column]
    return warnings


def required_columns(cfg: Any) -> list[str]:
    cols: set[str] = set()
    cols.update(as_columns(getattr(cfg.dataset, "prompt_column", None)))
    cols.update(as_columns(getattr(cfg.dataset, "answer_column", None)))

    rejected_answer = getattr(cfg.dataset, "rejected_answer_column", None)
    cols.update(as_columns(rejected_answer))

    rejected_prompt = getattr(cfg.dataset, "rejected_prompt_column", None)
    cols.update(as_columns(rejected_prompt))

    parent_id = getattr(cfg.dataset, "parent_id_column", None)
    if not is_none_like(parent_id):
        cols.add(str(parent_id))
        id_column = getattr(cfg.dataset, "id_column", None)
        if not is_none_like(id_column):
            cols.add(str(id_column))

    return sorted(cols)


def optional_warnings(cfg: Any, df: pd.DataFrame) -> list[str]:
    warnings: list[str] = []
    system_column = getattr(cfg.dataset, "system_column", None)
    if not is_none_like(system_column) and str(system_column) not in df.columns:
        warnings.append(
            f"system_column {system_column!r} is not present; systems will be treated as empty strings."
        )
    return warnings


def check_required_columns(cfg: Any, df: pd.DataFrame, split: str) -> None:
    missing = [col for col in required_columns(cfg) if col not in df.columns]
    if missing:
        raise ValueError(
            f"{split} dataframe is missing configured required columns: {missing}; "
            f"available columns: {list(df.columns)}"
        )


def run_dataset_sanity(cfg: Any, train_df: pd.DataFrame, val_df: pd.DataFrame) -> None:
    if cfg.problem_type == DPO_PROBLEM and not cfg.dataset.limit_chained_samples:
        raise ValueError("DPO requires dataset.limit_chained_samples to stay enabled")

    dataset_cls = cfg.dataset.dataset_class
    dataset_cls.sanity_check(train_df, cfg, mode="train")
    if not val_df.empty:
        dataset_cls.sanity_check(val_df, cfg, mode="validation")


def chain_summary(cfg: Any, df: pd.DataFrame) -> str:
    parent_id = getattr(cfg.dataset, "parent_id_column", None)
    if is_none_like(parent_id):
        return "disabled"
    handler = ConversationChainHandler(df, cfg)
    lengths = [len(ids) for ids in handler.conversation_chain_ids]
    if not lengths:
        return "enabled, 0 chains"
    return (
        f"enabled, chains={len(lengths)}, min_length={min(lengths)}, "
        f"max_length={max(lengths)}"
    )


def print_check_results(results: dict[str, list[Any]]) -> bool:
    titles = results.get("title", [])
    messages = results.get("message", [])
    types = results.get("type", [])
    if not titles:
        print("problem_checks: ok")
        return False

    has_error = False
    print("problem_checks:")
    for level, title, message in zip(types, titles, messages, strict=False):
        has_error = has_error or level == "error"
        print(f"  - [{level}] {title}: {message}")
    return has_error


def print_preview(df: pd.DataFrame, cols: list[str], label: str, rows: int) -> None:
    if rows <= 0:
        return
    keep_cols = [col for col in cols if col in df.columns]
    if not keep_cols:
        return
    print(f"{label}_preview:")
    print(df[keep_cols].head(rows).to_string(index=False, max_colwidth=120))


def main() -> int:
    args = parse_args()
    root, config_path = resolve_under_root(args.root, args.config)
    if not root.exists():
        print(f"Root does not exist: {root}", file=sys.stderr)
        return 2
    if not config_path.is_file():
        print(f"Config file does not exist: {config_path}", file=sys.stderr)
        return 2

    os.chdir(root)

    try:
        cfg = load_config_yaml(str(config_path))
        if args.expect_problem_type and cfg.problem_type != args.expect_problem_type:
            raise ValueError(
                f"resolved problem_type {cfg.problem_type!r} does not match expected "
                f"{args.expect_problem_type!r}"
            )

        normalization_warnings = normalize_deprecated_answer_column(cfg)
        check_files(cfg)
        train_df, val_df = load_train_valid_data(cfg)

        check_required_columns(cfg, train_df, "train")
        if not val_df.empty:
            check_required_columns(cfg, val_df, "validation")
        run_dataset_sanity(cfg, train_df, val_df)

        check_errors = print_check_results(cfg.check())

        cols = required_columns(cfg)
        all_warnings = normalization_warnings + optional_warnings(cfg, train_df)
        for warning in all_warnings:
            print(f"warning: {warning}")

        print(f"config: {config_path}")
        print(f"root: {root}")
        print(f"problem_type: {cfg.problem_type}")
        print(f"dataset_class: {cfg.dataset.dataset_class.__module__}.{cfg.dataset.dataset_class.__name__}")
        print(f"validation_strategy: {cfg.dataset.validation_strategy}")
        print(f"required_columns: {cols}")
        print(f"train_dataframe: {cfg.dataset.train_dataframe}")
        print(f"train_rows_after_split: {len(train_df)}")
        print(f"train_columns: {list(train_df.columns)}")
        print(f"validation_rows_after_split: {len(val_df)}")
        print(f"validation_columns: {list(val_df.columns)}")
        print(f"conversation_chains: {chain_summary(cfg, train_df)}")
        print_preview(train_df, cols, "train", args.preview_rows)
        print_preview(val_df, cols, "validation", args.preview_rows)

        return 1 if check_errors else 0
    except Exception as exc:  # noqa: BLE001 - command-line validator should report clean failures.
        print(f"dataset_validation: failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
