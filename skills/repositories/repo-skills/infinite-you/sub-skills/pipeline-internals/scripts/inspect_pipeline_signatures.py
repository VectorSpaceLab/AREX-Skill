#!/usr/bin/env python3
"""Inspect InfiniteYou pipeline signatures safely from the bundled runtime.

This helper imports the generated skill's bundled runtime implementation by
default. It does not instantiate models, load checkpoints, or download weights.
Use --implementation-root only when intentionally comparing another compatible
source tree.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import os
import sys
import warnings
from pathlib import Path
from typing import Dict

MODULE_TARGETS = [
    ("pipelines.pipeline_infu_flux", "InfUFluxPipeline.__init__"),
    ("pipelines.pipeline_infu_flux", "InfUFluxPipeline.__call__"),
    ("pipelines.pipeline_flux_infusenet", "FluxInfuseNetPipeline.__call__"),
    ("pipelines.resampler", "Resampler.__init__"),
    ("pipelines.pipeline_flux_infusenet", "retrieve_timesteps"),
    ("pipelines.pipeline_flux_infusenet", "calculate_shift"),
]


def skill_root() -> Path:
    return Path(__file__).resolve().parents[3]


def bundled_runtime_root() -> Path:
    return skill_root() / "runtime"


def configure_no_network_version_checks() -> None:
    os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")
    os.environ.setdefault("ALBUMENTATIONS_DISABLE_VERSION_CHECK", "1")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    warnings.filterwarnings(
        "ignore",
        category=FutureWarning,
        message="The pynvml package is deprecated.*",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect InfiniteYou pipeline signatures without instantiating models.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--implementation-root",
        "--repo-root",
        dest="implementation_root",
        help="Optional override root containing pipelines/. Omit this to inspect the bundled runtime. The --repo-root alias is kept for compatibility.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a human-readable list.")
    return parser.parse_args()


def configure_implementation_path(implementation_root: str | None) -> Dict[str, object]:
    runtime = bundled_runtime_root()
    report: Dict[str, object] = {
        "bundled_runtime": str(runtime),
        "implementation_root": implementation_root,
        "selected": None,
        "warnings": [],
    }
    if not (runtime / "pipelines" / "pipeline_infu_flux.py").is_file():
        raise SystemExit(f"Bundled runtime is incomplete: {runtime}")
    sys.path.insert(0, str(runtime))
    report["selected"] = str(runtime)

    if implementation_root:
        root_path = Path(implementation_root).expanduser().resolve()
        if not root_path.is_dir():
            raise SystemExit(f"--implementation-root does not exist or is not a directory: {implementation_root}")
        if not (root_path / "pipelines" / "pipeline_infu_flux.py").is_file():
            raise SystemExit("--implementation-root must contain pipelines/pipeline_infu_flux.py")
        sys.path.insert(0, str(root_path))
        report["selected"] = str(root_path)
        report["warnings"] = ["Using an implementation override instead of the bundled runtime."]
    return report


def import_module(module_name: str):
    try:
        return importlib.import_module(module_name)
    except ImportError as exc:
        raise SystemExit(
            f"ImportError while importing {module_name}: {exc}\n"
            "Install runtime dependencies first, for example with the generated "
            "runtime/requirements.txt. This helper never downloads models or instantiates pipelines."
        ) from exc


def resolve_target(module, target_path: str):
    obj = module
    for part in target_path.split("."):
        obj = getattr(obj, part)
    return obj


def collect_signatures() -> Dict[str, str]:
    signatures: Dict[str, str] = {}
    for module_name, target_path in MODULE_TARGETS:
        module = import_module(module_name)
        target = resolve_target(module, target_path)
        try:
            signatures[target_path] = str(inspect.signature(target))
        except (TypeError, ValueError) as exc:
            raise SystemExit(f"Could not inspect {target_path} from {module_name}: {exc}") from exc
    return signatures


def main() -> int:
    configure_no_network_version_checks()
    args = parse_args()
    implementation = configure_implementation_path(args.implementation_root)
    signatures = collect_signatures()

    if args.json:
        print(json.dumps({"implementation": implementation, "signatures": signatures}, indent=2, sort_keys=True))
    else:
        print(f"Implementation source: {implementation['selected']}")
        for name, signature in signatures.items():
            print(f"{name}: {signature}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
