#!/usr/bin/env python3
"""Probe ExecuTorch backend Python modules without running delegates."""
from __future__ import annotations
import argparse, importlib, json, os

MODULES = {
    "xnnpack": "executorch.backends.xnnpack.partition.xnnpack_partitioner",
    "coreml": "executorch.backends.apple.coreml.partition.coreml_partitioner",
    "mps": "executorch.backends.apple.mps.partition.mps_partitioner",
    "cuda": "executorch.backends.cuda.cuda_partitioner",
    "openvino": "executorch.backends.openvino.partitioner",
    "qnn": "executorch.backends.qualcomm.partition.qnn_partitioner",
    "cortex_m": "executorch.backends.cortex_m.quantizer.quantizer",
}


def probe(name, module):
    try:
        mod = importlib.import_module(module)
        return {"backend": name, "module": module, "ok": True, "file": getattr(mod, "__file__", None)}
    except Exception as exc:
        return {"backend": name, "module": module, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def main():
    ap = argparse.ArgumentParser(description="Check importability of selected ExecuTorch backend Python modules.")
    ap.add_argument("--backend", action="append", choices=sorted(MODULES), help="Backend to check; repeatable. Default checks all known probes.")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    selected = args.backend or sorted(MODULES)
    report = {
        "imports": [probe(name, MODULES[name]) for name in selected],
        "env": {k: os.environ.get(k) for k in ["QNN_SDK_ROOT", "ANDROID_NDK", "ANDROID_NDK_ROOT", "VULKAN_SDK", "COREMLTOOLS_HOME"] if os.environ.get(k)},
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for row in report["imports"]:
            print(f"{row['backend']}: {'OK' if row['ok'] else row['error']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

