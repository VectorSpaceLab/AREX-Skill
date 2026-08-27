#!/usr/bin/env python3
"""Generate a minimal Triton config.pbtxt skeleton.

This helper does not start Triton. It only emits a config template from explicit
input/output specs of the form name:TYPE:dim,dim,... . Use -1 for dynamic dims.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import List


@dataclass
class TensorSpec:
    name: str
    dtype: str
    dims: List[int]


def parse_spec(text: str) -> TensorSpec:
    parts = text.split(":")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("spec must be name:TYPE:dim,dim,...")
    name, dtype, dims_s = parts
    if not name or not dtype:
        raise argparse.ArgumentTypeError("name and TYPE must be non-empty")
    try:
        dims = [int(x) for x in dims_s.split(",") if x]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("dims must be integers, use -1 for dynamic") from exc
    if not dims:
        raise argparse.ArgumentTypeError("at least one dim is required")
    return TensorSpec(name=name, dtype=dtype, dims=dims)


def block(kind: str, specs: List[TensorSpec]) -> str:
    chunks = []
    for spec in specs:
        dims = ", ".join(str(d) for d in spec.dims)
        chunks.append(f"""  {{
    name: \"{spec.name}\"
    data_type: TYPE_{spec.dtype.upper()}
    dims: [ {dims} ]
  }}""")
    return f"{kind} [\n" + ",\n".join(chunks) + "\n]"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a minimal Triton config.pbtxt skeleton.")
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--backend", choices=["pytorch", "tensorrt", "python"], default="pytorch")
    parser.add_argument("--max-batch-size", type=int, default=0)
    parser.add_argument("--input", action="append", type=parse_spec, required=True, help="name:TYPE:dim,dim,...")
    parser.add_argument("--output", action="append", type=parse_spec, required=True, help="name:TYPE:dim,dim,...")
    args = parser.parse_args()

    print(f'name: "{args.model_name}"')
    print(f'backend: "{args.backend}"')
    print(f"max_batch_size: {args.max_batch_size}")
    print(block("input", args.input))
    print(block("output", args.output))
    print("\n# Review this skeleton against the actual Torch-TensorRT artifact before serving.")
    print("# Ensure dynamic dims stay within the engine optimization profile ranges.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
