#!/usr/bin/env python3
"""Print the bundled Orbit custom-model architecture snapshot.

This script is intentionally safe:
- it does not require the original Orbit checkout to be present
- it reads only the bundled JSON snapshot by default
- optional live imports are best-effort and never fail the script
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / "references" / "architecture_snapshot.json"

KEY_FILES = [
    ROOT / "SKILL.md",
    ROOT / "references" / "architecture.md",
    ROOT / "references" / "build-your-own-model.md",
    ROOT / "references" / "troubleshooting.md",
    ROOT / "references" / "source-evidence.md",
    SNAPSHOT_PATH,
]

LIVE_MODULES = [
    "orbit.template.model_template",
    "orbit.template.ets",
    "orbit.template.lgt",
    "orbit.template.dlt",
    "orbit.template.ktrlite",
    "orbit.template.ktr",
    "orbit.forecaster.forecaster",
    "orbit.forecaster.map",
    "orbit.forecaster.full_bayes",
    "orbit.forecaster.svi",
    "orbit.estimators.base_estimator",
    "orbit.estimators.stan_estimator",
    "orbit.estimators.pyro_estimator",
    "orbit.pyro.lgt",
    "orbit.pyro.ktr",
    "orbit.utils.stan",
    "orbit.utils.set_cmdstan_path",
]


def load_snapshot() -> dict[str, Any]:
    if not SNAPSHOT_PATH.exists():
        raise SystemExit(f"missing snapshot: {SNAPSHOT_PATH}")
    return json.loads(SNAPSHOT_PATH.read_text())


def fmt_signature(entry: Any) -> str:
    if isinstance(entry, dict) and "signature" in entry:
        return entry["signature"]
    return str(entry)


def print_section(title: str) -> None:
    print(f"\n== {title} ==")


def print_snapshot(snapshot: dict[str, Any]) -> None:
    print_section("Snapshot")
    print(f"source_root: {snapshot.get('source_root')}")
    print(f"notebook: {snapshot.get('notebook')}")
    config = snapshot.get("config", {})
    print(f"CMDSTAN_VERSION: {config.get('CMDSTAN_VERSION')}")
    print(f"ORBIT_MODELS: {config.get('ORBIT_MODELS')}")

    print_section("Compatibility matrix")
    for model_name, estimators in snapshot.get("compatibility_matrix", {}).items():
        print(f"{model_name}: {', '.join(estimators)}")

    print_section("Core signatures")
    files = snapshot.get("files", {})
    for key in [
        "orbit/template/model_template.py",
        "orbit/forecaster/forecaster.py",
        "orbit/estimators/stan_estimator.py",
        "orbit/estimators/pyro_estimator.py",
        "orbit/utils/stan.py",
        "orbit/utils/set_cmdstan_path.py",
    ]:
        entry = files.get(key)
        if not entry:
            continue
        print(f"-- {key}")
        for name, payload in entry.items():
            if isinstance(payload, dict) and "methods" in payload:
                print(f"  {name}:")
                for method in payload.get("methods", []):
                    print(f"    {method['name']}{method['signature']}")
            else:
                print(f"  {name}: {payload}")

    print_section("Runtime notes")
    for note in snapshot.get("runtime_notes", []):
        print(f"- {note}")

    print_section("Evidence files")
    for path in KEY_FILES:
        print(f"- {path.relative_to(ROOT)}: {'yes' if path.exists() else 'missing'}")


def _sanitize_origin(origin: str | None) -> str:
    if not origin:
        return "<module>"
    path = Path(origin)
    for index in range(len(path.parts) - 1, -1, -1):
        if path.parts[index] == "orbit":
            return "/".join(path.parts[index:])
    return path.name


def _sanitize_exception_message(message: str) -> str:
    return re.sub(r"/[^\s)]+", "<path>", message)


def probe_live_imports() -> None:
    print_section("Live import probe")
    for mod_name in LIVE_MODULES:
        try:
            module = importlib.import_module(mod_name)
            origin = _sanitize_origin(getattr(module, "__file__", None))
            print(f"OK  {mod_name} -> {origin}")
        except Exception as exc:  # pragma: no cover - best effort only
            print(f"SKIP {mod_name} -> {type(exc).__name__}: {_sanitize_exception_message(str(exc))}")


def probe_dependency_specs() -> None:
    print_section("Dependency specs")
    for pkg in ["orbit", "cmdstanpy", "pyro", "importlib_resources"]:
        spec = importlib.util.find_spec(pkg)
        print(f"{pkg}: {'present' if spec else 'missing'}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--probe-installed",
        action="store_true",
        help="Try best-effort imports against the active Python environment.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the raw bundled snapshot as JSON instead of the summary.",
    )
    args = parser.parse_args()

    snapshot = load_snapshot()

    if args.json:
        print(json.dumps(snapshot, indent=2, ensure_ascii=False))
        return

    print_snapshot(snapshot)
    probe_dependency_specs()

    if args.probe_installed:
        probe_live_imports()


if __name__ == "__main__":
    main()
