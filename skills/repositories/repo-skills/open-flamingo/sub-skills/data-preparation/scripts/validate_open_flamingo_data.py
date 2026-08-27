#!/usr/bin/env python3
"""Safe, bounded validators for OpenFlamingo data-preparation inputs.

The validator intentionally avoids expensive image decoding, tar extraction, or full
training/evaluation reads. Use --max-records to cap JSON/JSONL schema checks.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple


class ValidationError(Exception):
    """Raised for fatal validation setup errors."""


def _json_line_records(handle: Iterable[str], max_records: int) -> Iterator[Dict[str, Any]]:
    checked = 0
    for line_no, line in enumerate(handle, start=1):
        if checked >= max_records:
            break
        stripped = line.strip()
        if not stripped:
            continue
        try:
            obj = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"line {line_no}: invalid JSON: {exc}") from exc
        if not isinstance(obj, dict):
            raise ValidationError(f"line {line_no}: expected a JSON object, got {type(obj).__name__}")
        checked += 1
        yield obj


def _load_json_records_from_plain(path: Path, max_records: int) -> Iterator[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        # Peek at the first non-whitespace character to support both JSONL and
        # small JSON objects/lists. JSONL remains streaming and is preferred for
        # large MMC4 metadata shards.
        prefix = f.read(4096)
        f.seek(0)
        first = next((ch for ch in prefix if not ch.isspace()), "")
        if first == "[":
            data = json.load(f)
            if not isinstance(data, list):
                raise ValidationError("top-level JSON array expected")
            for idx, obj in enumerate(data[:max_records]):
                if not isinstance(obj, dict):
                    raise ValidationError(
                        f"record {idx}: expected a JSON object, got {type(obj).__name__}"
                    )
                yield obj
        elif first == "{":
            # A single JSON object may be either one sample or an object with a
            # common list key. Keep this bounded by only yielding max_records.
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                f.seek(0)
                yield from _json_line_records(f, max_records)
                return
            if isinstance(data, dict) and "records" in data and isinstance(data["records"], list):
                for idx, obj in enumerate(data["records"][:max_records]):
                    if not isinstance(obj, dict):
                        raise ValidationError(
                            f"records[{idx}]: expected a JSON object, got {type(obj).__name__}"
                        )
                    yield obj
            elif isinstance(data, dict):
                yield data
            else:
                raise ValidationError(f"expected JSON object/list, got {type(data).__name__}")
        else:
            yield from _json_line_records(f, max_records)


def _first_json_member(zip_path: Path) -> str:
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = [name for name in zf.namelist() if not name.endswith("/")]
        json_names = [name for name in names if name.lower().endswith((".json", ".jsonl"))]
        if json_names:
            return json_names[0]
        if names:
            return names[0]
        raise ValidationError(f"{zip_path}: archive contains no files")


def _load_json_records(path: Path, max_records: int, zip_member: Optional[str]) -> Iterator[Dict[str, Any]]:
    if not path.exists():
        raise ValidationError(f"input path does not exist: {path}")
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path, "r") as zf:
            member = zip_member or _first_json_member(path)
            if member not in zf.namelist():
                raise ValidationError(f"zip member not found: {member}")
            with zf.open(member, "r") as raw:
                text = io.TextIOWrapper(raw, encoding="utf-8")
                yield from _json_line_records(text, max_records)
    else:
        yield from _load_json_records_from_plain(path, max_records)


def _is_str_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _check_base64_string(value: Any) -> Tuple[bool, str]:
    if not isinstance(value, str) or not value:
        return False, "not a non-empty string"
    try:
        # Validate encoding only; do not open/decode as an image here.
        base64.b64decode(value, validate=True)
    except Exception as exc:  # noqa: BLE001 - any decode failure is a validation signal.
        return False, str(exc)
    return True, "ok"


def _validate_gpt_record(record: Dict[str, Any], idx: int, errors: List[str], warnings: List[str]) -> None:
    example = record.get("example")
    image_map = record.get("image_map")
    if not isinstance(example, str) or not example:
        errors.append(f"record {idx}: ChatGPT sample missing non-empty 'example' string")
    if not isinstance(image_map, dict) or not image_map:
        errors.append(f"record {idx}: ChatGPT sample missing non-empty 'image_map' object")
        return
    for key, value in image_map.items():
        if not isinstance(key, str) or not key.startswith("_!_IMAGE"):
            warnings.append(f"record {idx}: image_map key {key!r} does not look like _!_IMAGEn_!_")
        if not isinstance(value, dict) or "base64_image" not in value:
            errors.append(f"record {idx}: image_map[{key!r}] missing 'base64_image'")
            continue
        ok, reason = _check_base64_string(value["base64_image"])
        if not ok:
            errors.append(f"record {idx}: image_map[{key!r}].base64_image invalid: {reason}")


def _validate_mmc4_record(
    record: Dict[str, Any],
    idx: int,
    require_image_base64: bool,
    errors: List[str],
    warnings: List[str],
) -> Dict[str, int]:
    stats = {"images": 0, "images_with_base64": 0, "images_with_name": 0}

    if "is_gpt" in record:
        _validate_gpt_record(record, idx, errors, warnings)
        return stats

    text_list = record.get("text_list")
    sim_matrix = record.get("similarity_matrix")
    image_info = record.get("image_info")

    if not _is_str_list(text_list) or len(text_list) == 0:
        errors.append(f"record {idx}: missing non-empty string list 'text_list'")
    if not isinstance(image_info, list) or len(image_info) == 0:
        errors.append(f"record {idx}: missing non-empty list 'image_info'")
        image_info = []
    if not isinstance(sim_matrix, list) or len(sim_matrix) == 0:
        errors.append(f"record {idx}: missing non-empty list 'similarity_matrix'")
        sim_matrix = []

    text_count = len(text_list) if isinstance(text_list, list) else None
    image_count = len(image_info) if isinstance(image_info, list) else None
    if isinstance(sim_matrix, list) and image_count is not None and len(sim_matrix) != image_count:
        errors.append(
            f"record {idx}: similarity_matrix has {len(sim_matrix)} rows but image_info has {image_count} entries"
        )
    if isinstance(sim_matrix, list) and text_count is not None:
        for row_no, row in enumerate(sim_matrix[:5]):
            if not isinstance(row, list):
                errors.append(f"record {idx}: similarity_matrix row {row_no} is not a list")
                continue
            if len(row) != text_count:
                errors.append(
                    f"record {idx}: similarity_matrix row {row_no} has {len(row)} columns but text_list has {text_count} entries"
                )
            if not all(isinstance(x, (int, float)) for x in row):
                errors.append(f"record {idx}: similarity_matrix row {row_no} contains non-numeric values")

    for img_no, image in enumerate(image_info):
        stats["images"] += 1
        if not isinstance(image, dict):
            errors.append(f"record {idx}: image_info[{img_no}] is not an object")
            continue
        if "image_name" in image and isinstance(image["image_name"], str) and image["image_name"]:
            stats["images_with_name"] += 1
        if "image_base64" in image:
            ok, reason = _check_base64_string(image["image_base64"])
            if ok:
                stats["images_with_base64"] += 1
            else:
                errors.append(f"record {idx}: image_info[{img_no}].image_base64 invalid: {reason}")
        elif "image_name" not in image:
            errors.append(f"record {idx}: image_info[{img_no}] missing both 'image_name' and 'image_base64'")

    if require_image_base64 and stats["images_with_base64"] == 0:
        errors.append(f"record {idx}: no image_info entries contain image_base64")
    elif not require_image_base64 and stats["images_with_base64"] == 0:
        warnings.append(f"record {idx}: no image_base64 entries found; acceptable before conversion, not after")

    return stats


def validate_mmc4_json(args: argparse.Namespace) -> int:
    path = Path(args.input_path)
    errors: List[str] = []
    warnings: List[str] = []
    checked = 0
    total_images = 0
    total_base64 = 0
    total_names = 0

    try:
        for idx, record in enumerate(_load_json_records(path, args.max_records, args.zip_member), start=1):
            checked += 1
            stats = _validate_mmc4_record(
                record,
                idx,
                args.require_image_base64,
                errors,
                warnings,
            )
            total_images += stats["images"]
            total_base64 += stats["images_with_base64"]
            total_names += stats["images_with_name"]
            if len(errors) >= args.max_errors:
                break
    except (OSError, zipfile.BadZipFile, ValidationError) as exc:
        errors.append(str(exc))

    report = {
        "mode": "mmc4-json",
        "input_path": str(path),
        "checked_records": checked,
        "max_records": args.max_records,
        "image_info_entries": total_images,
        "image_names": total_names,
        "image_base64_entries": total_base64,
        "warnings": warnings[: args.max_errors],
        "errors": errors[: args.max_errors],
        "ok": checked > 0 and not errors,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


def validate_vqa_predictions(args: argparse.Namespace) -> int:
    path = Path(args.input_path)
    errors: List[str] = []
    warnings: List[str] = []
    checked = 0
    total_records: Optional[int] = None
    seen: Dict[str, int] = {}

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValidationError(f"expected a JSON list, got {type(data).__name__}")
        total_records = len(data)
        for idx, item in enumerate(data[: args.max_records], start=1):
            checked += 1
            if not isinstance(item, dict):
                errors.append(f"record {idx}: expected object, got {type(item).__name__}")
                continue
            if "question_id" not in item:
                errors.append(f"record {idx}: missing 'question_id'")
                continue
            qid = str(item["question_id"])
            if qid in seen:
                errors.append(f"record {idx}: duplicate question_id {item['question_id']!r} first seen at record {seen[qid]}")
            else:
                seen[qid] = idx
            if "answer" not in item:
                errors.append(f"record {idx}: missing 'answer'")
            elif not isinstance(item["answer"], str):
                errors.append(f"record {idx}: answer must be a string, got {type(item['answer']).__name__}")
            elif "\n" in item["answer"] or "\t" in item["answer"]:
                warnings.append(f"record {idx}: answer contains newline/tab; filler will normalize whitespace")
            if len(errors) >= args.max_errors:
                break
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        errors.append(str(exc))

    report = {
        "mode": "vqa-predictions",
        "input_path": str(path),
        "total_records": total_records,
        "checked_records": checked,
        "max_records": args.max_records,
        "warnings": warnings[: args.max_errors],
        "errors": errors[: args.max_errors],
        "ok": checked > 0 and not errors,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


def _expand_pattern(pattern: str) -> Tuple[List[str], Optional[str]]:
    try:
        import braceexpand  # type: ignore
    except Exception:  # noqa: BLE001
        return [pattern], "braceexpand is not installed; checked the literal input path only"
    return list(braceexpand.braceexpand(pattern)), None


def validate_webdataset_name(args: argparse.Namespace) -> int:
    expanded, warning = _expand_pattern(args.input_path)
    errors: List[str] = []
    warnings: List[str] = []
    if warning:
        warnings.append(warning)
    if not expanded:
        errors.append("pattern expanded to zero paths")

    checked_paths: List[str] = []
    for item in expanded[: args.max_records]:
        checked_paths.append(item)
        p = Path(item)
        if p.suffix.lower() != ".tar":
            errors.append(f"not a .tar shard path: {item}")
        if args.require_existing and not p.exists():
            errors.append(f"shard path does not exist: {item}")

    report = {
        "mode": "webdataset-name",
        "input_path": args.input_path,
        "expanded_count": len(expanded),
        "checked_count": len(checked_paths),
        "checked_paths_preview": checked_paths[:10],
        "warnings": warnings[: args.max_errors],
        "errors": errors[: args.max_errors],
        "ok": bool(expanded) and not errors,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bounded validators for OpenFlamingo MMC4, VQA prediction, and WebDataset path inputs."
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=["mmc4-json", "vqa-predictions", "webdataset-name"],
        help="Validation mode to run.",
    )
    parser.add_argument("--input-path", required=True, help="Path or brace pattern to validate.")
    parser.add_argument(
        "--max-records",
        type=int,
        default=100,
        help="Maximum records or expanded paths to inspect. Default: 100.",
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=20,
        help="Maximum errors/warnings to include before stopping. Default: 20.",
    )
    parser.add_argument(
        "--zip-member",
        default=None,
        help="For --mode mmc4-json on ZIP input, read this member instead of the first JSON member.",
    )
    parser.add_argument(
        "--require-image-base64",
        action="store_true",
        help="For --mode mmc4-json, require each checked record to contain at least one image_base64 entry.",
    )
    parser.add_argument(
        "--require-existing",
        action="store_true",
        help="For --mode webdataset-name, require expanded .tar paths to exist.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.max_records <= 0:
        parser.error("--max-records must be positive")
    if args.max_errors <= 0:
        parser.error("--max-errors must be positive")

    if args.mode == "mmc4-json":
        return validate_mmc4_json(args)
    if args.mode == "vqa-predictions":
        return validate_vqa_predictions(args)
    if args.mode == "webdataset-name":
        return validate_webdataset_name(args)
    parser.error(f"unsupported mode: {args.mode}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
