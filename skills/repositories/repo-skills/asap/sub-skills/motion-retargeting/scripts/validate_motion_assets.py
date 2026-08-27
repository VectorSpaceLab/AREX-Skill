#!/usr/bin/env python3
"""Safe ASAP motion-retargeting asset checker.

This script is intentionally read-only and avoids importing ASAP, Hydra, MuJoCo,
Open3D, or smpl_sim. It checks repository-relative file layout, robot XML
structure, mesh references, raw AMASS/SMPL .npz keys, shape joblib files, and
retargeted motion joblib files before a user launches expensive fitting or GUI
visualization.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


@dataclass
class Finding:
    level: str
    check: str
    message: str
    detail: dict[str, Any] = field(default_factory=dict)


class Report:
    def __init__(self) -> None:
        self.findings: list[Finding] = []

    def add(self, level: str, check: str, message: str, **detail: Any) -> None:
        self.findings.append(Finding(level.upper(), check, message, {k: v for k, v in detail.items() if v is not None}))

    @property
    def errors(self) -> int:
        return sum(1 for item in self.findings if item.level == "ERROR")

    @property
    def warnings(self) -> int:
        return sum(1 for item in self.findings if item.level == "WARN")

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": "ok" if self.errors == 0 else "failed",
            "errors": self.errors,
            "warnings": self.warnings,
            "findings": [item.__dict__ for item in self.findings],
        }

    def print_human(self) -> None:
        for item in self.findings:
            suffix = ""
            if item.detail:
                suffix = " " + json.dumps(item.detail, sort_keys=True, default=str)
            print(f"[{item.level}] {item.check}: {item.message}{suffix}")
        print(f"summary: {'OK' if self.errors == 0 else 'FAILED'} ({self.errors} errors, {self.warnings} warnings)")


def repo_path(repo_root: Path, value: str | Path | None) -> Path | None:
    if value is None:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return repo_root / path


def robot_config_path(repo_root: Path, robot: str) -> Path:
    rel = Path(robot)
    if rel.suffix not in {".yaml", ".yml"}:
        rel = rel.with_suffix(".yaml")
    return repo_root / "humanoidverse" / "config" / "robot" / rel


def try_load_yaml(path: Path, report: Report) -> dict[str, Any] | None:
    try:
        import yaml  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on caller env
        report.add("WARN", "yaml", "PyYAML is not available; using regex fallback for key config fields", error=repr(exc))
        return None
    try:
        data = yaml.safe_load(path.read_text())
    except Exception as exc:
        report.add("ERROR", "robot-config", "failed to parse robot YAML", path=str(path), error=repr(exc))
        return None
    if not isinstance(data, dict):
        report.add("ERROR", "robot-config", "robot YAML did not parse to a mapping", path=str(path))
        return None
    return data


def regex_value(text: str, key: str) -> str | None:
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*:\s*[\"']?([^\"'\n#]+)[\"']?", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return None
    return match.group(1).strip()


def extract_motion_config(path: Path, report: Report) -> dict[str, Any]:
    data = try_load_yaml(path, report)
    if data is not None:
        robot = data.get("robot", {}) if isinstance(data.get("robot", {}), dict) else {}
        motion = robot.get("motion", {}) if isinstance(robot.get("motion", {}), dict) else {}
        asset = motion.get("asset", {}) if isinstance(motion.get("asset", {}), dict) else {}
        return {
            "assetRoot": asset.get("assetRoot"),
            "assetFileName": asset.get("assetFileName"),
            "urdfFileName": asset.get("urdfFileName"),
            "humanoid_type": motion.get("humanoid_type"),
            "motion_file": motion.get("motion_file"),
            "extend_config": motion.get("extend_config") or [],
            "joint_matches": motion.get("joint_matches") or [],
            "body_names": motion.get("body_names") or [],
            "dof_names": motion.get("dof_names") or [],
            "source": "yaml",
        }

    text = path.read_text(errors="replace")
    return {
        "assetRoot": regex_value(text, "assetRoot"),
        "assetFileName": regex_value(text, "assetFileName"),
        "urdfFileName": regex_value(text, "urdfFileName"),
        "humanoid_type": regex_value(text, "humanoid_type"),
        "motion_file": regex_value(text, "motion_file"),
        "extend_config": [],
        "joint_matches": [],
        "body_names": [],
        "dof_names": [],
        "source": "regex",
    }


def check_file(report: Report, check: str, path: Path, required: bool, what: str) -> bool:
    if path.exists():
        report.add("OK", check, f"found {what}", path=str(path))
        return True
    report.add("ERROR" if required else "WARN", check, f"missing {what}", path=str(path))
    return False


def check_robot_assets(repo_root: Path, robot: str, report: Report) -> dict[str, Any]:
    cfg_path = robot_config_path(repo_root, robot)
    if not check_file(report, "robot-config", cfg_path, True, "robot motion config"):
        return {"motor_count": None, "humanoid_type": Path(robot).name}

    cfg = extract_motion_config(cfg_path, report)
    humanoid_type = cfg.get("humanoid_type") or Path(robot).name
    asset_root_text = cfg.get("assetRoot") or ""
    asset_file = cfg.get("assetFileName") or ""
    urdf_file = cfg.get("urdfFileName") or ""

    if not asset_root_text:
        report.add("ERROR", "robot-config", "robot.motion.asset.assetRoot is missing", path=str(cfg_path))
    if not asset_file:
        report.add("ERROR", "robot-config", "robot.motion.asset.assetFileName is missing", path=str(cfg_path))

    asset_root = repo_path(repo_root, asset_root_text) if asset_root_text else None
    xml_path = (asset_root / asset_file) if asset_root is not None and asset_file else None
    urdf_path = (asset_root / urdf_file) if asset_root is not None and urdf_file else None

    motor_count: int | None = None
    body_names: list[str] = []
    if asset_root is not None:
        check_file(report, "robot-assets", asset_root, True, "robot asset root directory")
    if urdf_path is not None:
        check_file(report, "robot-assets", urdf_path, False, "robot URDF")
    if xml_path is None or not check_file(report, "robot-assets", xml_path, True, "MuJoCo XML"):
        return {"motor_count": motor_count, "humanoid_type": humanoid_type, "config": cfg}

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except Exception as exc:
        report.add("ERROR", "robot-xml", "failed to parse MuJoCo XML", path=str(xml_path), error=repr(exc))
        return {"motor_count": motor_count, "humanoid_type": humanoid_type, "config": cfg}

    worldbody = root.find("worldbody")
    if worldbody is None:
        report.add("ERROR", "robot-xml", "XML has no <worldbody>", path=str(xml_path))
    actuator = root.find("actuator")
    if actuator is None:
        report.add("ERROR", "robot-xml", "XML has no <actuator>", path=str(xml_path))

    bodies = root.findall(".//body")
    joints = root.findall(".//joint")
    motors = root.findall(".//motor")
    body_names = [b.attrib.get("name", "") for b in bodies if b.attrib.get("name")]
    joint_names = [j.attrib.get("name", "") for j in joints if j.attrib.get("name")]
    motor_names = [m.attrib.get("name", "") for m in motors if m.attrib.get("name")]
    motor_count = len(motor_names)

    if motor_count <= 0:
        report.add("ERROR", "robot-xml", "XML has no motors; Humanoid_Batch requires actuators", path=str(xml_path))
    else:
        report.add(
            "OK",
            "robot-xml",
            "parsed XML skeleton and actuators",
            path=str(xml_path),
            bodies=len(body_names),
            joints=len(joint_names),
            motors=motor_count,
        )

    missing_motor_joints = [name for name in motor_names if name not in joint_names]
    if missing_motor_joints:
        report.add("WARN", "robot-xml", "some motor names are not joint names", names=missing_motor_joints[:10])

    compiler = root.find("compiler")
    meshdir = compiler.attrib.get("meshdir", "") if compiler is not None else ""
    mesh_base = xml_path.parent / meshdir if meshdir else xml_path.parent
    mesh_files = [m.attrib.get("file") for m in root.findall(".//mesh") if m.attrib.get("file")]
    missing_meshes = [str(mesh_base / mesh_file) for mesh_file in mesh_files if not (mesh_base / mesh_file).exists()]
    if missing_meshes:
        report.add("ERROR", "robot-meshes", "XML references missing mesh files", count=len(missing_meshes), examples=missing_meshes[:10])
    else:
        report.add("OK", "robot-meshes", "all XML mesh references exist", meshdir=meshdir, count=len(mesh_files))

    extend_config = cfg.get("extend_config") if isinstance(cfg.get("extend_config"), list) else []
    extend_names: set[str] = set()
    for item in extend_config:
        if not isinstance(item, dict):
            continue
        joint_name = item.get("joint_name")
        parent_name = item.get("parent_name")
        if joint_name:
            extend_names.add(str(joint_name))
        if parent_name and parent_name not in body_names:
            report.add("ERROR", "robot-config", "extend_config parent_name is not an XML body", parent_name=parent_name)

    joint_matches = cfg.get("joint_matches") if isinstance(cfg.get("joint_matches"), list) else []
    missing_matches = []
    for pair in joint_matches:
        if isinstance(pair, (list, tuple)) and pair:
            robot_name = str(pair[0])
            if robot_name not in body_names and robot_name not in extend_names:
                missing_matches.append(robot_name)
    if missing_matches:
        report.add("ERROR", "robot-config", "joint_matches robot-side names missing from XML bodies and extend_config", names=missing_matches[:20])
    elif joint_matches:
        report.add("OK", "robot-config", "joint_matches robot-side names resolve", count=len(joint_matches))
    else:
        report.add("WARN", "robot-config", "joint_matches were not parsed; install PyYAML for deeper config checks")

    return {
        "motor_count": motor_count,
        "humanoid_type": humanoid_type,
        "config": cfg,
        "xml_path": str(xml_path),
        "body_names": body_names,
    }


def check_smpl(repo_root: Path, report: Report, required: bool) -> None:
    smpl_dir = repo_root / "humanoidverse" / "data" / "smpl"
    if not check_file(report, "smpl-assets", smpl_dir, required, "SMPL directory"):
        return
    expected = ["SMPL_FEMALE.pkl", "SMPL_MALE.pkl", "SMPL_NEUTRAL.pkl"]
    missing = [name for name in expected if not (smpl_dir / name).exists()]
    if missing:
        report.add("ERROR" if required else "WARN", "smpl-assets", "missing SMPL model files", missing=missing, directory=str(smpl_dir))
    else:
        report.add("OK", "smpl-assets", "SMPL model files are present", files=expected)


def check_raw_motion(repo_root: Path, raw_motion_dir: str, report: Report, required: bool, sample_count: int) -> None:
    raw_dir = repo_path(repo_root, raw_motion_dir)
    assert raw_dir is not None
    if not check_file(report, "raw-motion", raw_dir, required, "raw motion directory"):
        return
    files = sorted(raw_dir.glob("*.npz"))
    if not files:
        report.add("ERROR" if required else "WARN", "raw-motion", "no .npz files found", directory=str(raw_dir))
        return
    report.add("OK", "raw-motion", "found raw .npz motion files", directory=str(raw_dir), count=len(files))
    try:
        import numpy as np  # type: ignore
    except Exception as exc:
        report.add("ERROR" if required else "WARN", "raw-motion", "numpy unavailable; cannot inspect .npz keys", error=repr(exc))
        return

    required_keys = {"mocap_framerate", "trans", "poses", "betas", "gender"}
    for path in files[: max(1, sample_count)]:
        try:
            data = np.load(path, allow_pickle=True)
        except Exception as exc:
            report.add("ERROR", "raw-motion", "failed to load raw .npz", path=str(path), error=repr(exc))
            continue
        keys = set(data.files)
        missing = sorted(required_keys - keys)
        if missing:
            report.add("ERROR", "raw-motion", "raw .npz missing required keys", path=str(path), missing=missing)
            continue
        poses = data["poses"]
        trans = data["trans"]
        fps_value = data["mocap_framerate"]
        try:
            fps = float(fps_value.item() if hasattr(fps_value, "item") else fps_value)
        except Exception:
            fps = math.nan
        if getattr(poses, "ndim", 0) != 2 or poses.shape[1] < 66:
            report.add("ERROR", "raw-motion", "poses must have shape (T, >=66)", path=str(path), shape=getattr(poses, "shape", None))
        if getattr(trans, "ndim", 0) != 2 or trans.shape[1] != 3:
            report.add("ERROR", "raw-motion", "trans must have shape (T, 3)", path=str(path), shape=getattr(trans, "shape", None))
        if not math.isfinite(fps) or fps <= 0:
            report.add("ERROR", "raw-motion", "mocap_framerate must be positive", path=str(path), value=str(fps_value))
        elif fps < 30:
            report.add("ERROR", "raw-motion", "mocap_framerate below 30 makes fit_smpl_motion skip=0", path=str(path), fps=fps)
        else:
            report.add("OK", "raw-motion", "raw .npz sample has required keys and basic shapes", path=str(path), frames=int(trans.shape[0]), fps=fps)


def check_shape(repo_root: Path, humanoid_type: str, shape_file: str | None, report: Report, required: bool) -> None:
    default = repo_root / "humanoidverse" / "data" / "shape" / humanoid_type / "shape_optimized_v1.pkl"
    path = repo_path(repo_root, shape_file) if shape_file else default
    assert path is not None
    if not check_file(report, "shape-file", path, required, "shape_optimized_v1.pkl"):
        return
    try:
        import joblib  # type: ignore
    except Exception as exc:
        report.add("WARN", "shape-file", "joblib unavailable; cannot inspect shape file", error=repr(exc))
        return
    try:
        obj = joblib.load(path)
    except Exception as exc:
        report.add("ERROR", "shape-file", "failed to load shape joblib", path=str(path), error=repr(exc))
        return
    if not isinstance(obj, tuple) or len(obj) != 2:
        report.add("ERROR", "shape-file", "shape file should be a tuple (shape_new, scale)", path=str(path), type=type(obj).__name__)
        return
    shape_new, scale = obj
    report.add(
        "OK",
        "shape-file",
        "shape joblib has expected tuple structure",
        path=str(path),
        shape_new_shape=str(getattr(shape_new, "shape", "unknown")),
        scale_shape=str(getattr(scale, "shape", "unknown")),
    )


def as_shape(value: Any) -> tuple[int, ...] | None:
    shape = getattr(value, "shape", None)
    if shape is None:
        return None
    try:
        return tuple(int(x) for x in shape)
    except Exception:
        return None


def check_motion_file(repo_root: Path, motion_file: str | None, report: Report, required: bool, motor_count: int | None, sample_count: int, require_key_matches_file: bool) -> None:
    if not motion_file:
        report.add("ERROR" if required else "WARN", "motion-file", "no motion file path was provided")
        return
    path = repo_path(repo_root, motion_file)
    assert path is not None
    if not check_file(report, "motion-file", path, required, "retargeted motion joblib"):
        return
    try:
        import joblib  # type: ignore
    except Exception as exc:
        report.add("ERROR" if required else "WARN", "motion-file", "joblib unavailable; cannot inspect motion file", error=repr(exc))
        return
    try:
        data = joblib.load(path)
    except Exception as exc:
        report.add("ERROR", "motion-file", "failed to load motion joblib", path=str(path), error=repr(exc))
        return
    if not isinstance(data, dict) or not data:
        report.add("ERROR", "motion-file", "motion joblib should be a non-empty dictionary", path=str(path), type=type(data).__name__)
        return
    keys = list(data.keys())
    report.add("OK", "motion-file", "loaded top-level motion dictionary", path=str(path), keys=keys[:10], count=len(keys))
    if require_key_matches_file and path.is_file() and path.suffix == ".pkl" and path.stem not in data:
        report.add("ERROR", "motion-file", "top-level key does not match file stem for MotionLib directory mode", file_stem=path.stem, keys=keys[:10])

    required_keys = {"root_trans_offset", "pose_aa", "dof", "root_rot", "fps"}
    for key in keys[: max(1, sample_count)]:
        entry = data[key]
        if not isinstance(entry, dict):
            report.add("ERROR", "motion-entry", "motion entry should be a dictionary", key=key, type=type(entry).__name__)
            continue
        missing = sorted(required_keys - set(entry.keys()))
        if missing:
            report.add("ERROR", "motion-entry", "motion entry missing required keys", key=key, missing=missing)
            continue
        root_trans_shape = as_shape(entry["root_trans_offset"])
        pose_shape = as_shape(entry["pose_aa"])
        dof_shape = as_shape(entry["dof"])
        root_rot_shape = as_shape(entry["root_rot"])
        fps = entry["fps"]
        frames = root_trans_shape[0] if root_trans_shape else None

        if root_trans_shape is None or len(root_trans_shape) != 2 or root_trans_shape[1] != 3:
            report.add("ERROR", "motion-entry", "root_trans_offset must have shape (T, 3)", key=key, shape=root_trans_shape)
        if pose_shape is None or len(pose_shape) != 3 or pose_shape[0] != frames or pose_shape[2] != 3:
            report.add("ERROR", "motion-entry", "pose_aa must have shape (T, J, 3) and match frame count", key=key, shape=pose_shape, frames=frames)
        if dof_shape is None or len(dof_shape) != 2 or dof_shape[0] != frames:
            report.add("ERROR", "motion-entry", "dof must have shape (T, num_motors) and match frame count", key=key, shape=dof_shape, frames=frames)
        elif motor_count is not None and dof_shape[1] != motor_count:
            report.add("ERROR", "motion-entry", "dof column count does not match XML motor count", key=key, dof_columns=dof_shape[1], motors=motor_count)
        if root_rot_shape is None or len(root_rot_shape) != 2 or root_rot_shape[0] != frames or root_rot_shape[1] != 4:
            report.add("ERROR", "motion-entry", "root_rot must have shape (T, 4) and match frame count", key=key, shape=root_rot_shape, frames=frames)
        if not isinstance(fps, (int, float)) or float(fps) <= 0:
            report.add("ERROR", "motion-entry", "fps must be a positive number", key=key, fps=fps)
        if "action" in entry:
            action_shape = as_shape(entry["action"])
            if action_shape is None or len(action_shape) < 1 or action_shape[0] != frames:
                report.add("ERROR", "motion-entry", "optional action key must have leading frame dimension T", key=key, shape=action_shape, frames=frames)
        if "smpl_joints" in entry:
            smpl_shape = as_shape(entry["smpl_joints"])
            if smpl_shape is None or len(smpl_shape) != 3 or smpl_shape[0] != frames or smpl_shape[2] != 3:
                report.add("WARN", "motion-entry", "smpl_joints should have shape (T, J, 3)", key=key, shape=smpl_shape, frames=frames)

        report.add(
            "OK",
            "motion-entry",
            "motion entry has expected required keys and basic shapes",
            key=key,
            frames=frames,
            dof_shape=dof_shape,
            pose_shape=pose_shape,
            fps=fps,
        )


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate ASAP motion-retargeting assets without running fitting or visualization.")
    parser.add_argument("--repo-root", default=".", help="ASAP repository root (default: current directory).")
    parser.add_argument("--robot", default="g1/g1_29dof_anneal_23dof", help="Hydra robot config id under humanoidverse/config/robot, without .yaml.")
    parser.add_argument("--require-smpl", action="store_true", help="Treat missing SMPL model files as errors instead of warnings.")
    parser.add_argument("--check-raw", action="store_true", help="Inspect raw .npz files under --raw-motion-dir.")
    parser.add_argument("--require-raw", action="store_true", help="Require raw .npz files; implies --check-raw.")
    parser.add_argument("--raw-motion-dir", default="humanoidverse/data/motions/raw_tairantestbed_smpl", help="Raw .npz motion directory used by unmodified fit_smpl_motion.py.")
    parser.add_argument("--require-shape", action="store_true", help="Require and inspect shape_optimized_v1.pkl.")
    parser.add_argument("--shape-file", default=None, help="Override shape file path; default derives from robot.motion.humanoid_type.")
    parser.add_argument("--motion-file", default=None, help="Retargeted motion .pkl file to inspect.")
    parser.add_argument("--require-motion", action="store_true", help="Require --motion-file and validate its structure.")
    parser.add_argument("--require-key-matches-file", action="store_true", help="Require top-level motion key to match the .pkl file stem for MotionLib directory mode.")
    parser.add_argument("--sample-count", type=int, default=3, help="Number of raw/motion samples to inspect per category (default: 3).")
    parser.add_argument("--json", action="store_true", help="Emit JSON report.")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] = sys.argv[1:]) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    report = Report()

    check_file(report, "repo-root", repo_root, True, "ASAP repo root")
    robot_info = check_robot_assets(repo_root, args.robot, report)
    humanoid_type = str(robot_info.get("humanoid_type") or Path(args.robot).name)
    motor_count = robot_info.get("motor_count")
    if not isinstance(motor_count, int):
        motor_count = None

    # Missing licensed SMPL files are warnings by default so the checker can still
    # pass on a checkout that only uses already-retargeted motions.
    check_smpl(repo_root, report, required=bool(args.require_smpl))

    if args.check_raw or args.require_raw:
        check_raw_motion(repo_root, args.raw_motion_dir, report, required=bool(args.require_raw), sample_count=args.sample_count)

    if args.require_shape or args.shape_file:
        check_shape(repo_root, humanoid_type, args.shape_file, report, required=bool(args.require_shape))

    if args.motion_file or args.require_motion:
        check_motion_file(
            repo_root,
            args.motion_file,
            report,
            required=bool(args.require_motion),
            motor_count=motor_count,
            sample_count=args.sample_count,
            require_key_matches_file=bool(args.require_key_matches_file),
        )

    if args.json:
        print(json.dumps(report.as_dict(), indent=2, sort_keys=True, default=str))
    else:
        report.print_human()
    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
