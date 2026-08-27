#!/usr/bin/env python3
"""Check optional DreamerV3 environment-suite module availability.

The checker uses importlib metadata/spec lookups instead of constructing heavy
Atari, DMLab, MuJoCo, Minecraft, or ProcGen environments.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import os
import platform
import shutil
import sys
from typing import Dict, Iterable, List, Optional


SUITES = [
    {
        "suite": "atari/atari100k",
        "task_prefixes": ["atari", "atari100k"],
        "modules": ["ale_py", "AutoROM"],
        "distributions": ["ale-py", "autorom"],
        "notes": "Needs Atari ROMs from AutoROM or ALE_ROM_PATH; Pillow is used for default resize, OpenCV only for resize=opencv.",
    },
    {
        "suite": "crafter",
        "task_prefixes": ["crafter"],
        "modules": ["crafter"],
        "distributions": ["crafter"],
        "notes": "Required only for Crafter reward/noreward tasks; achievement stats require env logging to be enabled.",
    },
    {
        "suite": "dmc/loconav",
        "task_prefixes": ["dmc", "loconav"],
        "modules": ["dm_control"],
        "distributions": ["dm-control"],
        "notes": "MuJoCo rendering often needs MUJOCO_GL=egl plus GL/EGL system libraries on headless hosts.",
    },
    {
        "suite": "dmlab",
        "task_prefixes": ["dmlab"],
        "modules": ["deepmind_lab"],
        "distributions": ["deepmind-lab"],
        "notes": "Native DMLab install is system-sensitive and NumPy-version-sensitive.",
    },
    {
        "suite": "gym/memmaze",
        "task_prefixes": ["gym", "memmaze"],
        "modules": ["gym", "memory_maze"],
        "distributions": ["gym", "memory-maze"],
        "notes": "Generic Gym tasks need gym; Memory Maze additionally needs memory_maze registration.",
    },
    {
        "suite": "procgen",
        "task_prefixes": ["procgen"],
        "modules": ["procgen", "gym"],
        "distributions": ["procgen", "procgen-mirror", "gym"],
        "notes": "The wrapper tries both procgen namespace registration forms; package registration must exist.",
    },
    {
        "suite": "minecraft",
        "task_prefixes": ["minecraft"],
        "modules": ["minerl"],
        "distributions": ["minerl", "minerl-mirror"],
        "notes": "MineRL tasks usually need Java and a Python/platform-compatible MineRL build.",
    },
    {
        "suite": "bsuite",
        "task_prefixes": ["bsuite"],
        "modules": ["bsuite"],
        "distributions": ["bsuite"],
        "notes": "BSuite logging is stateful; interrupted runs may not resume cleanly.",
    },
]

LIGHT_MODULES = ["PIL", "cv2"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Report optional DreamerV3 environment-suite module availability "
            "without constructing heavy environments."
        )
    )
    parser.add_argument(
        "--task",
        default="",
        help="Optional task id such as atari_pong or dmc_walker_walk; marks matching suite as selected.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a text table.",
    )
    parser.add_argument(
        "--include-light",
        action="store_true",
        help="Also report light helper modules such as PIL and cv2.",
    )
    return parser.parse_args()


def find_module(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, AttributeError, ValueError):
        return False


def dist_version(names: Iterable[str]) -> Optional[str]:
    for name in names:
        try:
            return importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            continue
    return None


def task_prefix(task: str) -> str:
    return task.split("_", 1)[0] if task else ""


def suite_status(suite: Dict[str, object], selected_prefix: str) -> Dict[str, object]:
    modules = list(suite["modules"])  # type: ignore[index]
    distributions = list(suite["distributions"])  # type: ignore[index]
    module_status = {name: find_module(name) for name in modules}
    version = dist_version(distributions)
    available = all(module_status.values())
    selected = selected_prefix in suite["task_prefixes"]  # type: ignore[operator]
    if selected and not available:
        severity = "missing-selected"
    elif available:
        severity = "available"
    else:
        severity = "missing-optional"
    return {
        "suite": suite["suite"],
        "task_prefixes": suite["task_prefixes"],
        "selected": selected,
        "available": available,
        "severity": severity,
        "modules": module_status,
        "version": version,
        "notes": suite["notes"],
    }


def build_report(task: str, include_light: bool) -> Dict[str, object]:
    selected_prefix = task_prefix(task)
    suites = [suite_status(suite, selected_prefix) for suite in SUITES]
    light = {}
    if include_light:
        light = {name: find_module(name) for name in LIGHT_MODULES}
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "task": task,
        "selected_prefix": selected_prefix,
        "mujo_co_gl": os.environ.get("MUJOCO_GL", ""),
        "ale_rom_path_set": bool(os.environ.get("ALE_ROM_PATH")),
        "java_on_path": shutil.which("java") is not None,
        "suites": suites,
        "light_modules": light,
    }


def print_text(report: Dict[str, object]) -> None:
    print(f"python\t{report['python']}")
    print(f"platform\t{report['platform']}")
    if report["task"]:
        print(f"task\t{report['task']}\tselected_prefix={report['selected_prefix']}")
    print(f"MUJOCO_GL\t{report['mujo_co_gl'] or 'unset'}")
    print(f"ALE_ROM_PATH\t{'set' if report['ale_rom_path_set'] else 'unset'}")
    print(f"java\t{'available' if report['java_on_path'] else 'missing'}")
    print("suite\tselected\tseverity\tmodules\tversion\tnotes")
    for suite in report["suites"]:  # type: ignore[index]
        modules = suite["modules"]  # type: ignore[index]
        module_text = ",".join(
            f"{name}={'yes' if present else 'no'}"
            for name, present in modules.items()  # type: ignore[union-attr]
        )
        print(
            "\t".join(
                [
                    str(suite["suite"]),
                    "yes" if suite["selected"] else "no",
                    str(suite["severity"]),
                    module_text,
                    str(suite["version"] or ""),
                    str(suite["notes"]),
                ]
            )
        )
    if report["light_modules"]:  # type: ignore[index]
        print("light_module\tavailable")
        for name, present in report["light_modules"].items():  # type: ignore[union-attr]
            print(f"{name}\t{'yes' if present else 'no'}")


def main() -> int:
    args = parse_args()
    report = build_report(args.task, args.include_light)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    missing_selected = [
        suite
        for suite in report["suites"]  # type: ignore[index]
        if suite["severity"] == "missing-selected"
    ]
    return 1 if missing_selected else 0


if __name__ == "__main__":
    raise SystemExit(main())
