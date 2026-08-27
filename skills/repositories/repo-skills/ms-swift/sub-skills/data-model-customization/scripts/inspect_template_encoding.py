#!/usr/bin/env python3
"""Safely plan or attempt ms-swift template encoding for a sample row."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional


def ensure_swift_importable() -> None:
    """Allow execution from an ms-swift source checkout as well as installed packages."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "swift" / "__init__.py").exists():
            parent_text = str(parent)
            if parent_text not in sys.path:
                sys.path.insert(0, parent_text)
            return


DEFAULT_ROW = {
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi, how can I help?"},
    ]
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Print an ms-swift template encoding plan by default. Add --attempt to load an installed "
            "processor/template and encode a sample."
        )
    )
    parser.add_argument("--model", default=None, help="Model ID or local model directory for get_processor.")
    parser.add_argument("--model-type", default=None, help="Optional model_type override for get_processor.")
    parser.add_argument("--template", default=None, help="Optional template_type override for get_template.")
    parser.add_argument("--agent-template", default=None, help="Optional agent_template override for get_template.")
    parser.add_argument("--mode", choices=["train", "rlhf", "pt", "infer"], default="train", help="Template mode.")
    parser.add_argument("--row-json", default=None, help="Inline JSON object row to encode.")
    parser.add_argument("--row-file", default=None, help="JSON/JSONL file containing a row to encode. Uses first row/list item.")
    parser.add_argument("--loss-scale", default="default", help="loss_scale argument for get_template.")
    parser.add_argument("--max-length", type=int, default=None, help="Optional max_length argument for get_template.")
    parser.add_argument("--max-pixels", type=int, default=None, help="Optional max_pixels argument for get_template.")
    parser.add_argument("--no-download", action="store_true", help="Pass download_model=False to get_processor.")
    parser.add_argument("--attempt", action="store_true", help="Actually import swift, load processor/template, and encode.")
    parser.add_argument("--print-inputs", action="store_true", help="Call template.print_inputs(encoded) when available.")
    return parser.parse_args()


def load_row(args: argparse.Namespace) -> Dict[str, Any]:
    if args.row_json:
        row = json.loads(args.row_json)
        if not isinstance(row, dict):
            raise SystemExit("--row-json must decode to an object")
        return row
    if args.row_file:
        path = Path(args.row_file)
        if not path.exists():
            raise SystemExit(f"row file not found: {path}")
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            raise SystemExit(f"row file is empty: {path}")
        if path.suffix.lower() == ".jsonl":
            first_line = next(line for line in text.splitlines() if line.strip())
            row = json.loads(first_line)
        else:
            data = json.loads(text)
            if isinstance(data, list):
                if not data:
                    raise SystemExit("row file JSON list is empty")
                row = data[0]
            else:
                row = data
        if not isinstance(row, dict):
            raise SystemExit("row file must contain a JSON object row")
        return row
    return DEFAULT_ROW


def print_plan(args: argparse.Namespace, row: Dict[str, Any]) -> None:
    print("Template encoding plan")
    print("======================")
    print("This script is safe by default: it has not imported swift or loaded a model processor.")
    print()
    print(f"model: {args.model or '<required for --attempt>'}")
    print(f"model_type override: {args.model_type or '<auto>'}")
    print(f"template override: {args.template or '<auto>'}")
    print(f"agent_template override: {args.agent_template or '<template default>'}")
    print(f"mode: {args.mode}")
    print(f"download_model: {not args.no_download}")
    print(f"row keys: {', '.join(sorted(row.keys()))}")
    if "messages" in row and isinstance(row["messages"], list):
        roles = [message.get("role") for message in row["messages"] if isinstance(message, dict)]
        print(f"message roles: {roles}")
    print()
    print("To attempt encoding with installed ms-swift and local/cached processor files, run with --attempt.")
    print("Use --no-download for offline checks. Registry inspection can pass even when processor files are absent.")


def safe_decode(template: Any, tokens: Any) -> Optional[str]:
    if tokens is None:
        return None
    try:
        return template.safe_decode(tokens)
    except Exception as exc:
        return f"<decode failed: {exc}>"


def preview_encoded(template: Any, encoded: Dict[str, Any]) -> Dict[str, Any]:
    preview: Dict[str, Any] = {"keys": sorted(encoded.keys())}
    for key in ["input_ids", "labels", "chosen_labels", "rejected_labels"]:
        if key in encoded:
            value = encoded[key]
            try:
                preview[f"{key}_length"] = len(value)
            except Exception:
                pass
            preview[f"{key}_decoded"] = safe_decode(template, value)
    if "loss_scale" in encoded:
        loss_scale = encoded["loss_scale"]
        try:
            preview["loss_scale_length"] = len(loss_scale)
            preview["loss_scale_preview"] = list(loss_scale[:40])
        except Exception:
            preview["loss_scale_preview"] = str(loss_scale)
    if "template_inputs" in encoded:
        template_inputs = encoded["template_inputs"]
        for field_name in ["images", "videos", "audios"]:
            value = getattr(template_inputs, field_name, None)
            if value is not None:
                try:
                    preview[f"template_inputs_{field_name}_count"] = len(value)
                except Exception:
                    preview[f"template_inputs_{field_name}"] = str(value)
    return preview


def attempt_encoding(args: argparse.Namespace, row: Dict[str, Any]) -> int:
    if not args.model:
        print("--model is required with --attempt", file=sys.stderr)
        return 2

    ensure_swift_importable()
    from swift import get_processor, get_template

    processor_kwargs: Dict[str, Any] = {}
    if args.model_type:
        processor_kwargs["model_type"] = args.model_type
    if args.no_download:
        processor_kwargs["download_model"] = False

    template_kwargs: Dict[str, Any] = {"loss_scale": args.loss_scale}
    if args.template:
        template_kwargs["template_type"] = args.template
    if args.agent_template:
        template_kwargs["agent_template"] = args.agent_template
    if args.max_length is not None:
        template_kwargs["max_length"] = args.max_length
    if args.max_pixels is not None:
        template_kwargs["max_pixels"] = args.max_pixels

    print("Loading processor...")
    processor = get_processor(args.model, **processor_kwargs)
    print("Creating template...")
    template = get_template(processor, **template_kwargs)
    if args.mode != "infer" and hasattr(template, "set_mode"):
        template.set_mode(args.mode)

    print("Encoding row...")
    encoded = template.encode(row)
    if args.print_inputs and hasattr(template, "print_inputs"):
        template.print_inputs(encoded)
    preview = preview_encoded(template, encoded)
    print(json.dumps(preview, indent=2, ensure_ascii=False))
    return 0


def main() -> int:
    args = parse_args()
    row = load_row(args)
    if not args.attempt:
        print_plan(args, row)
        return 0
    try:
        return attempt_encoding(args, row)
    except Exception as exc:
        print(f"Template encoding failed: {exc}", file=sys.stderr)
        print("Triage: inspect registries, verify local processor/tokenizer files, check optional dependencies, then retry.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
