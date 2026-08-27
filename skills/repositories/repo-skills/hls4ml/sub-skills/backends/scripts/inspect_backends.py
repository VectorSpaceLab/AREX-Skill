#!/usr/bin/env python3
"""Inspect installed hls4ml backends without running synthesis.

This helper imports hls4ml, prints the backend registry, and safely probes
`create_config(...)` defaults. It never calls `write()`, `compile()`, `build()`,
or any vendor synthesis command. Some backend config constructors still need
vendor prerequisites just to infer include/library paths; those failures are
reported as environment prerequisites.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Any

EXPECTED_BUILTINS = [
    "vivado",
    "vivadoaccelerator",
    "vitis",
    "quartus",
    "catapult",
    "symbolicexpression",
    "oneapi",
    "libero",
]

SELECTED_KEYS = [
    "OutputDir",
    "ProjectName",
    "Backend",
    "Version",
    "Part",
    "ClockPeriod",
    "ClockUncertainty",
    "IOType",
    "WriterConfig",
    "AcceleratorConfig",
    "Technology",
    "ASICLibs",
    "FIFO",
    "HyperoptHandshake",
    "FPGAFamily",
    "Board",
    "SmartHLSPath",
    "Compiler",
    "HLSIncludePath",
    "HLSLibsPath",
]

PREREQ_HINTS = {
    "vivado": "Vivado builds require vivado_hls on PATH.",
    "vitis": "Vitis builds require vitis-run on PATH.",
    "vivadoaccelerator": "Accelerator bitfile/package flows require the Vivado board toolchain.",
    "quartus": "Quartus builds require Intel HLS i++; FPGA synthesis also requires quartus_sh.",
    "catapult": "Catapult builds require catapult on PATH, or MGC_HOME/CATAPULT_HOME.",
    "symbolicexpression": "SymbolicExpression config needs Vivado/Vitis HLS include and library paths for math support.",
    "oneapi": "oneAPI builds require icpx, cmake, and a supported oneAPI FPGA compiler release.",
    "libero": "Libero config/build needs shls on PATH or an explicit SmartHLS installation path.",
}

NONFATAL_PREREQ_BACKENDS = {"symbolicexpression", "libero"}


def jsonable(value: Any) -> Any:
    """Convert hls4ml config values into JSON-safe data."""

    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def probe_backend(backend: str, create_config, registry: list[str], args: argparse.Namespace) -> dict[str, Any]:
    """Probe one backend's initial config without writing files."""

    key = backend.lower()
    record: dict[str, Any] = {
        "backend": backend,
        "registryKey": key,
        "registered": key in registry,
        "hint": PREREQ_HINTS.get(key),
    }
    if key not in registry:
        record.update({"status": "missing", "error": "backend not registered"})
        return record

    try:
        cfg = create_config(output_dir=args.output_dir, project_name=args.project_name, backend=backend)
        selected = {k: jsonable(cfg.get(k)) for k in SELECTED_KEYS if k in cfg}
        accel = cfg.get("AcceleratorConfig")
        if isinstance(accel, dict):
            for key in ("Board", "Interface", "Driver", "Platform"):
                if key not in selected and key in accel:
                    selected[key] = jsonable(accel.get(key))
            if "Precision" in accel and "AcceleratorPrecision" not in selected:
                selected["AcceleratorPrecision"] = jsonable(accel.get("Precision"))
        record.update({"status": "ok", "config": selected})
    except Exception as exc:  # noqa: BLE001 - this is an inspection script
        record.update(
            {
                "status": "prerequisite-error",
                "exceptionType": exc.__class__.__name__,
                "error": str(exc),
            }
        )
        if args.include_traceback:
            record["traceback"] = traceback.format_exc()
    return record


def print_text(summary: dict[str, Any]) -> None:
    """Emit a compact human-readable summary."""

    print(f"hls4ml version: {summary.get('hls4mlVersion')}")
    print("registry: " + ", ".join(summary["registry"]))
    if summary["missingExpectedBuiltins"]:
        print("missing expected built-ins: " + ", ".join(summary["missingExpectedBuiltins"]))
    print()

    for record in summary["records"]:
        print(f"[{record['status']}] {record['backend']}")
        if record.get("hint"):
            print(f"  hint: {record['hint']}")
        if record["status"] == "ok":
            for key, value in record["config"].items():
                print(f"  {key}: {value}")
        else:
            print(f"  error: {record.get('error')}")
        print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect hls4ml backend registry and create_config defaults without running synthesis."
    )
    parser.add_argument("--backend", action="append", help="Backend to probe. Repeat to probe multiple backends.")
    parser.add_argument("--output-dir", default="my-hls-test", help="OutputDir value used for create_config probes.")
    parser.add_argument("--project-name", default="myproject", help="ProjectName value used for create_config probes.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if a backend is missing or if a probe fails outside the known prerequisite-only cases.",
    )
    parser.add_argument("--include-traceback", action="store_true", help="Include traceback strings in JSON/text records.")
    args = parser.parse_args(argv)

    try:
        import hls4ml
        from hls4ml.utils.config import create_config
    except Exception as exc:  # noqa: BLE001 - import diagnostics
        print(f"Failed to import hls4ml: {exc}", file=sys.stderr)
        return 2

    registry = list(hls4ml.backends.get_available_backends())
    requested = args.backend if args.backend else registry
    records = [probe_backend(name, create_config, registry, args) for name in requested]
    missing_expected = [name for name in EXPECTED_BUILTINS if name not in registry]

    summary = {
        "hls4mlVersion": getattr(hls4ml, "__version__", None),
        "expectedBuiltins": EXPECTED_BUILTINS,
        "registry": registry,
        "missingExpectedBuiltins": missing_expected,
        "records": records,
    }

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_text(summary)

    failures = missing_expected or any(record["status"] == "missing" for record in records)
    failures = failures or any(
        record["status"] == "prerequisite-error" and record["backend"].lower() not in NONFATAL_PREREQ_BACKENDS
        for record in records
    )
    return 1 if args.strict and failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
