#!/usr/bin/env python3
"""Inspect Cirq provider imports and signatures without live service calls.

This script is intentionally offline-only. It imports installed packages, inspects
public signatures, optionally performs a tiny Cirq JSON round-trip, and can check
that cirq_web returns structural HTML. It never creates cloud jobs, opens sockets,
uses credentials, or prints token values.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import inspect
import json
import os
import re
import sys
from typing import Any


CREDENTIAL_ENV_VARS = (
    "GOOGLE_APPLICATION_CREDENTIALS",
    "CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE",
    "CIRQ_IONQ_API_KEY",
    "IONQ_API_KEY",
    "CIRQ_IONQ_REMOTE_HOST",
    "IONQ_REMOTE_HOST",
    "AQT_ACCESS_TOKEN",
    "PASQAL_API_ACCESS_TOKEN",
)

DISTRIBUTIONS = {
    "cirq": "cirq-core",
    "cirq_google": "cirq-google",
    "cirq_ionq": "cirq-ionq",
    "cirq_aqt": "cirq-aqt",
    "cirq_pasqal": "cirq-pasqal",
    "cirq_web": "cirq-web",
}

SIGNATURE_TARGETS = {
    "cirq": ["to_json", "read_json"],
    "cirq_google": [
        "Engine",
        "get_engine_sampler",
        "CircuitSerializer",
        "SycamoreTargetGateset",
        "GoogleCZTargetGateset",
    ],
    "cirq_ionq": [
        "Service",
        "Sampler",
        "Serializer",
        "IonQTargetGateset",
        "AriaNativeGateset",
        "ForteNativeGateset",
    ],
    "cirq_aqt": ["AQTSampler", "AQTSamplerLocalSimulator"],
    "cirq_pasqal": [
        "PasqalSampler",
        "PasqalDevice",
        "PasqalVirtualDevice",
        "TwoDQubit",
        "ThreeDQubit",
    ],
    "cirq_web": ["Circuit3D", "Widget", "BlochSphere"],
}

METHOD_SIGNATURE_TARGETS = {
    "cirq_pasqal.TwoDQubit": ["square"],
    "cirq_pasqal.ThreeDQubit": ["cube"],
}


def _sanitize_signature(value: str) -> str:
    """Remove nondeterministic object addresses from a signature string."""
    value = re.sub(r"0x[0-9a-fA-F]+", "0x...", value)
    value = re.sub(r"object at 0x\.\.\.>", "object at 0x...>", value)
    return value


def _version_for(module_name: str) -> str | None:
    distribution = DISTRIBUTIONS.get(module_name)
    if not distribution:
        return None
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def _safe_signature(obj: Any) -> str:
    try:
        return _sanitize_signature(str(inspect.signature(obj)))
    except (TypeError, ValueError) as exc:
        return f"<unavailable: {type(exc).__name__}: {exc}>"


def import_and_inspect(allow_missing: bool) -> tuple[dict[str, Any], bool]:
    report: dict[str, Any] = {
        "offline_only": True,
        "credential_environment": {name: (name in os.environ) for name in CREDENTIAL_ENV_VARS},
        "packages": {},
        "signatures": {},
    }
    ok = True
    modules: dict[str, Any] = {}

    for module_name in DISTRIBUTIONS:
        package_info: dict[str, Any] = {"imported": False, "version": None}
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover - depends on external environment
            ok = False
            package_info["error"] = f"{type(exc).__name__}: {exc}"
            report["packages"][module_name] = package_info
            if not allow_missing:
                continue
        else:
            modules[module_name] = module
            package_info["imported"] = True
            package_info["version"] = getattr(module, "__version__", None) or _version_for(module_name)
            report["packages"][module_name] = package_info

    for module_name, names in SIGNATURE_TARGETS.items():
        module = modules.get(module_name)
        if module is None:
            continue
        for name in names:
            obj = getattr(module, name, None)
            key = f"{module_name}.{name}"
            if obj is None:
                ok = False
                report["signatures"][key] = "<missing>"
            else:
                report["signatures"][key] = _safe_signature(obj)

    for qualified_name, method_names in METHOD_SIGNATURE_TARGETS.items():
        module_name, class_name = qualified_name.split(".", 1)
        module = modules.get(module_name)
        if module is None:
            continue
        cls = getattr(module, class_name, None)
        if cls is None:
            ok = False
            report["signatures"][qualified_name] = "<missing>"
            continue
        for method_name in method_names:
            method = getattr(cls, method_name, None)
            key = f"{qualified_name}.{method_name}"
            if method is None:
                ok = False
                report["signatures"][key] = "<missing>"
            else:
                report["signatures"][key] = _safe_signature(method)

    return report, ok or allow_missing


def add_json_roundtrip(report: dict[str, Any]) -> bool:
    try:
        import cirq

        q = cirq.LineQubit(0)
        circuit = cirq.Circuit(cirq.X(q) ** 0.5, cirq.measure(q, key="m"))
        json_text = cirq.to_json(circuit)
        loaded = cirq.read_json(json_text=json_text)
        report["json_roundtrip"] = {
            "checked": True,
            "object_type": type(loaded).__name__,
            "equal": loaded == circuit,
            "json_length": len(json_text),
            "contains_cirq_type": "cirq_type" in json_text,
        }
        return loaded == circuit
    except Exception as exc:  # pragma: no cover - depends on external environment
        report["json_roundtrip"] = {"checked": True, "error": f"{type(exc).__name__}: {exc}"}
        return False


def add_widget_html_check(report: dict[str, Any]) -> bool:
    try:
        import cirq
        import cirq_web

        q0, q1 = cirq.LineQubit.range(2)
        circuit = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1), cirq.measure(q0, q1, key="m"))
        html = cirq_web.Circuit3D(circuit)._repr_html_()
        report["widget_html"] = {
            "checked": True,
            "contains_div": "<div" in html,
            "contains_script": "<script" in html,
            "length": len(html),
        }
        return "<div" in html and "<script" in html
    except Exception as exc:  # pragma: no cover - depends on external environment
        report["widget_html"] = {"checked": True, "error": f"{type(exc).__name__}: {exc}"}
        return False


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Offline import/signature inspection for Cirq provider packages.",
        epilog=(
            "The script deliberately avoids Engine/Service/Sampler live methods, resource "
            "discovery, credential values, sockets, browser opening, and cloud jobs."
        ),
    )
    parser.add_argument(
        "--skip-json-roundtrip",
        action="store_true",
        help="Skip the tiny Cirq to_json/read_json round-trip check.",
    )
    parser.add_argument(
        "--check-widget-html",
        action="store_true",
        help="Check cirq_web.Circuit3D._repr_html_ structural output without opening a browser.",
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Report missing optional provider packages but exit successfully.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output with indentation.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    report, ok = import_and_inspect(allow_missing=args.allow_missing)

    if not args.skip_json_roundtrip:
        ok = add_json_roundtrip(report) and ok
    else:
        report["json_roundtrip"] = {"checked": False}

    if args.check_widget_html:
        ok = add_widget_html_check(report) and ok
    else:
        report["widget_html"] = {"checked": False}

    report["status"] = "ok" if ok else "failed"
    json.dump(report, sys.stdout, indent=2 if args.pretty else None, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
