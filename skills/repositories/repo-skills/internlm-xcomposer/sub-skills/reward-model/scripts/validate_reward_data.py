#!/usr/bin/env python3
"""Validate IXC-2.5-Reward preference data without model imports.

The checker is intentionally stdlib-only. It validates JSON list files and
source-style data.txt manifests; it never imports PIL, torch, transformers, or
repo code, and it never opens image bytes unless --check-images asks for simple
path-existence probes.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


ASSISTANT_ROLES = {"assistant", "bot", "gpt", "model"}
USER_ROLES = {"human", "user"}
KNOWN_ROLES = ASSISTANT_ROLES | USER_ROLES | {"system"}
CHAT_TEMPLATE_TOKENS = ("<|im_start|>", "<|im_end|>")


def add_issue(report: Dict[str, Any], level: str, location: str, message: str) -> None:
    report["issues"].append({"level": level, "location": location, "message": message})
    report["totals"][level + "s"] += 1


def role_of(message: Dict[str, Any]) -> str:
    return str(message.get("from", "")).strip().lower()


def response_filter_reasons(response: str) -> List[str]:
    reasons: List[str] = []
    for token in CHAT_TEMPLATE_TOKENS:
        if token in response:
            reasons.append(f"contains chat template token {token!r}")
    if len(response) == 0:
        reasons.append("final response is empty")
        return reasons
    pieces: List[str] = []
    for part in response.split(" "):
        pieces.extend(piece for piece in part.split("\n") if piece)
    if not pieces:
        reasons.append("final response has only whitespace")
        return reasons
    if len(response) > 500 and max(len(piece) for piece in pieces) > 100:
        reasons.append("long response contains an extremely long unbroken token")
    return reasons


def human_turn_values(conversation: Any) -> List[str]:
    if not isinstance(conversation, list):
        return []
    values: List[str] = []
    for message in conversation:
        if isinstance(message, dict) and role_of(message) in USER_ROLES:
            value = message.get("value")
            if isinstance(value, str):
                values.append(value)
    return values


def placeholder_count(conversation: Any) -> int:
    if not isinstance(conversation, list):
        return 0
    return sum(
        message.get("value", "").count("<ImageHere>")
        for message in conversation
        if isinstance(message, dict) and isinstance(message.get("value"), str)
    )


def validate_conversation(
    conversation: Any,
    report: Dict[str, Any],
    location: str,
) -> None:
    if not isinstance(conversation, list):
        add_issue(report, "error", location, "must be a list of messages")
        return
    if not conversation:
        add_issue(report, "error", location, "must not be empty")
        return

    for index, message in enumerate(conversation):
        msg_loc = f"{location}[{index}]"
        if not isinstance(message, dict):
            add_issue(report, "error", msg_loc, "message must be an object")
            continue
        if "from" not in message:
            add_issue(report, "error", msg_loc, "missing 'from' role key")
        elif not isinstance(message["from"], str):
            add_issue(report, "error", f"{msg_loc}.from", "role must be a string")
        else:
            role = role_of(message)
            if role not in KNOWN_ROLES:
                add_issue(
                    report,
                    "warning",
                    f"{msg_loc}.from",
                    "unknown role; source conv2text will treat it as assistant",
                )
        if "value" not in message:
            add_issue(report, "error", msg_loc, "missing 'value' text key")
        elif not isinstance(message["value"], str):
            add_issue(report, "error", f"{msg_loc}.value", "value must be a string")
        elif message["value"] == "":
            add_issue(report, "warning", f"{msg_loc}.value", "message value is empty")

    last = conversation[-1]
    if isinstance(last, dict) and isinstance(last.get("value"), str):
        last_role = role_of(last)
        if last_role in USER_ROLES or last_role == "system":
            add_issue(
                report,
                "warning",
                f"{location}[-1].from",
                "final message is not assistant-like; preference training expects judged assistant/bot responses",
            )
        for reason in response_filter_reasons(last["value"]):
            add_issue(
                report,
                "error",
                f"{location}[-1].value",
                f"source filter_data would drop this response: {reason}",
            )


def normalize_images(image_value: Any, report: Dict[str, Any], location: str) -> Optional[List[str]]:
    if isinstance(image_value, str):
        if not image_value:
            add_issue(report, "error", location, "image path string must not be empty")
            return []
        return [image_value]
    if isinstance(image_value, list):
        if not image_value:
            add_issue(report, "warning", location, "image key is present but the list is empty")
            return []
        images: List[str] = []
        for index, item in enumerate(image_value):
            item_loc = f"{location}[{index}]"
            if not isinstance(item, str):
                add_issue(report, "error", item_loc, "multi-image entries must be strings")
                continue
            if not item:
                add_issue(report, "error", item_loc, "image path string must not be empty")
            images.append(item)
        return images
    add_issue(report, "error", location, "image must be a string path or a list of string paths")
    return None


def resolve_image_path(raw: str, json_path: Path, image_base: str) -> Path:
    image_path = Path(raw).expanduser()
    if image_path.is_absolute():
        return image_path
    if image_base == "cwd":
        return (Path.cwd() / image_path).resolve()
    if image_base == "json":
        return (json_path.parent / image_path).resolve()
    return (Path(image_base).expanduser() / image_path).resolve()


def validate_sample(
    sample: Any,
    report: Dict[str, Any],
    json_path: Path,
    sample_index: int,
    args: argparse.Namespace,
) -> None:
    base_loc = f"{json_path}:sample[{sample_index}]"
    if not isinstance(sample, dict):
        add_issue(report, "error", base_loc, "sample must be an object")
        return

    for key in ("id", "conversations_a", "conversations_b"):
        if key not in sample:
            add_issue(report, "error", base_loc, f"missing required key {key!r}")

    conv_a = sample.get("conversations_a")
    conv_b = sample.get("conversations_b")
    validate_conversation(conv_a, report, f"{base_loc}.conversations_a")
    validate_conversation(conv_b, report, f"{base_loc}.conversations_b")

    a_user = human_turn_values(conv_a)
    b_user = human_turn_values(conv_b)
    if a_user and b_user and a_user != b_user:
        add_issue(
            report,
            "warning",
            base_loc,
            "human/user turns differ between conversations_a and conversations_b; pair may not compare the same prompt",
        )

    if "image" in sample:
        report["totals"]["image_samples"] += 1
        images = normalize_images(sample["image"], report, f"{base_loc}.image")
        if images and len(images) > 1:
            for side_name, conversation in (("conversations_a", conv_a), ("conversations_b", conv_b)):
                seen = placeholder_count(conversation)
                if seen < len(images):
                    add_issue(
                        report,
                        "error",
                        f"{base_loc}.{side_name}",
                        f"multi-image sample has {len(images)} image paths but only {seen} '<ImageHere>' placeholders",
                    )
        if images and args.check_images:
            for raw in images:
                candidate = resolve_image_path(raw, json_path, args.image_base)
                if not candidate.exists():
                    add_issue(
                        report,
                        "error",
                        f"{base_loc}.image",
                        f"image path does not exist under --image-base {args.image_base!r}: {raw} -> {candidate}",
                    )
                elif not candidate.is_file():
                    add_issue(
                        report,
                        "error",
                        f"{base_loc}.image",
                        f"image path is not a file: {raw} -> {candidate}",
                    )
    else:
        report["totals"]["text_samples"] += 1
        if placeholder_count(conv_a) or placeholder_count(conv_b):
            add_issue(
                report,
                "warning",
                base_loc,
                "conversation contains '<ImageHere>' but sample has no image key",
            )


def load_json_list(path: Path, report: Dict[str, Any]) -> Optional[List[Any]]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        add_issue(report, "error", str(path), "file does not exist")
        return None
    except json.JSONDecodeError as exc:
        add_issue(report, "error", str(path), f"invalid JSON: {exc}")
        return None
    except OSError as exc:
        add_issue(report, "error", str(path), f"cannot read file: {exc}")
        return None
    if not isinstance(data, list):
        add_issue(report, "error", str(path), "top-level JSON value must be a list")
        return None
    return data


def validate_json_file(path: Path, report: Dict[str, Any], args: argparse.Namespace, origin: str = "input") -> None:
    resolved = path.expanduser().resolve()
    file_report: Dict[str, Any] = {
        "path": str(resolved),
        "kind": "json",
        "origin": origin,
        "samples": 0,
        "inspected": 0,
        "truncated": False,
    }
    report["files"].append(file_report)
    report["totals"]["json_files"] += 1

    data = load_json_list(resolved, report)
    if data is None:
        return
    file_report["samples"] = len(data)
    report["totals"]["samples"] += len(data)

    limit = args.max_samples if args.max_samples and args.max_samples > 0 else len(data)
    if limit < len(data):
        file_report["truncated"] = True
    for index, sample in enumerate(data[:limit]):
        file_report["inspected"] += 1
        report["totals"]["inspected_samples"] += 1
        validate_sample(sample, report, resolved, index, args)


def resolve_manifest_entry(raw_path: str, manifest_path: Path, args: argparse.Namespace) -> Path:
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        return candidate
    base = Path.cwd() if args.manifest_base == "cwd" else manifest_path.parent
    return base / candidate


def parse_manifest(path: Path, report: Dict[str, Any], args: argparse.Namespace) -> List[Tuple[Path, Optional[float]]]:
    entries: List[Tuple[Path, Optional[float]]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        add_issue(report, "error", str(path), "manifest does not exist")
        return entries
    except OSError as exc:
        add_issue(report, "error", str(path), f"cannot read manifest: {exc}")
        return entries

    for line_number, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        loc = f"{path}:line[{line_number}]"
        if len(parts) > 2:
            add_issue(report, "error", loc, "manifest lines must be '<json path>' or '<json path> <number>'")
            continue
        if args.given_num and len(parts) != 2:
            add_issue(report, "error", loc, "--given-num mode requires a sample-number column")
            continue
        number: Optional[float] = None
        if len(parts) == 2:
            try:
                number = float(parts[1])
            except ValueError:
                add_issue(report, "error", loc, f"sample number/ratio is not numeric: {parts[1]!r}")
                continue
            if number <= 0:
                add_issue(report, "error", loc, "sample number/ratio must be positive")
                continue
        entries.append((resolve_manifest_entry(parts[0], path, args), number))
    return entries


def validate_manifest(path: Path, report: Dict[str, Any], args: argparse.Namespace) -> None:
    resolved = path.expanduser().resolve()
    file_report: Dict[str, Any] = {
        "path": str(resolved),
        "kind": "manifest",
        "manifest_base": args.manifest_base,
        "entries": [],
    }
    report["files"].append(file_report)
    report["totals"]["manifest_files"] += 1

    entries = parse_manifest(resolved, report, args)
    for json_path, number in entries:
        expected = None
        if number is not None:
            expected = int(number * 1000) if args.given_num else number
        file_report["entries"].append({"json_path": str(json_path), "number": number, "expected": expected})
        validate_json_file(json_path, report, args, origin=f"manifest:{resolved.name}")


def should_treat_as_manifest(path: Path) -> bool:
    return path.suffix.lower() == ".txt"


def print_text_report(report: Dict[str, Any]) -> None:
    totals = report["totals"]
    status = "OK" if totals["errors"] == 0 else "FAILED"
    print(f"{status}: inspected {totals['inspected_samples']} of {totals['samples']} samples "
          f"from {totals['json_files']} JSON file(s) and {totals['manifest_files']} manifest(s)")
    print(f"Samples: text={totals['text_samples']} image={totals['image_samples']}")
    print(f"Issues: errors={totals['errors']} warnings={totals['warnings']}")
    for file_report in report["files"]:
        if file_report["kind"] == "json":
            suffix = " (truncated)" if file_report.get("truncated") else ""
            print(f"- JSON {file_report['path']}: {file_report['inspected']}/{file_report['samples']} inspected{suffix}")
        else:
            print(f"- manifest {file_report['path']}: {len(file_report['entries'])} entr{'y' if len(file_report['entries']) == 1 else 'ies'}")
    if report["issues"]:
        print("\nIssues:")
        for issue in report["issues"]:
            print(f"[{issue['level'].upper()}] {issue['location']}: {issue['message']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate IXC-2.5-Reward preference JSON files or data.txt manifests without model imports.",
    )
    parser.add_argument("paths", nargs="+", help="Reward JSON list file(s) or source-style .txt manifest(s).")
    parser.add_argument(
        "--given-num",
        action="store_true",
        help="Interpret manifest second column as thousands of samples, matching source --given_num True.",
    )
    parser.add_argument(
        "--manifest-base",
        choices=("manifest", "cwd"),
        default="manifest",
        help="Resolve relative JSON paths in manifests from the manifest directory (default) or current working directory.",
    )
    parser.add_argument(
        "--check-images",
        action="store_true",
        help="Check image path existence with pathlib only; image bytes are not opened.",
    )
    parser.add_argument(
        "--image-base",
        default="cwd",
        help="For --check-images, resolve relative image paths from 'cwd', 'json', or a directory path. Default: cwd.",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=0,
        help="Inspect at most this many samples per JSON file; 0 means all samples.",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Output format.")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.max_samples < 0:
        parser.error("--max-samples must be non-negative")

    report: Dict[str, Any] = {
        "ok": False,
        "files": [],
        "issues": [],
        "totals": {
            "json_files": 0,
            "manifest_files": 0,
            "samples": 0,
            "inspected_samples": 0,
            "text_samples": 0,
            "image_samples": 0,
            "errors": 0,
            "warnings": 0,
        },
    }

    for raw in args.paths:
        path = Path(raw)
        if should_treat_as_manifest(path):
            validate_manifest(path, report, args)
        else:
            validate_json_file(path, report, args)

    report["ok"] = report["totals"]["errors"] == 0
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_text_report(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
