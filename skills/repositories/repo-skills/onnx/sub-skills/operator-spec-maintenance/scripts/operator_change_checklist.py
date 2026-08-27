#!/usr/bin/env python3
"""Print a task-specific ONNX operator-maintenance checklist.

The script does not modify the repository. It prints the source-of-truth files,
common follow-up tests, and generated artifacts that usually accompany an ONNX
operator/schema/function-body change.
"""

from __future__ import annotations

import argparse
import json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print an ONNX operator-maintenance checklist.")
    parser.add_argument("--action", choices=["add", "update", "remove"], required=True)
    parser.add_argument("--op-name", required=True, help="Operator name, e.g. Resize.")
    parser.add_argument("--domain", default="", help="Operator domain, empty string for ai.onnx.")
    parser.add_argument("--function-body", action="store_true", help="Include function-body checklist items.")
    parser.add_argument("--proto-change", action="store_true", help="Include proto regeneration items.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    return parser.parse_args()


def checklist(args: argparse.Namespace) -> dict[str, object]:
    items = [
        "Edit the schema source-of-truth in onnx/defs/<domain>/defs.cc.",
        "Update onnx/defs/operator_sets.h if the opset export changes.",
        "Add or update reference implementation coverage in onnx/reference/ops/ when the semantics are user-visible.",
        "Add or update backend node tests in onnx/backend/test/case/node/.",
        "Add or update Python shape-inference tests when the output shape or rank changes.",
        "Regenerate operator docs and backend coverage after the source-of-truth change settles.",
    ]
    if args.action == "update":
        items.append("Preserve the old version in onnx/defs/<domain>/old.cc when compatibility matters.")
        items.append("Add or update a version-converter adapter when the signature or behavior changes.")
    if args.action == "remove":
        items.append("Document the replacement or deprecation path and keep any old-version mapping explicit.")
    if args.function_body:
        items.append("Author the function body with compact ONNX text syntax and validate with parser-based fixtures.")
    if args.proto_change:
        items.append("Edit .in.proto source files first, then regenerate protobuf outputs.")
    return {
        "action": args.action,
        "op_name": args.op_name,
        "domain": args.domain or "ai.onnx",
        "source_truth": [
            "onnx/defs/<domain>/defs.cc",
            "onnx/defs/operator_sets.h",
            "onnx/reference/ops/op_<name>.py",
            "onnx/backend/test/case/node/<name>.py",
            "tests/python/shape_inference_test.py",
        ],
        "checklist": items,
        "focused_commands": [
            "python onnx/defs/gen_doc.py",
            "python onnx/backend/test/stat_coverage.py",
            "lintrunner -a --output oneline",
        ],
    }


def main() -> int:
    args = parse_args()
    data = checklist(args)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(f"ONNX operator-maintenance checklist for {data['op_name']} ({data['domain']})")
        for item in data["checklist"]:
            print(f"- {item}")
        print("Focused commands:")
        for cmd in data["focused_commands"]:
            print(f"- {cmd}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
