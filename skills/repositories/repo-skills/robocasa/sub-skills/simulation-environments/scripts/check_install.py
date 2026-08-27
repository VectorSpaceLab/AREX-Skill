#!/usr/bin/env python3
"""Diagnose RoboCasa package, asset, and render readiness without downloading.

This helper is intentionally read-only. It can be run from any current working
 directory. Examples:
    python check_install.py --help
    python check_install.py --json
    python check_install.py --probe-constructor --require-assets

By default, missing large external assets and optional render signals are
reported but do not fail a package-only check. Use --require-assets or
--require-renderer when those are acceptance requirements.
"""

from __future__ import annotations

import argparse
import contextlib
import ctypes.util
import importlib.metadata
import importlib.util
import io
import json
import os
import sys
from pathlib import Path
from typing import Any


EXPECTED_EXACT = {
    "numpy": "2.2.5",
    "mujoco": "3.3.1",
    "gymnasium": "0.29.1",
    "h5py": "3.16.0",
    "lerobot": "0.3.3",
}
DISTRIBUTION_NAMES = {
    "robocasa": "robocasa",
    "robosuite": "robosuite",
    **{name: name for name in EXPECTED_EXACT},
}


def _version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None
    except Exception:
        return None


def _version_tuple(value: str | None) -> tuple[int, ...] | None:
    if not value:
        return None
    parts: list[int] = []
    for part in value.split("."):
        digits = "".join(ch for ch in part if ch.isdigit())
        if not digits:
            break
        parts.append(int(digits))
    return tuple(parts) if parts else None


def _import_quietly() -> dict[str, Any]:
    """Import the public package while keeping optional warning text separate."""
    captured = io.StringIO()
    result: dict[str, Any] = {"ok": False, "error": None, "warnings": ""}
    try:
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
            import robocasa  # type: ignore[import-not-found]

        result["ok"] = True
        result["module"] = robocasa
        result["version"] = getattr(robocasa, "__version__", None)
        result["kitchen_environments"] = len(list(robocasa.ALL_KITCHEN_ENVIRONMENTS))
    except Exception as exc:  # import gates intentionally become structured output
        result["error"] = f"{type(exc).__name__}: {exc}"
    # Import-time warnings can contain machine-specific executable paths.
    # Report only their presence so the diagnostic remains safe to share.
    result["warnings_present"] = bool(captured.getvalue().strip())
    return result


def _package_root(module: Any | None) -> Path | None:
    if module is not None:
        try:
            return Path(next(iter(module.__path__)))
        except Exception:
            pass
    spec = importlib.util.find_spec("robocasa")
    if spec is not None and spec.submodule_search_locations:
        return Path(next(iter(spec.submodule_search_locations)))
    return None


def _asset_report(root: Path | None) -> dict[str, Any]:
    """Check representative paths, never enumerate or download large payloads."""
    if root is None:
        return {"status": "unknown", "missing": ["package-root"]}

    # The fixture registry is shipped with the code, but Window069 is a
    # representative downloaded fixture referenced by that registry. Object
    # and texture directories are separate download categories.
    checks = {
        "fixture_registry": root / "models" / "assets" / "fixtures" / "fixture_registry",
        "representative_fixture_xml": root
        / "models"
        / "assets"
        / "fixtures"
        / "windows"
        / "Window069"
        / "model.xml",
        "objaverse_objects": root / "models" / "assets" / "objects" / "objaverse",
        "lightwheel_objects": root / "models" / "assets" / "objects" / "lightwheel",
        "textures": root / "models" / "assets" / "textures",
    }
    present: dict[str, bool] = {}
    for label, path in checks.items():
        present[label] = path.exists()

    missing = [label for label, exists in present.items() if not exists]
    # A registry alone is useful code evidence but is not enough to reset.
    complete = not any(
        not present[label]
        for label in (
            "representative_fixture_xml",
            "objaverse_objects",
            "lightwheel_objects",
            "textures",
        )
    )
    return {
        "status": "ready" if complete else "incomplete",
        "present": present,
        "missing": missing,
        "note": "Representative checks only; a reset can require additional task-specific XML/meshes.",
    }


def _render_report() -> dict[str, Any]:
    display = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    egl = ctypes.util.find_library("EGL")
    osmesa = ctypes.util.find_library("OSMesa")
    mujoco_gl = os.environ.get("MUJOCO_GL")
    return {
        "display_signal": display,
        "egl_library": bool(egl),
        "osmesa_library": bool(osmesa),
        "mujoco_gl": mujoco_gl or "unset",
        "status": "signal-present" if (display or egl or osmesa) else "no-display-or-GL-signal",
        "note": "Signals do not prove that a reset, camera render, or video encode will succeed.",
    }


def _dependency_report() -> dict[str, Any]:
    versions = {name: _version(dist) for name, dist in DISTRIBUTION_NAMES.items()}
    exact = {
        name: {"expected": expected, "actual": versions.get(name), "ok": versions.get(name) == expected}
        for name, expected in EXPECTED_EXACT.items()
    }
    robosuite_version = versions.get("robosuite")
    robosuite_ok = (
        _version_tuple(robosuite_version) is not None
        and _version_tuple(robosuite_version) >= (1, 5, 2)
    )
    return {
        "versions": versions,
        "exact_gates": exact,
        "robosuite_gate": {
            "minimum": "1.5.2",
            "actual": robosuite_version,
            "ok": robosuite_ok,
        },
    }


def _constructor_probe(env_name: str, split: str, render_onscreen: bool) -> dict[str, Any]:
    captured = io.StringIO()
    result: dict[str, Any] = {"ok": False, "reset_called": False}
    try:
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
            from robocasa.utils.env_utils import create_env  # type: ignore[import-not-found]

            env = create_env(
                env_name,
                split=split,
                camera_names=[],
                render_onscreen=render_onscreen,
            )
        result.update(
            {
                "ok": True,
                "class": type(env).__name__,
                "horizon": getattr(env, "horizon", None),
                "ignore_done": getattr(env, "ignore_done", None),
                "render_onscreen": render_onscreen,
                "note": "Constructor only; reset was intentionally not called.",
            }
        )
        try:
            env.close()
        except Exception as exc:
            result["close_error"] = f"{type(exc).__name__}: {exc}"
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    # Keep warning output shareable; imports may print private executable paths.
    result["warnings_present"] = bool(captured.getvalue().strip())
    return result


def build_report(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    deps = _dependency_report()
    imported = _import_quietly()
    root = _package_root(imported.get("module"))
    assets = _asset_report(root)
    renderer = _render_report()

    package_gate_ok = all(item["ok"] for item in deps["exact_gates"].values()) and bool(
        deps["robosuite_gate"]["ok"]
    )
    # RoboCasa's own assertions are authoritative when import is attempted.
    package_gate_ok = package_gate_ok and bool(imported["ok"])

    report: dict[str, Any] = {
        "status": "ok" if package_gate_ok else "package-gate-failed",
        "package": deps,
        "robocasa_import": {
            key: value
            for key, value in imported.items()
            if key != "module"
        },
        "assets": assets,
        "render": renderer,
        "optional": {
            "mimicgen": _version("mimicgen"),
            "mimicgen_present": _version("mimicgen") is not None,
        },
    }

    if args.probe_constructor and package_gate_ok:
        report["constructor_probe"] = _constructor_probe(
            args.env_name, args.split, args.render_onscreen
        )

    exit_code = 0 if package_gate_ok else 1
    if args.require_assets and assets.get("status") != "ready":
        exit_code = max(exit_code, 2)
    if args.require_renderer and renderer.get("status") == "no-display-or-GL-signal":
        exit_code = max(exit_code, 3)
    if args.probe_constructor and not report.get("constructor_probe", {}).get("ok", False):
        exit_code = max(exit_code, 4)
    return report, exit_code


def _print_human(report: dict[str, Any], exit_code: int) -> None:
    print(f"status: {report['status']} (exit {exit_code})")
    package = report["package"]
    print("packages:")
    for name, version in package["versions"].items():
        print(f"  {name}: {version or 'MISSING'}")
    for name, gate in package["exact_gates"].items():
        print(f"  gate {name}: {'PASS' if gate['ok'] else 'FAIL'} (expected {gate['expected']})")
    print(f"  gate robosuite>=1.5.2: {'PASS' if package['robosuite_gate']['ok'] else 'FAIL'}")

    imported = report["robocasa_import"]
    print(f"robocasa import: {'PASS' if imported['ok'] else 'FAIL'}")
    if imported.get("error"):
        print(f"  error: {imported['error']}")
    if imported.get("kitchen_environments") is not None:
        print(f"  kitchen environments: {imported['kitchen_environments']}")

    assets = report["assets"]
    print(f"assets: {assets.get('status', 'unknown')}")
    if assets.get("missing"):
        print("  missing representative categories: " + ", ".join(assets["missing"]))
    renderer = report["render"]
    print(
        "render signals: "
        f"{renderer['status']} (DISPLAY={renderer['display_signal']}, "
        f"EGL={renderer['egl_library']}, OSMesa={renderer['osmesa_library']}, "
        f"MUJOCO_GL={renderer['mujoco_gl']})"
    )
    optional = report["optional"]
    print(f"MimicGen: {'present' if optional['mimicgen_present'] else 'absent (optional)'}")
    if "constructor_probe" in report:
        probe = report["constructor_probe"]
        print(f"constructor probe: {'PASS' if probe['ok'] else 'FAIL'}")
        if probe.get("error"):
            print(f"  error: {probe['error']}")
        if probe.get("note"):
            print(f"  note: {probe['note']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only RoboCasa package, asset, and render-backend diagnostic; never downloads."
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--probe-constructor",
        action="store_true",
        help="construct one environment without reset (asset-dependent reset is not attempted)",
    )
    parser.add_argument(
        "--env-name",
        default="PickPlaceCounterToCabinet",
        help="task name for --probe-constructor (default: %(default)s)",
    )
    parser.add_argument(
        "--split",
        choices=("pretrain", "target", "all"),
        default="pretrain",
        help="supported split for --probe-constructor (default: %(default)s)",
    )
    parser.add_argument(
        "--render-onscreen",
        action="store_true",
        help="request onscreen rendering for the constructor probe; requires a viewer",
    )
    parser.add_argument(
        "--require-assets",
        action="store_true",
        help="return exit code 2 when representative external assets are incomplete",
    )
    parser.add_argument(
        "--require-renderer",
        action="store_true",
        help="return exit code 3 when no display/EGL/OSMesa signal is detected",
    )
    args = parser.parse_args(argv)
    report, exit_code = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_human(report, exit_code)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
