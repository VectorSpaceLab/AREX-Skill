#!/usr/bin/env python3
"""Credential-free Cirq environment and smoke checker.

This helper verifies that Cirq and, optionally, the provider packages import in
the active Python environment. It performs only local CPU work: a tiny circuit
simulation and a JSON roundtrip. It never reads a source checkout, contacts
cloud services, or uses credentials.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib import metadata
from typing import Any


def distribution_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not-installed"


def import_module(name: str) -> dict[str, Any]:
    try:
        mod = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - environment dependent.
        return {"imported": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"imported": True, "version": getattr(mod, "__version__", None)}


def cirq_smoke() -> dict[str, Any]:
    import cirq

    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1), cirq.measure(q0, q1, key="m"))
    result = cirq.Simulator(seed=1234).run(circuit, repetitions=8)
    histogram = {str(k): v for k, v in sorted(result.histogram(key="m").items())}
    json_text = cirq.to_json(circuit)
    restored = cirq.read_json(json_text=json_text)
    return {
        "circuit": str(circuit),
        "histogram": histogram,
        "json_roundtrip_equal": restored == circuit,
        "measurement_keys": sorted(circuit.all_measurement_key_names()),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify local Cirq imports, versions, a tiny simulation, and JSON roundtrip."
    )
    parser.add_argument(
        "--skip-providers",
        action="store_true",
        help="Check only the main cirq package and skip provider package imports.",
    )
    parser.add_argument(
        "--text",
        action="store_true",
        help="Print a compact text report instead of JSON.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    modules = ["cirq"]
    distributions = ["cirq-core"]
    if not args.skip_providers:
        modules.extend(["cirq_google", "cirq_ionq", "cirq_aqt", "cirq_pasqal", "cirq_web"])
        distributions.extend(
            ["cirq-google", "cirq-ionq", "cirq-aqt", "cirq-pasqal", "cirq-web"]
        )

    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "distributions": {name: distribution_version(name) for name in distributions},
        "imports": {name: import_module(name) for name in modules},
        "offline_only": True,
    }

    if report["imports"]["cirq"].get("imported"):
        try:
            report["smoke"] = cirq_smoke()
        except Exception as exc:  # pragma: no cover - environment dependent.
            report["smoke"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    else:
        report["smoke"] = {"ok": False, "error": "cirq import failed"}

    failed_imports = [name for name, item in report["imports"].items() if not item.get("imported")]
    smoke_failed = not report.get("smoke", {}).get("json_roundtrip_equal", False)
    status = "ok" if not failed_imports and not smoke_failed else "failed"
    report["status"] = status

    if args.text:
        print(f"status: {status}")
        print("distributions:")
        for name, version in report["distributions"].items():
            print(f"  {name}: {version}")
        print("imports:")
        for name, item in report["imports"].items():
            print(f"  {name}: {'ok' if item.get('imported') else item.get('error')}")
        print("smoke:", report["smoke"])
    else:
        print(json.dumps(report, indent=2, sort_keys=True))

    return 0 if status == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
