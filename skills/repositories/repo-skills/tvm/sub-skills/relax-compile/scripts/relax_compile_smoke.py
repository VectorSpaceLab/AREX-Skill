#!/usr/bin/env python3
"""Run a tiny TVM Relax compile/VM smoke test."""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import numpy as np


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default="llvm", help="TVM target, default llvm")
    parser.add_argument(
        "--device",
        default="cpu",
        help="Execution device helper name for non-LLVM targets, e.g. cuda, rocm, opencl, vulkan",
    )
    parser.add_argument("--work-dir", type=Path, help="Directory for optional export artifact")
    parser.add_argument("--skip-export", action="store_true", help="Do not export/load executable")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary")
    args = parser.parse_args(argv)

    import tvm
    from tvm import relax
    from tvm.script import ir as I
    from tvm.script import relax as R

    @I.ir_module
    class TinyAdd:
        @R.function
        def main(x: R.Tensor((4,), dtype="float32"), y: R.Tensor((4,), dtype="float32")):
            with R.dataflow():
                z = R.add(x, y)
                R.output(z)
            return z

    mod = TinyAdd
    try:
        mod = relax.get_pipeline("zero")(mod)
    except Exception:
        # Some future releases may not need/accept this baseline pipeline for
        # such a tiny module. tvm.compile is the authoritative check.
        pass
    ex = tvm.compile(mod, target=args.target)
    dev = tvm.cpu() if str(args.target).startswith("llvm") else getattr(tvm, args.device)(0)
    vm = relax.VirtualMachine(ex, dev)
    a = tvm.runtime.tensor(np.arange(4, dtype="float32"), dev)
    b = tvm.runtime.tensor(np.ones(4, dtype="float32"), dev)
    out = vm["main"](a, b).numpy()
    expected = np.arange(4, dtype="float32") + 1.0
    np.testing.assert_allclose(out, expected)

    artifact = None
    if not args.skip_export:
        work_dir = args.work_dir or Path(tempfile.mkdtemp(prefix="tvm-relax-smoke-"))
        work_dir.mkdir(parents=True, exist_ok=True)
        artifact = work_dir / "tiny_relax.tar"
        ex.export_library(str(artifact))
        loaded = tvm.runtime.load_module(str(artifact))
        vm2 = relax.VirtualMachine(loaded, dev)
        np.testing.assert_allclose(vm2["main"](a, b).numpy(), expected)

    summary = {"target": args.target, "result": "pass", "artifact": str(artifact) if artifact else None}
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("PASS tiny Relax compile", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
