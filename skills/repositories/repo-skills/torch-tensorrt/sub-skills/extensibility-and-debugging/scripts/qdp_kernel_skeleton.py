#!/usr/bin/env python3
"""Emit a tiny, non-running QDP/custom-kernel skeleton.

The goal is to help a future user sketch the exact op schema and kernel
boundaries without copying source-repo files.
"""

from __future__ import annotations

import argparse
from pathlib import Path

TEMPLATE = '''# QDP/custom-kernel skeleton
# Replace the placeholders with the exact op schema and kernel code.

# op_name = "my_namespace::my_op"
# spec = torch_tensorrt.kernels.KernelSpec(...)
# torch_tensorrt.kernels.cuda_kernel_op(op_name, spec, meta_fn=..., eager_fn=..., aot_fn=..., schema="...")
'''


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a Torch-TensorRT QDP/custom-kernel skeleton.")
    parser.add_argument("--output", type=Path, help="write the skeleton to a file")
    args = parser.parse_args()

    if args.output:
        args.output.write_text(TEMPLATE, encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print(TEMPLATE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
