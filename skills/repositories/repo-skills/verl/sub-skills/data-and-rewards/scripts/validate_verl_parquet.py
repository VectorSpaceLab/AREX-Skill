#!/usr/bin/env python3
"""Validate core verl post-training parquet schema without importing verl."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REQUIRED_COLUMNS = ("data_source", "prompt", "reward_model", "extra_info")
VALID_ROLES = {"system", "user", "assistant", "tool"}


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if hasattr(value, "as_py"):
        return _jsonable(value.as_py())
    return value


def _read_parquet(path: Path):
    try:
        import pandas as pd  # noqa: PLC0415
    except Exception as exc:  # pragma: no cover - environment-specific
        raise RuntimeError("pandas is required to read parquet files") from exc

    try:
        return pd.read_parquet(path)
    except ImportError as exc:  # pragma: no cover - environment-specific
        raise RuntimeError("pyarrow or another pandas parquet engine is required") from exc


def _is_missing(value: Any) -> bool:
    try:
        import pandas as pd  # noqa: PLC0415

        if value is None:
            return True
        if isinstance(value, (list, tuple, dict)):
            return False
        missing = pd.isna(value)
        return bool(missing) if not hasattr(missing, "any") else bool(missing.all())
    except Exception:
        return value is None


def _validate_prompt(prompt: Any, row_index: int, errors: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> None:
    prompt = _jsonable(prompt)
    if not isinstance(prompt, list):
        errors.append({"row": row_index, "field": "prompt", "message": "prompt must be a list of chat messages"})
        return
    if not prompt:
        errors.append({"row": row_index, "field": "prompt", "message": "prompt must not be empty"})
        return

    for message_index, message in enumerate(prompt):
        location = f"prompt[{message_index}]"
        if not isinstance(message, dict):
            errors.append({"row": row_index, "field": location, "message": "message must be an object"})
            continue
        role = message.get("role")
        if not isinstance(role, str) or not role:
            errors.append({"row": row_index, "field": f"{location}.role", "message": "role must be a non-empty string"})
        elif role not in VALID_ROLES:
            warnings.append({"row": row_index, "field": f"{location}.role", "message": f"unusual role {role!r}"})
        if "content" not in message:
            errors.append({"row": row_index, "field": f"{location}.content", "message": "content is required"})
            continue
        content = message["content"]
        if isinstance(content, str):
            continue
        if isinstance(content, list):
            if not content:
                errors.append({"row": row_index, "field": f"{location}.content", "message": "content parts must not be empty"})
            for part_index, part in enumerate(content):
                part_location = f"{location}.content[{part_index}]"
                if not isinstance(part, dict):
                    errors.append({"row": row_index, "field": part_location, "message": "content part must be an object"})
                    continue
                part_type = part.get("type")
                if not isinstance(part_type, str) or not part_type:
                    errors.append({"row": row_index, "field": f"{part_location}.type", "message": "content part type is required"})
                elif part_type == "text" and "text" not in part:
                    errors.append({"row": row_index, "field": part_location, "message": "text part requires text key"})
                elif part_type in {"image", "video", "audio"} and part_type not in part and f"{part_type}_url" not in part:
                    errors.append({"row": row_index, "field": part_location, "message": f"{part_type} part requires payload key"})
                elif part_type not in {"text", "image", "video", "audio"}:
                    warnings.append({"row": row_index, "field": part_location, "message": f"unusual content part type {part_type!r}"})
            continue
        errors.append({"row": row_index, "field": f"{location}.content", "message": "content must be a string or list of content parts"})


def _validate_row(row: dict[str, Any], row_index: int, args: argparse.Namespace, errors: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> None:
    for column in REQUIRED_COLUMNS:
        if column not in row:
            errors.append({"row": row_index, "field": column, "message": "required column is missing"})

    data_source = _jsonable(row.get("data_source"))
    if _is_missing(data_source) or not isinstance(data_source, str) or not data_source.strip():
        errors.append({"row": row_index, "field": "data_source", "message": "data_source must be a non-empty string"})

    if "prompt" in row and not _is_missing(row.get("prompt")):
        _validate_prompt(row.get("prompt"), row_index, errors, warnings)
    elif "prompt" in row:
        errors.append({"row": row_index, "field": "prompt", "message": "prompt must not be null"})

    reward_model = _jsonable(row.get("reward_model"))
    if _is_missing(reward_model) or not isinstance(reward_model, dict):
        errors.append({"row": row_index, "field": "reward_model", "message": "reward_model must be an object"})
        return

    style = reward_model.get("style")
    if style is not None and not isinstance(style, str):
        errors.append({"row": row_index, "field": "reward_model.style", "message": "style must be a string when present"})
    if args.style_rule_requires_ground_truth and style == "rule" and "ground_truth" not in reward_model:
        errors.append({"row": row_index, "field": "reward_model.ground_truth", "message": "rule reward_model requires ground_truth"})
    if "ground_truth" in reward_model and _is_missing(reward_model.get("ground_truth")):
        errors.append({"row": row_index, "field": "reward_model.ground_truth", "message": "ground_truth must not be null when present"})

    extra_info = _jsonable(row.get("extra_info"))
    if "extra_info" in row and not _is_missing(extra_info) and not isinstance(extra_info, dict):
        errors.append({"row": row_index, "field": "extra_info", "message": "extra_info must be an object or null"})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate core verl post-training parquet schema.")
    parser.add_argument("parquet", type=Path, help="Path to one parquet file to validate.")
    parser.add_argument("--max-rows", type=int, default=1000, help="Maximum rows to validate from the start of the file.")
    parser.add_argument(
        "--style-rule-requires-ground-truth",
        action="store_true",
        help="Fail rows where reward_model.style is 'rule' and reward_model.ground_truth is missing.",
    )
    parser.add_argument("--json-output", type=Path, default=None, help="Optional path to write the validation report as JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.max_rows <= 0:
        parser.error("--max-rows must be positive")
    if not args.parquet.exists():
        parser.error(f"parquet file does not exist: {args.parquet}")
    if not args.parquet.is_file():
        parser.error(f"parquet path is not a file: {args.parquet}")

    try:
        dataframe = _read_parquet(args.parquet)
    except Exception as exc:
        report = {"ok": False, "path": str(args.parquet), "errors": [{"message": str(exc)}], "warnings": []}
        print(json.dumps(report, indent=2, sort_keys=True))
        return 2

    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    columns = list(dataframe.columns)
    row_count = int(len(dataframe))
    checked_count = min(row_count, args.max_rows)

    for missing_column in [column for column in REQUIRED_COLUMNS if column not in columns]:
        errors.append({"row": None, "field": missing_column, "message": "required column is missing"})

    for row_index, row in enumerate(dataframe.head(checked_count).to_dict(orient="records")):
        _validate_row(row, row_index, args, errors, warnings)

    report = {
        "ok": not errors,
        "path": str(args.parquet),
        "row_count": row_count,
        "checked_count": checked_count,
        "columns": columns,
        "errors": errors,
        "warnings": warnings,
    }

    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if args.json_output is not None:
        args.json_output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
