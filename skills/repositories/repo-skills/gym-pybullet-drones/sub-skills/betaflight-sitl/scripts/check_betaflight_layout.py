#!/usr/bin/env python3
"""Check whether the external Betaflight SITL layout expected by BetaAviary exists.

The helper is read-only. It inspects the installed gym-pybullet-drones package to
find the expected base layout, reports per-drone SITL artifacts, and prints a JSON
summary that future agents can use before attempting execution.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any


def _default_base_dir() -> Path:
    from importlib import import_module

    beta_module = import_module("gym_pybullet_drones.envs.BetaAviary")
    return Path(beta_module.__file__).resolve().parents[2] / "betaflight_sitl"


@dataclass
class Entry:
    folder: Path
    executable: Path
    eeprom: Path
    present: bool


def inspect_layout(base_dir: str | Path | None, num_drones: int) -> dict[str, Any]:
    root = Path(base_dir).expanduser().resolve() if base_dir is not None else _default_base_dir()
    entries: list[Entry] = []
    for idx in range(num_drones):
        folder = root / f"bf{idx}"
        executable = folder / "obj" / "main" / "betaflight_SITL.elf"
        eeprom = folder / "eeprom.bin"
        entries.append(Entry(folder=folder, executable=executable, eeprom=eeprom, present=folder.exists() and executable.exists()))

    asset_root = files("gym_pybullet_drones") / "assets"
    package_assets = {
        "beta-traj.csv": (asset_root / "beta-traj.csv").is_file(),
        "eeprom.bin": (asset_root / "eeprom.bin").is_file(),
    }
    launcher = shutil.which("gnome-terminal") is not None
    payload: dict[str, Any] = {
        "base_dir": str(root),
        "num_drones": int(num_drones),
        "package_assets": package_assets,
        "terminal_launcher": {"gnome-terminal": launcher},
        "drone_layout": [
            {
                "drone": idx,
                "folder": str(entry.folder),
                "executable": str(entry.executable),
                "eeprom": str(entry.eeprom),
                "present": entry.present,
                "missing": [name for name, path in (("folder", entry.folder), ("executable", entry.executable), ("eeprom", entry.eeprom)) if not path.exists()],
            }
            for idx, entry in enumerate(entries)
        ],
        "ports": {
            str(idx): {"pwm": 9002 + 10 * idx, "state": 9003 + 10 * idx, "rc": 9004 + 10 * idx}
            for idx in range(num_drones)
        },
    }
    payload["complete"] = all(item["present"] for item in payload["drone_layout"]) and all(package_assets.values())
    payload["missing_count"] = sum(len(item["missing"]) for item in payload["drone_layout"])
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check the Betaflight SITL layout expected by BetaAviary.")
    parser.add_argument("--base-dir", default=None, help="Betaflight SITL base directory. Defaults to the package-relative location that BetaAviary expects.")
    parser.add_argument("--num-drones", type=int, default=2, help="Number of bfN directories to verify.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.num_drones <= 0:
        raise SystemExit("--num-drones must be a positive integer")
    try:
        payload = inspect_layout(args.base_dir, args.num_drones)
    except Exception as exc:  # noqa: BLE001 - CLI boundary.
        raise SystemExit(
            "Failed to inspect the Betaflight SITL layout. Ensure the gym-pybullet-drones package is installed "
            f"and the external layout exists if you intend to execute BetaAviary. Original error: {type(exc).__name__}: {exc}"
        ) from exc

    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if payload["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
