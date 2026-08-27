#!/usr/bin/env python3
"""Check an installed onnxsim environment without needing a source checkout.

The script imports the public package, verifies the compiled extension, reports
optional ONNX Runtime provider availability, optionally validates a requested
provider list, and can run a tiny in-memory simplification smoke test.
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def import_or_error(name: str) -> tuple[Any | None, str | None]:
    try:
        return importlib.import_module(name), None
    except Exception as exc:  # noqa: BLE001 - diagnostics should report any import failure
        return None, f"{type(exc).__name__}: {exc}"


def tiny_smoke() -> dict[str, Any]:
    import numpy as np
    import onnx
    from onnx import TensorProto, helper, numpy_helper
    import onnxsim
    from onnxsim import backend

    x = helper.make_tensor_value_info("x", TensorProto.FLOAT, [1, 2])
    y = helper.make_tensor_value_info("y", TensorProto.FLOAT, [1, 2])
    c = numpy_helper.from_array(np.asarray([[1.0, 2.0]], dtype=np.float32), "c")
    graph = helper.make_graph(
        [helper.make_node("Add", ["x", "c"], ["y"])],
        "onnxsim_env_smoke",
        [x],
        [y],
        [c],
    )
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 13)], ir_version=10)
    simplified, check_ok = onnxsim.simplify(model, check_n=1, input_fill="ones")
    before = backend.run_model(model, {"x": np.ones((1, 2), dtype=np.float32)})
    after = backend.run_model(simplified, {"x": np.ones((1, 2), dtype=np.float32)})
    np.testing.assert_allclose(list(before.values())[0], list(after.values())[0])
    return {
        "check_ok": bool(check_ok),
        "input_nodes": [node.op_type for node in model.graph.node],
        "output_nodes": [node.op_type for node in simplified.graph.node],
    }


def run_cli_probe() -> dict[str, Any]:
    exe = shutil.which("onnxsim")
    sibling = Path(sys.executable).with_name("onnxsim")
    if exe is None and sibling.exists():
        exe = str(sibling)
    if not exe:
        return {
            "available": False,
            "error": "onnxsim executable not found on PATH or next to sys.executable",
        }
    proc = subprocess.run(
        [exe, "--list-default-optimizers"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )
    optimizers = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    return {
        "available": proc.returncode == 0,
        "executable": exe,
        "returncode": proc.returncode,
        "optimizer_count": len(optimizers),
        "first_optimizers": optimizers[:10],
        "stderr": proc.stderr.strip(),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect an installed onnxsim package and optional execution providers."
    )
    parser.add_argument(
        "--providers",
        nargs="*",
        default=None,
        metavar="PROVIDER",
        help=(
            "Optional onnxruntime provider list to validate, e.g. "
            "--providers CUDAExecutionProvider CPUExecutionProvider."
        ),
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run a tiny in-memory simplify/execute smoke test.",
    )
    parser.add_argument(
        "--skip-cli",
        action="store_true",
        help="Skip probing the onnxsim console script.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report: dict[str, Any] = {"python": sys.version.split()[0], "ok": True}

    onnxsim_mod, onnxsim_err = import_or_error("onnxsim")
    ext_mod, ext_err = import_or_error("onnxsim.onnxsim_cpp2py_export")
    backend_mod, backend_err = import_or_error("onnxsim.backend")

    report["imports"] = {
        "onnxsim": None if onnxsim_err is None else onnxsim_err,
        "onnxsim.onnxsim_cpp2py_export": None if ext_err is None else ext_err,
        "onnxsim.backend": None if backend_err is None else backend_err,
    }
    if onnxsim_mod is not None:
        report["version"] = getattr(onnxsim_mod, "__version__", None)
    if any(report["imports"].values()):
        report["ok"] = False

    if backend_mod is not None:
        report["has_onnxruntime"] = bool(backend_mod.has_onnxruntime())
        if backend_mod.has_onnxruntime():
            import onnxruntime as ort

            report["onnxruntime"] = {
                "version": getattr(ort, "__version__", None),
                "available_providers": list(ort.get_available_providers()),
            }
        if args.providers is not None:
            try:
                backend_mod.validate_providers(args.providers)
                report["provider_validation"] = {"providers": args.providers, "ok": True}
            except Exception as exc:  # noqa: BLE001 - diagnostics should preserve exact message
                report["provider_validation"] = {
                    "providers": args.providers,
                    "ok": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
                report["ok"] = False

    if not args.skip_cli:
        try:
            report["cli"] = run_cli_probe()
            if not report["cli"].get("available"):
                report["ok"] = False
        except Exception as exc:  # noqa: BLE001
            report["cli"] = {"available": False, "error": f"{type(exc).__name__}: {exc}"}
            report["ok"] = False

    if args.smoke:
        try:
            report["smoke"] = tiny_smoke()
            if not report["smoke"].get("check_ok"):
                report["ok"] = False
        except Exception as exc:  # noqa: BLE001
            report["smoke"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            report["ok"] = False

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"onnxsim environment ok: {report['ok']}")
        if "version" in report:
            print(f"version: {report['version']}")
        print("imports:")
        for name, err in report["imports"].items():
            print(f"  {name}: {'ok' if err is None else err}")
        if "onnxruntime" in report:
            print("onnxruntime providers: " + ", ".join(report["onnxruntime"]["available_providers"]))
        if "provider_validation" in report:
            pv = report["provider_validation"]
            print(f"provider validation {pv['providers']}: {'ok' if pv['ok'] else pv['error']}")
        if "cli" in report:
            print(f"cli optimizer count: {report['cli'].get('optimizer_count', 0)}")
        if "smoke" in report:
            print(f"smoke: {report['smoke']}")

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
