#!/usr/bin/env python3
"""Small ExecuTorch export smoke test.

This script does not download assets. It exports a tiny add module and writes a .pte
when the installed package supports the required export path.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys


def main() -> int:
    ap = argparse.ArgumentParser(description="Export a tiny PyTorch module through ExecuTorch.")
    ap.add_argument("--output-dir", type=Path, required=False, default=Path("executorch-export-smoke"))
    ap.add_argument("--dynamic", action="store_true", help="Use a simple dynamic shape bound for the first dimension.")
    ap.add_argument("--recipe-api", action="store_true", help="Also import the higher-level executorch.export recipe API.")
    args = ap.parse_args()
    try:
        import torch
        from executorch.exir import to_edge_transform_and_lower
    except Exception as exc:
        print(f"missing export dependency: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    class Add(torch.nn.Module):
        def forward(self, x, y):
            return x + y

    x = torch.ones(2, 2)
    y = torch.ones(2, 2)
    kwargs = {}
    if args.dynamic:
        from torch.export import Dim
        kwargs["dynamic_shapes"] = {"x": {0: Dim("batch", min=1, max=4)}, "y": {0: Dim("batch", min=1, max=4)}}
    try:
        exported = torch.export.export(Add().eval(), (x, y), **kwargs)
        manager = to_edge_transform_and_lower(exported).to_executorch()
    except FileNotFoundError as exc:
        print(
            "export reached serialization but required packaged schema/resource files are missing. "
            "Install a full ExecuTorch wheel or editable build instead of a source-path-only import. "
            f"Details: {exc}",
            file=sys.stderr,
        )
        return 3
    except Exception as exc:
        print(f"export smoke failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 3
    args.output_dir.mkdir(parents=True, exist_ok=True)
    out = args.output_dir / "add.pte"
    out.write_bytes(manager.buffer)
    print(f"wrote {out} ({out.stat().st_size} bytes)")
    if args.recipe_api:
        from executorch.export import ExportRecipe, LoweringRecipe, QuantizationRecipe, export as session_export
        print("recipe API import OK", ExportRecipe, LoweringRecipe, QuantizationRecipe, session_export)
    try:
        from executorch.runtime import Runtime
        program = Runtime.get().load_program(str(out))
        print("runtime load OK", getattr(program, "method_names", None))
    except Exception as exc:
        print(f"runtime validation skipped/failed: {type(exc).__name__}: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

