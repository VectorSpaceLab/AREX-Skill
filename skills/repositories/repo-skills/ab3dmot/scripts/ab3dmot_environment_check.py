#!/usr/bin/env python3
"""Safe AB3DMOT import/config/API smoke checker.

This script is designed for agents using the generated AB3DMOT repo skill. It
performs read-only import and parser checks and can optionally run one synthetic
AB3DMOT.track call that does not require dataset files.
"""
from __future__ import annotations

import argparse
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check AB3DMOT imports and optional synthetic tracking smoke.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="AB3DMOT checkout root; default: current directory")
    parser.add_argument("--toolbox-root", type=Path, default=None, help="Optional Xinshuo_PyToolbox root to add to sys.path")
    parser.add_argument("--smoke-track", action="store_true", help="Run one no-dataset AB3DMOT.track call")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    return parser.parse_args(argv)


def add_paths(repo_root: Path, toolbox_root: Optional[Path]) -> None:
    for path in [repo_root, toolbox_root]:
        if path is None:
            continue
        text = str(path.resolve())
        if text not in sys.path:
            sys.path.insert(0, text)


def check_paths(repo_root: Path, toolbox_root: Optional[Path]) -> List[str]:
    errors: List[str] = []
    for rel in ["AB3DMOT_libs", "configs", "main.py"]:
        if not (repo_root / rel).exists():
            errors.append(f"repo root does not contain {rel}")
    if toolbox_root is not None:
        for rel in ["xinshuo_io", "xinshuo_miscellaneous"]:
            if not (toolbox_root / rel).exists():
                errors.append(f"toolbox root does not contain {rel}")
    return errors


def import_facts() -> Dict[str, Any]:
    facts: Dict[str, Any] = {"imports": {}, "signatures": {}}
    modules = [
        "AB3DMOT_libs.box",
        "AB3DMOT_libs.model",
        "AB3DMOT_libs.io",
        "AB3DMOT_libs.utils",
        "AB3DMOT_libs.matching",
        "AB3DMOT_libs.kalman_filter",
        "AB3DMOT_libs.kitti_calib",
        "AB3DMOT_libs.kitti_obj",
        "AB3DMOT_libs.kitti_trk",
    ]
    for name in modules:
        try:
            __import__(name)
            facts["imports"][name] = "ok"
        except Exception as exc:  # noqa: BLE001 - report any import blocker.
            facts["imports"][name] = f"FAIL {type(exc).__name__}: {exc}"
    try:
        from AB3DMOT_libs.box import Box3D
        from AB3DMOT_libs.matching import data_association
        from AB3DMOT_libs.model import AB3DMOT

        facts["signatures"] = {
            "Box3D.__init__": str(inspect.signature(Box3D.__init__)),
            "AB3DMOT.__init__": str(inspect.signature(AB3DMOT.__init__)),
            "AB3DMOT.track": str(inspect.signature(AB3DMOT.track)),
            "data_association": str(inspect.signature(data_association)),
        }
    except Exception as exc:  # noqa: BLE001
        facts["signature_error"] = f"{type(exc).__name__}: {exc}"
    return facts


def config_facts(repo_root: Path) -> Dict[str, Any]:
    facts: Dict[str, Any] = {}
    try:
        from AB3DMOT_libs.utils import Config, get_threshold

        for dataset in ["KITTI", "nuScenes"]:
            cfg_path = repo_root / "configs" / f"{dataset}.yml"
            if not cfg_path.exists():
                facts[dataset] = {"error": "config missing"}
                continue
            cfg, _ = Config(str(cfg_path))
            facts[dataset] = {
                "dataset": cfg.dataset,
                "split": cfg.split,
                "det_name": cfg.det_name,
                "cat_list": list(cfg.cat_list),
                "save_root": cfg.save_root,
                "num_hypo": cfg.num_hypo,
                "ego_com": bool(cfg.ego_com),
                "vis": bool(cfg.vis),
                "affi_pro": bool(cfg.affi_pro),
            }
        facts["KITTI_pointrcnn_thresholds"] = get_threshold("KITTI", "pointrcnn")
    except Exception as exc:  # noqa: BLE001
        facts["error"] = f"{type(exc).__name__}: {exc}"
    return facts


def help_check(repo_root: Path, toolbox_root: Optional[Path]) -> Dict[str, Any]:
    commands = {
        "main": [sys.executable, str(repo_root / "main.py"), "--help"],
        "convert_det2input": [sys.executable, str(repo_root / "scripts" / "pre_processing" / "convert_det2input.py"), "--help"],
        "threshold": [sys.executable, str(repo_root / "scripts" / "post_processing" / "trk_conf_threshold.py"), "--help"],
        "visualization": [sys.executable, str(repo_root / "scripts" / "post_processing" / "visualization.py"), "--help"],
        "nuscenes_evaluator": [sys.executable, str(repo_root / "scripts" / "nuScenes" / "evaluate.py"), "--help"],
        "nuscenes_export": [sys.executable, str(repo_root / "scripts" / "nuScenes" / "export_kitti.py"), "--help"],
    }
    env = os.environ.copy()
    path_entries = [str(repo_root)]
    if toolbox_root is not None:
        path_entries.append(str(toolbox_root))
    if env.get("PYTHONPATH"):
        path_entries.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(path_entries)
    results: Dict[str, Any] = {}
    for name, command in commands.items():
        try:
            proc = subprocess.run(command, cwd=repo_root, env=env, text=True, capture_output=True, timeout=30)
            results[name] = {
                "returncode": proc.returncode,
                "stdout_first_line": proc.stdout.splitlines()[0] if proc.stdout.splitlines() else "",
                "stderr_first_line": proc.stderr.splitlines()[0] if proc.stderr.splitlines() else "",
            }
        except Exception as exc:  # noqa: BLE001 - report timeout/spawn failures.
            results[name] = {"error": f"{type(exc).__name__}: {exc}"}
    results["not_checked"] = {
        "kitti_evaluator": "legacy positional CLI has no --help mode; use its documented result_sha/num_hypothesis/dimension invocation",
        "nuScenes_quick_evaluator": "legacy positional CLI has no --help mode; no dataset/evaluation was run",
    }
    return results


def failure_reasons(report: Dict[str, Any]) -> List[str]:
    """Return every critical failure instead of only the first/top-level one."""
    failures = list(report.get("path_errors", []))
    imports = report.get("imports", {})
    failures.extend(
        "import {}: {}".format(name, status)
        for name, status in imports.get("imports", {}).items()
        if isinstance(status, str) and status.startswith("FAIL")
    )
    if imports.get("signature_error"):
        failures.append("imports.signature_error: {}".format(imports["signature_error"]))
    required_signatures = {"Box3D.__init__", "AB3DMOT.__init__", "AB3DMOT.track", "data_association"}
    missing_signatures = required_signatures.difference(imports.get("signatures", {}))
    if missing_signatures:
        failures.append("imports.signatures missing: {}".format(", ".join(sorted(missing_signatures))))

    configs = report.get("configs", {})
    if configs.get("error"):
        failures.append("configs.error: {}".format(configs["error"]))
    for dataset in ("KITTI", "nuScenes"):
        value = configs.get(dataset)
        if not isinstance(value, dict) or value.get("error"):
            failures.append("configs.{}: {}".format(dataset, value.get("error", "config missing or unreadable") if isinstance(value, dict) else "config missing or unreadable"))
    if "KITTI_pointrcnn_thresholds" not in configs:
        failures.append("configs.KITTI_pointrcnn_thresholds: missing")

    for name, result in report.get("help", {}).items():
        if name == "not_checked":
            continue
        if not isinstance(result, dict):
            failures.append("help.{}: invalid result".format(name))
        elif result.get("error") or result.get("returncode") != 0:
            failures.append("help.{}: {}".format(name, result.get("error", "returncode {}".format(result.get("returncode")))))

    smoke = report.get("smoke_track")
    if isinstance(smoke, dict) and smoke.get("status") == "failed":
        failures.append("smoke_track: {}".format(smoke.get("error", "failed")))
    return failures


def smoke_track() -> Dict[str, Any]:
    try:
        import numpy as np
        from easydict import EasyDict as edict
        from AB3DMOT_libs.model import AB3DMOT

        class DummyLog:
            def write(self, _text: str) -> None:
                return None

            def flush(self) -> None:
                return None

        cfg = edict(dataset="KITTI", det_name="pointrcnn", ego_com=False, vis=False, affi_pro=True)
        tracker = AB3DMOT(
            cfg,
            "Car",
            calib=None,
            oxts=None,
            img_dir=None,
            vis_dir=None,
            hw={"image": (375, 1242), "lidar": (720, 1920)},
            log=DummyLog(),
            ID_init=1,
        )
        dets_all = {
            "dets": np.array([[1.5, 1.6, 3.7, 0.0, 1.5, 10.0, 0.0]], dtype=float),
            "info": np.array([[0.0, 0, 0, 50, 50, 0, 9.9]], dtype=float),
        }
        results, affinity = tracker.track(dets_all, 0, "0000")
        return {
            "status": "ok",
            "result_shape": list(results[0].shape),
            "first_track_prefix": [float(x) for x in np.round(results[0][0, :8], 3)],
            "affinity_shape": None if affinity is None else list(affinity.shape),
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    toolbox_root = args.toolbox_root.resolve() if args.toolbox_root else None
    add_paths(repo_root, toolbox_root)
    report: Dict[str, Any] = {
        "path_errors": check_paths(repo_root, toolbox_root),
        "imports": import_facts(),
        "configs": config_facts(repo_root),
        "help": help_check(repo_root, toolbox_root),
    }
    if args.smoke_track:
        report["smoke_track"] = smoke_track()

    failures = failure_reasons(report)
    report["failures"] = failures
    report["status"] = "FAILED" if failures else "OK"

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("AB3DMOT environment check")
        for err in report["path_errors"]:
            print(f"PATH ERROR: {err}")
        print("Imports:")
        for name, status in report["imports"].get("imports", {}).items():
            print(f"  {name}: {status}")
        if report["imports"].get("signatures"):
            print("Signatures:")
            for name, sig in report["imports"]["signatures"].items():
                print(f"  {name}{sig}")
        print("Configs:")
        for name, value in report["configs"].items():
            print(f"  {name}: {value}")
        print("Help checks:")
        for name, value in report["help"].items():
            print(f"  {name}: {value}")
        if "smoke_track" in report:
            print(f"Synthetic smoke: {report['smoke_track']}")
        if failures:
            print("Failures:")
            for failure in failures:
                print(f"  - {failure}")
        print("STATUS:", report["status"])
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
