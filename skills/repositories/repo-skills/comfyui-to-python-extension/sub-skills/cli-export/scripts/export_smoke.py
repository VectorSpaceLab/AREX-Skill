#!/usr/bin/env python3
"""Smoke-test the exporter against a tiny stub workflow.

This helper is safe to run in a CPU-only environment. It checks that the
public exporter API can render a minimal workflow and that the generated code
contains the expected structural sections.
"""

from __future__ import annotations

import argparse
import json
import sys
from io import StringIO
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke-test ComfyUI-to-Python-Extension export behavior."
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        help="Optional checkout root to add to sys.path when the package is not installed.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.source_root is not None:
        sys.path.insert(0, str(args.source_root))

    from comfyui_to_python import ComfyUItoPython

    class SimpleNode:
        CATEGORY = "utils"
        FUNCTION = "run"

        @classmethod
        def INPUT_TYPES(cls):
            return {"required": {"text": ("STRING",)}}

        def run(self, text):
            return (text,)

    workflow = {"1": {"class_type": "SimpleNode", "inputs": {"text": "hello"}}}
    output = StringIO()
    ComfyUItoPython(
        workflow=json.dumps(workflow),
        output_file=output,
        node_class_mappings={"SimpleNode": SimpleNode},
    )
    code = output.getvalue()

    required_markers = [
        "# Imports",
        "# Workflow data",
        "# Workflow execution",
        "# Entrypoint",
        "def main(unload_models: bool | None = None):",
        "simplenode = SimpleNode()",
        "simplenode_1 = simplenode.run(text=\"hello\")",
    ]
    missing = [marker for marker in required_markers if marker not in code]
    if missing:
        raise SystemExit(f"Missing generated-code markers: {', '.join(missing)}")

    print(f"generated_lines={len(code.splitlines())}")
    print("export_smoke_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
