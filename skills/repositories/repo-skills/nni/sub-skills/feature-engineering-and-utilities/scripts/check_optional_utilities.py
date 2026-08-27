#!/usr/bin/env python3
"""Safely report import readiness for NNI feature-engineering and utility modules."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Optional, Tuple


@dataclass
class ProbeResult:
    module: str
    ok: bool
    version: Optional[str] = None
    error_type: Optional[str] = None
    error: Optional[str] = None


PROBES: Tuple[Tuple[str, str], ...] = (
    ("nni", "Core NNI package"),
    ("nni.feature_engineering", "Base feature-engineering package"),
    ("nni.feature_engineering.feature_selector", "Base FeatureSelector contract"),
    ("nni.algorithms.feature_engineering.gbdt_selector", "GBDTSelector module"),
    ("nni.algorithms.feature_engineering.gradient_selector", "FeatureGradientSelector module"),
    ("nni.common.serializer", "Trace serializer utilities"),
    ("nni.common.concrete_trace_utils", "Concrete trace package"),
    ("nni.common.graph_utils", "PyTorch JIT graph utilities"),
    ("nni.common.concrete_trace_utils.flop_utils", "FLOP utilities"),
    ("nni.common.concrete_trace_utils.counter", "FX graph profiler utilities"),
    ("torch", "PyTorch optional stack"),
    ("sklearn", "scikit-learn optional stack"),
    ("pandas", "pandas optional stack"),
    ("numpy", "NumPy optional stack"),
    ("scipy", "SciPy optional stack"),
    ("lightgbm", "LightGBM optional stack"),
    ("tabulate", "Profiler verbose table formatting"),
)


def get_version(module: Any) -> Optional[str]:
    version = getattr(module, "__version__", None)
    if version is not None:
        return str(version)
    version_module = getattr(module, "version", None)
    nested_version = getattr(version_module, "__version__", None)
    if nested_version is not None:
        return str(nested_version)
    return None


def probe_module(module_name: str) -> ProbeResult:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - diagnostic should capture any import-time failure.
        return ProbeResult(
            module=module_name,
            ok=False,
            error_type=exc.__class__.__name__,
            error=str(exc),
        )
    return ProbeResult(module=module_name, ok=True, version=get_version(module))


def build_summary(results: list) -> dict:
    by_module = {result.module: result for result in results}

    def ok(module_name: str) -> bool:
        return by_module.get(module_name, ProbeResult(module_name, False)).ok

    capabilities = {
        "base_feature_selector": ok("nni.feature_engineering.feature_selector"),
        "gbdt_selector": ok("nni.algorithms.feature_engineering.gbdt_selector"),
        "gradient_feature_selector": ok("nni.algorithms.feature_engineering.gradient_selector"),
        "serializer": ok("nni.common.serializer"),
        "concrete_trace": ok("nni.common.concrete_trace_utils"),
        "graph_utils": ok("nni.common.graph_utils"),
        "flop_utils": ok("nni.common.concrete_trace_utils.flop_utils"),
        "counter_pass": ok("nni.common.concrete_trace_utils.counter"),
    }
    missing_optional = sorted(result.module for result in results if not result.ok)
    return {
        "ok": all(result.ok for result in results if result.module.startswith("nni.common.serializer")),
        "capabilities": capabilities,
        "missing_or_failed_imports": missing_optional,
    }


def render_text(results: Iterable[ProbeResult], include_errors: bool) -> str:
    lines = ["NNI utility optional import report", ""]
    label_width = max(len(module) for module, _ in PROBES)
    descriptions = dict(PROBES)
    for result in results:
        status = "OK" if result.ok else "FAIL"
        version = f" version={result.version}" if result.version else ""
        lines.append(f"{status:4} {result.module:<{label_width}}  {descriptions.get(result.module, '')}{version}")
        if include_errors and not result.ok:
            lines.append(f"     {result.error_type}: {result.error}")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Report import readiness for NNI feature-engineering and standalone utility modules.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format. Defaults to text.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Shortcut for --format json.",
    )
    parser.add_argument(
        "--show-errors",
        action="store_true",
        help="Include import exception details in text output.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_format = "json" if args.json else args.format
    results = [probe_module(module_name) for module_name, _ in PROBES]
    payload = {
        "summary": build_summary(results),
        "probes": [asdict(result) for result in results],
    }
    if output_format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_text(results, include_errors=args.show_errors))
    return 0


if __name__ == "__main__":
    sys.exit(main())
