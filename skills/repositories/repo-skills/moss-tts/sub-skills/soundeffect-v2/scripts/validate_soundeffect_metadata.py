#!/usr/bin/env python3
"""Validate MOSS-SoundEffect v2 fine-tuning JSONL metadata."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


AUDIO_EXTENSIONS = {
    "",
    ".wav",
    ".mp3",
    ".flac",
    ".ogg",
    ".m4a",
    ".aac",
    ".wma",
    ".mp4",
    ".aiff",
    ".wv",
}


def _error(line: int | None, message: str, **extra: Any) -> dict[str, Any]:
    item: dict[str, Any] = {"message": message}
    if line is not None:
        item["line"] = line
    item.update(extra)
    return item


def _resolve_audio_path(audio_value: str, dataset_base: Path) -> Path:
    path = Path(audio_value).expanduser()
    if path.is_absolute():
        return path
    return dataset_base / path


def validate_metadata(
    metadata: Path,
    dataset_base: Path,
    check_audio_exists: bool,
    allow_empty_lines: bool,
    max_errors: int,
) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    records = 0
    blank_lines = 0

    if not metadata.is_file():
        errors.append(_error(None, "metadata path is not a file", path=str(metadata)))
        return {
            "ok": False,
            "metadata": str(metadata),
            "dataset_base": str(dataset_base),
            "check_audio_exists": check_audio_exists,
            "records": records,
            "blank_lines": blank_lines,
            "errors": errors,
            "warnings": warnings,
        }

    if check_audio_exists and not dataset_base.exists():
        errors.append(_error(None, "dataset base does not exist", path=str(dataset_base)))

    try:
        handle = metadata.open("r", encoding="utf-8")
    except OSError as exc:
        errors.append(_error(None, "cannot open metadata", path=str(metadata), detail=str(exc)))
        return {
            "ok": False,
            "metadata": str(metadata),
            "dataset_base": str(dataset_base),
            "check_audio_exists": check_audio_exists,
            "records": records,
            "blank_lines": blank_lines,
            "errors": errors,
            "warnings": warnings,
        }

    with handle:
        for line_no, raw in enumerate(handle, start=1):
            line = raw.strip()
            if not line:
                blank_lines += 1
                if not allow_empty_lines:
                    errors.append(_error(line_no, "blank line is not valid JSONL"))
                if len(errors) >= max_errors:
                    break
                continue

            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(_error(line_no, "invalid JSON", detail=str(exc)))
                if len(errors) >= max_errors:
                    break
                continue

            if not isinstance(row, dict):
                errors.append(_error(line_no, "JSONL row must be an object"))
                if len(errors) >= max_errors:
                    break
                continue

            records += 1

            audio = row.get("audio")
            prompt = row.get("prompt")

            if not isinstance(audio, str) or not audio.strip():
                errors.append(_error(line_no, "required field 'audio' must be a non-empty string"))
            else:
                audio_path = _resolve_audio_path(audio.strip(), dataset_base)
                suffix = audio_path.suffix.lower()
                if suffix not in AUDIO_EXTENSIONS:
                    warnings.append(
                        _error(
                            line_no,
                            "audio file extension is not in the known loader list",
                            audio=audio,
                            resolved_path=str(audio_path),
                            extension=suffix,
                        )
                    )
                if check_audio_exists:
                    if not audio_path.exists():
                        errors.append(
                            _error(
                                line_no,
                                "audio path does not exist",
                                audio=audio,
                                resolved_path=str(audio_path),
                            )
                        )
                    elif not audio_path.is_file():
                        errors.append(
                            _error(
                                line_no,
                                "audio path exists but is not a file",
                                audio=audio,
                                resolved_path=str(audio_path),
                            )
                        )

            if not isinstance(prompt, str) or not prompt.strip():
                errors.append(_error(line_no, "required field 'prompt' must be a non-empty string"))

            if len(errors) >= max_errors:
                break

    truncated = len(errors) >= max_errors
    if truncated:
        errors.append(_error(None, "stopped after reaching max_errors", max_errors=max_errors))

    if records == 0:
        errors.append(_error(None, "metadata contains no valid JSON object records"))

    return {
        "ok": not errors,
        "metadata": str(metadata),
        "dataset_base": str(dataset_base),
        "check_audio_exists": check_audio_exists,
        "records": records,
        "blank_lines": blank_lines,
        "errors": errors,
        "warnings": warnings,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate MOSS-SoundEffect v2 JSONL metadata. Each row must be a "
            "JSON object with non-empty string fields 'audio' and 'prompt'."
        )
    )
    parser.add_argument("--metadata", required=True, type=Path, help="JSONL metadata file to validate.")
    parser.add_argument(
        "--dataset-base",
        required=True,
        type=Path,
        help="Base directory for resolving relative audio paths.",
    )
    parser.add_argument(
        "--check-audio-exists",
        action="store_true",
        help="Require every resolved audio path to exist and be a file.",
    )
    parser.add_argument(
        "--allow-empty-lines",
        action="store_true",
        help="Ignore blank lines instead of treating them as JSONL errors.",
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=100,
        help="Stop collecting errors after this many failures. Default: 100.",
    )
    parser.add_argument("--json", action="store_true", help="Emit a JSON validation summary.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.max_errors < 1:
        print("--max-errors must be >= 1", file=sys.stderr)
        return 2

    result = validate_metadata(
        metadata=args.metadata.expanduser(),
        dataset_base=args.dataset_base.expanduser(),
        check_audio_exists=args.check_audio_exists,
        allow_empty_lines=args.allow_empty_lines,
        max_errors=args.max_errors,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result["ok"]:
            print(
                f"OK: {result['records']} records validated "
                f"({result['blank_lines']} blank lines)."
            )
            if result["warnings"]:
                print(f"Warnings: {len(result['warnings'])}")
                for warning in result["warnings"]:
                    line = f"line {warning['line']}: " if "line" in warning else ""
                    print(f"  - {line}{warning['message']}")
        else:
            print(
                f"INVALID: {len(result['errors'])} errors across "
                f"{result['records']} parsed records.",
                file=sys.stderr,
            )
            for err in result["errors"]:
                line = f"line {err['line']}: " if "line" in err else ""
                detail = f" ({err['detail']})" if "detail" in err else ""
                print(f"  - {line}{err['message']}{detail}", file=sys.stderr)
            if result["warnings"]:
                print(f"Warnings: {len(result['warnings'])}", file=sys.stderr)

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
