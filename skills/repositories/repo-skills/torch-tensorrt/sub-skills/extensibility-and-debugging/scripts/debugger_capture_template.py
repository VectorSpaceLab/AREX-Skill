#!/usr/bin/env python3
"""Template for a Torch-TensorRT Debugger capture workflow.

This is intentionally light-weight. It prints a starter script skeleton and
optionally writes it to a file when --output is provided.
"""

from __future__ import annotations

import argparse
from pathlib import Path

TEMPLATE = '''import torch
import torch_tensorrt

# Fill in your model, inputs, and compile settings.
# Example:
# debugger = torch_tensorrt.dynamo.Debugger(
#     log_level="debug",
#     save_layer_info=True,
#     logging_dir="./debug_logs",
# )
# compiled = torch_tensorrt.compile(model, ir="dynamo", inputs=inputs, dryrun=True)
# out = compiled(*inputs)
'''


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a minimal Torch-TensorRT debugger capture template.")
    parser.add_argument("--output", type=Path, help="write the template to a file")
    args = parser.parse_args()

    if args.output:
        args.output.write_text(TEMPLATE, encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print(TEMPLATE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
