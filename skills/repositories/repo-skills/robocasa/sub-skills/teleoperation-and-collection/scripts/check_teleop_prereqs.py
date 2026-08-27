#!/usr/bin/env python3
"""Safely inspect RoboCasa teleoperation and collection prerequisites.

The default mode reads package metadata, display environment variables, command
availability, and (when requested) output-directory permissions. It does not
import RoboCasa or pynput, instantiate an environment, open a viewer, write any
file, or enumerate/open an HID device.

HID enumeration is opt-in with ``--enumerate-hid``. Enumeration queries the HID
subsystem but this helper never calls ``hid.device().open*``.

Examples:
    python scripts/check_teleop_prereqs.py --device keyboard
    python scripts/check_teleop_prereqs.py --device spacemouse
    python scripts/check_teleop_prereqs.py --device spacemouse --enumerate-hid
    python scripts/check_teleop_prereqs.py --output-directory ./collected-demos
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import shutil
import sys
from typing import Any


EXPECTED_VERSIONS = {
    "robocasa": ("exact", "1.0.1"),
    "mujoco": ("exact", "3.3.1"),
    "numpy": ("exact", "2.2.5"),
    "robosuite": ("minimum", "1.5.2"),
}

# Import names differ from some distribution names.
REQUIRED_DISTRIBUTIONS = {
    "robocasa": "robocasa",
    "robosuite": "robosuite",
    "mujoco": "mujoco",
    "numpy": "numpy",
    "pynput": "pynput",
    "hidapi": "hid",
    "h5py": "h5py",
    "imageio": "imageio",
    "termcolor": "termcolor",
    "PyYAML": "yaml",
    "torch": "torch",
}

OPTIONAL_CONVERSION_DISTRIBUTIONS = {
    "lerobot": "lerobot",
}


def parse_int(value: str) -> int:
    """Parse decimal or ``0x``-prefixed integer CLI values."""
    try:
        return int(value, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid integer: {value!r}") from exc


def version_tuple(value: str) -> tuple[int, ...]:
    """Extract a numeric prefix suitable for the pinned versions used here."""
    match = re.match(r"^(\d+(?:\.\d+)*)", value)
    if not match:
        return ()
    return tuple(int(part) for part in match.group(1).split("."))


def distribution_probe(distribution: str, module: str) -> dict[str, Any]:
    """Inspect metadata and module discoverability without importing the module."""
    try:
        version = metadata.version(distribution)
        installed = True
        error = None
    except metadata.PackageNotFoundError:
        version = None
        installed = False
        error = f"distribution {distribution!r} is not installed"

    try:
        discoverable = importlib.util.find_spec(module) is not None
    except (ImportError, AttributeError, ValueError) as exc:
        discoverable = False
        error = f"module discovery failed: {type(exc).__name__}: {exc}"

    return {
        "distribution": distribution,
        "module": module,
        "installed": installed,
        "discoverable": discoverable,
        "version": version,
        "error": error,
    }


def check_version(name: str, probe: dict[str, Any]) -> dict[str, Any]:
    rule, expected = EXPECTED_VERSIONS[name]
    actual = probe["version"]
    if actual is None:
        return {"rule": rule, "expected": expected, "ok": False}
    if rule == "exact":
        ok = actual == expected
    else:
        ok = version_tuple(actual) >= version_tuple(expected)
    return {"rule": rule, "expected": expected, "ok": ok}


def display_probe() -> dict[str, Any]:
    system = platform.system().lower()
    display = bool(os.environ.get("DISPLAY"))
    wayland = bool(os.environ.get("WAYLAND_DISPLAY"))
    session_type = os.environ.get("XDG_SESSION_TYPE") or None

    if system == "linux":
        available = display or wayland
        if not available:
            note = "No DISPLAY or WAYLAND_DISPLAY is set; pynput and onscreen MuJoCo are not ready."
        elif wayland and not display:
            note = "Wayland is advertised, but pynput may still require XWayland or another supported backend."
        else:
            note = "A display variable is set; connection, focus, and pynput backend access remain untested."
    elif system == "darwin":
        available = True
        note = "macOS detected; Accessibility/input permission and actual viewer startup remain untested."
    else:
        available = True
        note = "Display readiness is not inferred on this platform; viewer and input access remain untested."

    return {
        "system": system,
        "display_set": display,
        "wayland_display_set": wayland,
        "session_type": session_type,
        "available": available,
        "note": note,
        "mjpython_on_path": shutil.which("mjpython") is not None,
    }


def nearest_existing_ancestor(path: Path) -> Path:
    candidate = path
    while not candidate.exists() and candidate != candidate.parent:
        candidate = candidate.parent
    return candidate


def output_probe(raw_path: str | None) -> dict[str, Any] | None:
    if raw_path is None:
        return None

    path = Path(raw_path).expanduser()
    ancestor = nearest_existing_ancestor(path)
    result: dict[str, Any] = {
        "requested": str(path),
        "exists": path.exists(),
        "is_directory": path.is_dir() if path.exists() else None,
        "nearest_existing_ancestor": str(ancestor),
        "writable": False,
        "free_bytes": None,
        "note": None,
    }

    if path.exists() and not path.is_dir():
        result["note"] = "The requested output path exists but is not a directory."
        return result
    if not ancestor.exists() or not ancestor.is_dir():
        result["note"] = "No existing directory ancestor could be inspected."
        return result

    result["writable"] = os.access(ancestor, os.W_OK | os.X_OK)
    try:
        result["free_bytes"] = shutil.disk_usage(ancestor).free
    except OSError as exc:
        result["note"] = f"Could not inspect free space: {type(exc).__name__}: {exc}"

    if result["note"] is None:
        if result["writable"]:
            result["note"] = (
                "Nearest existing ancestor appears writable; no directory or file was created."
            )
        else:
            result["note"] = "Nearest existing ancestor is not writable by this process."
    return result


def enumerate_hid(vendor_id: int, product_id: int) -> dict[str, Any]:
    """Enumerate HID metadata without opening a device handle."""
    result: dict[str, Any] = {
        "attempted": True,
        "ok": False,
        "configured_vendor_id": vendor_id,
        "configured_product_id": product_id,
        "configured_match": False,
        "three_dconnexion_count": 0,
        "devices": [],
        "error": None,
    }
    try:
        import hid  # Imported only after explicit --enumerate-hid.

        entries = hid.enumerate()
        safe_entries = []
        for entry in entries:
            manufacturer = entry.get("manufacturer_string")
            product = entry.get("product_string")
            current_vendor = entry.get("vendor_id")
            current_product = entry.get("product_id")
            is_3dconnexion = manufacturer == "3Dconnexion"
            is_configured = (
                current_vendor == vendor_id and current_product == product_id
            )
            if not (is_3dconnexion or is_configured):
                continue
            safe_entries.append(
                {
                    "manufacturer": manufacturer,
                    "product": product,
                    "vendor_id": current_vendor,
                    "product_id": current_product,
                    "vendor_id_hex": (
                        f"0x{current_vendor:04x}" if isinstance(current_vendor, int) else None
                    ),
                    "product_id_hex": (
                        f"0x{current_product:04x}" if isinstance(current_product, int) else None
                    ),
                    "matches_configured_ids": is_configured,
                }
            )
            result["configured_match"] = result["configured_match"] or is_configured
            if is_3dconnexion:
                result["three_dconnexion_count"] += 1
        result["devices"] = safe_entries
        result["ok"] = result["three_dconnexion_count"] > 0 or result["configured_match"]
    except Exception as exc:  # HID backends raise platform-specific OSError variants.
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect RoboCasa teleoperation prerequisites without opening a viewer, "
            "writing a dataset, or querying HID unless explicitly requested."
        )
    )
    parser.add_argument(
        "--device",
        choices=("keyboard", "spacemouse", "auto"),
        default="keyboard",
        help="Input path to assess (default: keyboard).",
    )
    parser.add_argument(
        "--output-directory",
        help="Check the nearest existing ancestor for write access without creating anything.",
    )
    parser.add_argument(
        "--enumerate-hid",
        action="store_true",
        help="Explicitly query HID metadata; never opens a device handle.",
    )
    parser.add_argument(
        "--vendor-id",
        type=parse_int,
        default=9583,
        help="Configured SpaceMouse vendor ID, decimal or 0x-prefixed (default: 9583).",
    )
    parser.add_argument(
        "--product-id",
        type=parse_int,
        default=50741,
        help="Configured SpaceMouse product ID, decimal or 0x-prefixed (default: 50741).",
    )
    parser.add_argument(
        "--check-lerobot",
        action="store_true",
        help="Also report optional LeRobot conversion package readiness.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    packages = {
        name: distribution_probe(name, module)
        for name, module in REQUIRED_DISTRIBUTIONS.items()
    }
    if args.check_lerobot:
        packages.update(
            {
                name: distribution_probe(name, module)
                for name, module in OPTIONAL_CONVERSION_DISTRIBUTIONS.items()
            }
        )

    version_checks = {
        name: check_version(name, packages[name]) for name in EXPECTED_VERSIONS
    }
    display = display_probe()
    output = output_probe(args.output_directory)

    hid_result: dict[str, Any] = {"attempted": False}
    if args.enumerate_hid:
        hid_result = enumerate_hid(args.vendor_id, args.product_id)

    failures: list[str] = []
    warnings: list[str] = []

    for name in REQUIRED_DISTRIBUTIONS:
        probe = packages[name]
        if not probe["installed"] or not probe["discoverable"]:
            failures.append(f"required package/module unavailable: {name}/{probe['module']}")
    for name, check in version_checks.items():
        if not check["ok"]:
            failures.append(
                f"version mismatch: {name} requires {check['rule']} {check['expected']}"
            )

    if not display["available"]:
        failures.append("no graphical display advertised for live viewer/input")
    elif display["system"] == "linux" and display["wayland_display_set"] and not display["display_set"]:
        warnings.append("Wayland-only session: verify pynput backend compatibility before live control")

    if display["system"] == "darwin" and not display["mjpython_on_path"]:
        failures.append("macOS interactive workflow requires mjpython on PATH")

    if output is not None and not output["writable"]:
        failures.append("output directory or its nearest existing ancestor is not writable")

    if args.device == "spacemouse" and not args.enumerate_hid:
        warnings.append("SpaceMouse visibility and permissions were not queried; use --enumerate-hid explicitly")
    if args.device == "auto":
        warnings.append("collector auto-selection requires an exact configured vendor/product ID match")

    if args.enumerate_hid:
        if not hid_result.get("ok", False):
            failures.append("HID enumeration did not find an eligible 3Dconnexion/configured device")
        elif not hid_result.get("configured_match", False):
            warnings.append(
                "3Dconnexion device found, but configured IDs do not match; collector auto-selection may choose keyboard"
            )

    if args.check_lerobot:
        for name in OPTIONAL_CONVERSION_DISTRIBUTIONS:
            probe = packages[name]
            if not probe["installed"] or not probe["discoverable"]:
                warnings.append(f"optional conversion package/module unavailable: {name}/{probe['module']}")

    report = {
        "ready_for_interactive_attempt": not failures,
        "device": args.device,
        "packages": packages,
        "version_checks": version_checks,
        "display": display,
        "output": output,
        "hid": hid_result,
        "failures": failures,
        "warnings": warnings,
        "safety": {
            "viewer_opened": False,
            "dataset_written": False,
            "device_opened": False,
            "hid_enumerated": bool(args.enumerate_hid),
            "package_imports_avoided": not args.enumerate_hid,
        },
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("RoboCasa teleoperation prerequisite check")
        print(f"  result: {'READY FOR INTERACTIVE ATTEMPT' if not failures else 'NOT READY'}")
        print(f"  device: {args.device}")
        print(f"  display: {display['note']}")
        print("  package metadata:")
        for name, probe in packages.items():
            status = "ok" if probe["installed"] and probe["discoverable"] else "missing"
            print(f"    - {name}: {status} (version={probe['version'] or 'unknown'})")
        for name, check in version_checks.items():
            if not check["ok"]:
                print(
                    f"    - required: {name} {check['rule']} {check['expected']}"
                )
        if output is not None:
            print(f"  output: {output['note']}")
            if output["free_bytes"] is not None:
                print(f"  free bytes at checked ancestor: {output['free_bytes']}")
        if args.enumerate_hid:
            print(
                "  HID: "
                f"{len(hid_result.get('devices', []))} relevant entrie(s); "
                f"configured match={hid_result.get('configured_match', False)}"
            )
            for entry in hid_result.get("devices", []):
                print(
                    "    - "
                    f"{entry['manufacturer'] or 'unknown'} {entry['product'] or 'unknown'} "
                    f"{entry['vendor_id_hex']}:{entry['product_id_hex']}"
                )
            if hid_result.get("error"):
                print(f"    enumeration error: {hid_result['error']}")
        if warnings:
            print("  warnings:")
            for warning in warnings:
                print(f"    - {warning}")
        if failures:
            print("  failures:")
            for failure in failures:
                print(f"    - {failure}")
        print("  safety: no viewer opened; no device opened; no dataset written")

    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
